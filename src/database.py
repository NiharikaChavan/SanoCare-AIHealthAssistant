# src/database.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()  # Shared database instance

class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Fixed: Double underscores
    __table_args__ = {'schema': 'medical'}
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    country_code = db.Column(db.String(3))
    preferred_language = db.Column(db.String(2), default='en')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Add relationship
    conversations = db.relationship('Conversation', backref='user', lazy=True)

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return True

class Conversation(db.Model):
    __tablename__ = 'conversations'  # Fixed: Double underscores
    __table_args__ = {'schema': 'medical'}
    
    conversation_id = db.Column(db.Integer, primary_key=True)
    # Include schema in foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('medical.users.user_id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    session_id = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)  # Added timestamp

    def __repr__(self):
        return f'<Conversation {self.conversation_id}>'