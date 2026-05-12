from flask import Blueprint, request, jsonify
from app import db
from app.models import User, LoginHistory
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_TIME_MINUTES = 15

def log_login_attempt(user_id, status, request):
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')[:255]
    log = LoginHistory(user_id=user_id, ip_address=ip_address, user_agent=user_agent, status=status)
    db.session.add(log)
    db.session.commit()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"msg": "Email already exists"}), 400
    
    user = User(name=data.get('name'), email=data.get('email'), role=data.get('role', 'Analyst'))
    user.set_password(data.get('password'))
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "User created successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user:
        return jsonify({"msg": "Invalid email or password"}), 401

    # Check if account is locked
    if user.is_locked:
        if user.locked_until and datetime.utcnow() < user.locked_until:
            return jsonify({"msg": "Account is locked. Please try again later."}), 403
        else:
            # Unlock if time has passed
            user.is_locked = False
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()

    if user.check_password(data.get('password')):
        # Reset failed attempts
        user.failed_login_attempts = 0
        db.session.commit()
        
        log_login_attempt(user.id, 'success', request)
        
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "profile_picture": user.profile_picture,
                "preferences": user.get_preferences()
            }
        }), 200
    else:
        # Increment failed attempts
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.is_locked = True
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_TIME_MINUTES)
        db.session.commit()
        
        log_login_attempt(user.id, 'failed', request)
        
        if user.is_locked:
             return jsonify({"msg": "Too many failed attempts. Account locked."}), 403
        return jsonify({"msg": "Invalid email or password"}), 401
