from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db, Registrant, Admin, AuditTrail
from utils import allowed_file, save_uploaded_file, validate_email
from sqlalchemy import or_

registrant_bp = Blueprint('registrant', __name__, url_prefix='/api/registrants')


@registrant_bp.route('/apply', methods=['POST'])
def apply():
    """
    Public endpoint - Registrant application
    Form data: organization_name, contact_person, email, phone, country, 
               num_facilities, total_capacity_kw, description, business_document (file)
    """
    # Get form data
    data = request.form
    
    # Validate required fields
    required_fields = ['organization_name', 'contact_person', 'email', 'country']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
    
    # Validate email
    if not validate_email(data.get('email')):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Check if email already exists
    existing = Registrant.query.filter_by(email=data.get('email')).first()
    if existing:
        return jsonify({'error': 'Email already registered'}), 409
    
    # Validate country
    if data.get('country') not in current_app.config['ALLOWED_COUNTRIES']:
        return jsonify({'error': 'Invalid country. Must be one of: Nigeria, Benin, Ghana, Kenya, South Africa'}), 400
    
    # Handle file upload
    business_doc_url = None
    if 'business_document' in request.files:
        file = request.files['business_document']
        if file and file.filename:
            if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                return jsonify({'error': 'Invalid file type'}), 400
            
            file_path, file_hash, file_size = save_uploaded_file(
                file, 
                current_app.config['UPLOAD_FOLDER'],
                'registrant_docs'
            )
            business_doc_url = file_path
    
    # Create registrant
    registrant = Registrant(
        organization_name=data.get('organization_name'),
        contact_person=data.get('contact_person'),
        email=data.get('email'),
        phone=data.get('phone'),
        country=data.get('country'),
        num_facilities=int(data.get('num_facilities')) if data.get('num_facilities') else None,
        total_capacity_kw=float(data.get('total_capacity_kw')) if data.get('total_capacity_kw') else None,
        description=data.get('description'),
        business_doc_url=business_doc_url,
        status='pending'
    )
    
    db.session.add(registrant)
    db.session.commit()
    
    return jsonify({
        'message': 'Application submitted successfully',
        'registrant': registrant.to_dict()
    }), 201


@registrant_bp.route('/status/<email>', methods=['GET'])
def check_status(email):
    """
    Public endpoint - Check application status by email
    """
    registrant = Registrant.query.filter_by(email=email).first()
    
    if not registrant:
        return jsonify({'error': 'No application found with this email'}), 404
    
    return jsonify({
        'status': registrant.status,
        'organization_name': registrant.organization_name,
        'submitted_at': registrant.created_at.isoformat(),
        'reviewed_at': registrant.reviewed_at.isoformat() if registrant.reviewed_at else None
    }), 200


@registrant_bp.route('/', methods=['GET'])
@jwt_required()
def list_registrants():
    """
    Admin endpoint - List all registrants with filtering
    Query params: status, country, page, per_page, search
    """
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', current_app.config['ITEMS_PER_PAGE'], type=int)
    
    # Build query
    query = Registrant.query
    
    # Filter by status
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    
    # Filter by country
    country = request.args.get('country')
    if country:
        query = query.filter_by(country=country)
    
    # Search
    search = request.args.get('search')
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            or_(
                Registrant.organization_name.ilike(search_pattern),
                Registrant.contact_person.ilike(search_pattern),
                Registrant.email.ilike(search_pattern)
            )
        )
    
    # Order by created_at desc
    query = query.order_by(Registrant.created_at.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'registrants': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@registrant_bp.route('/<int:registrant_id>', methods=['GET'])
@jwt_required()
def get_registrant(registrant_id):
    """
    Admin endpoint - Get single registrant details
    """
    registrant = Registrant.query.get(registrant_id)
    
    if not registrant:
        return jsonify({'error': 'Registrant not found'}), 404
    
    return jsonify(registrant.to_dict()), 200


@registrant_bp.route('/<int:registrant_id>/approve', methods=['PUT'])
@jwt_required()
def approve_registrant(registrant_id):
    """
    Admin endpoint - Approve registrant
    Body: { "notes": "optional notes" }
    """
    current_user_id = get_jwt_identity()
    registrant = Registrant.query.get(registrant_id)
    
    if not registrant:
        return jsonify({'error': 'Registrant not found'}), 404
    
    if registrant.status != 'pending':
        return jsonify({'error': f'Cannot approve registrant with status: {registrant.status}'}), 400
    
    data = request.get_json() or {}
    
    # Update registrant
    registrant.status = 'approved'
    registrant.reviewed_at = datetime.utcnow()
    registrant.reviewed_by = current_user_id
    registrant.reviewer_notes = data.get('notes')
    
    # Create audit log
    audit = AuditTrail(
        action_type='approve',
        entity_type='registrant',
        entity_id=registrant_id,
        performed_by=current_user_id,
        action_details={'notes': data.get('notes')},
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    db.session.add(audit)
    db.session.commit()
    
    return jsonify({
        'message': 'Registrant approved successfully',
        'registrant': registrant.to_dict()
    }), 200


@registrant_bp.route('/<int:registrant_id>/reject', methods=['PUT'])
@jwt_required()
def reject_registrant(registrant_id):
    """
    Admin endpoint - Reject registrant
    Body: { "notes": "required rejection reason" }
    """
    current_user_id = get_jwt_identity()
    registrant = Registrant.query.get(registrant_id)
    
    if not registrant:
        return jsonify({'error': 'Registrant not found'}), 404
    
    if registrant.status != 'pending':
        return jsonify({'error': f'Cannot reject registrant with status: {registrant.status}'}), 400
    
    data = request.get_json()
    
    if not data or not data.get('notes'):
        return jsonify({'error': 'Rejection reason (notes) is required'}), 400
    
    # Update registrant
    registrant.status = 'rejected'
    registrant.reviewed_at = datetime.utcnow()
    registrant.reviewed_by = current_user_id
    registrant.reviewer_notes = data.get('notes')
    
    # Create audit log
    audit = AuditTrail(
        action_type='reject',
        entity_type='registrant',
        entity_id=registrant_id,
        performed_by=current_user_id,
        action_details={'notes': data.get('notes')},
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    db.session.add(audit)
    db.session.commit()
    
    return jsonify({
        'message': 'Registrant rejected',
        'registrant': registrant.to_dict()
    }), 200


@registrant_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    Admin endpoint - Get registrant statistics
    """
    total = Registrant.query.count()
    pending = Registrant.query.filter_by(status='pending').count()
    approved = Registrant.query.filter_by(status='approved').count()
    rejected = Registrant.query.filter_by(status='rejected').count()
    
    by_country = db.session.query(
        Registrant.country,
        db.func.count(Registrant.id)
    ).group_by(Registrant.country).all()
    
    return jsonify({
        'total': total,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'by_country': {country: count for country, count in by_country}
    }), 200
