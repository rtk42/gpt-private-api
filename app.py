from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_session import Session
from dotenv import load_dotenv
import os
import openai
from werkzeug.security import generate_password_hash, check_password_hash
from google.cloud import firestore
from datetime import timedelta
import redis
import logging
import traceback
from utils import count_tokens

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Use environment variable for secret key in production
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

# Configure session based on environment
if os.getenv('FLASK_ENV') == 'development':
    logger.info("Using filesystem session for development")
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
else:
    logger.info("Using Redis session for production")
    app.config['SESSION_TYPE'] = 'redis'
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    logger.info(f"Using Redis URL: {redis_url}")
    try:
        app.config['SESSION_REDIS'] = redis.from_url(redis_url)
        logger.info("Successfully connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        logger.error(traceback.format_exc())
        raise

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_COOKIE_SECURE'] = True  # Enable secure cookies in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize Flask-Session
Session(app)

load_dotenv()

# OpenAI configuration
MODELS = ['gpt-3.5-turbo', 'gpt-4']
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Clean up API key if it contains quotes or prefix
if OPENAI_API_KEY:
    OPENAI_API_KEY = OPENAI_API_KEY.strip().strip('"').strip("'")
    if OPENAI_API_KEY.startswith('OPENAI_API_KEY='):
        OPENAI_API_KEY = OPENAI_API_KEY[len('OPENAI_API_KEY='):].strip()

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not set")
    raise ValueError("Please set OPENAI_API_KEY in your .env file")

# Set the API key and initialize the OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize Firestore
try:
    db = firestore.Client()
    logger.info("Successfully connected to Firestore")
except Exception as e:
    logger.error(f"Failed to connect to Firestore: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# User management
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = username  # Use username as the ID for Flask-Login
        self.username = username
        self.password_hash = password_hash
        self._firestore_id = id  # Store Firestore document ID separately

    @staticmethod
    def get(user_id):
        try:
            users_ref = db.collection('users')
            query = users_ref.where('username', '==', user_id).limit(1).get()
            
            if query:
                user_data = query[0].to_dict()
                return User(query[0].id, user_data['username'], user_data['password_hash'])
            return None
        except Exception as e:
            logger.error(f"Error getting user from Firestore: {str(e)}")
            logger.error(traceback.format_exc())
            return None

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            user = User.get(username)
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                session.permanent = True
                logger.info(f"User logged in successfully: {username}")
                return redirect(url_for('home'))
            
            logger.warning(f"Failed login attempt for username: {username}")
            flash('Invalid username or password')
        except Exception as e:
            logger.error(f"Error during login for user {username}: {str(e)}")
            logger.error(traceback.format_exc())
            flash('An error occurred during login')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    session.clear()
    logger.info(f"User logged out: {username}")
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    logger.info(f"User accessed home page: {current_user.username}")
    return render_template('index.html', models=MODELS, username=current_user.username)

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    model = data.get('model')
    message = data.get('message')
    username = current_user.username

    if not all([model, message]):
        logger.warning(f"Missing parameters in chat request from user: {username}")
        return jsonify({'error': 'Missing required parameters'}), 400

    if model not in MODELS:
        logger.warning(f"Invalid model requested by user {username}: {model}")
        return jsonify({'error': 'Invalid model'}), 400

    try:
        # Log the request details
        token_count = count_tokens(message, model)
        logger.info(f"Chat request from user {username} - Model: {model}, Tokens: {token_count}")

        response = openai_client.chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': message}]
        )
        
        # Log the response details
        response_content = response.choices[0].message.content
        response_tokens = count_tokens(response_content, model)
        logger.info(f"Chat response for user {username} - Tokens: {response_tokens}")
        
        return jsonify({'response': response_content})

    except Exception as e:
        logger.error(f"Error in chat endpoint for user {username}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'An error occurred while processing your request'}), 500

if __name__ == '__main__':
    os.environ['FLASK_ENV'] = 'development'
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 