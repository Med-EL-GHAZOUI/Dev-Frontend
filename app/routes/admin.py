from flask import Blueprint, jsonify, request
from app import db
from app.models import User
from flask_jwt_extended import jwt_required, get_jwt_identity

admin_bp = Blueprint('admin', __name__)

def check_admin():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user and user.role == 'Admin'

@admin_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    if not check_admin():
        return jsonify({"msg": "Admin access required"}), 403
    
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "role": u.role
    } for u in users]), 200

@admin_bp.route('/<int:user_id>/role', methods=['PUT'])
@jwt_required()
def update_role(user_id):
    if not check_admin():
        return jsonify({"msg": "Admin access required"}), 403
    
    data = request.get_json()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    user.role = data.get('role', user.role)
    db.session.commit()
    return jsonify({"msg": "Role updated successfully"}), 200
