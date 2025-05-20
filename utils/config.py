import os
from pathlib import Path
from dotenv import load_dotenv
from .logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env files"""
    # Look for .env file in current directory and parent directories
    env_path = Path(".env")
    if env_path.exists():
        logger.debug(f"Loading environment from {env_path}")
        load_dotenv(env_path)
    else:
        # Try to load from data/.env as fallback
        data_env_path = Path("data/.env")
        if data_env_path.exists():
            logger.debug(f"Loading environment from {data_env_path}")
            load_dotenv(data_env_path)
        else:
            logger.warning("No .env file found. Using default or system environment variables.")
    
    # Check for db and api keys
    required_keys = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_HOST", "POSTGRES_PORT", "CLAUDE_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        logger.warning(f"Missing environment variables: {', '.join(missing_keys)}")
    else:
        logger.debug("All required environment variables are set.")

# Database configuration
def get_db_config():
    """Get database configuration from environment variables"""
    load_env()
    config = {
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "database": os.getenv("POSTGRES_DB", "hdb_data"),
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432")
    }
    logger.debug(f"Database configuration: host={config['host']}, port={config['port']}, db={config['database']}")
    return config

# Claude API configuration
def get_claude_api_key():
    """Get Claude API key from environment variables"""
    load_env()
    api_key = os.getenv("CLAUDE_API_KEY", "")
    if not api_key:
        logger.warning("CLAUDE_API_KEY not found in environment variables")
    else:
        logger.debug("CLAUDE_API_KEY found in environment")
    return api_key
