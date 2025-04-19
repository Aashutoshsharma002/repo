from app import app, db
from models import User
from werkzeug.security import generate_password_hash
import sys

def create_admin_user(force=False):
    with app.app_context():
        # Check if admin user already exists
        existing_admin = User.query.filter_by(username='admin').first()
        
        if existing_admin:
            if force:
                # Update existing admin password
                existing_admin.password_hash = generate_password_hash('admin@123')
                existing_admin.email = 'admin@jockeywarehouse.com'
                existing_admin.role = 'admin'
                db.session.commit()
                print("Admin user updated successfully!")
                print("Username: admin")
                print("Password: admin@123")
            else:
                print("Admin user already exists. Use --force to update password.")
            return
        
        # Create new admin user
        admin_user = User(
            username='admin',
            email='admin@jockeywarehouse.com',
            password_hash=generate_password_hash('admin@123'),
            role='admin'  # Set role to admin
        )
        
        # Add to database and commit
        db.session.add(admin_user)
        db.session.commit()
        
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin@123")

if __name__ == "__main__":
    force_update = '--force' in sys.argv
    create_admin_user(force=force_update)