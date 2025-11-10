from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB, INET

db = SQLAlchemy()


# ============================================
# PHASE 1: REGISTRANT MANAGEMENT
# ============================================

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    reviewed_registrants = db.relationship('Registrant', back_populates='reviewer', foreign_keys='Registrant.reviewed_by')
    reviewed_devices = db.relationship('Device', back_populates='reviewer', foreign_keys='Device.reviewed_by')
    verifier_reviews = db.relationship('VerifierReview', back_populates='verifier')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Registrant(db.Model):
    __tablename__ = 'registrants'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    country = db.Column(db.String(50), nullable=False)
    num_facilities = db.Column(db.Integer)
    total_capacity_kw = db.Column(db.Numeric(10, 2))
    description = db.Column(db.Text)
    business_doc_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    reviewer_notes = db.Column(db.Text)
    guardian_did = db.Column(db.String(255))
    
    # Relationships
    reviewer = db.relationship('Admin', back_populates='reviewed_registrants', foreign_keys=[reviewed_by])
    devices = db.relationship('Device', back_populates='registrant', cascade='all, delete-orphan')
    issuance_submissions = db.relationship('IssuanceSubmission', back_populates='registrant', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'organization_name': self.organization_name,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'country': self.country,
            'num_facilities': self.num_facilities,
            'total_capacity_kw': float(self.total_capacity_kw) if self.total_capacity_kw else None,
            'description': self.description,
            'business_doc_url': self.business_doc_url,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by': self.reviewed_by,
            'reviewer_notes': self.reviewer_notes,
            'guardian_did': self.guardian_did,
            'reviewer_name': self.reviewer.full_name if self.reviewer else None
        }


# ============================================
# PHASE 2: DEVICE REGISTRATION
# ============================================

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    registrant_id = db.Column(db.Integer, db.ForeignKey('registrants.id'), nullable=False)
    device_id = db.Column(db.String(100), nullable=False)
    facility_id = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(100))
    manufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))
    capacity_kw = db.Column(db.Numeric(10, 2), nullable=False)
    technology = db.Column(db.String(50))
    country = db.Column(db.String(50), nullable=False)
    grid_connection_point = db.Column(db.String(100))
    latitude = db.Column(db.Numeric(10, 7))
    longitude = db.Column(db.Numeric(10, 7))
    commissioning_date = db.Column(db.Date)
    device_hash = db.Column(db.String(64))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    reviewer_notes = db.Column(db.Text)
    
    # Relationships
    registrant = db.relationship('Registrant', back_populates='devices')
    reviewer = db.relationship('Admin', back_populates='reviewed_devices', foreign_keys=[reviewed_by])
    documents = db.relationship('DeviceDocument', back_populates='device', cascade='all, delete-orphan')
    issuance_submissions = db.relationship('IssuanceSubmission', back_populates='device', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'registrant_id': self.registrant_id,
            'device_id': self.device_id,
            'facility_id': self.facility_id,
            'serial_number': self.serial_number,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'capacity_kw': float(self.capacity_kw) if self.capacity_kw else None,
            'technology': self.technology,
            'country': self.country,
            'grid_connection_point': self.grid_connection_point,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'commissioning_date': self.commissioning_date.isoformat() if self.commissioning_date else None,
            'device_hash': self.device_hash,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by': self.reviewed_by,
            'reviewer_notes': self.reviewer_notes,
            'registrant_name': self.registrant.organization_name if self.registrant else None,
            'reviewer_name': self.reviewer.full_name if self.reviewer else None
        }


class DeviceDocument(db.Model):
    __tablename__ = 'device_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_hash = db.Column(db.String(64))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    device = db.relationship('Device', back_populates='documents')
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'document_type': self.document_type,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_hash': self.file_hash,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }


# ============================================
# PHASE 3: ISSUANCE & VERIFICATION
# ============================================

class IssuanceSubmission(db.Model):
    __tablename__ = 'issuance_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    registrant_id = db.Column(db.Integer, db.ForeignKey('registrants.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    issuance_period_start = db.Column(db.DateTime, nullable=False)
    issuance_period_end = db.Column(db.DateTime, nullable=False)
    total_kwh = db.Column(db.Numeric(12, 3))
    num_readings = db.Column(db.Integer)
    csv_file_path = db.Column(db.String(500))
    csv_hash = db.Column(db.String(64))
    registrant_declaration_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_by = db.Column(db.String(100))
    deduplication_result = db.Column(JSONB)
    verifier_review_id = db.Column(db.Integer)
    
    # Relationships
    registrant = db.relationship('Registrant', back_populates='issuance_submissions')
    device = db.relationship('Device', back_populates='issuance_submissions')
    verifier_review = db.relationship('VerifierReview', back_populates='issuance_submission', uselist=False)
    deduplication_entries = db.relationship('DeduplicationLog', back_populates='issuance_submission', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'registrant_id': self.registrant_id,
            'device_id': self.device_id,
            'issuance_period_start': self.issuance_period_start.isoformat() if self.issuance_period_start else None,
            'issuance_period_end': self.issuance_period_end.isoformat() if self.issuance_period_end else None,
            'total_kwh': float(self.total_kwh) if self.total_kwh else None,
            'num_readings': self.num_readings,
            'csv_file_path': self.csv_file_path,
            'csv_hash': self.csv_hash,
            'registrant_declaration_path': self.registrant_declaration_path,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'submitted_by': self.submitted_by,
            'deduplication_result': self.deduplication_result,
            'verifier_review_id': self.verifier_review_id,
            'registrant_name': self.registrant.organization_name if self.registrant else None,
            'device_info': f"{self.device.device_id} - {self.device.facility_id}" if self.device else None
        }


class DeduplicationLog(db.Model):
    __tablename__ = 'deduplication_log'
    
    id = db.Column(db.Integer, primary_key=True)
    audit_trail_id = db.Column(db.String(64), unique=True, nullable=False)
    device_id = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    kwh = db.Column(db.Numeric(10, 3), nullable=False)
    issuance_submission_id = db.Column(db.Integer, db.ForeignKey('issuance_submissions.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    issuance_submission = db.relationship('IssuanceSubmission', back_populates='deduplication_entries')
    
    def to_dict(self):
        return {
            'id': self.id,
            'audit_trail_id': self.audit_trail_id,
            'device_id': self.device_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'kwh': float(self.kwh) if self.kwh else None,
            'issuance_submission_id': self.issuance_submission_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class VerifierReview(db.Model):
    __tablename__ = 'verifier_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    issuance_submission_id = db.Column(db.Integer, db.ForeignKey('issuance_submissions.id'), nullable=False)
    verifier_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    decision = db.Column(db.String(20), nullable=False)
    review_notes = db.Column(db.Text)
    checklist = db.Column(JSONB)
    verifier_vc_issued = db.Column(db.Boolean, default=False)
    verifier_vc_data = db.Column(JSONB)
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    measurement_tier = db.Column(db.String(10), default='2.3')
    device_scope_confirmed = db.Column(db.Boolean, default=False)
    grouping_keys_consistent = db.Column(db.Boolean, default=False)
    no_dedupe_collisions = db.Column(db.Boolean, default=False)
    
    # Relationships
    issuance_submission = db.relationship('IssuanceSubmission', back_populates='verifier_review')
    verifier = db.relationship('Admin', back_populates='verifier_reviews')
    
    def to_dict(self):
        return {
            'id': self.id,
            'issuance_submission_id': self.issuance_submission_id,
            'verifier_id': self.verifier_id,
            'decision': self.decision,
            'review_notes': self.review_notes,
            'checklist': self.checklist,
            'verifier_vc_issued': self.verifier_vc_issued,
            'verifier_vc_data': self.verifier_vc_data,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'measurement_tier': self.measurement_tier,
            'device_scope_confirmed': self.device_scope_confirmed,
            'grouping_keys_consistent': self.grouping_keys_consistent,
            'no_dedupe_collisions': self.no_dedupe_collisions,
            'verifier_name': self.verifier.full_name if self.verifier else None
        }


# ============================================
# AUDIT & ANALYTICS
# ============================================

class AuditTrail(db.Model):
    __tablename__ = 'audit_trail'
    
    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer)
    performed_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    action_details = db.Column(JSONB)
    ip_address = db.Column(INET)
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'action_type': self.action_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'performed_by': self.performed_by,
            'action_details': self.action_details,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Analytics(db.Model):
    __tablename__ = 'analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Numeric(15, 3))
    metric_data = db.Column(JSONB)
    period_start = db.Column(db.DateTime)
    period_end = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_value': float(self.metric_value) if self.metric_value else None,
            'metric_data': self.metric_data,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
