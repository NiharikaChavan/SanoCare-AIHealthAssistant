# src/database.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import text

db = SQLAlchemy()  # Shared database instance

def create_missing_columns(app):
    """Create missing columns in the users table if they don't exist"""
    with app.app_context():
        try:
            # List of columns to add
            columns_to_add = [
                "language_preference VARCHAR(10) DEFAULT 'en'",
                "region VARCHAR(100)",
                "city VARCHAR(100)",
                "occupation VARCHAR(100)",
                "ethnicity VARCHAR(100)",
                "blood_type VARCHAR(5)",
                "allergies JSONB",
                "chronic_conditions JSONB",
                "medications JSONB",
                "family_history JSONB",
                "traditional_medicine_preferences JSONB",
                "medical_history JSONB",
                "vaccination_history JSONB",
                "last_checkup DATE"
            ]
            
            # Add each column if it doesn't exist
            for column in columns_to_add:
                column_name = column.split()[0]
                try:
                    db.session.execute(text(f"""
                        DO $$ 
                        BEGIN 
                            IF NOT EXISTS (
                                SELECT 1 
                                FROM information_schema.columns 
                                WHERE table_schema = 'medical' 
                                AND table_name = 'users' 
                                AND column_name = '{column_name}'
                            ) THEN
                                ALTER TABLE medical.users ADD COLUMN {column};
                            END IF;
                        END $$;
                    """))
                    print(f"Added column {column_name} if it didn't exist")
                except Exception as e:
                    print(f"Error adding column {column_name}: {str(e)}")
            
            db.session.commit()
            print("Successfully updated users table schema")
        except Exception as e:
            print(f"Error updating users table schema: {str(e)}")
            db.session.rollback()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'medical'}
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20))
    
    # Essential Cultural and Demographic Information
    ethnicity = db.Column(db.String(100))
    region = db.Column(db.String(100))
    city = db.Column(db.String(100))
    occupation = db.Column(db.String(100))
    language_preference = db.Column(db.String(10), default='en')
    
    # Health Information
    blood_type = db.Column(db.String(5))
    allergies = db.Column(db.JSON)
    chronic_conditions = db.Column(db.JSON)
    medications = db.Column(db.JSON)
    family_history = db.Column(db.JSON)
    
    # Traditional Medicine Preference
    traditional_medicine_preferences = db.Column(db.JSON)  # Ayurveda, TCM, etc.
    
    # Medical History
    medical_history = db.Column(db.JSON)
    vaccination_history = db.Column(db.JSON)
    last_checkup = db.Column(db.Date)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversations = db.relationship('Conversation', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def get_id(self):
        return str(self.user_id)
        
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'ethnicity': self.ethnicity,
            'region': self.region,
            'city': self.city,
            'occupation': self.occupation,
            'language_preference': self.language_preference,
            'blood_type': self.blood_type,
            'allergies': self.allergies,
            'chronic_conditions': self.chronic_conditions,
            'medications': self.medications,
            'family_history': self.family_history,
            'traditional_medicine_preferences': self.traditional_medicine_preferences,
            'medical_history': self.medical_history,
            'vaccination_history': self.vaccination_history,
            'last_checkup': self.last_checkup.isoformat() if self.last_checkup else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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

class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'
    __table_args__ = {'schema': 'medical'}
    
    record_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('medical.users.user_id'), nullable=False)
    record_type = db.Column(db.String(50), nullable=False)  # diagnosis, prescription, lab_result, etc.
    date = db.Column(db.DateTime, nullable=False)
    provider = db.Column(db.String(100))
    details = db.Column(db.JSON)
    attachments = db.Column(db.JSON)  # URLs to stored files
    cultural_context = db.Column(db.JSON)  # cultural considerations in treatment
    region_specific_info = db.Column(db.JSON)  # region-specific treatment details
    age_group = db.Column(db.String(20))  # child, adolescent, adult, elderly
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)