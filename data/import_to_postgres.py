#!/usr/bin/env python
"""
Import processed HDB data into PostgreSQL database using SQLAlchemy ORM models.
"""
import os
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent.absolute()
sys.path.append(str(parent_dir))

# Import utility modules
from utils.db import get_engine, create_tables
from utils.models import ResalePrice, CompletionStatus

# Data file paths
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RESALE_PRICES_FILE = os.path.join(PROCESSED_DIR, "resale_prices_all_combined_cleaned.csv")
COMPLETION_STATUS_FILE = os.path.join(PROCESSED_DIR, "completion_status_cleaned.csv")

def import_resale_prices(engine):
    """Import resale prices data into PostgreSQL using ORM models"""
    print("Importing resale prices data...")
    
    # Create a database session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Truncate the table by deleting all rows
        print("Clearing existing resale prices data...")
        session.query(ResalePrice).delete()
        session.commit()
        
        # Read and process CSV in chunks to handle large files
        chunksize = 50000
        chunks_imported = 0
        total_rows_imported = 0
        
        print(f"Reading {RESALE_PRICES_FILE} in chunks of {chunksize}...")
        for chunk in pd.read_csv(RESALE_PRICES_FILE, chunksize=chunksize):
            # Clean and prepare data
            chunk['month'] = pd.to_datetime(chunk['month'], errors='coerce')
            
            # Convert numeric columns
            numeric_cols = ['floor_area_sqm', 'resale_price', 'lease_commence_date', 'remaining_lease_years']
            for col in numeric_cols:
                if col in chunk.columns:
                    chunk[col] = pd.to_numeric(chunk[col], errors='coerce')
            
            # Drop rows with null values in critical columns
            chunk = chunk.dropna(subset=['month', 'town', 'flat_type', 'resale_price', 'floor_area_sqm'])
            
            # Convert DataFrame rows to model objects
            resale_objects = []
            for _, row in chunk.iterrows():
                resale_objects.append(ResalePrice.from_dict(row))
            
            # Bulk insert into database
            if resale_objects:
                session.bulk_save_objects(resale_objects)
                session.commit()
                
                chunks_imported += 1
                total_rows_imported += len(resale_objects)
                print(f"Imported chunk {chunks_imported}, rows: {len(resale_objects)}")
        
        print(f"Resale prices data import completed! Total rows: {total_rows_imported}")
    
    except Exception as e:
        session.rollback()
        print(f"Error during resale prices import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def import_completion_status(engine):
    """Import HDB completion status data into PostgreSQL using ORM models"""
    print("Importing completion status data...")
    
    # Create a database session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Truncate the table by deleting all rows
        print("Clearing existing completion status data...")
        session.query(CompletionStatus).delete()
        session.commit()
        
        # Read CSV file
        df = pd.read_csv(COMPLETION_STATUS_FILE)
        
        # Clean and prepare data
        df['financial_year'] = pd.to_numeric(df['financial_year'], errors='coerce')
        df['no_of_units'] = pd.to_numeric(df['no_of_units'], errors='coerce')
        
        # Drop rows with null values in critical columns
        df = df.dropna(subset=['financial_year', 'town_or_estate', 'status'])
        
        # Convert DataFrame rows to model objects
        completion_objects = []
        for _, row in df.iterrows():
            completion_objects.append(CompletionStatus.from_dict(row))
        
        # Bulk insert into database
        if completion_objects:
            session.bulk_save_objects(completion_objects)
            session.commit()
        
        print(f"Completion status data import completed! Rows: {len(completion_objects)}")
    
    except Exception as e:
        session.rollback()
        print(f"Error during completion status import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def main():
    """Main function to import all data"""
    print(f"Starting data import process at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    
    try:
        # Get database engine and create tables if they don't exist
        engine = get_engine()
        create_tables()
        
        # Test connection
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"Connected to PostgreSQL: {version}")
        
        # Import data
        import_resale_prices(engine)
        import_completion_status(engine)
        
        print(f"All data imported successfully! Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    except Exception as e:
        print(f"Error during import process: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 