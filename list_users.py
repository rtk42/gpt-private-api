from google.cloud import firestore

def list_users():
    # Initialize Firestore
    db = firestore.Client()
    
    # Get all users
    users_ref = db.collection('users')
    users = users_ref.get()
    
    print("\nUsers in Firestore:")
    print("-" * 50)
    for user in users:
        user_data = user.to_dict()
        print(f"Username: {user_data['username']}")
        print(f"Password Hash: {user_data['password_hash']}")
        print(f"Document ID: {user.id}")
        print("-" * 50)

if __name__ == "__main__":
    list_users() 