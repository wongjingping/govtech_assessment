"""
Module for predicting HDB resale prices using the trained model.
"""
import os
from datetime import datetime

import joblib
import pandas as pd

from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Path to the model artifacts
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modeling", "artifacts")
MODEL_PATH = os.path.join(MODEL_DIR, "resale_price_model.joblib")

def load_model():
    """
    Load the trained model from disk.
    
    Returns:
        object: The loaded model.
    """
    logger.debug(f"Loading model from {MODEL_PATH}")
    try:
        model = joblib.load(MODEL_PATH)
        logger.info("Model loaded successfully")
        return model
    except FileNotFoundError:
        error_msg = f"Model file not found at {MODEL_PATH}. Please train the model first."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}", exc_info=True)
        raise

def prepare_input_data(town, flat_type, storey_range, floor_area_sqm, flat_model, 
                      lease_commence_date, remaining_lease_years=None):
    """
    Prepare input data for prediction.
    
    Parameters:
        town (str): Town or area (e.g., 'ANG MO KIO', 'BEDOK')
        flat_type (str): Type of flat (e.g., '3 ROOM', '4 ROOM')
        storey_range (str): Range of floors (e.g., '01 TO 03', '10 TO 12')
        floor_area_sqm (float): Floor area in square meters
        flat_model (str): Model of the flat (e.g., 'IMPROVED', 'NEW GENERATION')
        lease_commence_date (int): Year the lease commenced
        remaining_lease_years (float, optional): Years of lease remaining
    
    Returns:
        DataFrame: Preprocessed input data ready for prediction.
    """
    logger.debug(f"Preparing input data for prediction: {town}, {flat_type}, {storey_range}")
    
    # Create a DataFrame with the input data
    data = pd.DataFrame({
        'town': [town.upper()],
        'flat_type': [flat_type.upper()],
        'storey_range': [storey_range.upper()],
        'floor_area_sqm': [float(floor_area_sqm)],
        'flat_model': [flat_model.upper()],
        'lease_commence_date': [int(lease_commence_date)],
        'remaining_lease_years': [remaining_lease_years],
        # Add current month for consistency with training data
        'month': [datetime.now().strftime('%Y-%m-%d')]
    })
    
    # Convert month to datetime
    data['month'] = pd.to_datetime(data['month'])
    
    # Extract year and month
    data['year'] = data['month'].dt.year
    data['month_num'] = data['month'].dt.month
    # Add month_str feature as a string representation of the month
    data['month_str'] = data['month'].dt.strftime('%B')
    
    # Calculate property age based on current year and lease commence date
    current_year = datetime.now().year
    data['property_age'] = current_year - data['lease_commence_date']
    
    # If remaining_lease_years is None, calculate it
    if data['remaining_lease_years'].iloc[0] is None:
        logger.debug("Calculating remaining lease years from property age")
        data['remaining_lease_years'] = 99 - data['property_age']
    
    # Extract storey information
    data['storey_min'] = data['storey_range'].str.split(' TO ', expand=True)[0].str.strip().astype(float)
    data['storey_max'] = data['storey_range'].str.split(' TO ', expand=True)[1].str.strip().astype(float)
    data['storey_avg'] = (data['storey_min'] + data['storey_max']) / 2
    
    # Drop columns not needed for prediction
    columns_to_drop = ['month', 'storey_range', 'storey_min', 'storey_max']
    data = data.drop(columns=columns_to_drop)
    
    logger.debug("Input data preparation complete")
    return data

def predict_property_price(town, flat_type, storey_range, floor_area_sqm, flat_model, 
                         lease_commence_date, remaining_lease_years=None):
    """
    Predict the resale price for a given HDB property.
    
    Parameters:
        town (str): Town or area (e.g., 'ANG MO KIO', 'BEDOK')
        flat_type (str): Type of flat (e.g., '3 ROOM', '4 ROOM')
        storey_range (str): Range of floors (e.g., '01 TO 03', '10 TO 12')
        floor_area_sqm (float): Floor area in square meters
        flat_model (str): Model of the flat (e.g., 'IMPROVED', 'NEW GENERATION')
        lease_commence_date (int): Year the lease commenced
        remaining_lease_years (float, optional): Years of lease remaining
    
    Returns:
        float: Predicted resale price.
    """
    logger.info(f"Predicting price for {flat_type} in {town}")
    
    # Load the model
    model = load_model()
    
    # Prepare the input data
    input_data = prepare_input_data(
        town=town,
        flat_type=flat_type,
        storey_range=storey_range,
        floor_area_sqm=floor_area_sqm,
        flat_model=flat_model,
        lease_commence_date=lease_commence_date,
        remaining_lease_years=remaining_lease_years
    )
    
    # Make prediction
    prediction = model.predict(input_data)[0]
    logger.info(f"Predicted price: {prediction}")
    
    return float(prediction) 