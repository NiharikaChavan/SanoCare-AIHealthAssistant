from datetime import datetime, timedelta
import re
import uuid
from flask import Flask, logging, render_template, jsonify, request, session, redirect, url_for, flash
from src.helper import download_hugging_face_embeddings,get_who_data
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
    print("\n=== Application Startup ===")
    print("Database initialized")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add a before_request handler to ensure clean session state
@app.before_request
def before_request():
    if not current_user.is_authenticated:
        session.clear()
        session.modified = True
        print("\n=== Request Start ===")
        print("Session cleared for non-authenticated user")
        print("Session data:", dict(session))

PINECONE_API_KEY=os.environ.get('PINECONE_API_KEY')
OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')

print("OpenAI API Key loaded:", "Yes" if OPENAI_API_KEY else "No")
print("Pinecone API Key loaded:", "Yes" if PINECONE_API_KEY else "No")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

embeddings = download_hugging_face_embeddings()

index_name = "sanocare"

#Embed each chunk and upsert the embeddings into your Pinecone index.
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k":3})
print(retriever)

value = get_who_data('India')

llm = ChatOpenAI(
    model='gpt-4',
    temperature=0.4,
    max_tokens=500
)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", """Please provide a response based on the following context and question. 
    
Context: {context}

Question: {input}

Remember to use the provided context to inform your response while maintaining a professional and empathetic tone.""")
])

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

def store_conversation(user_id, message, bot_response, session_id):
    """Store conversation in the database"""
    try:
        print("\nAttempting to store conversation:")
        print(f"User ID: {user_id}")
        print(f"Session ID: {session_id}")
        print(f"Message length: {len(message)}")
        print(f"Response length: {len(bot_response)}")
        
        # Strict validation for user authentication
        if not user_id or not isinstance(user_id, int):
            print("Error: Invalid or missing user_id")
            return False
            
        # Verify user exists in database
        user = User.query.get(user_id)
        if not user:
            print("Error: User not found in database")
            return False
            
        if not session_id:
            print("Error: No session_id provided")
            return False
            
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
            
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            date_of_birth = datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date()
            gender = data.get('gender')
            country_code = data.get('country_code')
            
            print(f"Parsed data: username={username}, email={email}, gender={gender}, country_code={country_code}")
            
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
            
            # Create new user
            user = User(
                username=username,
                email=email,
                date_of_birth=date_of_birth,
                gender=gender,
                country_code=country_code
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
                        'email': user.email
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
def chat():
    try:
        # Get message from JSON data
        data = request.get_json() if request.is_json else request.form
        msg = data.get("msg")
        if not msg:
            return jsonify({
                "success": False,
                "error": "No message provided"
            }), 400

        print("\n" + "="*50)
        print("Received input:", msg)
        print("User authenticated:", current_user.is_authenticated)
        print("Current user:", current_user.get_id() if current_user.is_authenticated else None)
        print("Session ID:", session.get('session_id'))
        print("Session data:", dict(session))
        
        # Create a direct chat without retrieval for non-health queries
        direct_chat = ChatOpenAI(
            model='gpt-4',
            temperature=0.4,
            max_tokens=500
        )
        
        # First, check if this is a health-related query
        health_check_response = direct_chat.invoke(
            "Is the following message asking about health, medical conditions, symptoms, lifestyle, or mental health? Reply with just 'yes' or 'no': " + msg
        )
        is_health_related = health_check_response.content.strip().lower() == 'yes'
        
        # Get the response based on whether it's health-related
        if is_health_related:
            # Use the RAG chain for health-related queries
            retrieved_docs = retriever.get_relevant_documents(msg)
            print("\nRetrieved documents from Pinecone:")
            for i, doc in enumerate(retrieved_docs):
                print(f"\nDocument {i+1}:")
                print(f"Content: {doc.page_content[:200]}...")
                print(f"Metadata: {doc.metadata}")
            
            chain_response = rag_chain.invoke({
                "input": msg
            })
            final_response = str(chain_response["answer"])
        else:
            # Use direct chat for non-health queries
            chat_response = direct_chat.invoke(
                "Respond to this message naturally without assuming any health context: " + msg
            )
            final_response = str(chat_response.content)
        
        # For non-authenticated users, just return the response without storing
        if not current_user.is_authenticated:
            print("User not logged in - skipping database storage")
            return jsonify({
                "success": True,
                "response": final_response,
                "timestamp": datetime.now().isoformat(),
                "message": "Please log in to save your conversations"
            })
        
        # Only proceed with storage if user is authenticated
        try:
            print("Authenticated user - storing conversation")
            # Generate or get session_id only for authenticated users
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())
                session.modified = True  # Ensure session is saved
                print("Generated new session ID:", session['session_id'])
            
            # Additional validation for authenticated user
            if not current_user.user_id:
                print("Error: User ID not found for authenticated user")
                return jsonify({
                    "success": True,
                    "response": final_response,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Error: User ID not found"
                })
                
            store_success = store_conversation(
                user_id=current_user.user_id,
                message=msg,
                bot_response=final_response,
                session_id=session['session_id']
            )
            print("Conversation stored:", store_success)
        except Exception as e:
            print("Error storing conversation:", str(e))
        
        return jsonify({
            "success": True,
            "response": final_response,
            "timestamp": datetime.now().isoformat()
        })
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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

