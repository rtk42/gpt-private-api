import os
import tiktoken
from google.cloud import secretmanager
import logging

logger = logging.getLogger(__name__)

def count_tokens(text, model="gpt-3.5-turbo"):
    """Count the number of tokens in a text string based on the model's encoding."""
    try:
        # Map models to their corresponding encodings
        model_encoding_map = {
            "gpt-3.5-turbo": "cl100k_base",
            "gpt-4": "cl100k_base",
            "gpt-4-turbo-preview": "cl100k_base",
            "gpt-3.5-turbo-16k": "cl100k_base",
            "gpt-3.5-turbo-instruct": "cl100k_base"
        }
        
        # Get the appropriate encoding for the model
        encoding_name = model_encoding_map.get(model, "cl100k_base")  # Default to cl100k_base if model not found
        encoding = tiktoken.get_encoding(encoding_name)
        
        # Count tokens
        token_count = len(encoding.encode(text))
        logger.debug(f"Token count for model {model} using encoding {encoding_name}: {token_count}")
        return token_count
    except Exception as e:
        logger.error(f"Error counting tokens for model {model}: {str(e)}")
        return 0 

def get_secret(secret_id, version_id="latest"):
    """Get secret from Google Cloud Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {str(e)}")
        raise 
    
