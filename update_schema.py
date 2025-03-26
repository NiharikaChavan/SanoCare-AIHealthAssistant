from flask import Flask
from src.database import db
from sqlalchemy import text

def update_schema():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost:5432/medicaldb'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        try:
            # Alter the password_hash column to increase its size
            db.session.execute(text("""
                ALTER TABLE medical.users 
                ALTER COLUMN password_hash TYPE VARCHAR(512);
            """))
            db.session.commit()
            print("✓ Successfully updated password_hash column size to VARCHAR(512)")

            # Make user_id nullable in conversations table
            db.session.execute(text("""
                ALTER TABLE medical.conversations 
                ALTER COLUMN user_id DROP NOT NULL;
            """))
            db.session.commit()
            print("✓ Successfully made user_id nullable in conversations table")
        except Exception as e:
            print("❌ Error updating schema:", str(e))
            db.session.rollback()

if __name__ == "__main__":
    update_schema() 