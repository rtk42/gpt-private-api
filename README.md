# LLM Chatbot with User Management

A Flask-based web application that provides a chat interface for interacting with OpenAI's language models (GPT-3.5 and GPT-4) with secure user authentication and management.

## Features

- **Chat Interface**
  - Support for GPT-3.5 and GPT-4 models
  - Real-time chat responses
  - Token counting for requests and responses
  - Error handling and logging

- **User Management**
  - Secure user authentication
  - User registration and deletion
  - Session management with Redis (production) or filesystem (development)
  - Password hashing using pbkdf2:sha256
  - Support for both Firestore and local user storage

- **Security**
  - Secure password hashing
  - Session protection
  - Environment variable configuration
  - Secure cookie settings

## Prerequisites

- Python 3.9 or higher
- Redis (for production)
- Google Cloud Project with Firestore enabled
- OpenAI API key

## Installation

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

4. Set up environment variables in `.env`:
```
FLASK_ENV=development
FLASK_SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key
```

## Local Development

1. Start Redis (if using production mode):
```bash
brew services start redis  # macOS
```

2. Run the application:
```bash
python app.py
```

3. Access the application at `http://localhost:8080`

## User Management

The application provides scripts for managing users:

1. Add a new user:
```bash
python add_user.py
```
This will prompt you to enter:
- Username
- Password

2. Delete a user:
```bash
python delete_user.py
```
This will prompt you to enter:
- Username to delete

3. List all users:
```bash
python list_users.py
```
This will display all registered users.

The user management system:
- Stores user credentials securely in Firestore
- Uses pbkdf2:sha256 for password hashing
- Maintains a local `.users` file for development purposes
- Provides logging for all user management operations

## Deployment

1. Build the Docker container:
```bash
gcloud builds submit --tag gcr.io/[PROJECT-ID]/llm-chatbot
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy llm-chatbot \
  --image gcr.io/[PROJECT-ID]/llm-chatbot \
  --platform managed \
  --region [REGION] \
  --allow-unauthenticated \
  --set-secrets=OPENAI_API_KEY=openai-api-key:latest,FLASK_SECRET_KEY=flask-secret-key:latest
```

## Project Structure

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

## Logging

The application includes comprehensive logging:
- User authentication events
- Chat requests and responses
- Token counts
- Error tracking
- Session management

## Security Considerations

- Passwords are hashed using pbkdf2:sha256
- Sessions are protected with secure cookie settings
- Environment variables for sensitive data
- Redis for production session storage
- Firestore for user data storage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.