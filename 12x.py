from app import create_app, db  # Ensure you're importing from the correct app module
from app.models.models import User  # Import your User model
from werkzeug.security import generate_password_hash
import getpass

# Create the Flask app
app = create_app()

def create_user():
    print("Starting user creation process...")  # Debugging print
    with app.app_context():  # Ensure app context is active
        # Create the database tables if they don't exist
        print("Creating database tables...")  # Debugging print
        db.create_all()

        # Check if the user already exists
        username = input("Enter New user Username: ")
        if User.query.filter_by(username=username).first():
            print("User with this username already exists.")
            return

        # Prompt for email
        email = input("Enter the email address for the user: ")

        # Check if the email is already registered
        if User.query.filter_by(email=email).first():
            print("A user with this email already exists.")
            return

        # Prompt for secure password
        password = getpass.getpass('Enter a secure password for the user: ')
        confirm_password = getpass.getpass('Confirm the password: ')

        # Check if passwords match
        if password != confirm_password:
            print("Passwords do not match. Please try again.")
            return

        # Prompt for user role
        role = input("Enter the role for this user (admin/owner/agent): ").lower()
        if role not in ['admin', 'owner', 'agent']:
            print("Invalid role. Please enter 'admin', 'owner', or 'agent'.")
            return

        # Create and add the user
        new_user = User(
            username=username,
            email=email,
            role=role  # Set the role here
        )
        new_user.set_password(password)  # Set the hashed password
        db.session.add(new_user)
        db.session.commit()
        print("User created successfully.")

if __name__ == '__main__':
    create_user()
