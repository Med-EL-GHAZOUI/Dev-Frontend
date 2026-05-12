from flask import Blueprint, request, jsonify
from app import db
from app.models import User, LoginHistory, ImportLog
from flask_jwt_extended import jwt_required, get_jwt_identity
import psutil
import platform
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != 'Admin':
            return jsonify({"msg": "Admin privileges required"}), 403
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.route('/', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    users = User.query.all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "is_locked": u.is_locked,
            "failed_login_attempts": u.failed_login_attempts,
            "created_at": u.created_at.isoformat() if u.created_at else None
        })
    return jsonify(result), 200

@admin_bp.route('/<int:user_id>/role', methods=['PUT'])
@jwt_required()
@admin_required
def update_user_role(user_id):
    data = request.get_json()
    new_role = data.get('role')
    if new_role not in ['Admin', 'Analyst']:
        return jsonify({"msg": "Invalid role"}), 400
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
        
    user.role = new_role
    db.session.commit()
    return jsonify({"msg": "User role updated"}), 200

@admin_bp.route('/<int:user_id>/lock', methods=['PUT'])
@jwt_required()
@admin_required
def toggle_user_lock(user_id):
    data = request.get_json()
    lock_status = data.get('is_locked', False)
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
        
    user.is_locked = lock_status
    if not lock_status:
        user.failed_login_attempts = 0
        user.locked_until = None
    db.session.commit()
    return jsonify({"msg": f"User lock status set to {lock_status}"}), 200

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_system_stats():
    # Application stats
    total_users = User.query.count()
    active_users = User.query.filter_by(is_locked=False).count()
    total_imports = ImportLog.query.count()
    failed_logins = LoginHistory.query.filter_by(status='failed').count()
    
    # System stats
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    return jsonify({
        "app": {
            "total_users": total_users,
            "active_users": active_users,
            "total_imports": total_imports,
            "failed_logins": failed_logins
        },
        "system": {
            "os": platform.system(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_mb": round(memory.used / (1024 * 1024), 2),
            "memory_total_mb": round(memory.total / (1024 * 1024), 2)
        }
    }), 200
