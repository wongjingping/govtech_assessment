"""
Database connection utilities.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from .config import get_db_config
from .models import Base

def get_engine():
    """
    Create a SQLAlchemy engine using configuration from environment.
    """
    db_config = get_db_config()
    connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    return create_engine(connection_string)

def get_session():
    """
    Create a SQLAlchemy session.
    """
    engine = get_engine()
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    return Session()

def create_tables():
    """
    Create all tables defined in models.
    """
    engine = get_engine()
    Base.metadata.create_all(engine)

def drop_tables():
    """
    Drop all tables defined in models.
    """
    engine = get_engine()
    Base.metadata.drop_all(engine) 