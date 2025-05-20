"""
Module for querying the database using natural language.
"""
import pandas as pd
from anthropic import Anthropic
from sqlalchemy import text

from utils.config import get_claude_api_key
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Claude API configuration
CLAUDE_API_KEY = get_claude_api_key()

def get_tables_schema():
    """
    Get the schema of the tables in the database.
    
    Returns:
        str: Schema description of database tables.
    """
    logger.debug("Getting tables schema for query generation")
    return """
    Table: resale_prices
    - id (Integer, primary key)
    - month (Date): Month of resale transaction
    - town (String): Town/region of the flat (e.g., ANG MO KIO, BEDOK)
    - flat_type (String): Type of flat (e.g., 3 ROOM, 4 ROOM)
    - block (String): Block number
    - street_name (String): Street name
    - storey_range (String): Range of floors (e.g., 01 TO 03, 10 TO 12)
    - floor_area_sqm (Float): Floor area in square meters
    - flat_model (String): Model of the flat (e.g., IMPROVED, NEW GENERATION)
    - lease_commence_date (Integer): Year the lease commenced
    - resale_price (Float): Price of the flat in Singapore dollars
    - remaining_lease_years (Float): Years of lease remaining

    Table: completion_status
    - id (Integer, primary key)
    - financial_year (Integer): Financial year of completion
    - town_or_estate (String): Town or estate name
    - status (String): Status of completion
    - no_of_units (Integer): Number of units completed
    """

def generate_sql_query(natural_query):
    """
    Generate a SQL query from a natural language query using Claude.
    
    Parameters:
        natural_query (str): Natural language query about HDB data.
    
    Returns:
        tuple: (SQL query, explanation)
    """
    logger.info(f"Generating SQL query from natural language: {natural_query}")
    
    api_key = get_claude_api_key()
    if not api_key:
        error_msg = "Claude API key not configured"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    client = Anthropic(api_key=api_key)
    
    # Database schema for context
    schema = get_tables_schema()
    
    # Create the prompt
    prompt = f"""
    You are a SQL query generator. Your task is to convert a natural language question into a SQL query that can be run on a PostgreSQL database.

    Here is the database schema:
    {schema}

    Natural language question: {natural_query}

    Please return ONLY a JSON object with the following fields:
    1. "sql": The SQL query to run
    2. "explanation": A brief explanation of what the query does in natural language

    Make sure the SQL query is valid PostgreSQL syntax and uses the correct table and column names as specified in the schema.
    Use appropriate joins, aggregations, filters, and sorting to answer the question effectively.
    """
    
    logger.debug("Sending request to Claude API")
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the response content
        response_text = response.content[0].text
        logger.debug("Received response from Claude API")
        
        # Parse the JSON response (need to handle this better in a real-world application)
        # For simplicity, we're using string parsing here
        sql_start = response_text.find('"sql": "') + 8
        sql_end = response_text.find('",', sql_start)
        sql_query = response_text[sql_start:sql_end].replace('\\n', ' ').replace('\\"', '"')
        
        explanation_start = response_text.find('"explanation": "') + 16
        explanation_end = response_text.find('"}', explanation_start)
        explanation = response_text[explanation_start:explanation_end].replace('\\n', ' ')
        
        logger.info("Successfully generated SQL query")
        logger.debug(f"Generated SQL: {sql_query}")
        
        return sql_query, explanation
    except Exception as e:
        logger.error(f"Error generating SQL query: {str(e)}", exc_info=True)
        raise

def execute_sql_query(sql_query, session):
    """
    Execute a SQL query on the database.
    
    Parameters:
        sql_query (str): SQL query to execute.
        session (Session): SQLAlchemy session.
    
    Returns:
        DataFrame: Query results as a pandas DataFrame.
    """
    logger.info("Executing SQL query")
    logger.debug(f"SQL: {sql_query}")
    
    try:
        result = session.execute(text(sql_query))
        
        # Convert to DataFrame
        if result.returns_rows:
            df = pd.DataFrame(result.fetchall())
            if not df.empty:
                df.columns = result.keys()
                logger.info(f"Query returned {len(df)} rows")
            else:
                logger.info("Query returned 0 rows")
            return df
        else:
            logger.info("Query did not return any rows")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error executing SQL query: {str(e)}", exc_info=True)
        raise

def query_database(natural_query, session):
    """
    Query the database using natural language.
    
    Parameters:
        natural_query (str): Natural language query about HDB data.
        session (Session): SQLAlchemy session.
    
    Returns:
        tuple: (DataFrame of results, SQL query string, natural language explanation)
    """
    logger.info(f"Processing natural language query: {natural_query}")
    
    # Generate SQL query from natural language
    sql_query, explanation = generate_sql_query(natural_query)
    
    # Execute the SQL query
    results = execute_sql_query(sql_query, session)
    
    logger.info("Query process completed successfully")
    return results, sql_query, explanation 