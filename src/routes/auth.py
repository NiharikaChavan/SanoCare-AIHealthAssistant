from flask import Blueprint, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from src.database import db, User
from datetime import datetime
import json

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    try:
        data = request.get_json()
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({
                'success': False,
                'message': 'Email already registered'
            }), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d'),
            gender=data['gender'],
            ethnicity=data['ethnicity'],
            religion=data.get('religion'),
            language_preference=data['language_preference'],
            region=data['region'],
            country_code=data['country_code'],
            city=data.get('city'),
            dietary_restrictions=json.dumps(data.get('dietary_restrictions', [])),
            traditional_medicine_preferences=json.dumps(data.get('traditional_medicine_preferences', [])),
            spiritual_practices=json.dumps(data.get('spiritual_practices', [])),
            wellness_rituals=json.dumps(data.get('wellness_rituals', [])),
            family_structure=data['family_structure'],
            health_decision_making=data['health_decision_making'],
            blood_type=data.get('blood_type'),
            allergies=data.get('allergies'),
            chronic_conditions=data.get('chronic_conditions'),
            medications=data.get('medications'),
            emergency_contact=json.dumps(data.get('emergency_contact', {}))
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user_id': user.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            # TODO: Implement session management
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user_id': user.id
            })
        
        return jsonify({
            'success': False,
            'message': 'Invalid email or password'
        }), 401
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@auth.route('/logout')
def logout():
    # TODO: Implement session cleanup
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    }) 