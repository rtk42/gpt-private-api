from flask import Flask, request, jsonify
from werkzeug.security import check_password_hash
from google.cloud import firestore
import openai
import os
from dotenv import load_dotenv
import logging
import traceback
from utils import count_tokens, get_secret
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load environment variables from .env file if it exists (for local development)
load_dotenv()

# OpenAI configuration
MODELS = ['gpt-3.5-turbo', 'gpt-4']

# Initialize OpenAI client
try:
    if os.getenv('GOOGLE_CLOUD_PROJECT'):
        # Production: Get API key from Secret Manager
        api_key = get_secret("openai-api-key")
    else:
        # Local development: Get API key from .env file
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
    
    client = openai.OpenAI(api_key=api_key)
    logger.info("Successfully initialized OpenAI client")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# Initialize Firestore
try:
    db = firestore.Client()
    logger.info("Successfully connected to Firestore")
except Exception as e:
    logger.error(f"Failed to connect to Firestore: {str(e)}")
    logger.error(traceback.format_exc())
    raise

def authenticate_user(username, password):
    """Authenticate user against Firestore."""
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username).limit(1).get()
        
        if query:
            user_data = query[0].to_dict()
            if check_password_hash(user_data['password_hash'], password):
                logger.info(f"User authenticated successfully: {username}")
                return True
        
        logger.warning(f"Authentication failed for user: {username}")
        return False
    except Exception as e:
        logger.error(f"Error authenticating user {username}: {str(e)}")
        logger.error(traceback.format_exc())
        return False

@app.route('/generate_itinerary', methods=['POST'])
def generate_itinerary():
    """Generate a trip itinerary based on city and number of days."""
    try:
        # Get request data
        data = request.json
        username = data.get('username')
        password = data.get('password')
        model = data.get('model')
        city = data.get('city')
        days = data.get('days')

        # Validate required parameters
        if not all([username, password, model, city, days]):
            logger.warning("Missing required parameters in request")
            return jsonify({'error': 'Missing required parameters'}), 400

        # Validate model
        if model not in MODELS:
            logger.warning(f"Invalid model requested: {model}")
            return jsonify({'error': 'Invalid model'}), 400

        # Authenticate user
        if not authenticate_user(username, password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Create prompt for itinerary generation
        prompt = f"""Create a detailed {days}-day itinerary for {city}. Return the response in the following JSON format:
        {{
            "city": "{city}",
            "days": {days},
            "itinerary": [
                {{
                    "day": 1,
                    "activities": [
                        {{
                            "time": "09:00",
                            "activity": "Activity name",
                            "duration": "2 hours",
                            "location": "Location name",
                            "description": "Brief description"
                        }}
                    ]
                }}
            ],
            "travel_tips": [
                "Tip 1",
                "Tip 2"
            ],
            "budget_considerations": {{
                "currency": "USD",
                "estimated_costs": {{
                    "accommodation": "Price range",
                    "food": "Price range",
                    "transportation": "Price range",
                    "activities": "Price range"
                }}
            }}
        }}
        
        Make sure to:
        1. Include realistic times and durations
        2. Provide specific locations and descriptions
        3. Include practical travel tips
        4. Give realistic budget estimates
        5. Format the response as valid JSON"""

        # Log the request
        token_count = count_tokens(prompt, model)
        logger.info(f"Generating itinerary for {city} - {days} days, Model: {model}, Tokens: {token_count}")

        # Generate itinerary using OpenAI
        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': 'You are a professional travel planner. Always respond with valid JSON format.'},
                {'role': 'user', 'content': prompt}
            ],
            response_format={ "type": "json_object" }
        )

        # Log the response
        response_content = response.choices[0].message.content
        response_tokens = count_tokens(response_content, model)
        logger.info(f"Generated itinerary - Tokens: {response_tokens}")

        # Parse the JSON response to ensure it's valid
        try:
            itinerary_json = json.loads(response_content)
            return jsonify(itinerary_json)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
            return jsonify({
                'error': 'Failed to generate valid itinerary format',
                'details': str(e)
            }), 500

    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'An error occurred while generating the itinerary'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) 