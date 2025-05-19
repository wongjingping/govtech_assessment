import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env files"""
    # Look for .env file in current directory and parent directories
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try to load from data/.env as fallback
        data_env_path = Path("data/.env")
        if data_env_path.exists():
            load_dotenv(data_env_path)

# Database configuration
def get_db_config():
    """Get database configuration from environment variables"""
    load_env()
    return {
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "database": os.getenv("POSTGRES_DB", "hdb_data"),
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432")
    }

# Claude API configuration
def get_claude_api_key():
    """Get Claude API key from environment variables"""
    load_env()
    return os.getenv("CLAUDE_API_KEY", "")

# Data directory configuration
def get_data_dir():
    """Get data directory from environment variables or default"""
    load_env()
    return os.getenv("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")) 