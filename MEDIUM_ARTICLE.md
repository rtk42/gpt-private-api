# Building a Secure LLM Chatbot with Flask, OpenAI, and Google Cloud

A comprehensive guide to building a production-ready chatbot application with user authentication, secure session management, and token counting.

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Architecture](#architecture)
- [Setup and Installation](#setup-and-installation)
- [Core Components](#core-components)
- [Security Implementation](#security-implementation)
- [Deployment](#deployment)
- [Best Practices](#best-practices)

## Introduction

In this article, we'll explore how to build a secure chatbot application that leverages OpenAI's language models (GPT-3.5 and GPT-4) while implementing robust user authentication and session management. The application is built with Flask and deployed on Google Cloud Run, making it scalable and production-ready.

## Features

- **Multi-Model Support**: Integration with OpenAI's GPT-3.5 and GPT-4 models
- **Secure Authentication**: User management with password hashing
- **Session Management**: Redis-based session handling in production
- **Token Counting**: Real-time token usage tracking
- **Structured Logging**: Comprehensive logging for monitoring and debugging
- **Cloud-Native**: Designed for deployment on Google Cloud Run
- **Development/Production Parity**: Consistent behavior across environments

## Architecture

The application follows a modular architecture with the following components:

```
llm-chatbot/
├── app.py              # Main Flask application
├── utils.py            # Utility functions (token counting)
├── add_user.py         # User registration script
├── delete_user.py      # User deletion script
├── list_users.py       # User listing script
├── templates/          # HTML templates
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container configuration
└── .env              # Environment variables
```

### Key Technologies
- **Backend**: Flask
- **Authentication**: Flask-Login
- **Session Management**: Flask-Session with Redis
- **Database**: Google Cloud Firestore
- **LLM Provider**: OpenAI
- **Containerization**: Docker
- **Cloud Platform**: Google Cloud Run

## Setup and Installation

### Prerequisites
- Python 3.9 or higher
- Redis (for production)
- Google Cloud Project with Firestore enabled
- OpenAI API key

### Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd llm-chatbot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables in `.env`:
```env
FLASK_ENV=development
FLASK_SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key
```

5. Start Redis (if using production mode):
```bash
brew services start redis  # macOS
```

6. Run the application:
```bash
python app.py
```

## Core Components

### 1. User Management

The application implements a robust user management system using Firestore and local storage for development:

```python
# app.py
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = username
        self.username = username
        self.password_hash = password_hash
        self._firestore_id = id

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
            return None
```

### 2. Session Management

The application uses different session backends based on the environment:

```python
# app.py
if os.getenv('FLASK_ENV') == 'development':
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
else:
    app.config['SESSION_TYPE'] = 'redis'
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    app.config['SESSION_REDIS'] = redis.from_url(redis_url)
```

### 3. Chat Implementation

The chat endpoint handles model selection and token counting:

```python
@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    model = data.get('model')
    message = data.get('message')
    
    try:
        token_count = count_tokens(message, model)
        logger.info(f"Chat request - Model: {model}, Tokens: {token_count}")

        response = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': message}]
        )
        
        response_content = response.choices[0].message.content
        response_tokens = count_tokens(response_content, model)
        logger.info(f"Chat response - Tokens: {response_tokens}")
        
        return jsonify({'response': response_content})
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500
```

### 4. Token Counting

The application includes a utility for counting tokens:

```python
# utils.py
def count_tokens(text, model):
    """Count the number of tokens in a text string."""
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': text}],
            max_tokens=1
        )
        return response.usage.total_tokens
    except Exception as e:
        logger.error(f"Error counting tokens: {str(e)}")
        return 0
```

## Security Implementation

### 1. Password Hashing

Passwords are securely hashed using Werkzeug's security functions:

```python
# app.py
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = User.get(username)
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        session.permanent = True
        return redirect(url_for('home'))
```

### 2. Session Security

The application implements secure session settings:

```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

## Deployment

### 1. Docker Configuration

The application is containerized using Docker:

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
```

### 2. Cloud Run Deployment

Deploy to Google Cloud Run:

```bash
# Build the container
gcloud builds submit --tag gcr.io/[PROJECT-ID]/llm-chatbot

# Deploy to Cloud Run
gcloud run deploy llm-chatbot \
  --image gcr.io/[PROJECT-ID]/llm-chatbot \
  --platform managed \
  --region [REGION] \
  --allow-unauthenticated \
  --set-secrets=OPENAI_API_KEY=openai-api-key:latest,FLASK_SECRET_KEY=flask-secret-key:latest
```

## Best Practices

### 1. Logging

The application implements structured logging:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### 2. Error Handling

Comprehensive error handling with detailed logging:

```python
try:
    # Operation
except Exception as e:
    logger.error(f"Error: {str(e)}")
    logger.error(traceback.format_exc())
    return jsonify({'error': 'An error occurred'}), 500
```

### 3. Environment Configuration

Environment-specific settings:

```python
if os.getenv('FLASK_ENV') == 'development':
    # Development settings
else:
    # Production settings
```

## Conclusion

This implementation provides a solid foundation for building a production-ready chatbot application. The combination of Flask, OpenAI, and Google Cloud services creates a scalable and secure solution that can be easily extended with additional features.

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Redis Documentation](https://redis.io/documentation)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)

## About the Author

[Your Name] is a software engineer specializing in cloud-native applications and AI/ML solutions. Connect with me on [LinkedIn](your-linkedin-profile) or follow me on [GitHub](your-github-profile). 