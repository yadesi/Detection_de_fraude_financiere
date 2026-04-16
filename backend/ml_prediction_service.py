#!/usr/bin/env python3
"""
ML Prediction Service using trained models
"""

import joblib
import numpy as np
import pandas as pd
import os
import logging
from typing import Dict, Any, List
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLPredictionService:
    """ML-based prediction service using trained models"""
    
    def __init__(self, model_dir='/app/models'):
        self.model_dir = model_dir
        self.models = {}
        self.scaler = None
        self.encoder = None
        self.feature_columns = []
        self.metadata = {}
        self.best_model_name = None
        self.load_models()
    
    def load_models(self):
        """Load trained models from disk"""
        logger.info(f"Loading ML models from {self.model_dir}...")
        
        try:
            # Load metadata
            with open(os.path.join(self.model_dir, 'metadata.json'), 'r') as f:
                self.metadata = json.load(f)
            
            # Load feature columns
            self.feature_columns = joblib.load(os.path.join(self.model_dir, 'features.pkl'))
            logger.info(f"Loaded feature columns: {self.feature_columns}")
            
            # Load scaler
            self.scaler = joblib.load(os.path.join(self.model_dir, 'scaler.pkl'))
            
            # Load encoder
            self.encoder = joblib.load(os.path.join(self.model_dir, 'encoder.pkl'))
            
            # Load models
            for model_name in self.metadata['models']:
                model_path = os.path.join(self.model_dir, f'{model_name}.pkl')
                self.models[model_name] = joblib.load(model_path)
                logger.info(f"Loaded {model_name} model")
            
            # Select best model (XGBoost has highest AUC)
            if 'xgboost' in self.models:
                self.best_model_name = 'xgboost'
            elif 'random_forest' in self.models:
                self.best_model_name = 'random_forest'
            else:
                self.best_model_name = list(self.models.keys())[0]
            
            logger.info(f"Using best model: {self.best_model_name}")
            logger.info(f"Model performance: {self.metadata.get('performance', {})}")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def prepare_features(self, transaction: Dict[str, Any]) -> np.ndarray:
        """Prepare features for ML prediction"""
        try:
            # Create DataFrame from transaction
            df = pd.DataFrame([transaction])
            
            # Feature engineering (same as training)
            df['hour_of_day'] = df.get('step', 0) % 24
            df['amount_log'] = np.log1p(df['amount'])
            
            # Encode transaction type
            if 'type' in df.columns and self.encoder:
                df['type_encoded'] = self.encoder.transform(df['type'])
            else:
                df['type_encoded'] = 0  # Default value
            
            # Select features in correct order
            features = []
            for col in self.feature_columns:
                if col in df.columns:
                    features.append(df[col].iloc[0])
                else:
                    features.append(0)  # Default value for missing features
            
            # Convert to numpy array and reshape
            feature_array = np.array(features).reshape(1, -1)
            
            # Scale features
            if self.scaler:
                feature_array = self.scaler.transform(feature_array)
            
            return feature_array
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            raise
    
    def predict_fraud(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Predict fraud using ML models"""
        try:
            # Prepare features
            features = self.prepare_features(transaction)
            
            # Get predictions from all models
            predictions = {}
            
            for model_name, model in self.models.items():
                try:
                    # Get probability of fraud
                    fraud_prob = model.predict_proba(features)[0, 1]
                    predictions[model_name] = fraud_prob
                except Exception as e:
                    logger.error(f"Error predicting with {model_name}: {e}")
                    predictions[model_name] = 0.5  # Default
            
            # Use best model for final prediction
            best_prob = predictions[self.best_model_name]
            
            # Make binary decision
            is_fraud = best_prob > 0.5
            confidence = max(0.5, 1.0 - abs(best_prob - 0.5))
            
            return {
                'is_fraud': bool(is_fraud),
                'fraud_probability': float(best_prob),
                'confidence': float(confidence),
                'model_used': self.best_model_name,
                'all_predictions': predictions,
                'model_version': 'ml_v1.0',
                'feature_count': len(self.feature_columns),
                'training_date': self.metadata.get('training_date'),
                'training_performance': self.metadata.get('performance', {})
            }
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            # Fallback to simple rule-based prediction
            return self._fallback_prediction(transaction)
    
    def _fallback_prediction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based prediction"""
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
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            'loaded_models': list(self.models.keys()),
            'best_model': self.best_model_name,
            'feature_columns': self.feature_columns,
            'model_count': len(self.models),
            'feature_count': len(self.feature_columns),
            'training_metadata': self.metadata,
            'model_performance': self.metadata.get('performance', {})
        }

# Global instance
ml_service = MLPredictionService()

def predict_fraud_ml(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Global function for ML prediction"""
    return ml_service.predict_fraud(transaction)

def get_ml_model_info() -> Dict[str, Any]:
    """Get ML model information"""
    return ml_service.get_model_info()
