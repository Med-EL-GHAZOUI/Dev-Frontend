from app import db
from datetime import datetime
import bcrypt
import json

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='Analyst') # Analyst, Admin
    profile_picture = db.Column(db.String(255), nullable=True)
    preferences = db.Column(db.Text, default='{}') # JSON string
    failed_login_attempts = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    login_history = db.relationship('LoginHistory', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        
    def get_preferences(self):
        try:
            return json.loads(self.preferences)
        except:
            return {}

class LoginHistory(db.Model):
    __tablename__ = 'login_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False) # 'success', 'failed'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    sales_value = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class Prediction(db.Model):
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    predicted_value = db.Column(db.Float, nullable=False)
    confidence_lower = db.Column(db.Float, nullable=True)
    confidence_upper = db.Column(db.Float, nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    model_type = db.Column(db.String(50), nullable=False) # Primary: Linear Regression, Prophet, ARIMA
    accuracy_score = db.Column(db.Float, nullable=True) # e.g. R2 or 1-MAPE
    product = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ImportLog(db.Model):
    __tablename__ = 'import_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False) # 'processing', 'completed', 'failed'
    rows_processed = db.Column(db.Integer, default=0)
    errors = db.Column(db.Text, nullable=True) # JSON array of error messages
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
