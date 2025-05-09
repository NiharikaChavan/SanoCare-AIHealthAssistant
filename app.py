from datetime import datetime, timedelta
import re
import uuid
from flask import Flask, logging, render_template, jsonify, request, session, redirect, url_for, flash
from src.helper import download_hugging_face_embeddings, get_relevant_medical_info, get_who_data
from langchain_pinecone import PineconeVectorStore
from langchain.chat_models import init_chat_model
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document 
from dotenv import load_dotenv
from src.prompt import *
import os
import requests
import json
from langchain_openai import ChatOpenAI
from flask_sqlalchemy import SQLAlchemy
from src.database import db, User, Conversation
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import text
import urllib3
from pinecone import Pinecone
from urllib3.exceptions import InsecureRequestWarning

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "X-Requested-With"],
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "Authorization"],
        "max_age": 3600,
        "allow_credentials": True
    }
})

load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:root@localhost:5432/medicaldb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allows cookies to be sent in cross-site requests
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevents JavaScript access to the cookie
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem for session storage
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Session expires after 1 day

if not app.config['SECRET_KEY']:
    raise ValueError("No SECRET_KEY set in environment variables")
db.init_app(app)

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

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def cleanup_session():
    """Helper function to clean up session data"""
    print("\n=== Cleaning up session ===")
    print("Current session data:", dict(session))
    
    # Clear all session data
    session.clear()
    
    # Remove specific session keys
    keys_to_remove = ['session_id', 'user_id', '_fresh', '_id', 'csrf_token']
    for key in keys_to_remove:
        session.pop(key, None)
    
    # Mark session as modified to ensure changes are saved
    session.modified = True
    
    print("Session after cleanup:", dict(session))

def cleanup_orphaned_sessions():
    """Clean up any orphaned sessions in the database"""
    try:
        print("\n=== Checking for orphaned sessions ===")
        # Get all unique session IDs from conversations
        active_sessions = db.session.query(Conversation.session_id).distinct().all()
        active_session_ids = [session[0] for session in active_sessions]
        
        # Get all session IDs from the filesystem
        session_dir = app.config['SESSION_TYPE']
        if os.path.exists(session_dir):
            for filename in os.listdir(session_dir):
                if filename.endswith('.session'):
                    session_id = filename[:-7]  # Remove .session extension
                    if session_id not in active_session_ids:
                        try:
                            os.remove(os.path.join(session_dir, filename))
                            print(f"Removed orphaned session: {session_id}")
                        except Exception as e:
                            print(f"Error removing session file {session_id}: {str(e)}")
        
        print("Session cleanup completed")
    except Exception as e:
        print(f"Error in cleanup_orphaned_sessions: {str(e)}")

# Update the before_request handler
@app.before_request
def before_request():
    print("\n=== Request Start ===")
    print("Current user:", current_user)
    print("Is authenticated:", current_user.is_authenticated if current_user else False)
    print("Session data before:", dict(session))
    
    # Clean up orphaned sessions
    cleanup_orphaned_sessions()
    
    # For non-authenticated users, only maintain session_id and diagnostic state
    if not current_user or not current_user.is_authenticated:
        # Keep or create session_id for conversation continuity
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            session.modified = True
        
        # Store the current session_id
        current_session_id = session['session_id']
        
        # Clear other session data but preserve session_id
        session.clear()
        session['session_id'] = current_session_id
        session.modified = True
        
        print("Session preserved for non-authenticated user")
        print("Session data after:", dict(session))

def get_or_create_session_id():
    """Get existing session ID or create a new one"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session.modified = True
    return session['session_id']

PINECONE_API_KEY=os.environ.get('PINECONE_API_KEY')
OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')

print("OpenAI API Key loaded:", "Yes" if OPENAI_API_KEY else "No")
print("Pinecone API Key loaded:", "Yes" if PINECONE_API_KEY else "No")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

embeddings = download_hugging_face_embeddings()

index_name = "sanocare"

# Initialize LLM first
llm = ChatOpenAI(
    model='gpt-4',
    temperature=0.4,
    max_tokens=500
)

# Initialize prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", """Please provide a response based on the following context and question. 
    
Context: {context}
Query: {input}

Remember to:
1. Use a warm, personal tone
2. Reference local customs and practices
3. Include culturally relevant examples
4. Consider the user's background and preferences
5. Make recommendations specific to their region and age
6. Use familiar local terms and references""")
])

# Initialize Pinecone with error handling
try:
    print("\n=== Initializing Pinecone ===")
    os.environ['REQUESTS_CA_BUNDLE'] = ''  # Disable SSL certificate verification
    os.environ['SSL_CERT_FILE'] = ''  # Disable SSL certificate verification
    
    # Initialize Pinecone client
    print("Creating Pinecone client...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    print("Pinecone client created successfully")
    
    # Create Pinecone vector store
    print("Creating vector store from index:", index_name)
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
    print("Vector store created successfully")

    # Test retrieval
    print("\nTesting document retrieval...")
    test_docs = docsearch.similarity_search("test", k=1)
    print(f"Test retrieval returned {len(test_docs)} documents")
    if test_docs:
        print("Sample document content:", test_docs[0].page_content[:100])

    # Create retriever
    print("\nCreating retriever...")
    retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k":3})
    print("Successfully initialized Pinecone and created retriever")

    # Create the chain that combines the retrieved documents
    question_answer_chain = create_stuff_documents_chain(
        llm,
        prompt,
        document_variable_name="context",
    )

    # Create the retrieval chain
    rag_chain = create_retrieval_chain(
        retriever,
        question_answer_chain
    )
    print("Successfully created RAG chain")

except Exception as e:
    print(f"\nError initializing Pinecone: {str(e)}")
    print("Continuing without Pinecone integration...")
    docsearch = None
    retriever = None
    rag_chain = None
    
    # Create a fallback chain that doesn't use retrieval
    fallback_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Have a friendly conversation about health and wellness. 
Current question: {input}

Respond naturally while maintaining medical accuracy:
- Use a warm, conversational tone
- Speak as if chatting with a friend
- Base advice on current medical knowledge
- Keep information accurate but approachable
- End with encouragement and openness to more questions""")
    ])
    
    fallback_chain = fallback_prompt | llm
    rag_chain = fallback_chain
    print("Created fallback chain without retrieval")

value = get_who_data('India')

def store_conversation(user_id, message, bot_response, session_id):
    """Store conversation in the database"""
    print("\n=== store_conversation called ===")
    print("Current user:", current_user)
    print("Is authenticated:", current_user.is_authenticated if current_user else False)
    print("User ID:", user_id)
    print("Session ID:", session_id)
    print("Session data:", dict(session))
    
    # Strict authentication check at the start
    if not current_user:
        print("Error: current_user is None")
        return False
        
    if not current_user.is_authenticated:
        print("Error: User is not authenticated")
        return False
        
    try:
        print("\nAttempting to store conversation:")
        print(f"User authenticated: {current_user.is_authenticated}")
        print(f"User ID: {user_id}")
        print(f"Session ID: {session_id}")
        print(f"Message length: {len(message)}")
        print(f"Response length: {len(bot_response)}")
        
        # Additional validation for authenticated user
        if not user_id or not isinstance(user_id, int):
            print("Error: Invalid or missing user_id")
            return False
            
        # Verify user exists in database and matches current_user
        user = User.query.get(user_id)
        if not user:
            print("Error: User not found in database")
            return False
            
        if user.user_id != current_user.user_id:
            print("Error: User ID mismatch")
            print(f"Provided user_id: {user_id}")
            print(f"Current user_id: {current_user.user_id}")
            return False
            
        if not session_id:
            print("Error: No session_id provided")
            return False
            
        # Double check authentication before database write
        if not current_user.is_authenticated:
            print("Error: User authentication lost during processing")
            return False
            
        # Triple check authentication right before database write
        if not current_user or not current_user.is_authenticated:
            print("Error: User authentication lost right before database write")
            return False
            
        # Final authentication check
        if not current_user.is_authenticated:
            print("Error: Final authentication check failed")
            return False
            
        print("All authentication checks passed, proceeding with database write")
        
        new_conversation = Conversation(
            user_id=user_id,
            message=message,
            bot_response=bot_response,
            session_id=session_id,
            timestamp=datetime.now()
        )
        db.session.add(new_conversation)
        db.session.commit()
        print("Successfully stored conversation")
        return True
    except Exception as e:
        print(f"Error storing conversation: {str(e)}")
        print("Stack trace:", e.__traceback__)
        db.session.rollback()
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                return jsonify({
                    'success': True,
                    'user': {
                        'user_id': user.user_id,
                        'username': user.username,
                        'email': user.email
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Invalid email or password'
                }), 401
        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An error occurred during login'
            }), 500
    
    # For GET requests, return success: false to indicate frontend should show login form
    return jsonify({
        'success': False,
        'message': 'Please log in'
    }), 401

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            print("\n=== Registration Request ===")
            print("Request headers:", dict(request.headers))
            print("Request data:", request.get_data())
            print("Content-Type:", request.headers.get('Content-Type'))
            print("Origin:", request.headers.get('Origin'))
            
            data = request.get_json()
            print("Parsed JSON data:", data)
            
            # Basic information
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            date_of_birth = datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date()
            gender = data.get('gender')
            
            # Demographic information
            ethnicity = data.get('ethnicity')
            region = data.get('region')
            city = data.get('city')
            occupation = data.get('occupation')
            language_preference = data.get('language_preference', 'en')
            
            # Health information
            blood_type = data.get('blood_type')
            allergies = data.get('allergies', [])
            chronic_conditions = data.get('chronic_conditions', [])
            medications = data.get('medications', [])
            family_history = data.get('family_history', {})
            traditional_medicine_preferences = data.get('traditional_medicine_preferences', {})
            
            # Medical history
            medical_history = data.get('medical_history', {})
            vaccination_history = data.get('vaccination_history', [])
            last_checkup = datetime.strptime(data.get('last_checkup'), '%Y-%m-%d').date() if data.get('last_checkup') else None
            
            print(f"Parsed data: username={username}, email={email}, gender={gender}")
            
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                print(f"Email {email} already registered")
                return jsonify({
                    'success': False,
                    'message': 'Email already registered'
                }), 400
            
            if User.query.filter_by(username=username).first():
                print(f"Username {username} already taken")
                return jsonify({
                    'success': False,
                    'message': 'Username already taken'
                }), 400
            
            # Create new user with all information
            user = User(
                username=username,
                email=email,
                date_of_birth=date_of_birth,
                gender=gender,
                ethnicity=ethnicity,
                region=region,
                city=city,
                occupation=occupation,
                language_preference=language_preference,
                blood_type=blood_type,
                allergies=allergies,
                chronic_conditions=chronic_conditions,
                medications=medications,
                family_history=family_history,
                traditional_medicine_preferences=traditional_medicine_preferences,
                medical_history=medical_history,
                vaccination_history=vaccination_history,
                last_checkup=last_checkup
            )
            user.set_password(password)
            
            try:
                db.session.add(user)
                db.session.commit()
                print(f"Successfully created user: {username}")
                login_user(user)
                print("User logged in successfully")
                return jsonify({
                    'success': True,
                    'user': {
                        'user_id': user.user_id,
                        'username': user.username,
                        'email': user.email,
                        'language_preference': user.language_preference
                    }
                })
            except Exception as e:
                print(f"Database error: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'Error creating account'
                }), 500
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An error occurred during registration'
            }), 500
    
    # For GET requests, return success: false to indicate frontend should show registration form
    return jsonify({
        'success': False,
        'message': 'Please register'
    }), 200

@app.route('/check-auth')
def check_auth():
    if current_user.is_authenticated:
        return jsonify({
            'user_id': current_user.user_id,
            'username': current_user.username,
            'email': current_user.email
        })
    return jsonify({'message': 'Not authenticated'}), 401

@app.route('/logout')
@login_required
def logout():
    try:
        # Clear all session data
        session.clear()
        session.pop('session_id', None)
        session.pop('user_id', None)
        session.pop('_fresh', None)
        session.pop('_id', None)
        
        # Logout the user
        logout_user()
        
        # Clear any remaining session data
        session.modified = True
        
        print("\n=== Logout Successful ===")
        print("Session cleared")
        print("User logged out")
        print("Session data:", dict(session))
        
        return jsonify({
            'success': True,
            'message': 'Successfully logged out'
        })
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during logout'
        }), 500

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat')
def chat_interface():
    return render_template('chat.html')

@app.route("/get", methods=["GET", "POST"])
def chat_api():
    try:
        data = request.get_json() if request.is_json else request.form
        msg = data.get("msg")
        selected_category = data.get("category")
        
        if not msg:
            return jsonify({
                "success": False,
                "error": "No message provided"
            }), 400

        print("\n" + "="*50)
        print("Received input:", msg)
        print("Selected category:", selected_category)
        
        # Get or create session_id
        session_id = get_or_create_session_id()
        
        # Get conversation context and diagnostic state
        conversation_context = []
        diagnostic_state = get_diagnostic_state(session_id)

        # Get user context if authenticated
        user_context = None
        if current_user and current_user.is_authenticated:
            user_context = generate_cultural_context(current_user)
            conversation_context = get_conversation_context(
                user_id=current_user.user_id,
                session_id=session_id
            )

        direct_chat = ChatOpenAI(
            model='gpt-4',
            temperature=0.4,
            max_tokens=500
        )

        # If category is provided, use it directly
        if selected_category:
            category = selected_category
            is_health_related = True
        else:
            # Check if health-related and determine category
            health_check_response = direct_chat.invoke(
                "Is the following message asking about health, medical conditions, symptoms, lifestyle, or mental health? Reply with just 'yes' or 'no': " + msg
            )
            is_health_related = health_check_response.content.strip().lower() == 'yes'
            if is_health_related:
                category = determine_health_category(msg, direct_chat)
            else:
                category = "GENERAL"
        
        print(f"Using category: {category}")

        try:
            if is_health_related:
                if docsearch is None:
                    final_response = "I apologize, but I'm currently experiencing technical difficulties accessing my medical knowledge base."
                    return jsonify({
                        "success": True,
                        "response": final_response,
                        "category": category,
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Process health query using RAG
                final_response = process_health_query(
                    query=msg,
                    user_context=user_context,
                    chat_history=conversation_context
                )

            else:
                # Non-health query
                category = "GENERAL"
                context_prompt = f"""Previous context:{conversation_context}

Current message: {msg}

Respond to this message naturally, taking into account the previous conversation context."""
                
                chat_response = direct_chat.invoke(context_prompt)
                final_response = str(chat_response.content)

            # Store conversation if user is authenticated
            if current_user and current_user.is_authenticated:
                try:
                    store_success = store_conversation(
                        user_id=current_user.user_id,
                        message=msg,
                        bot_response=final_response,
                        session_id=session_id
                    )
                    print("Conversation stored:", store_success)
                except Exception as e:
                    print("Error storing conversation:", str(e))

            return jsonify({
                "success": True,
                "response": final_response,
                "category": category,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            print(f"Error in chat processing: {str(e)}")
            return jsonify({
                "success": False,
                "error": "An error occurred while processing your request",
                "details": str(e)
            }), 500

    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({
            "success": False,
            "error": "An error occurred while processing your request",
            "details": str(e)
        }), 500

@app.route("/conversations", methods=["GET"])
def get_conversations():
    """Retrieve conversations for the logged-in user"""
    try:
        if not current_user.is_authenticated:
            return jsonify({
                "success": True,
                "conversations": []
            })
            
        # Query conversations for the current user, ordered by timestamp
        conversations = Conversation.query.filter_by(user_id=current_user.user_id)\
            .order_by(Conversation.timestamp.desc())\
            .all()
            
        # Format conversations
        conversation_history = [{
            "conversation_id": conv.conversation_id,
            "message": conv.message,
            "response": conv.bot_response,
            "timestamp": conv.timestamp.isoformat(),
            "session_id": conv.session_id
        } for conv in conversations]
        
        return jsonify({
            "success": True,
            "conversations": conversation_history
        })
        
    except Exception as e:
        print("Error retrieving conversations:", str(e))
        return jsonify({
            "error": "Failed to retrieve conversations",
            "details": str(e)
        }), 500

@app.route("/conversations/session", methods=["GET"])
def get_session_conversations():
    """Retrieve conversations for a specific session"""
    try:
        session_id = request.args.get("session_id")
        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400
            
        # Query conversations for the session, ordered by timestamp
        conversations = Conversation.query.filter_by(session_id=session_id)\
            .order_by(Conversation.timestamp.asc())\
            .all()
            
        # Format conversations
        conversation_history = [{
            "conversation_id": conv.conversation_id,
            "message": conv.message,
            "response": conv.bot_response,
            "timestamp": conv.timestamp.isoformat()
        } for conv in conversations]
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "conversations": conversation_history
        })
        
    except Exception as e:
        print("Error retrieving session conversations:", str(e))
        return jsonify({
            "error": "Failed to retrieve session conversations",
            "details": str(e)
        }), 500

def delete_user_and_conversations(user_id):
    """Safely delete a user and all their conversations"""
    try:
        print(f"\n=== Attempting to delete user {user_id} and their conversations ===")
        
        # First delete all conversations for this user
        conversations = Conversation.query.filter_by(user_id=user_id).all()
        for conv in conversations:
            db.session.delete(conv)
        print(f"Deleted {len(conversations)} conversations")
        
        # Then delete the user
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            print(f"Deleted user {user_id}")
        
        db.session.commit()
        print("Successfully deleted user and all conversations")
        return True
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        print("Stack trace:", e.__traceback__)
        db.session.rollback()
        return False

@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Route to delete a user and their conversations"""
    try:
        # Only allow users to delete their own account
        if not current_user or not current_user.is_authenticated or current_user.user_id != user_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 401
            
        success = delete_user_and_conversations(user_id)
        if success:
            # Logout the user after successful deletion
            logout_user()
            cleanup_session()
            return jsonify({
                'success': True,
                'message': 'User and conversations deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to delete user'
            }), 500
    except Exception as e:
        print(f"Error in delete_user route: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while deleting the user'
        }), 500

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in ["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"]:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/check-db-state')
def check_db_state():
    """Check the current state of the database"""
    try:
        print("\n=== Checking Database State ===")
        
        # Check users
        users = User.query.all()
        print(f"Total users: {len(users)}")
        for user in users:
            print(f"User ID: {user.user_id}, Email: {user.email}")
        
        # Check conversations
        conversations = Conversation.query.all()
        print(f"\nTotal conversations: {len(conversations)}")
        for conv in conversations:
            print(f"Conversation ID: {conv.conversation_id}, User ID: {conv.user_id}, Session ID: {conv.session_id}")
        
        # Check session files
        session_dir = app.config['SESSION_TYPE']
        if os.path.exists(session_dir):
            session_files = [f for f in os.listdir(session_dir) if f.endswith('.session')]
            print(f"\nTotal session files: {len(session_files)}")
            for file in session_files:
                print(f"Session file: {file}")
        
        return jsonify({
            'success': True,
            'users': len(users),
            'conversations': len(conversations),
            'session_files': len(session_files) if 'session_files' in locals() else 0
        })
    except Exception as e:
        print(f"Error checking database state: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/cleanup-db')
def cleanup_database():
    """Clean up any orphaned data in the database"""
    try:
        print("\n=== Cleaning up Database ===")
        
        # Delete all conversations
        conversations = Conversation.query.all()
        for conv in conversations:
            db.session.delete(conv)
        print(f"Deleted {len(conversations)} conversations")
        
        # Delete all users
        users = User.query.all()
        for user in users:
            db.session.delete(user)
        print(f"Deleted {len(users)} users")
        
        # Clean up session files
        session_dir = app.config['SESSION_TYPE']
        if os.path.exists(session_dir):
            session_files = [f for f in os.listdir(session_dir) if f.endswith('.session')]
            for file in session_files:
                try:
                    os.remove(os.path.join(session_dir, file))
                    print(f"Deleted session file: {file}")
                except Exception as e:
                    print(f"Error deleting session file {file}: {str(e)}")
        
        db.session.commit()
        print("Database cleanup completed")
        
        return jsonify({
            'success': True,
            'message': 'Database cleaned up successfully'
        })
    except Exception as e:
        print(f"Error cleaning up database: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_cultural_context(user):
    """Generate cultural context based on user's database preferences"""
    if not user:
        return {}
    
    print("\n=== Generating User Context ===")
    
    try:
        # Calculate age and age group
        today = datetime.now().date()
        age = today.year - user.date_of_birth.year - ((today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day))
        
        age_group = "young_adult" if age < 35 else "middle_adult" if age < 50 else "mature_adult" if age < 65 else "elderly"
        
        # Build context only from explicitly provided information
        context = {
            "age_group": age_group,
            "age": age
        }
        
        # Add basic demographic information if provided
        if user.gender:
            context["gender"] = user.gender
        if user.ethnicity:
            context["ethnicity"] = user.ethnicity
        if user.region:
            context["region"] = user.region
        if user.city:
            context["city"] = user.city
        if user.language_preference:
            context["language"] = user.language_preference
        if user.occupation:
            context["occupation"] = user.occupation

        # Build medical background from explicitly provided information
        medical_data = {}
        
        # Add medical information if provided
        if user.blood_type:
            medical_data["blood_type"] = user.blood_type
        if user.allergies:
            medical_data["allergies"] = user.allergies
        if user.chronic_conditions:
            medical_data["chronic_conditions"] = user.chronic_conditions
        if user.medications:
            medical_data["medications"] = user.medications
        if user.family_history:
            medical_data["family_history"] = user.family_history
            
        # Handle traditional medicine preferences
        if user.traditional_medicine_preferences:
            if isinstance(user.traditional_medicine_preferences, dict):
                # If it's a dictionary of preferences
                medical_data["traditional_medicine_preferences"] = {
                    k: v for k, v in user.traditional_medicine_preferences.items() 
                    if v  # Only include preferences that are True/enabled
                }
            else:
                # If it's a string or other format
                medical_data["traditional_medicine_preferences"] = user.traditional_medicine_preferences
        
        # Add other medical history if provided
        if user.vaccination_history:
            medical_data["vaccination_history"] = user.vaccination_history
        if user.last_checkup:
            medical_data["last_checkup"] = user.last_checkup

        if medical_data:
            context["medical_background"] = medical_data
        
        print("Generated context:", context)
        return context
        
    except Exception as e:
        print(f"Error generating cultural context: {str(e)}")
        return {}

def get_cultural_prompt(user_context, category):
    """Generate a culturally appropriate prompt based on user preferences from database"""
    if not user_context:
        return "Provide professional healthcare guidance based on modern medical evidence."
        
    try:
        print("\n=== Generating Cultural Context ===")
        print("User context:", user_context)
        
        # Get medical preferences from user context
        medical_background = user_context.get("medical_background", {})
        traditional_prefs = medical_background.get("traditional_medicine_preferences", {})
        
        print("Traditional medicine preferences:", traditional_prefs)
        
        # Build query based on user preferences
        if traditional_prefs:
            # User has traditional medicine preferences
            query = f"healthcare recommendations incorporating "
            if isinstance(traditional_prefs, dict):
                practices = ", ".join(traditional_prefs.keys())
                query += f"{practices} and modern medicine"
            else:
                query += f"{traditional_prefs} and modern medicine"
        else:
            # User prefers modern medicine only
            query = "modern medical recommendations and evidence-based practices"
            
        print("Cultural query:", query)
        
        # Get relevant cultural and medical documents
        if docsearch:
            cultural_docs = docsearch.similarity_search(query, k=2)
            print(f"Retrieved {len(cultural_docs)} cultural context documents")
            
            cultural_info = [doc.page_content for doc in cultural_docs]
            
            # Build prompt based on user preferences
            if traditional_prefs:
                prompt = f"""Based on the following medical and traditional healthcare information:

{cultural_info}

Consider that this user has expressed interest in {practices if isinstance(traditional_prefs, dict) else traditional_prefs}.

Provide healthcare guidance that:
1. Integrates both modern medical evidence and traditional practices where appropriate
2. Clearly distinguishes between evidence-based medical advice and traditional approaches
3. Prioritizes user safety and medical accuracy
4. Respects the user's interest in traditional practices while maintaining medical rigor

Remember to:
- Always lead with evidence-based medical information
- Include traditional practices only where they complement modern medical advice
- Be clear about which recommendations come from modern medicine vs traditional practices
- Maintain a balanced and professional tone"""
            else:
                prompt = f"""Based on the following modern medical information:

{cultural_info}

This user prefers modern, evidence-based medical approaches.

Provide healthcare guidance that:
1. Is strictly based on current medical evidence and research
2. Focuses on proven medical interventions and lifestyle modifications
3. Uses clear, scientific explanations
4. Emphasizes evidence-based practices

Remember to:
- Stick to modern medical recommendations
- Provide scientific context for advice
- Use precise medical terminology
- Maintain a professional and scientific tone"""
            
            return prompt
        else:
            print("Warning: docsearch not available, using fallback prompt")
            if traditional_prefs:
                return "Provide healthcare guidance that respectfully balances modern medical evidence with traditional practices."
            else:
                return "Provide healthcare guidance based strictly on modern medical evidence."
            
    except Exception as e:
        print(f"Error generating cultural prompt: {str(e)}")
        return "Provide professional healthcare guidance based on modern medical evidence."

def get_relevant_medical_info(msg, docsearch, user_context=None):
    """Get relevant medical information with cultural and demographic context"""
    try:
        print("\n=== Retrieving Medical Information ===")
        print("Input message:", msg)
        print("User context:", user_context)
        
        if docsearch is None:
            print("Error: docsearch is None")
            return []
            
        # Get base medical information
        print("Performing similarity search...")
        medical_info = docsearch.similarity_search(msg, k=3)
        print(f"Retrieved {len(medical_info)} documents")
        
        for i, doc in enumerate(medical_info):
            print(f"\nDocument {i+1}:")
            print("Content:", doc.page_content[:200])
            
        if user_context:
            # Add region-specific medical information
            region = user_context.get("region", "general")
            print(f"\nSearching for region-specific info ({region})...")
            region_specific_info = docsearch.similarity_search(
                f"medical information specific to {region} region",
                k=2
            )
            print(f"Retrieved {len(region_specific_info)} region-specific documents")
            medical_info.extend(region_specific_info)
        
        return medical_info
    except Exception as e:
        print(f"\nError getting relevant medical information: {str(e)}")
        print("Stack trace:", e.__traceback__)
        return []

def generate_lifestyle_response(user_context):
    """Generate personalized lifestyle recommendations based on user context"""
    
    base_recommendations = [
        "Regular exercise (aim for at least 30 minutes of moderate activity daily)",
        "Adequate sleep (7-9 hours per night)",
        "Stay hydrated (drink water throughout the day)",
        "Balanced diet rich in fruits, vegetables, whole grains, and proteins",
        "Regular health check-ups",
        "Stress management through relaxation techniques"
    ]
    
    personalized_recommendations = []
    
    # Add age-specific recommendations
    age_group = user_context.get("age_group", "")
    if age_group in ["young_adult", "middle_adult"]:
        personalized_recommendations.extend([
            "Take regular breaks during work/study sessions",
            "Practice good posture, especially if working at a desk",
            "Include strength training in your exercise routine"
        ])
    
    # Add occupation-specific recommendations
    occupation = user_context.get("occupation", "")
    if occupation and "student" in occupation.lower():
        personalized_recommendations.extend([
            "Take regular study breaks (every 45-60 minutes)",
            "Practice active learning techniques",
            "Maintain a consistent sleep schedule even during exam periods"
        ])
    
    # Add medical background specific recommendations
    medical_background = user_context.get("medical_background", {})
    if medical_background:
        if medical_background.get("chronic_conditions"):
            personalized_recommendations.append("Follow your healthcare provider's specific guidelines for managing your conditions")
        
        if medical_background.get("allergies"):
            personalized_recommendations.append("Be mindful of your known allergies and maintain necessary precautions")
            
        if medical_background.get("traditional_medicine_preferences"):
            trad_prefs = medical_background["traditional_medicine_preferences"]
            if isinstance(trad_prefs, dict) and trad_prefs:
                for practice, preference in trad_prefs.items():
                    if preference:
                        personalized_recommendations.append(f"Consider incorporating {practice} as per your preferences")
    
    # Combine all recommendations
    all_recommendations = base_recommendations + personalized_recommendations
    
    # Format the response
    response = "Here are some personalized recommendations for maintaining a healthy lifestyle:\n\n"
    for i, rec in enumerate(all_recommendations, 1):
        response += f"{i}. {rec}\n"
    
    response += "\nWould you like more specific details about any of these recommendations?"
    
    return response

class DiagnosticState:
    def __init__(self):
        self.questions_asked = 0
        self.symptoms_collected = set()
        self.current_focus = None
        self.diagnosis_ready = False
        self.conversation_history = []

    def update(self, user_response, symptoms):
        """Update the diagnostic state with new information"""
        self.questions_asked += 1
        self.symptoms_collected.update(symptoms)
        self.conversation_history.append({"response": user_response, "symptoms": list(symptoms)})
        
    def get_next_question_focus(self):
        """Determine what to ask about next"""
        questions = {
            0: "duration_location",  # First ask about duration and location
            1: "characteristics",    # Then ask about characteristics
            2: "severity",          # Then ask about severity
            3: "associated_symptoms" # Finally ask about any associated symptoms
        }
        return questions.get(self.questions_asked, "additional_info")

    def has_sufficient_information(self):
        """Check if we have enough information for initial assessment"""
        return len(self.symptoms_collected) >= 2 or self.questions_asked >= 2

diagnostic_states = {}

def get_diagnostic_state(session_id):
    """Get or create diagnostic state for the session"""
    if session_id not in diagnostic_states:
        diagnostic_states[session_id] = DiagnosticState()
    return diagnostic_states[session_id]

def determine_health_category(msg, direct_chat):
    """Determine the category of the health-related query"""
    category_prompt = """Determine the category of this health-related message. Reply with ONLY ONE of these categories:
    - EMERGENCY (life-threatening conditions, severe symptoms)
    - SYMPTOM_DIAGNOSIS (analyzing specific symptoms)
    - MENTAL_HEALTH (psychological, emotional, or behavioral concerns)
    - LIFESTYLE (diet, exercise, sleep, general wellness)
    - GENERAL_HEALTH (medical information, conditions, treatments)

Message: """ + msg
    
    try:
        category_response = direct_chat.invoke(category_prompt)
        return category_response.content.strip().upper()
    except Exception as e:
        print(f"Error determining health category: {str(e)}")
        return "GENERAL_HEALTH"

def get_conversation_context(user_id, session_id, limit=5):
    """Get recent conversation history for context"""
    try:
        recent_conversations = Conversation.query.filter_by(
            user_id=user_id,
            session_id=session_id
        ).order_by(Conversation.timestamp.desc()).limit(limit).all()
        
        # Reverse to get chronological order
        recent_conversations.reverse()
        
        context = []
        for conv in recent_conversations:
            context.append({"role": "user", "content": conv.message})
            context.append({"role": "assistant", "content": conv.bot_response})
        return context
    except Exception as e:
        print(f"Error getting conversation context: {str(e)}")
        return []

def extract_symptoms(msg):
    """Extract symptoms from user message"""
    # Simple symptom extraction - can be enhanced with NLP
    symptoms = set(msg.lower().split())
    return symptoms

def generate_follow_up_question(focus, symptoms_collected):
    """Generate specific follow-up questions based on context"""
    general_questions = {
        "duration_location": "Could you tell me when these symptoms started and where exactly you're experiencing them?",
        "characteristics": "How would you describe the symptoms - their nature, pattern, and any specific triggers you've noticed?",
        "severity": "On a scale of 1-10, how would you rate the severity of your symptoms? Has this changed over time?",
        "associated_symptoms": "Have you noticed any other symptoms occurring alongside these main concerns?",
        "additional_info": "Is there anything else you'd like to share about your symptoms or health concerns?"
    }
    
    # If we have symptoms, make the question more specific
    if symptoms_collected:
        symptoms_list = list(symptoms_collected)
        if focus == "duration_location":
            return f"When did you first notice the {symptoms_list[0]} and where exactly do you experience it?"
        elif focus == "characteristics":
            return f"Could you describe how the {symptoms_list[0]} feels? For example, is it constant or does it come and go?"
        elif focus == "severity":
            return f"On a scale of 1-10, how severe is the {symptoms_list[0]}? Has this changed since it started?"
        elif focus == "associated_symptoms":
            return f"Besides {', '.join(symptoms_list)}, have you noticed any other symptoms?"
    
    return general_questions.get(focus, "Could you tell me more about what you're experiencing?")

def check_pinecone_index():
    """Check Pinecone index status and content"""
    try:
        print("\n=== Checking Pinecone Index ===")
        if not pc or not docsearch:
            print("Error: Pinecone client or vector store not initialized")
            return False
            
        # Get index statistics
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        print("\nIndex Statistics:")
        print(f"Total vectors: {stats.total_vector_count}")
        print(f"Dimension: {stats.dimension}")
        
        # Test query
        print("\nPerforming test query...")
        test_query = "health"
        results = docsearch.similarity_search(test_query, k=1)
        if results:
            print("Test query successful")
            print("Sample result:", results[0].page_content[:100])
        else:
            print("Test query returned no results")
            
        return True
    except Exception as e:
        print(f"Error checking Pinecone index: {str(e)}")
        return False

def get_medical_documents(query, user_context=None, k=3):
    """Retrieve relevant medical documents from the knowledge base"""
    try:
        print("\n=== Retrieving Medical Documents ===")
        print(f"Query: {query}")
        print(f"User context: {user_context}")
        
        if not docsearch:
            print("Error: docsearch is None")
            return []
            
        # Build enhanced query based on user context
        enhanced_query = query
        if user_context:
            # Add traditional medicine preferences to query if present
            medical_background = user_context.get("medical_background", {})
            traditional_prefs = medical_background.get("traditional_medicine_preferences", {})
            
            if traditional_prefs:
                if isinstance(traditional_prefs, dict):
                    practices = ", ".join(traditional_prefs.keys())
                    enhanced_query += f" including {practices} approaches"
                else:
                    enhanced_query += f" including {traditional_prefs} approaches"
            
            # Add chronic conditions to query
            if medical_background.get("chronic_conditions"):
                conditions = medical_background["chronic_conditions"]
                enhanced_query += f" considering conditions: {', '.join(conditions)}"
            
            # Add region-specific context
            region = user_context.get("region", "general")
            enhanced_query += f" for {region} region"
            
        print(f"Enhanced query: {enhanced_query}")
        
        # Retrieve documents
        docs = docsearch.similarity_search(enhanced_query, k=k)
        print(f"Retrieved {len(docs)} documents")
        
        # Log document contents
        for i, doc in enumerate(docs):
            print(f"\nDocument {i+1}:")
            print("Content:", doc.page_content[:200])
            print("Source:", getattr(doc.metadata, 'source', 'Unknown'))
            
        # If user has traditional medicine preferences, get additional relevant documents
        if user_context and user_context.get("medical_background", {}).get("traditional_medicine_preferences"):
            trad_prefs = user_context["medical_background"]["traditional_medicine_preferences"]
            if isinstance(trad_prefs, dict):
                for practice, enabled in trad_prefs.items():
                    if enabled:
                        print(f"\nRetrieving additional documents for {practice}...")
                        practice_docs = docsearch.similarity_search(
                            f"{practice} medicine {query}",
                            k=2
                        )
                        docs.extend(practice_docs)
                        print(f"Added {len(practice_docs)} documents for {practice}")
        
        return docs
    except Exception as e:
        print(f"\nError getting relevant medical information: {str(e)}")
        print("Stack trace:", e.__traceback__)
        return []

def generate_rag_response(query, docs, user_context=None, chat_history=None):
    """Generate a response using retrieved documents and user context"""
    try:
        print("\n=== Generating RAG Response ===")
        
        # Process retrieved information
        doc_content = "\n\n".join([doc.page_content for doc in docs])
        
        # Format chat history if available
        history_context = ""
        if chat_history:
            history_context = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in chat_history[-3:]
            ])
        
        # Build personalization context
        user_details = ""
        greeting = "Hello! "
        
        if user_context:
            # Get user information
            username = user_context.get("username", "")
            age_group = user_context.get("age_group", "")
            region = user_context.get("region", "")
            city = user_context.get("city", "")
            
            # Create personalized greeting with just the username
            if username:
                greeting = f"Hello {username}! "
            
            # Build age-appropriate context
            age_specific = ""
            if age_group == "young_adult":
                age_specific = "considering your busy lifestyle as a young adult"
            elif age_group == "middle_adult":
                age_specific = "at this stage of life"
            elif age_group == "mature_adult":
                age_specific = "as we focus on maintaining good health"
            elif age_group == "elderly":
                age_specific = "with a focus on gentle and sustainable practices"
            
            # Get medical background
            medical_background = user_context.get("medical_background", {})
            traditional_prefs = medical_background.get("traditional_medicine_preferences", {})
            
            # Build cultural context
            cultural_notes = ""
            if region.lower() == "india":
                cultural_notes = """
Consider:
- Local seasonal fruits and vegetables
- Traditional Indian cooking methods
- Regional exercise practices like yoga
- Local weather and lifestyle
- Common local ingredients and spices
- Cultural dietary preferences
- Traditional wellness practices"""
            
            user_details = f"""
Personalization Notes:
- Greeting: {greeting}
- Age Context: {age_specific}
- Region: {region}
- Traditional Preferences: {traditional_prefs if traditional_prefs else 'Modern approach preferred'}
{cultural_notes}"""
        
        # Build the prompt
        prompt = f"""You are having a friendly conversation about health and wellness. Use the following medical information to provide accurate, evidence-based advice while keeping the tone conversational:

Retrieved Medical Information:
{doc_content}

About the User:
{user_details}

Previous Conversation:
{history_context}

Current Question: {query}

Respond in a warm, conversational way while incorporating the retrieved medical information:
- Start with the personalized greeting (use ONLY the user's name, not their location)
- Speak naturally as if chatting with a friend
- Use local references and examples when relevant
- Include specific information from the retrieved medical knowledge
- Keep medical information accurate but approachable
- Make recommendations based on both medical evidence and cultural context
- End with an encouraging note and invite further questions"""

        # Generate response
        chat = ChatOpenAI(model='gpt-4', temperature=0.7)
        response = chat.invoke(prompt)
        
        print("\nGenerated evidence-based conversational response")
        return str(response.content)
        
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return "I'm having trouble accessing the medical information right now. Could you please try asking your question again?"

def process_health_query(query, user_context=None, chat_history=None):
    """Process a health-related query using RAG"""
    try:
        print("\n=== Processing Health Query ===")
        print(f"Query: {query}")
        
        # Get relevant medical documents
        docs = get_medical_documents(query, user_context)
        if not docs:
            return "I apologize, but I couldn't retrieve the relevant medical information. Please try rephrasing your question."
            
        # Generate response using RAG
        response = generate_rag_response(query, docs, user_context, chat_history)
        
        return response
        
    except Exception as e:
        print(f"Error processing health query: {str(e)}")
        return "I apologize, but something went wrong while processing your query. Please try again."

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

