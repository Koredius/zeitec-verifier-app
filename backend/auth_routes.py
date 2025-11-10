from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime
import bcrypt
from models import db, Admin

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Admin login endpoint
    Body: { "username": "admin", "password": "admin123" }
    Returns: { "access_token": "...", "refresh_token": "...", "user": {...} }
    """
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    # Find admin user
    admin = Admin.query.filter_by(username=username).first()
    
    if not admin:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Verify password
    if not bcrypt.checkpw(password.encode('utf-8'), admin.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Update last login
    admin.last_login = datetime.utcnow()
    db.session.commit()
    
    # Create tokens
    access_token = create_access_token(identity=admin.id)
    refresh_token = create_refresh_token(identity=admin.id)
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': admin.to_dict()
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token
    Requires refresh token in Authorization header
    Returns: { "access_token": "..." }
    """
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    
    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user
    Requires access token in Authorization header
    Returns: { "user": {...} }
    """
    current_user_id = get_jwt_identity()
    admin = Admin.query.get(current_user_id)
    
    if not admin:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': admin.to_dict()}), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change password for current user
    Body: { "current_password": "...", "new_password": "..." }
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Current and new password required'}), 400
    
    admin = Admin.query.get(current_user_id)
    
    if not admin:
        return jsonify({'error': 'User not found'}), 404
    
    # Verify current password
    if not bcrypt.checkpw(data['current_password'].encode('utf-8'), admin.password_hash.encode('utf-8')):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Hash new password
    new_password_hash = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt())
    admin.password_hash = new_password_hash.decode('utf-8')
    
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200
