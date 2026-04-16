#!/usr/bin/env python3
"""
Script to train ML models with PaySim dataset and save them to disk
"""

import pandas as pd
import numpy as np
import joblib
import os
import logging
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import xgboost as xgb
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MLModelTrainer:
    """Train ML models with PaySim dataset"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_columns = []
        
    def load_paysim_data(self, sample_size=50000):
        """Load and prepare PaySim dataset"""
        logger.info("Loading PaySim dataset...")
        
        # Load the dataset
        df = pd.read_csv('/app/data/raw/paysim.csv')
        logger.info(f"Original dataset: {len(df):,} transactions")
        
        # Take a sample for faster training
        if len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)
            logger.info(f"Using sample: {len(df):,} transactions")
        
        # Map columns and add features
        df = df.rename(columns={'isFraud': 'is_fraud'})
        df['hour_of_day'] = df['step'] % 24
        df['day_of_week'] = (df['step'] // 24) % 7
        
        # Feature engineering
        df['amount_log'] = np.log1p(df['amount'])
        df['balance_change_orig'] = df['newbalanceOrig'] - df['oldbalanceOrg']
        df['balance_change_dest'] = df['newbalanceDest'] - df['oldbalanceDest']
        df['error_orig'] = ((df['oldbalanceOrg'] - df['newbalanceOrig'] != df['amount']) & (df['amount'] > 0)).astype(int)
        df['error_dest'] = ((df['newbalanceDest'] - df['oldbalanceDest'] != df['amount']) & (df['amount'] > 0)).astype(int)
        
        # Clean data
        df = df.dropna()
        logger.info(f"After cleaning: {len(df):,} transactions")
        logger.info(f"Fraud rate: {df['is_fraud'].mean():.3%}")
        
        return df
    
    def prepare_features(self, df):
        """Prepare features for training"""
        logger.info("Preparing features...")
        
        # Select feature columns
        feature_cols = [
            'amount', 'oldbalanceOrg', 'newbalanceOrig', 
            'oldbalanceDest', 'newbalanceDest', 'hour_of_day', 'day_of_week',
            'amount_log', 'balance_change_orig', 'balance_change_dest',
            'error_orig', 'error_dest'
        ]
        
        # Add encoded transaction type
        if 'type' in df.columns:
            le = LabelEncoder()
            df['type_encoded'] = le.fit_transform(df['type'])
            self.encoders['type'] = le
            feature_cols.append('type_encoded')
        
        # Prepare features and target
        X = df[feature_cols].fillna(0)
        y = df['is_fraud']
        
        self.feature_columns = feature_cols
        logger.info(f"Features: {len(feature_cols)} columns")
        logger.info(f"Feature columns: {feature_cols}")
        
        return X, y
    
    def train_models(self, X, y):
        """Train multiple ML models"""
        logger.info("Training ML models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['standard'] = scaler
        
        logger.info(f"Training set: {len(X_train):,} samples")
        logger.info(f"Test set: {len(X_test):,} samples")
        logger.info(f"Fraud in train: {y_train.mean():.3%}")
        logger.info(f"Fraud in test: {y_test.mean():.3%}")
        
        # Train models
        models_to_train = {
            'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
            'xgboost': xgb.XGBClassifier(random_state=42, n_estimators=100, eval_metric='logloss')
        }
        
        results = {}
        
        for name, model in models_to_train.items():
            logger.info(f"Training {name}...")
            
            # Train model
            if name == 'xgboost':
                model.fit(X_train_scaled, y_train)
            else:
                model.fit(X_train_scaled, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
            
            # Calculate metrics
            auc = roc_auc_score(y_test, y_pred_proba)
            
            # Store model and results
            self.models[name] = model
            results[name] = {
                'model': model,
                'auc': auc,
                'predictions': y_pred,
                'probabilities': y_pred_proba
            }
            
            logger.info(f"{name} - AUC: {auc:.4f}")
        
        return results, X_test, y_test
    
    def save_models(self, model_dir='/app/models'):
        """Save trained models to disk"""
        logger.info(f"Saving models to {model_dir}...")
        
        # Create directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
        
        # Save models
        for name, model in self.models.items():
            model_path = os.path.join(model_dir, f'{name}.pkl')
            joblib.dump(model, model_path)
            logger.info(f"Saved {name} to {model_path}")
        
        # Save scalers and encoders
        scaler_path = os.path.join(model_dir, 'scaler.pkl')
        joblib.dump(self.scalers, scaler_path)
        logger.info(f"Saved scaler to {scaler_path}")
        
        encoder_path = os.path.join(model_dir, 'encoders.pkl')
        joblib.dump(self.encoders, encoder_path)
        logger.info(f"Saved encoders to {encoder_path}")
        
        # Save feature columns
        features_path = os.path.join(model_dir, 'feature_columns.pkl')
        joblib.dump(self.feature_columns, features_path)
        logger.info(f"Saved feature columns to {features_path}")
        
        # Save metadata
        metadata = {
            'training_date': datetime.now().isoformat(),
            'model_count': len(self.models),
            'feature_count': len(self.feature_columns),
            'models': list(self.models.keys())
        }
        
        metadata_path = os.path.join(model_dir, 'metadata.json')
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")
        
        logger.info("All models saved successfully!")
    
    def train_and_save(self):
        """Complete training pipeline"""
        logger.info("Starting ML model training pipeline...")
        
        # Load data
        df = self.load_paysim_data()
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        # Train models
        results, X_test, y_test = self.train_models(X, y)
        
        # Save models
        self.save_models()
        
        # Print final results
        logger.info("\n=== TRAINING RESULTS ===")
        for name, result in results.items():
            logger.info(f"{name}: AUC = {result['auc']:.4f}")
        
        logger.info(f"\nModels trained and saved to /app/models/")
        return results

if __name__ == "__main__":
    trainer = MLModelTrainer()
    trainer.train_and_save()
