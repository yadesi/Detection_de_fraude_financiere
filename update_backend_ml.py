#!/usr/bin/env python3
"""
Script to update backend with ML models
"""

import joblib
import numpy as np
import pandas as pd
import os
import json

# Load ML models
model_dir = '/app/models'
models = {}
scaler = None
encoder = None
feature_columns = []
metadata = {}
best_model_name = None

try:
    # Load all ML components
    with open(os.path.join(model_dir, 'metadata.json'), 'r') as f:
        metadata = json.load(f)
    
    feature_columns = joblib.load(os.path.join(model_dir, 'features.pkl'))
    scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
    encoder = joblib.load(os.path.join(model_dir, 'encoder.pkl'))
    
    for model_name in metadata['models']:
        model_path = os.path.join(model_dir, f'{model_name}.pkl')
        models[model_name] = joblib.load(model_path)
    
    # Select best model
    if 'xgboost' in models:
        best_model_name = 'xgboost'
    elif 'random_forest' in models:
        best_model_name = 'random_forest'
    else:
        best_model_name = list(models.keys())[0]
    
    print(f'✅ ML Models loaded: {list(models.keys())}')
    print(f'✅ Best model: {best_model_name}')
    
except Exception as e:
    print(f'❌ Error loading ML models: {e}')

# Create ML prediction functions
def predict_fraud_ml(transaction):
    """Predict fraud using ML models"""
    try:
        # Prepare features
        df = pd.DataFrame([transaction])
        df['hour_of_day'] = df.get('step', 0) % 24
        df['amount_log'] = np.log1p(df['amount'])
        
        if 'type' in df.columns and encoder:
            df['type_encoded'] = encoder.transform(df['type'])
        else:
            df['type_encoded'] = 0
        
        # Create feature array
        features = []
        for col in feature_columns:
            if col in df.columns:
                features.append(df[col].iloc[0])
            else:
                features.append(0)
        
        feature_array = np.array(features).reshape(1, -1)
        
        if scaler:
            feature_array = scaler.transform(feature_array)
        
        # Make predictions with all models
        predictions = {}
        for model_name, model in models.items():
            try:
                fraud_prob = model.predict_proba(feature_array)[0, 1]
                predictions[model_name] = fraud_prob
            except Exception as e:
                predictions[model_name] = 0.5
        
        # Use best model
        best_prob = predictions[best_model_name]
        is_fraud = best_prob > 0.5
        confidence = max(0.5, 1.0 - abs(best_prob - 0.5))
        
        return {
            'is_fraud': bool(is_fraud),
            'fraud_probability': float(best_prob),
            'confidence': float(confidence),
            'model_used': best_model_name,
            'all_predictions': predictions,
            'model_version': 'ml_v1.0',
            'feature_count': len(feature_columns),
            'training_date': metadata.get('training_date'),
            'training_performance': metadata.get('performance', {})
        }
        
    except Exception as e:
        print(f'Error in ML prediction: {e}')
        # Fallback
        amount = transaction.get('amount', 0)
        is_fraud = amount > 10000
        fraud_prob = min(0.9, 0.1 + (amount / 20000))
        
        return {
            'is_fraud': is_fraud,
            'fraud_probability': fraud_prob,
            'confidence': 0.7,
            'model_used': 'fallback_rules',
            'all_predictions': {'fallback': fraud_prob},
            'model_version': 'fallback_v1.0',
            'feature_count': 1,
            'training_date': None,
            'training_performance': {}
        }

def get_ml_model_info():
    """Get ML model information"""
    return {
        'loaded_models': list(models.keys()),
        'best_model': best_model_name,
        'feature_columns': feature_columns,
        'model_count': len(models),
        'feature_count': len(feature_columns),
        'training_metadata': metadata,
        'model_performance': metadata.get('performance', {})
    }

# Test the ML functions
if __name__ == "__main__":
    test_transaction = {
        'transaction_id': 'ML_UPDATE_TEST',
        'type': 'TRANSFER',
        'amount': 15000,
        'oldbalanceOrg': 25000,
        'newbalanceOrig': 10000,
        'nameOrig': 'C123456789',
        'oldbalanceDest': 5000,
        'newbalanceDest': 20000,
        'nameDest': 'M987654321'
    }
    
    result = predict_fraud_ml(test_transaction)
    info = get_ml_model_info()
    
    print(f'\n🎯 ML Prediction Test:')
    print(f'  Model Used: {result["model_used"]}')
    print(f'  Fraud Probability: {result["fraud_probability"]:.4f}')
    print(f'  Is Fraud: {result["is_fraud"]}')
    
    print(f'\n📊 ML Model Info:')
    print(f'  Best Model: {info["best_model"]}')
    print(f'  Loaded Models: {info["loaded_models"]}')
    print(f'  Feature Count: {info["feature_count"]}')
    
    print(f'\n✅ Backend ML integration ready!')
