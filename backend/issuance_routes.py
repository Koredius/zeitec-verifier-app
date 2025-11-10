from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import (db, IssuanceSubmission, Device, Registrant, DeduplicationLog, 
                    VerifierReview, Admin, AuditTrail)
from utils import (allowed_file, save_uploaded_file, validate_issuance_period_csv,
                   check_duplicates, create_verifier_checklist)
import os

issuance_bp = Blueprint('issuance', __name__, url_prefix='/api/issuance')


@issuance_bp.route('/submit', methods=['POST'])
def submit_issuance():
    """
    Registrant endpoint - Submit issuance period CSV
    Form data:
        - registrant_email (required)
        - device_id (required - the database device ID)
        - issuance_period_csv (required file)
        - registrant_declaration (optional file)
    """
    # Get form data
    registrant_email = request.form.get('registrant_email')
    device_id = request.form.get('device_id', type=int)
    
    if not registrant_email or not device_id:
        return jsonify({'error': 'registrant_email and device_id are required'}), 400
    
    # Find registrant
    registrant = Registrant.query.filter_by(email=registrant_email).first()
    
    if not registrant:
        return jsonify({'error': 'Registrant not found'}), 404
    
    if registrant.status != 'approved':
        return jsonify({'error': f'Registrant must be approved. Current status: {registrant.status}'}), 403
    
    # Find device
    device = Device.query.get(device_id)
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    if device.registrant_id != registrant.id:
        return jsonify({'error': 'Device does not belong to this registrant'}), 403
    
    if device.status != 'approved':
        return jsonify({'error': f'Device must be approved. Current status: {device.status}'}), 403
    
    # Check for CSV file
    if 'issuance_period_csv' not in request.files:
        return jsonify({'error': 'issuance_period_csv file is required'}), 400
    
    csv_file = request.files['issuance_period_csv']
    
    if not csv_file or not csv_file.filename:
        return jsonify({'error': 'issuance_period_csv file is required'}), 400
    
    if not allowed_file(csv_file.filename, {'csv'}):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    # Save CSV file
    csv_path, csv_hash, csv_size = save_uploaded_file(
        csv_file,
        current_app.config['UPLOAD_FOLDER'],
        f'issuance/{registrant.id}/{device_id}'
    )
    
    # Validate CSV
    validation_result = validate_issuance_period_csv(
        csv_path,
        current_app.config['REQUIRED_ISSUANCE_PERIOD_COLUMNS']
    )
    
    if not validation_result['valid']:
        # Delete uploaded file if validation fails
        os.remove(csv_path)
        return jsonify({
            'error': 'CSV validation failed',
            'errors': validation_result['errors']
        }), 400
    
    # Check for duplicates
    existing_audit_trail_ids = [
        log.audit_trail_id 
        for log in DeduplicationLog.query.all()
    ]
    
    duplicate_check = check_duplicates(
        validation_result['audit_trail_ids'],
        existing_audit_trail_ids
    )
    
    # Determine status based on duplicate check
    if duplicate_check['has_duplicates']:
        submission_status = 'duplicate_detected'
    else:
        submission_status = 'pending'
    
    # Handle registrant declaration file
    declaration_path = None
    if 'registrant_declaration' in request.files:
        file = request.files['registrant_declaration']
        if file and file.filename:
            if allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                declaration_path, _, _ = save_uploaded_file(
                    file,
                    current_app.config['UPLOAD_FOLDER'],
                    f'issuance/{registrant.id}/{device_id}'
                )
    
    # Create issuance submission
    submission = IssuanceSubmission(
        registrant_id=registrant.id,
        device_id=device_id,
        issuance_period_start=validation_result['summary']['period_start'],
        issuance_period_end=validation_result['summary']['period_end'],
        total_kwh=validation_result['summary']['total_kwh'],
        num_readings=validation_result['summary']['total_rows'],
        csv_file_path=csv_path,
        csv_hash=csv_hash,
        registrant_declaration_path=declaration_path,
        status=submission_status,
        submitted_by=registrant_email,
        deduplication_result=duplicate_check
    )
    
    db.session.add(submission)
    db.session.flush()  # Get submission ID
    
    # Store audit trail IDs (only if no duplicates)
    if not duplicate_check['has_duplicates']:
        df = validation_result['data']
        for _, row in df.iterrows():
            dedupe_log = DeduplicationLog(
                audit_trail_id=row['auditTrailId'],
                device_id=str(row['deviceId']),
                timestamp=row['timestamp'],
                kwh=float(row['kWh']),
                issuance_submission_id=submission.id
            )
            db.session.add(dedupe_log)
    
    db.session.commit()
    
    response_data = {
        'message': 'Issuance submission created successfully',
        'submission_id': submission.id,
        'status': submission_status,
        'deduplication_check': duplicate_check,
        'summary': validation_result['summary']
    }
    
    if duplicate_check['has_duplicates']:
        response_data['warning'] = f"⚠️ {duplicate_check['duplicate_count']} duplicate auditTrailIds found. Submission marked for review."
    
    return jsonify(response_data), 201


@issuance_bp.route('/', methods=['GET'])
@jwt_required()
def list_submissions():
    """
    Verifier/Admin endpoint - List all issuance submissions
    Query params: status, registrant_id, device_id, page, per_page
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', current_app.config['ITEMS_PER_PAGE'], type=int)
    
    query = IssuanceSubmission.query
    
    # Filters
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    
    registrant_id = request.args.get('registrant_id', type=int)
    if registrant_id:
        query = query.filter_by(registrant_id=registrant_id)
    
    device_id = request.args.get('device_id', type=int)
    if device_id:
        query = query.filter_by(device_id=device_id)
    
    # Order by created_at desc
    query = query.order_by(IssuanceSubmission.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'submissions': [s.to_dict() for s in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@issuance_bp.route('/<int:submission_id>', methods=['GET'])
@jwt_required()
def get_submission(submission_id):
    """
    Verifier/Admin endpoint - Get issuance submission details with evidence package
    """
    submission = IssuanceSubmission.query.get(submission_id)
    
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404
    
    submission_data = submission.to_dict()
    
    # Add device details
    device = submission.device
    submission_data['device'] = device.to_dict()
    submission_data['device_documents'] = [doc.to_dict() for doc in device.documents]
    
    # Add registrant details
    submission_data['registrant'] = submission.registrant.to_dict()
    
    # Add verifier review if exists
    if submission.verifier_review:
        submission_data['verifier_review'] = submission.verifier_review.to_dict()
    
    return jsonify(submission_data), 200


@issuance_bp.route('/<int:submission_id>/review', methods=['POST'])
@jwt_required()
def create_review(submission_id):
    """
    Verifier endpoint - Create verifier review (approve or reject)
    Body: {
        "decision": "approved" | "rejected",
        "review_notes": "optional notes",
        "checklist": { ... verifier checklist object ... },
        "measurement_tier": "2.3",
        "device_scope_confirmed": true,
        "grouping_keys_consistent": true,
        "no_dedupe_collisions": true
    }
    """
    current_user_id = get_jwt_identity()
    submission = IssuanceSubmission.query.get(submission_id)
    
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404
    
    if submission.status not in ['pending', 'under_review']:
        return jsonify({'error': f'Cannot review submission with status: {submission.status}'}), 400
    
    data = request.get_json()
    
    if not data or not data.get('decision'):
        return jsonify({'error': 'decision is required (approved or rejected)'}), 400
    
    decision = data.get('decision')
    
    if decision not in ['approved', 'rejected']:
        return jsonify({'error': 'decision must be "approved" or "rejected"'}), 400
    
    # Get or create checklist
    checklist = data.get('checklist', create_verifier_checklist())
    
    # Create verifier review
    review = VerifierReview(
        issuance_submission_id=submission_id,
        verifier_id=current_user_id,
        decision=decision,
        review_notes=data.get('review_notes'),
        checklist=checklist,
        measurement_tier=data.get('measurement_tier', '2.3'),
        device_scope_confirmed=data.get('device_scope_confirmed', False),
        grouping_keys_consistent=data.get('grouping_keys_consistent', False),
        no_dedupe_collisions=data.get('no_dedupe_collisions', False)
    )
    
    # Update submission status
    if decision == 'approved':
        submission.status = 'approved'
        # Issue Verifier VC
        review.verifier_vc_issued = True
        review.verifier_vc_data = {
            'issuer': 'Zeitec Verifier',
            'issued_at': datetime.utcnow().isoformat(),
            'measurement_tier': review.measurement_tier,
            'device_scope': f"≤{current_app.config['MAX_DEVICE_CAPACITY_KW']} kW",
            'submission_id': submission_id,
            'total_kwh': float(submission.total_kwh),
            'period_start': submission.issuance_period_start.isoformat(),
            'period_end': submission.issuance_period_end.isoformat()
        }
    else:
        submission.status = 'rejected'
    
    submission.verifier_review_id = review.id
    
    db.session.add(review)
    
    # Audit log
    audit = AuditTrail(
        action_type=f'verifier_{decision}',
        entity_type='issuance_submission',
        entity_id=submission_id,
        performed_by=current_user_id,
        action_details={
            'decision': decision,
            'total_kwh': float(submission.total_kwh),
            'device_id': submission.device.device_id
        },
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    db.session.add(audit)
    db.session.commit()
    
    return jsonify({
        'message': f'Submission {decision} successfully',
        'review': review.to_dict(),
        'submission': submission.to_dict()
    }), 201


@issuance_bp.route('/<int:submission_id>/csv/download', methods=['GET'])
@jwt_required()
def download_csv(submission_id):
    """
    Verifier/Admin endpoint - Download issuance period CSV
    """
    submission = IssuanceSubmission.query.get(submission_id)
    
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404
    
    if not os.path.exists(submission.csv_file_path):
        return jsonify({'error': 'CSV file not found on server'}), 404
    
    return send_file(
        submission.csv_file_path, 
        as_attachment=True, 
        download_name=f'issuance_period_{submission_id}.csv'
    )


@issuance_bp.route('/<int:submission_id>/declaration/download', methods=['GET'])
@jwt_required()
def download_declaration(submission_id):
    """
    Verifier/Admin endpoint - Download registrant declaration
    """
    submission = IssuanceSubmission.query.get(submission_id)
    
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404
    
    if not submission.registrant_declaration_path:
        return jsonify({'error': 'No declaration file uploaded'}), 404
    
    if not os.path.exists(submission.registrant_declaration_path):
        return jsonify({'error': 'Declaration file not found on server'}), 404
    
    return send_file(
        submission.registrant_declaration_path,
        as_attachment=True,
        download_name=f'registrant_declaration_{submission_id}.pdf'
    )


@issuance_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    Verifier/Admin endpoint - Get issuance statistics
    """
    total = IssuanceSubmission.query.count()
    pending = IssuanceSubmission.query.filter_by(status='pending').count()
    approved = IssuanceSubmission.query.filter_by(status='approved').count()
    rejected = IssuanceSubmission.query.filter_by(status='rejected').count()
    duplicate_detected = IssuanceSubmission.query.filter_by(status='duplicate_detected').count()
    
    total_kwh = db.session.query(
        db.func.sum(IssuanceSubmission.total_kwh)
    ).filter(IssuanceSubmission.status == 'approved').scalar() or 0
    
    # Recent submissions
    recent = IssuanceSubmission.query.order_by(
        IssuanceSubmission.created_at.desc()
    ).limit(10).all()
    
    return jsonify({
        'total': total,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'duplicate_detected': duplicate_detected,
        'total_approved_kwh': float(total_kwh),
        'recent_submissions': [
            {
                'id': s.id,
                'registrant_name': s.registrant.organization_name,
                'device_info': f"{s.device.device_id}",
                'total_kwh': float(s.total_kwh),
                'status': s.status,
                'created_at': s.created_at.isoformat()
            }
            for s in recent
        ]
    }), 200
