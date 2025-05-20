"""
Database connection utilities.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from .config import get_db_config
from .models import Base
from .logger import get_logger

# Initialize logger
logger = get_logger(__name__)

def get_engine():
    """
    Create a SQLAlchemy engine using configuration from environment.
    
    Returns:
        Engine: The SQLAlchemy engine instance.
    """
    db_config = get_db_config()
    connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    logger.debug(f"Creating database engine for host: {db_config['host']}:{db_config['port']}")
    return create_engine(connection_string)

def get_session_factory():
    """
    Create a SQLAlchemy session factory.
    
    Returns:
        sessionmaker: A factory for creating new sessions.
    """
    logger.debug("Creating session factory")
    engine = get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return scoped_session(session_factory)

# Create a scoped session
Session = get_session_factory()

def get_session():
    """
    Get a database session.
    
    Returns:
        SQLAlchemy Session: A session for interacting with the database.
    """
    logger.debug("Creating new database session")
    db = Session()
    try:
        return db
    finally:
        db.close()

def create_tables():
    """
    Create all tables defined in models.
    """
    logger.info("Creating database tables")
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("Database tables created successfully")

def drop_tables():
    """
    Drop all tables defined in models.
    """
    logger.warning("Dropping all database tables")
    engine = get_engine()
    Base.metadata.drop_all(engine)
    logger.info("Database tables dropped successfully") 