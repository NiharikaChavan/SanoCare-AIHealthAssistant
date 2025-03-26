from flask import Flask
from src.database import db, User, Conversation
from dotenv import load_dotenv
import os
from sqlalchemy import text
from app import app

app = Flask(__name__)
load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost:5432/medicaldb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_database():
    print("Checking database connection and contents...")
    
    try:
        # Test database connection
        with app.app_context():
            # Check if schema exists
            result = db.session.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'medical'"))
            schema_exists = result.scalar() is not None
            print(f"\n1. Schema 'medical' exists: {schema_exists}")
            
            if schema_exists:
                # Check if users table exists
                result = db.session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'medical' 
                    AND table_name = 'users'
                """))
                table_exists = result.scalar() is not None
                print(f"2. Users table exists: {table_exists}")
                
                if table_exists:
                    # Get table structure
                    result = db.session.execute(text("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_schema = 'medical' 
                        AND table_name = 'users'
                    """))
                    columns = result.fetchall()
                    print("\n3. Users table structure:")
                    for col in columns:
                        print(f"   - {col[0]}: {col[1]}")
                    
                    # Count users
                    user_count = User.query.count()
                    print(f"\n4. Total users in database: {user_count}")
                    
                    # List all users
                    users = User.query.all()
                    print("\n5. User records:")
                    for user in users:
                        print(f"   - ID: {user.user_id}, Username: {user.username}, Email: {user.email}")
                else:
                    print("Users table does not exist!")
            else:
                print("Schema 'medical' does not exist!")
                
    except Exception as e:
        print(f"Error checking database: {str(e)}")

if __name__ == "__main__":
    check_database() 