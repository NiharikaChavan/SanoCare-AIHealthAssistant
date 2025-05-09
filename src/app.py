from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from src.database import db, User, Conversation
from src.helper import get_health_recommendations, update_knowledge_base
from src.cultural_health import CulturalHealthContext
from src.routes.auth import auth
import os
from dotenv import load_dotenv
from datetime import timedelta
from sqlalchemy import text

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost:5432/medicaldb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allows cookies to be sent in cross-site requests
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevents JavaScript access to the cookie
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem for session storage
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Session expires after 1 day

if not app.config['SECRET_KEY']:
    raise ValueError("No SECRET_KEY set in environment variables")

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(auth)

# Create tables if they don't exist
with app.app_context():
    # Create schema if it doesn't exist
    db.session.execute(text('CREATE SCHEMA IF NOT EXISTS medical'))
    db.session.commit()
    # Create all tables
    db.create_all()
    # Create missing columns
    from src.database import create_missing_columns
    create_missing_columns(app)
    print("\n=== Application Startup ===")
    print("Database initialized")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        message = data.get('message')
        
        if not user_id or not message:
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
        # Get user context
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Create cultural health context
        cultural_context = CulturalHealthContext(user)
        
        # Get health recommendations based on user's cultural context
        recommendations = get_health_recommendations(message, cultural_context)
        
        # Create conversation record
        conversation = Conversation(
            user_id=user_id,
            message=message,
            response=recommendations['response'],
            context=recommendations['context']
        )
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': recommendations['response'],
            'context': recommendations['context']
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/update-knowledge', methods=['POST'])
def update_knowledge():
    try:
        # Check for admin authentication
        # TODO: Implement proper admin authentication
        if not request.headers.get('X-Admin-Key') == os.getenv('ADMIN_KEY'):
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 401
        
        # Update knowledge base
        result = update_knowledge_base()
        
        return jsonify({
            'success': True,
            'message': 'Knowledge base updated successfully',
            'details': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/user-profile/<int:user_id>')
def get_user_profile(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Convert JSON fields back to Python objects
        profile = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'date_of_birth': user.date_of_birth.isoformat(),
            'gender': user.gender,
            'ethnicity': user.ethnicity,
            'religion': user.religion,
            'language_preference': user.language_preference,
            'region': user.region,
            'country_code': user.country_code,
            'city': user.city,
            'dietary_restrictions': user.dietary_restrictions,
            'traditional_medicine_preferences': user.traditional_medicine_preferences,
            'spiritual_practices': user.spiritual_practices,
            'wellness_rituals': user.wellness_rituals,
            'family_structure': user.family_structure,
            'health_decision_making': user.health_decision_making,
            'blood_type': user.blood_type,
            'allergies': user.allergies,
            'chronic_conditions': user.chronic_conditions,
            'medications': user.medications,
            'emergency_contact': user.emergency_contact,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat()
        }
        
        return jsonify({
            'success': True,
            'profile': profile
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 