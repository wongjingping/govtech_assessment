#!/usr/bin/env python
"""
Train a machine learning model to predict HDB resale prices.

This script:
1. Loads resale price data from Postgres
2. Preprocesses the data (encoding, scaling, feature engineering)
3. Trains a model to predict resale prices
4. Evaluates model performance
5. Saves the model and preprocessing objects for later use in predictions
"""
import os
import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.base import clone

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent.absolute()
sys.path.append(str(parent_dir))

# Import utility modules
from utils.db import get_session

# Create model directory if it doesn't exist
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
os.makedirs(MODEL_DIR, exist_ok=True)

def load_data():
    """Load resale price data from PostgreSQL database"""
    print("Loading data from PostgreSQL...")
    
    try:
        session = get_session()
        
        # Execute a query to get all resale price data
        query = """
            SELECT 
                month, 
                town, 
                flat_type, 
                block, 
                street_name, 
                storey_range, 
                floor_area_sqm, 
                flat_model, 
                lease_commence_date, 
                resale_price, 
                remaining_lease_years
            FROM resale_prices
        """
        
        # Load data into a pandas DataFrame
        df = pd.read_sql(query, session.connection())
        print(f"Loaded {len(df)} records from database")
        
        return df
    
    except Exception as e:
        print(f"Error loading data: {e}")
        raise
    finally:
        session.close()

def preprocess_data(df):
    """
    Preprocess the resale price data.
    
    Includes:
    - Feature engineering
    - Handling missing values
    - Encoding categorical variables
    """
    print("Preprocessing data...")
    
    # Make a copy to avoid modifying the original data
    data = df.copy()
    
    # Convert month to datetime and extract year and month as features
    data['month'] = pd.to_datetime(data['month'])
    data['year'] = data['month'].dt.year
    data['month_num'] = data['month'].dt.month
    # add a string representation of the month to model seasonal effects discretely
    data['month_str'] = data['month'].dt.strftime('%B')
    
    # Extract storey information (take the average of the range)
    data['storey_range'] = data['storey_range'].astype(str)
    data['storey_min'] = data['storey_range'].str.split(' TO ', expand=True)[0].str.strip().astype(float)
    data['storey_max'] = data['storey_range'].str.split(' TO ', expand=True)[1].str.strip().astype(float)
    data['storey_avg'] = (data['storey_min'] + data['storey_max']) / 2
    
    # Calculate property age based on current year and lease commence date
    current_year = datetime.now().year
    data['property_age'] = current_year - data['lease_commence_date']
    
    # Drop columns that won't be used in the model
    columns_to_drop = ['month', 'block', 'street_name', 'storey_range', 'storey_min', 'storey_max']
    data = data.drop(columns=columns_to_drop)
    
    # Fill missing values in remaining_lease_years with median - fixed inplace warning
    median_lease = data['remaining_lease_years'].median()
    data['remaining_lease_years'] = data['remaining_lease_years'].fillna(median_lease)
    
    # Handle missing values in flat_model - fixed inplace warning
    data['flat_model'] = data['flat_model'].fillna('UNKNOWN')
    
    print(f"Data shape after preprocessing: {data.shape}")
    return data

def build_pipeline(X):
    """
    Build preprocessing and model pipeline.
    
    Returns a scikit-learn pipeline that handles:
    - Categorical feature encoding
    - Numerical feature scaling
    - Model training
    """
    print("Building preprocessing and model pipeline...")
    
    # Identify categorical and numerical features
    categorical_features = X.select_dtypes(include=['object']).columns.tolist()
    numerical_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    # Make sure 'month_str' is in the categorical features if it exists in X
    if 'month_str' in X.columns and 'month_str' not in categorical_features:
        categorical_features.append('month_str')
    
    # Preprocessing for categorical features
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='unknown')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    # Preprocessing for numerical features
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    # Combine preprocessing steps
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_features),
            ('cat', categorical_transformer, categorical_features)
        ]
    )
    
    # Full pipeline with preprocessing and model
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', GradientBoostingRegressor(random_state=42))
    ])
    
    return pipeline

def analyze_by_flat_type(model, data):
    """Analyze model performance by flat type using time-series CV"""
    print("Analyzing performance by flat type...")
    
    # Group data by flat type
    flat_types = data['flat_type'].unique()
    
    # Create a dataframe to store results
    results = []
    
    for flat_type in flat_types:
        # Filter data for this flat type
        flat_data = data[data['flat_type'] == flat_type]
        
        # Use time series split if enough data is available
        if len(flat_data['year'].unique()) >= 3:
            # Sort by year for time-based split
            flat_data = flat_data.sort_values('year')
            
            # Get unique years
            years = sorted(flat_data['year'].unique())
            test_year = years[-1]
            
            # Split data by time
            train_data = flat_data[flat_data['year'] < test_year]
            test_data = flat_data[flat_data['year'] == test_year]
            
            # Split features and target
            y_train = train_data['resale_price']
            X_train = train_data.drop(columns=['resale_price'])
            y_test = test_data['resale_price']
            X_test = test_data.drop(columns=['resale_price'])
        else:
            # Not enough years, use regular split
            y = flat_data['resale_price']
            X = flat_data.drop(columns=['resale_price'])
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        
        # Only train if we have sufficient data
        if len(X_train) > 10 and len(X_test) > 10:
            # Train a model just for this flat type
            flat_model = build_pipeline(X_train)
            flat_model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = flat_model.predict(X_test)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            
            # Store results
            results.append({
                'flat_type': flat_type,
                'count': len(flat_data),
                'train_count': len(X_train),
                'test_count': len(X_test),
                'mean_price': flat_data['resale_price'].mean(),
                'rmse': rmse,
                'r2': r2
            })
        else:
            print(f"Skipping {flat_type} - insufficient data for modeling")
    
    # Convert to DataFrame and sort by count
    results_df = pd.DataFrame(results).sort_values('count', ascending=False)
    
    # Print results
    print("\nPerformance by flat type:")
    print(results_df)
    
    # Create visualization if we have results
    if not results_df.empty:
        plt.figure(figsize=(12, 6))
        sns.barplot(x='flat_type', y='rmse', data=results_df)
        plt.title('Model RMSE by Flat Type')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(MODEL_DIR, 'flat_type_performance.png'))
    
    return results_df

def save_model(model, metrics):
    """Save the trained model and metrics to disk"""
    print("Saving model and metrics...")
    
    # Save model
    model_path = os.path.join(MODEL_DIR, 'resale_price_model.joblib')
    joblib.dump(model, model_path)
    
    # Save metrics
    metrics_path = os.path.join(MODEL_DIR, 'model_metrics.txt')
    with open(metrics_path, 'w') as f:
        f.write(f"Model trained on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"RMSE: ${metrics['rmse']:.2f}\n")
        f.write(f"MAE: ${metrics['mae']:.2f}\n")
        f.write(f"R² Score: {metrics['r2']:.4f}\n")
    
    print(f"Model saved to {model_path}")
    print(f"Metrics saved to {metrics_path}")

def perform_time_series_cv(data, model_pipeline, n_folds=3):
    """
    Perform time-series cross-validation with multiple folds.
    
    Example:
    Fold 1: train 1990-2020, test 2021
    Fold 2: train 1990-2021, test 2022
    ...
    
    Parameters:
    - data: DataFrame with resale price data
    - model_pipeline: Scikit-learn pipeline for preprocessing and model
    - n_folds: Number of time-based folds (default: 3)
    
    Returns:
    - Dictionary with cross-validation results
    """
    print(f"Performing time-series cross-validation with {n_folds} folds...")
    
    # Sort data by year for time-based splits
    data = data.sort_values('year')
    
    # Get unique years
    years = sorted(data['year'].unique())
    
    # Need at least n_folds+1 years of data
    if len(years) < n_folds + 1:
        print(f"Warning: Less than {n_folds + 1} years of data available. Reducing folds.")
        n_folds = max(1, len(years) - 1)
        
    # Prepare results storage
    cv_results = {
        'fold': [],
        'train_years': [],
        'test_year': [],
        'train_samples': [],
        'test_samples': [],
        'rmse': [],
        'mae': [],
        'r2': []
    }
    
    # Perform cross-validation
    for i in range(n_folds):
        # Determine test year for this fold
        test_year_idx = len(years) - n_folds + i
        test_year = years[test_year_idx]
        
        # Split data
        train_data = data[data['year'] < test_year]
        test_data = data[data['year'] == test_year]
        
        # Split features and target
        y_train = train_data['resale_price']
        X_train = train_data.drop(columns=['resale_price'])
        y_test = test_data['resale_price']
        X_test = test_data.drop(columns=['resale_price'])
        
        # Train model
        fold_model = clone(model_pipeline)
        fold_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = fold_model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Store results
        cv_results['fold'].append(i + 1)
        cv_results['train_years'].append(f"{years[0]}-{years[test_year_idx-1]}")
        cv_results['test_year'].append(test_year)
        cv_results['train_samples'].append(len(X_train))
        cv_results['test_samples'].append(len(X_test))
        cv_results['rmse'].append(rmse)
        cv_results['mae'].append(mae)
        cv_results['r2'].append(r2)
        
        print(f"\nFold {i + 1} results:")
        print(f"  Train: {years[0]}-{years[test_year_idx-1]} ({len(X_train)} samples)")
        print(f"  Test: {test_year} ({len(X_test)} samples)")
        print(f"  RMSE: ${rmse:.2f}")
        print(f"  MAE: ${mae:.2f}")
        print(f"  R²: {r2:.4f}")
    
    # Create summary DataFrame
    cv_df = pd.DataFrame(cv_results)
    
    # Calculate average metrics
    avg_rmse = np.mean(cv_results['rmse'])
    avg_mae = np.mean(cv_results['mae'])
    avg_r2 = np.mean(cv_results['r2'])
    
    print("\nTime-series cross-validation summary:")
    print(cv_df)
    print(f"\nAverage performance across {n_folds} folds:")
    print(f"  RMSE: ${avg_rmse:.2f}")
    print(f"  MAE: ${avg_mae:.2f}")
    print(f"  R²: {avg_r2:.4f}")
    
    # Create visualization
    plt.figure(figsize=(12, 6))
    plt.bar(range(1, n_folds + 1), cv_results['rmse'], alpha=0.7)
    plt.axhline(y=avg_rmse, color='r', linestyle='--', label=f'Average RMSE: ${avg_rmse:.2f}')
    plt.xlabel('Fold')
    plt.ylabel('RMSE ($)')
    plt.title('Time-Series Cross-Validation Performance')
    plt.xticks(range(1, n_folds + 1))
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(MODEL_DIR, 'time_series_cv_performance.png'))
    
    return {
        'cv_results': cv_df,
        'avg_rmse': avg_rmse,
        'avg_mae': avg_mae,
        'avg_r2': avg_r2
    }

def save_feature_importance(model, output_dir):
    """
    Generate and save a feature importance visualization for the trained model.
    
    Parameters:
    - model: Trained scikit-learn pipeline with GradientBoostingRegressor
    - output_dir: Directory to save the visualization
    """
    print("Generating feature importance visualization...")
    
    if not hasattr(model['model'], 'feature_importances_'):
        print("Model doesn't have feature_importances_ attribute, skipping visualization")
        return
    
    # Get feature names after preprocessing
    feature_names = []
    preprocessor = model['preprocessor']
    
    # Extract feature names from the column transformer
    for name, pipe, cols in preprocessor.transformers_:
        if name == 'cat':
            for i, col in enumerate(cols):
                # Get categories from the one-hot encoder
                categories = pipe.named_steps['onehot'].categories_[i]
                feature_names.extend([f"{col}_{cat}" for cat in categories])
        else:
            # Add numerical feature names directly
            feature_names.extend(cols)
    
    # Get feature importances from the model
    importances = model['model'].feature_importances_
    
    # Sort features by importance (descending)
    indices = np.argsort(importances)[::-1]
    
    # Take top 20 features for better readability
    top_n = min(20, len(indices))
    top_indices = indices[:top_n]
    
    # Create the figure
    plt.figure(figsize=(12, 8))
    plt.title('Feature Importance (Top 20)')
    
    # Plot horizontal bar chart
    plt.barh(range(len(top_indices)), 
            importances[top_indices], 
            align='center', 
            color='skyblue')
    
    # Add feature names as y-axis labels
    plt.yticks(range(len(top_indices)), 
              [feature_names[i] if i < len(feature_names) else f"feature_{i}" for i in top_indices])
    
    plt.xlabel('Relative Importance')
    plt.tight_layout()
    
    # Save the figure
    output_path = os.path.join(output_dir, 'feature_importance.png')
    plt.savefig(output_path)
    plt.close()
    
    print(f"Feature importance visualization saved to {output_path}")

def main():
    """Main function to train and evaluate the model"""
    print(f"Starting model training at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    
    try:
        # Load data
        df = load_data()
        
        # Preprocess data
        data = preprocess_data(df)
        
        # Build pipeline with the full dataset first to understand feature types
        pipeline = build_pipeline(data.drop(columns=['resale_price']))
        
        # Perform time-series cross-validation to evaluate model
        cv_results = perform_time_series_cv(data, pipeline, n_folds=3)
        
        # Train final model on all data
        print("\nTraining final model on all data...")
        X = data.drop(columns=['resale_price'])
        y = data['resale_price']
        final_model = clone(pipeline)
        final_model.fit(X, y)
        
        # Save the final model and metrics
        save_model(final_model, {
            'rmse': cv_results['avg_rmse'],
            'mae': cv_results['avg_mae'],
            'r2': cv_results['avg_r2']
        })
        
        # Generate and save feature importance visualization
        save_feature_importance(final_model, MODEL_DIR)
        
        # Analyze by flat type
        flat_type_analysis = analyze_by_flat_type(final_model, data)
        
        print(f"Model training completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    except Exception as e:
        print(f"Error during model training: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 