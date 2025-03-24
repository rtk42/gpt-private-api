from google.cloud import firestore
import os

def delete_user(username):
    # Initialize Firestore
    db = firestore.Client()
    
    # Find user document in Firestore
    users_ref = db.collection('users')
    query = users_ref.where('username', '==', username).limit(1).get()
    
    if not query:
        print(f"User {username} does not exist")
        return False
    
    # Delete user from Firestore
    query[0].reference.delete()
    
    # Delete user from .users file
    if os.path.exists('.users'):
        with open('.users', 'r') as f:
            lines = f.readlines()
        
        with open('.users', 'w') as f:
            for line in lines:
                if not line.startswith(f"{username}:"):
                    f.write(line)
    
    print(f"User {username} has been deleted successfully")
    return True

if __name__ == "__main__":
    username = input("Enter username to delete: ")
    delete_user(username) 