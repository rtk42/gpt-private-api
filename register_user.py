from google.cloud import firestore
from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def register_user(username, password):
    # Initialize Firestore
    db = firestore.Client()
    
    # Check if user already exists
    users_ref = db.collection('users')
    query = users_ref.where('username', '==', username).limit(1).get()
    
    if query:
        print(f"User {username} already exists")
        return False
    
    # Generate password hash using pbkdf2:sha256 method
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    # Add user to Firestore
    users_ref.add({
        'username': username,
        'password_hash': password_hash,
        'created_at': firestore.SERVER_TIMESTAMP
    })
    
    # Add user to .users file
    with open('.users', 'a') as f:
        f.write(f"{username}:{password}\n")
    
    print(f"User {username} registered successfully")
    return True

if __name__ == "__main__":
    username = input("Enter username: ")
    password = input("Enter password: ")
    register_user(username, password) 