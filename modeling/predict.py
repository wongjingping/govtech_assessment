#!/usr/bin/env python
"""
Use the trained model to predict HDB resale prices.

This script:
1. Loads the trained model
2. Takes input data for a property
3. Preprocesses the input data
4. Returns a prediction of the resale price
"""
import os
import sys
import joblib
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent.absolute()
sys.path.append(str(parent_dir))

# Model directory
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
MODEL_PATH = os.path.join(MODEL_DIR, 'resale_price_model.joblib')

def load_model():
    """Load the trained model from disk"""
    try:
        model = joblib.load(MODEL_PATH)
        return model
    except FileNotFoundError:
        print(f"Error: Model file not found at {MODEL_PATH}")
        print("Please train the model first by running train_model.py")
        sys.exit(1)

def prepare_input_data(town, flat_type, storey_range, floor_area_sqm, flat_model, 
                      lease_commence_date, remaining_lease_years=None):
    """
    Prepare input data for prediction.
    
    Parameters:
    - town: Town or area (e.g., 'ANG MO KIO', 'BEDOK')
    - flat_type: Type of flat (e.g., '3 ROOM', '4 ROOM')
    - storey_range: Range of floors (e.g., '01 TO 03', '10 TO 12')
    - floor_area_sqm: Floor area in square meters
    - flat_model: Model of the flat (e.g., 'IMPROVED', 'NEW GENERATION')
    - lease_commence_date: Year the lease commenced
    - remaining_lease_years: Years of lease remaining (optional)
    
    Returns:
    - DataFrame with preprocessed input data
    """
    # Create a DataFrame with the input data
    data = pd.DataFrame({
        'town': [town],
        'flat_type': [flat_type],
        'storey_range': [storey_range],
        'floor_area_sqm': [floor_area_sqm],
        'flat_model': [flat_model],
        'lease_commence_date': [lease_commence_date],
        'remaining_lease_years': [remaining_lease_years],
        # Add current month for consistency with training data
        'month': [datetime.now().strftime('%Y-%m-%d')]
    })
    
    # Convert month to datetime
    data['month'] = pd.to_datetime(data['month'])
    
    # Extract year and month
    data['year'] = data['month'].dt.year
    data['month_num'] = data['month'].dt.month
    
    # Calculate property age based on current year and lease commence date
    current_year = datetime.now().year
    data['property_age'] = current_year - data['lease_commence_date']
    
    # Extract storey information
    data['storey_min'] = data['storey_range'].str.split(' TO ', expand=True)[0].str.strip().astype(float)
    data['storey_max'] = data['storey_range'].str.split(' TO ', expand=True)[1].str.strip().astype(float)
    data['storey_avg'] = (data['storey_min'] + data['storey_max']) / 2
    
    # Drop columns not needed for prediction
    columns_to_drop = ['month', 'storey_range', 'storey_min', 'storey_max']
    data = data.drop(columns=columns_to_drop)
    
    return data

def predict_price(model, input_data):
    """
    Predict resale price using the trained model.
    
    Parameters:
    - model: Trained model
    - input_data: Preprocessed input data
    
    Returns:
    - Predicted resale price
    """
    # Make prediction
    prediction = model.predict(input_data)[0]
    return prediction

def main():
    """Main function for prediction demo"""
    
    print("HDB Resale Price Predictor")
    print("=========================")
    
    # Load the model
    print("Loading model...")
    model = load_model()
    
    # Get user input or use example data
    use_example = input("Would you like to use an example property? (y/n): ").lower().strip() == 'y'
    
    if use_example:
        # Example data
        town = 'TAMPINES'
        flat_type = '4 ROOM'
        storey_range = '07 TO 09'
        floor_area_sqm = 90.0
        flat_model = 'NEW GENERATION'
        lease_commence_date = 1985
        remaining_lease_years = 65.0
    else:
        # Get user input
        print("\nPlease provide the following information:")
        town = input("Town (e.g., TAMPINES, BEDOK, ANG MO KIO): ").strip().upper()
        flat_type = input("Flat Type (e.g., 3 ROOM, 4 ROOM, 5 ROOM): ").strip().upper()
        storey_range = input("Storey Range (e.g., 01 TO 03, 07 TO 09): ").strip().upper()
        
        try:
            floor_area_sqm = float(input("Floor Area (sqm): ").strip())
        except ValueError:
            print("Invalid floor area. Using default value of 90 sqm.")
            floor_area_sqm = 90.0
            
        flat_model = input("Flat Model (e.g., NEW GENERATION, IMPROVED, STANDARD): ").strip().upper()
        
        try:
            lease_commence_date = int(input("Lease Commencement Year (e.g., 1985): ").strip())
        except ValueError:
            print("Invalid lease commencement year. Using default value of 1990.")
            lease_commence_date = 1990
            
        try:
            remaining_lease_years = float(input("Remaining Lease Years (e.g., 65.5): ").strip())
        except ValueError:
            # Calculate based on lease commencement date if not provided
            remaining_lease_years = 99 - (datetime.now().year - lease_commence_date)
            print(f"Using calculated remaining lease: {remaining_lease_years:.1f} years")
    
    # Prepare input data
    print("\nPreparing input data...")
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
    print("Predicting price...")
    predicted_price = predict_price(model, input_data)
    
    # Output result
    print("\nPrediction Results:")
    print("===================")
    print(f"Town: {town}")
    print(f"Flat Type: {flat_type}")
    print(f"Floor Area: {floor_area_sqm} sqm")
    print(f"Storey Range: {storey_range}")
    print(f"Flat Model: {flat_model}")
    print(f"Lease Commence Date: {lease_commence_date}")
    print(f"Remaining Lease: {remaining_lease_years:.1f} years")
    print(f"\nPredicted Resale Price: ${predicted_price:,.2f}")

if __name__ == "__main__":
    main() 