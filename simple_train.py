#!/usr/bin/env python3
import pandas as pd
import numpy as np
import joblib
import os
import logging
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import xgboost as xgb
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_ml_models():
    logger.info("Starting ML model training...")
    
    # Load PaySim dataset
    df = pd.read_csv('/app/data/raw/paysim.csv')
    logger.info(f"Loaded {len(df)} transactions")
    
    # Sample for faster training
    df = df.sample(n=50000, random_state=42)
    logger.info(f"Using sample of {len(df)} transactions")
    
    # Prepare features
    df = df.rename(columns={'isFraud': 'is_fraud'})
    df['hour_of_day'] = df['step'] % 24
    df['amount_log'] = np.log1p(df['amount'])
    
    # Feature columns
    feature_cols = ['amount', 'oldbalanceOrg', 'newbalanceOrig', 
                   'oldbalanceDest', 'newbalanceDest', 'hour_of_day', 'amount_log']
    
    # Encode transaction type
    le = LabelEncoder()
    df['type_encoded'] = le.fit_transform(df['type'])
    feature_cols.append('type_encoded')
    
    # Prepare X and y
    X = df[feature_cols].fillna(0)
    y = df['is_fraud']
    
    logger.info(f"Features: {len(feature_cols)} columns")
    logger.info(f"Fraud rate: {y.mean():.3%}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train models
    models = {}
    
    # Logistic Regression
    logger.info("Training Logistic Regression...")
    lr = LogisticRegression(random_state=42, max_iter=1000)
    lr.fit(X_train_scaled, y_train)
    lr_pred = lr.predict_proba(X_test_scaled)[:, 1]
    lr_auc = roc_auc_score(y_test, lr_pred)
    models['logistic_regression'] = lr
    logger.info(f"Logistic Regression AUC: {lr_auc:.4f}")
    
    # Random Forest
    logger.info("Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train_scaled, y_train)
    rf_pred = rf.predict_proba(X_test_scaled)[:, 1]
    rf_auc = roc_auc_score(y_test, rf_pred)
    models['random_forest'] = rf
    logger.info(f"Random Forest AUC: {rf_auc:.4f}")
    
    # XGBoost
    logger.info("Training XGBoost...")
    xgb_model = xgb.XGBClassifier(random_state=42, n_estimators=100, eval_metric='logloss')
    xgb_model.fit(X_train_scaled, y_train)
    xgb_pred = xgb_model.predict_proba(X_test_scaled)[:, 1]
    xgb_auc = roc_auc_score(y_test, xgb_pred)
    models['xgboost'] = xgb_model
    logger.info(f"XGBoost AUC: {xgb_auc:.4f}")
    
    # Save models
    model_dir = '/app/models'
    os.makedirs(model_dir, exist_ok=True)
    
    for name, model in models.items():
        model_path = os.path.join(model_dir, f'{name}.pkl')
        joblib.dump(model, model_path)
        logger.info(f"Saved {name} to {model_path}")
    
    # Save scaler and encoder
    joblib.dump(scaler, os.path.join(model_dir, 'scaler.pkl'))
    joblib.dump(le, os.path.join(model_dir, 'encoder.pkl'))
    joblib.dump(feature_cols, os.path.join(model_dir, 'features.pkl'))
    
    # Save metadata
    metadata = {
        'training_date': datetime.now().isoformat(),
        'models': list(models.keys()),
        'features': feature_cols,
        'performance': {
            'logistic_regression': float(lr_auc),
            'random_forest': float(rf_auc),
            'xgboost': float(xgb_auc)
        }
    }
    
    with open(os.path.join(model_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info("Training completed successfully!")
    logger.info(f"Models saved to {model_dir}")
    
    return models

if __name__ == "__main__":
    train_ml_models()
