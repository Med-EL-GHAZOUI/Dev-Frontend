from flask import Blueprint, request, jsonify
from app import db
from app.models import User, LoginHistory
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/me', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
        
    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "profile_picture": user.profile_picture,
        "preferences": user.get_preferences(),
        "created_at": user.created_at.isoformat() if user.created_at else None
    }), 200

@profile_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
        
    data = request.get_json()
    
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        # Check if email is already taken by another user
        existing = User.query.filter_by(email=data['email']).first()
        if existing and str(existing.id) != str(user_id):
             return jsonify({"msg": "Email already in use"}), 400
        user.email = data['email']
    if 'preferences' in data:
        user.preferences = json.dumps(data['preferences'])
    if 'profile_picture' in data:
        user.profile_picture = data['profile_picture']
        
    db.session.commit()
    return jsonify({"msg": "Profile updated successfully"}), 200

@profile_bp.route('/me/password', methods=['PUT'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
        
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({"msg": "Missing password fields"}), 400
        
    if not user.check_password(current_password):
        return jsonify({"msg": "Invalid current password"}), 400
        
    user.set_password(new_password)
    db.session.commit()
    return jsonify({"msg": "Password changed successfully"}), 200

@profile_bp.route('/me/history', methods=['GET'])
@jwt_required()
def get_login_history():
    user_id = get_jwt_identity()
    history = LoginHistory.query.filter_by(user_id=user_id).order_by(LoginHistory.timestamp.desc()).limit(20).all()
    
    result = []
    for h in history:
        result.append({
            "ip_address": h.ip_address,
            "user_agent": h.user_agent,
            "status": h.status,
            "timestamp": h.timestamp.isoformat() if h.timestamp else None
        })
        
    return jsonify(result), 200
