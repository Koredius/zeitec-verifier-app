from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db, Device, Registrant, DeviceDocument, Admin, AuditTrail
from utils import (allowed_file, save_uploaded_file, validate_device_registry_csv,
                   calculate_file_hash)
import os

device_bp = Blueprint('device', __name__, url_prefix='/api/devices')


@device_bp.route('/submit', methods=['POST'])
def submit_device_registry():
    """
    Registrant endpoint - Submit device registry CSV with supporting documents
    Form data: 
        - registrant_email (required)
        - device_registry_csv (required file)
        - owner_declaration (optional file)
        - single_line_diagram (optional file)
        - ppa (optional file)
        - site_photos (optional files, multiple)
    """
    # Get registrant email
    registrant_email = request.form.get('registrant_email')
    
    if not registrant_email:
        return jsonify({'error': 'registrant_email is required'}), 400
    
    # Find registrant
    registrant = Registrant.query.filter_by(email=registrant_email).first()
    
    if not registrant:
        return jsonify({'error': 'Registrant not found'}), 404
    
    if registrant.status != 'approved':
        return jsonify({'error': f'Registrant must be approved. Current status: {registrant.status}'}), 403
    
    # Check for CSV file
    if 'device_registry_csv' not in request.files:
        return jsonify({'error': 'device_registry_csv file is required'}), 400
    
    csv_file = request.files['device_registry_csv']
    
    if not csv_file or not csv_file.filename:
        return jsonify({'error': 'device_registry_csv file is required'}), 400
    
    if not allowed_file(csv_file.filename, {'csv'}):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    # Save CSV file
    csv_path, csv_hash, csv_size = save_uploaded_file(
        csv_file,
        current_app.config['UPLOAD_FOLDER'],
        f'device_registry/{registrant.id}'
    )
    
    # Validate CSV
    validation_result = validate_device_registry_csv(
        csv_path,
        current_app.config['REQUIRED_DEVICE_REGISTRY_COLUMNS'],
        current_app.config['MAX_DEVICE_CAPACITY_KW']
    )
    
    if not validation_result['valid']:
        # Delete uploaded file if validation fails
        os.remove(csv_path)
        return jsonify({
            'error': 'CSV validation failed',
            'errors': validation_result['errors']
        }), 400
    
    # Create device records
    devices_created = []
    df = validation_result['data']
    
    for _, row in df.iterrows():
        device = Device(
            registrant_id=registrant.id,
            device_id=str(row['deviceId']),
            facility_id=str(row['facilityId']),
            serial_number=str(row.get('serialNumber', '')),
            manufacturer=str(row.get('manufacturer', '')),
            model=str(row.get('model', '')),
            capacity_kw=float(row['capacityKW']),
            technology=str(row.get('technology', '')),
            country=str(row['country']),
            grid_connection_point=str(row.get('gridConnectionPoint', '')),
            commissioning_date=row.get('commissioningDate'),
            status='pending'
        )
        
        # Calculate device hash
        device_data = f"{device.device_id}{device.facility_id}{device.serial_number}"
        from utils import calculate_sha256
        device.device_hash = calculate_sha256(device_data)
        
        db.session.add(device)
        db.session.flush()  # Get device ID
        
        devices_created.append(device.id)
    
    # Handle supporting documents
    document_types = {
        'owner_declaration': 'owner_declaration',
        'single_line_diagram': 'single_line_diagram',
        'ppa': 'ppa'
    }
    
    for form_field, doc_type in document_types.items():
        if form_field in request.files:
            file = request.files[form_field]
            if file and file.filename:
                if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                    continue
                
                file_path, file_hash, file_size = save_uploaded_file(
                    file,
                    current_app.config['UPLOAD_FOLDER'],
                    f'device_docs/{registrant.id}'
                )
                
                # Associate with all devices in this submission
                for device_id in devices_created:
                    doc = DeviceDocument(
                        device_id=device_id,
                        document_type=doc_type,
                        file_name=file.filename,
                        file_path=file_path,
                        file_hash=file_hash,
                        file_size=file_size,
                        mime_type=file.mimetype
                    )
                    db.session.add(doc)
    
    # Handle multiple site photos
    if 'site_photos' in request.files:
        photos = request.files.getlist('site_photos')
        for photo in photos:
            if photo and photo.filename:
                if not allowed_file(photo.filename, current_app.config['ALLOWED_EXTENSIONS']):
                    continue
                
                file_path, file_hash, file_size = save_uploaded_file(
                    photo,
                    current_app.config['UPLOAD_FOLDER'],
                    f'device_docs/{registrant.id}'
                )
                
                # Associate with all devices
                for device_id in devices_created:
                    doc = DeviceDocument(
                        device_id=device_id,
                        document_type='site_photo',
                        file_name=photo.filename,
                        file_path=file_path,
                        file_hash=file_hash,
                        file_size=file_size,
                        mime_type=photo.mimetype
                    )
                    db.session.add(doc)
    
    db.session.commit()
    
    return jsonify({
        'message': f'Successfully submitted {len(devices_created)} devices',
        'devices_count': len(devices_created),
        'validation_summary': validation_result['summary']
    }), 201


@device_bp.route('/', methods=['GET'])
@jwt_required()
def list_devices():
    """
    Admin endpoint - List all devices with filtering
    Query params: status, registrant_id, country, page, per_page
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', current_app.config['ITEMS_PER_PAGE'], type=int)
    
    query = Device.query
    
    # Filters
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    
    registrant_id = request.args.get('registrant_id', type=int)
    if registrant_id:
        query = query.filter_by(registrant_id=registrant_id)
    
    country = request.args.get('country')
    if country:
        query = query.filter_by(country=country)
    
    # Order by created_at desc
    query = query.order_by(Device.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'devices': [d.to_dict() for d in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@device_bp.route('/<int:device_id>', methods=['GET'])
@jwt_required()
def get_device(device_id):
    """
    Admin endpoint - Get device details with documents
    """
    device = Device.query.get(device_id)
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    device_data = device.to_dict()
    device_data['documents'] = [doc.to_dict() for doc in device.documents]
    
    return jsonify(device_data), 200


@device_bp.route('/<int:device_id>/approve', methods=['PUT'])
@jwt_required()
def approve_device(device_id):
    """
    Admin endpoint - Approve device
    Body: { "notes": "optional notes" }
    """
    current_user_id = get_jwt_identity()
    device = Device.query.get(device_id)
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    if device.status != 'pending':
        return jsonify({'error': f'Cannot approve device with status: {device.status}'}), 400
    
    data = request.get_json() or {}
    
    device.status = 'approved'
    device.reviewed_at = datetime.utcnow()
    device.reviewed_by = current_user_id
    device.reviewer_notes = data.get('notes')
    
    # Audit log
    audit = AuditTrail(
        action_type='approve',
        entity_type='device',
        entity_id=device_id,
        performed_by=current_user_id,
        action_details={'device_id': device.device_id, 'facility_id': device.facility_id},
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    db.session.add(audit)
    db.session.commit()
    
    return jsonify({
        'message': 'Device approved successfully',
        'device': device.to_dict()
    }), 200


@device_bp.route('/<int:device_id>/reject', methods=['PUT'])
@jwt_required()
def reject_device(device_id):
    """
    Admin endpoint - Reject device
    Body: { "notes": "required rejection reason" }
    """
    current_user_id = get_jwt_identity()
    device = Device.query.get(device_id)
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    if device.status != 'pending':
        return jsonify({'error': f'Cannot reject device with status: {device.status}'}), 400
    
    data = request.get_json()
    
    if not data or not data.get('notes'):
        return jsonify({'error': 'Rejection reason (notes) is required'}), 400
    
    device.status = 'rejected'
    device.reviewed_at = datetime.utcnow()
    device.reviewed_by = current_user_id
    device.reviewer_notes = data.get('notes')
    
    # Audit log
    audit = AuditTrail(
        action_type='reject',
        entity_type='device',
        entity_id=device_id,
        performed_by=current_user_id,
        action_details={'device_id': device.device_id, 'notes': data.get('notes')},
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    db.session.add(audit)
    db.session.commit()
    
    return jsonify({
        'message': 'Device rejected',
        'device': device.to_dict()
    }), 200


@device_bp.route('/documents/<int:doc_id>/download', methods=['GET'])
@jwt_required()
def download_document(doc_id):
    """
    Admin endpoint - Download device document
    """
    doc = DeviceDocument.query.get(doc_id)
    
    if not doc:
        return jsonify({'error': 'Document not found'}), 404
    
    if not os.path.exists(doc.file_path):
        return jsonify({'error': 'File not found on server'}), 404
    
    return send_file(doc.file_path, as_attachment=True, download_name=doc.file_name)


@device_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    Admin endpoint - Get device statistics
    """
    total = Device.query.count()
    pending = Device.query.filter_by(status='pending').count()
    approved = Device.query.filter_by(status='approved').count()
    rejected = Device.query.filter_by(status='rejected').count()
    
    total_capacity = db.session.query(db.func.sum(Device.capacity_kw)).scalar() or 0
    
    by_country = db.session.query(
        Device.country,
        db.func.count(Device.id),
        db.func.sum(Device.capacity_kw)
    ).group_by(Device.country).all()
    
    return jsonify({
        'total': total,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'total_capacity_kw': float(total_capacity),
        'by_country': [
            {
                'country': country,
                'count': count,
                'total_capacity_kw': float(capacity) if capacity else 0
            }
            for country, count, capacity in by_country
        ]
    }), 200
