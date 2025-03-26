from flask import Flask
from src.database import db, User, Conversation
from sqlalchemy import text
from datetime import datetime
import sys

def test_db():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost:5432/medicaldb'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        try:
            print("Test 1: Testing database connection...")
            # Test connection
            result = db.session.execute(text("SELECT 1")).scalar()
            print("✓ Database connection successful!")
            
            print("\nTest 2: Checking if 'medical' schema exists...")
            result = db.session.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'medical';
            """)).scalar()
            if result:
                print("✓ Medical schema exists!")
            else:
                print("❌ Medical schema does not exist!")
                
            print("\nTest 3: Checking if tables exist in the medical schema...")
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'medical';
            """)).fetchall()
            tables = [row[0] for row in result]
            print(f"Tables found in medical schema: {tables}")

            print("\nTest 4: Updating password_hash column size...")
            db.session.execute(text("""
                ALTER TABLE medical.users 
                ALTER COLUMN password_hash TYPE VARCHAR(512);
            """))
            db.session.commit()
            print("✓ Column size updated successfully!")

            print("\nTest 5: Verifying password_hash column size...")
            result = db.session.execute(text("""
                SELECT character_maximum_length 
                FROM information_schema.columns 
                WHERE table_schema = 'medical' 
                AND table_name = 'users' 
                AND column_name = 'password_hash';
            """)).scalar()
            print(f"Password hash column size: {result}")
            
            print("\nTest 6: Attempting to create a test user...")
            # Try to create a test user
            test_user = User(
                username='test_user',
                email='test@example.com',
                date_of_birth=datetime.strptime('2000-01-01', '%Y-%m-%d').date(),
                gender='other',
                country_code='+1'
            )
            test_user.set_password('test_password')
            
            # Check if user already exists
            existing_user = User.query.filter_by(email='test@example.com').first()
            if existing_user:
                print("✓ Test user already exists")
            else:
                db.session.add(test_user)
                db.session.commit()
                print("✓ Test user created successfully!")
                
        except Exception as e:
            print("\n❌ Error:", str(e))
            db.session.rollback()

if __name__ == "__main__":
    test_db() 