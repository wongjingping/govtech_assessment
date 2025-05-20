# HDB Resale Price Prediction Model

This directory contains machine learning models for predicting HDB resale prices based on historical transaction data.

## Overview

The model predicts resale prices for different flat types using features such as:
- Town/location
- Flat type (e.g., 3 ROOM, 4 ROOM)
- Floor area
- Storey range
- Flat model
- Lease commencement date
- Remaining lease years

## Model Architecture

The model uses a Gradient Boosting Regressor implemented with scikit-learn, which offers:
- Strong predictive performance
- Good handling of mixed data types (numerical and categorical)
- Feature importance estimates for model explainability
- Robustness to outliers

The full pipeline includes:
- Preprocessing for categorical features (one-hot encoding)
- Preprocessing for numerical features (scaling, imputation)
- Feature engineering (e.g., property age calculation, storey averages)

## Files

- `train_model.py`: Script to train and evaluate the model
- `predict.py`: Script to make predictions using the trained model
- `artifacts/`: Directory containing trained model and evaluation metrics
  - `resale_price_model.joblib`: Serialized model file
  - `model_metrics.txt`: Performance metrics on test data
  - `time_series_cv_performance.png`: Visualization of cross-validation performance
  - `feature_importance.png`: Visualization of the most important features for prediction
  - `flat_type_performance.png`: Model performance by flat type

## Usage

### Training the Model

To train the model:

```bash
python modeling/train_model.py
```

This will:
1. Load resale price data from the PostgreSQL database
2. Preprocess the data
3. Perform time-series cross-validation to evaluate model performance
4. Train a final model on all available data
5. Save the model and metrics to the artifacts directory

### Making Predictions

To use the model for predictions:

```bash
python modeling/predict.py
```

This interactive script will:
1. Load the trained model
2. Prompt for property details (or use example data)
3. Generate and display a price prediction

## Performance

The model was evaluated using time-series cross-validation with 3 folds:
- Fold 1: Train on 1990-2022, test on 2023
- Fold 2: Train on 1990-2023, test on 2024
- Fold 3: Train on 1990-2024, test on 2025

Average performance metrics across all folds:
- Root Mean Squared Error (RMSE): ~$133,668
- Mean Absolute Error (MAE): ~$102,303
- R² score: ~0.49

Unfortunately we didn't have time to do a proper hyperparameter tuning, and relied on the default parameters.

### Observations

- Performance varies by forecast year, with RMSE increasing in more recent years (2024-2025)
- Different flat types show varying prediction accuracy:
  - 4 ROOM and 3 ROOM flats (most common) have R² scores of ~0.26-0.27
  - 5 ROOM flats show R² of ~0.18
  - EXECUTIVE flats have lower R² (~0.03), suggesting different price dynamics
  - MULTI GENERATION flats have highest R² (0.44) but very small sample size (279 records)
- The model performs reasonably for a real estate price predictor, considering the complexity of housing markets

## Preprocessing Decisions

Several preprocessing decisions were made to improve model performance:

1. **Feature Engineering**:
   - Created property age from lease commencement date
   - Converted storey ranges to numerical values (min, max, average)
   - Extracted time features (year, month) from transaction date
   - Added a string representation of the month to model seasonal effects discretely

2. **Feature Selection**:
   - Removed highly specific features like block and street name to prevent overfitting
   - Kept town as a categorical feature to capture location effects

3. **Categorical Encoding**:
   - Used one-hot encoding for categorical features (town, flat type, flat model)
   - Added handling for unknown categories at prediction time

4. **Numerical Scaling**:
   - Applied standard scaling to numerical features
   - Used median imputation for missing numerical values

5. **Time-Series Cross-Validation**:
   - Implemented proper time-series splitting instead of random sampling
   - Trains on historical data and tests on future data to simulate real-world predictive use 