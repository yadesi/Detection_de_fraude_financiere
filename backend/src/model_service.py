import asyncio
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime
import mlflow
import mlflow.pytorch
import mlflow.sklearn
import mlflow.xgboost
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import joblib
import json
import os

class ModelService:
    """Machine Learning model service for fraud detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.spark = None
        self.models = {}
        self.scalers = None
        self.model_metrics = {}
        self.training_jobs = {}
        
    async def load_models(self):
        """Load trained models from MLflow registry"""
        try:
            # Initialize MLflow
            mlflow.set_tracking_uri("http://localhost:5000")
            
            # Load models from registry
            model_names = ["isolation_forest", "xgboost_classifier", "ensemble_model"]
            
            for model_name in model_names:
                try:
                    model_uri = f"models:/fraud_detection_{model_name}/latest"
                    self.models[model_name] = mlflow.sklearn.load_model(model_uri)
                    self.logger.info(f"Loaded model: {model_name}")
                except Exception as e:
                    self.logger.warning(f"Could not load {model_name}: {str(e)}")
                    # Create fallback model
                    self.models[model_name] = self._create_fallback_model(model_name)
            
            # Load scalers
            try:
                scaler_uri = "models:/fraud_scalers/latest"
                self.scalers = mlflow.sklearn.load_model(scaler_uri)
            except Exception as e:
                self.logger.warning(f"Could not load scalers: {str(e)}")
                self.scalers = StandardScaler()
            
            self.logger.info("Model loading completed")
            
        except Exception as e:
            self.logger.error(f"Failed to load models: {str(e)}")
            # Create fallback models
            self._create_fallback_models()
    
    def _create_fallback_model(self, model_name: str):
        """Create fallback models for development"""
        if model_name == "isolation_forest":
            return IsolationForest(contamination=0.1, random_state=42)
        elif model_name == "xgboost_classifier":
            return xgb.XGBClassifier(
                objective='binary:logistic',
                eval_metric='auc',
                use_label_encoder=False,
                random_state=42
            )
        elif model_name == "ensemble_model":
            # Simple ensemble wrapper
            return EnsembleModel(self.models)
        else:
            return None
    
    def _create_fallback_models(self):
        """Create all fallback models"""
        self.models["isolation_forest"] = IsolationForest(contamination=0.1, random_state=42)
        self.models["xgboost_classifier"] = xgb.XGBClassifier(
            objective='binary:logistic',
            eval_metric='auc',
            use_label_encoder=False,
            random_state=42
        )
        self.scalers = StandardScaler()
    
    async def train_models(self, data_path: str = None) -> Dict[str, Any]:
        """
        Train fraud detection models
        """
        try:
            # Load and prepare data
            if data_path:
                data = await self._load_training_data(data_path)
            else:
                # Use real datasets by default
                data = await self._load_real_dataset()
            
            # Preprocess data
            X_train, X_test, y_train, y_test = await self._preprocess_data(data)
            
            # Train models
            models_results = {}
            
            # Train Isolation Forest
            isolation_result = await self._train_isolation_forest(X_train, X_test, y_train, y_test)
            models_results["isolation_forest"] = isolation_result
            
            # Train XGBoost
            xgboost_result = await self._train_xgboost(X_train, X_test, y_train, y_test)
            models_results["xgboost"] = xgboost_result
            
            # Train ensemble
            ensemble_result = await self._train_ensemble(X_train, X_test, y_train, y_test)
            models_results["ensemble"] = ensemble_result
            
            # Save models to MLflow
            await self._save_models_to_mlflow(models_results)
            
            return {
                "status": "success",
                "models_trained": list(models_results.keys()),
                "results": models_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Training failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _load_training_data(self, data_path: str) -> pd.DataFrame:
        """Load training data from file"""
        try:
            if data_path.endswith('.csv'):
                return pd.read_csv(data_path)
            elif data_path.endswith('.json'):
                return pd.read_json(data_path)
            else:
                raise ValueError("Unsupported file format")
        except Exception as e:
            self.logger.error(f"Failed to load data: {str(e)}")
            raise
    
    async def _load_real_dataset(self) -> pd.DataFrame:
        """Load real dataset from data/raw directory"""
        try:
            # Try to load PaySim dataset first
            paysim_path = '/app/data/raw/paysim.csv'
            if os.path.exists(paysim_path):
                self.logger.info("Loading PaySim dataset...")
                df = pd.read_csv(paysim_path)
                
                # Map PaySim columns to our format
                df = df.rename(columns={
                    'step': 'hour_of_day',
                    'type': 'type',
                    'amount': 'amount',
                    'nameOrig': 'nameOrig',
                    'oldbalanceOrg': 'oldbalanceOrg',
                    'newbalanceOrig': 'newbalanceOrig',
                    'nameDest': 'nameDest',
                    'oldbalanceDest': 'oldbalanceDest',
                    'newbalanceDest': 'newbalanceDest',
                    'isFraud': 'is_fraud'
                })
                
                # Add time features
                df['hour_of_day'] = df['hour_of_day'] % 24
                df['day_of_week'] = (df['hour_of_day'] // 24) % 7
                
                # Take a sample for faster training (optional - remove for full dataset)
                if len(df) > 100000:
                    df = df.sample(n=100000, random_state=42)
                    self.logger.info(f"Using sample of 100,000 transactions for faster training")
                
                # Clean data
                df = df.dropna()
                self.logger.info(f"Loaded PaySim dataset: {len(df):,} transactions, fraud rate: {df['is_fraud'].mean():.3%}")
                return df
            
            # Try to load Credit Card dataset
            creditcard_path = '/app/data/raw/creditcard.csv'
            if os.path.exists(creditcard_path):
                self.logger.info("Loading Credit Card dataset...")
                df = pd.read_csv(creditcard_path)
                
                # Map Credit Card columns to our format
                df = df.rename(columns={
                    'Time': 'hour_of_day',
                    'Amount': 'amount',
                    'Class': 'is_fraud'
                })
                
                # Add missing columns with default values
                df['type'] = 'PAYMENT'
                df['nameOrig'] = f'CUST_{np.random.randint(100000, 999999)}'
                df['oldbalanceOrg'] = np.random.exponential(scale=5000, size=len(df))
                df['newbalanceOrig'] = df['oldbalanceOrg'] - df['amount']
                df['nameDest'] = f'MERCH_{np.random.randint(100000, 999999)}'
                df['oldbalanceDest'] = np.random.exponential(scale=3000, size=len(df))
                df['newbalanceDest'] = df['oldbalanceDest'] + df['amount']
                
                # Add time features
                df['hour_of_day'] = (df['hour_of_day'] // 3600) % 24
                df['day_of_week'] = (df['hour_of_day'] // 86400) % 7
                
                # Clean data
                df = df.dropna()
                self.logger.info(f"Loaded Credit Card dataset: {len(df):,} transactions, fraud rate: {df['is_fraud'].mean():.3%}")
                return df
            
            # Fallback to sample data
            self.logger.warning("No real datasets found, using sample data...")
            return await self._generate_sample_data_fallback()
            
        except Exception as e:
            self.logger.error(f"Failed to load real dataset: {str(e)}")
            return await self._generate_sample_data_fallback()
    
    async def _generate_sample_data_fallback(self) -> pd.DataFrame:
        """Generate sample training data as fallback"""
        np.random.seed(42)
        n_samples = 10000
        
        # Generate features
        data = {
            'amount': np.random.exponential(scale=1000, size=n_samples),
            'oldbalanceOrg': np.random.exponential(scale=5000, size=n_samples),
            'newbalanceOrig': np.random.exponential(scale=4500, size=n_samples),
            'oldbalanceDest': np.random.exponential(scale=3000, size=n_samples),
            'newbalanceDest': np.random.exponential(scale=3500, size=n_samples),
            'type': np.random.choice(['CASH-IN', 'CASH-OUT', 'DEBIT', 'PAYMENT', 'TRANSFER'], n_samples),
            'hour_of_day': np.random.randint(0, 24, n_samples),
            'day_of_week': np.random.randint(0, 7, n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Generate labels (fraud patterns)
        fraud_conditions = [
            (df['amount'] > 10000) & (df['type'].isin(['TRANSFER', 'CASH-OUT'])),
            (df['oldbalanceOrg'] - df['newbalanceOrig'] != df['amount']) & (df['amount'] > 0),
            (df['hour_of_day'] < 6) & (df['amount'] > 5000)
        ]
        
        df['is_fraud'] = np.select(fraud_conditions, [1, 1, 1], default=0)
        
        # Add some noise
        fraud_indices = np.random.choice(df[df['is_fraud'] == 0].index, size=int(0.02 * n_samples), replace=False)
        df.loc[fraud_indices, 'is_fraud'] = 1
        
        return df
    
    async def _preprocess_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Preprocess training data"""
        try:
            # Feature engineering
            features = await self._engineer_features(data)
            
            # Prepare features and target
            X = features.drop('is_fraud', axis=1, errors='ignore')
            y = data['is_fraud'] if 'is_fraud' in data.columns else np.zeros(len(data))
            
            # Handle categorical variables
            X = pd.get_dummies(X, columns=['type'], prefix='type')
            
            # Fill missing values
            X = X.fillna(0)
            
            # Split data with proper stratification handling
            try:
                # Check if we have enough samples for stratification
                if len(y) >= 10 and y.nunique() >= 2:
                    # Check minimum samples per class for stratification
                    class_counts = y.value_counts()
                    min_class_count = class_counts.min()
                    
                    if min_class_count >= 2:  # Need at least 2 samples per class for stratification
                        X_train, X_test, y_train, y_test = train_test_split(
                            X, y, test_size=0.2, random_state=42, stratify=y
                        )
                    else:
                        self.logger.warning(f"Insufficient samples per class for stratification (min: {min_class_count}), using random split")
                        X_train, X_test, y_train, y_test = train_test_split(
                            X, y, test_size=0.2, random_state=42
                        )
                else:
                    self.logger.warning("Insufficient data or single class, using random split")
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=0.2, random_state=42
                    )
            except ValueError as e:
                self.logger.warning(f"Stratification failed: {str(e)}, using random split")
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
            
            # Scale features
            self.scalers = StandardScaler()
            X_train_scaled = self.scalers.fit_transform(X_train)
            X_test_scaled = self.scalers.transform(X_test)
            
            return X_train_scaled, X_test_scaled, y_train, y_test
            
        except Exception as e:
            self.logger.error(f"Data preprocessing failed: {str(e)}")
            raise
    
    async def _engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer features from raw data"""
        features = data.copy()
        
        # Amount features
        features['amount_log'] = np.log1p(features['amount'])
        features['amount_sqrt'] = np.sqrt(features['amount'])
        
        # Balance features
        features['balance_change_orig'] = features['newbalanceOrig'] - features['oldbalanceOrg']
        features['balance_change_dest'] = features['newbalanceDest'] - features['oldbalanceDest']
        
        # Error indicators
        features['error_orig'] = ((features['oldbalanceOrg'] - features['newbalanceOrig'] != features['amount']) & (features['amount'] > 0)).astype(int)
        features['error_dest'] = ((features['newbalanceDest'] - features['oldbalanceDest'] != features['amount']) & (features['amount'] > 0)).astype(int)
        
        # Time features
        features['is_weekend'] = (features['day_of_week'] >= 5).astype(int)
        features['is_night'] = ((features['hour_of_day'] < 6) | (features['hour_of_day'] > 22)).astype(int)
        
        return features
    
    async def _train_isolation_forest(self, X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Train Isolation Forest model"""
        try:
            with mlflow.start_run(run_name="Isolation_Forest_Training"):
                # Hyperparameter tuning
                param_grid = {
                    'contamination': [0.01, 0.05, 0.1],
                    'n_estimators': [100, 200],
                    'max_features': ['auto', 'sqrt']
                }
                
                model = IsolationForest(random_state=42)
                grid_search = GridSearchCV(model, param_grid, cv=3, scoring='roc_auc')
                grid_search.fit(X_train, y_train)
                
                best_model = grid_search.best_estimator_
                
                # Evaluate
                y_pred = best_model.predict(X_test)
                y_pred_binary = [1 if p == -1 else 0 for p in y_pred]  # Convert -1 to 1 (fraud), 1 to 0 (normal)
                
                auc_score = roc_auc_score(y_test, y_pred_binary)
                precision = np.mean(y_test[y_pred_binary == 1] == 1) if sum(y_pred_binary) > 0 else 0
                recall = np.mean(y_pred_binary[y_test == 1] == 1) if sum(y_test == 1) > 0 else 0
                
                # Log metrics
                mlflow.log_params(grid_search.best_params_)
                mlflow.log_metric("auc", auc_score)
                mlflow.log_metric("precision", precision)
                mlflow.log_metric("recall", recall)
                
                # Save model
                mlflow.sklearn.log_model(best_model, "model")
                
                return {
                    "model": best_model,
                    "auc": auc_score,
                    "precision": precision,
                    "recall": recall,
                    "params": grid_search.best_params_
                }
                
        except Exception as e:
            self.logger.error(f"Isolation Forest training failed: {str(e)}")
            raise
    
    async def _train_xgboost(self, X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Train XGBoost model"""
        try:
            with mlflow.start_run(run_name="XGBoost_Training"):
                # Hyperparameter tuning
                param_grid = {
                    'n_estimators': [100, 200],
                    'max_depth': [3, 6],
                    'learning_rate': [0.01, 0.1],
                    'subsample': [0.8, 1.0]
                }
                
                model = xgb.XGBClassifier(
                    objective='binary:logistic',
                    eval_metric='auc',
                    use_label_encoder=False,
                    random_state=42
                )
                
                grid_search = GridSearchCV(model, param_grid, cv=3, scoring='roc_auc')
                grid_search.fit(X_train, y_train)
                
                best_model = grid_search.best_estimator_
                
                # Evaluate
                y_pred_proba = best_model.predict_proba(X_test)[:, 1]
                y_pred = best_model.predict(X_test)
                
                auc_score = roc_auc_score(y_test, y_pred_proba)
                precision = np.mean(y_test[y_pred == 1] == 1) if sum(y_pred) > 0 else 0
                recall = np.mean(y_pred[y_test == 1] == 1) if sum(y_test == 1) > 0 else 0
                
                # Log metrics
                mlflow.log_params(grid_search.best_params_)
                mlflow.log_metric("auc", auc_score)
                mlflow.log_metric("precision", precision)
                mlflow.log_metric("recall", recall)
                
                # Save model
                mlflow.xgboost.log_model(best_model, "model")
                
                return {
                    "model": best_model,
                    "auc": auc_score,
                    "precision": precision,
                    "recall": recall,
                    "params": grid_search.best_params_
                }
                
        except Exception as e:
            self.logger.error(f"XGBoost training failed: {str(e)}")
            raise
    
    async def _train_ensemble(self, X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Train ensemble model"""
        try:
            with mlflow.start_run(run_name="Ensemble_Training"):
                # Create ensemble from trained models
                isolation_model = self.models.get("isolation_forest")
                xgboost_model = self.models.get("xgboost_classifier")
                
                if isolation_model and xgboost_model:
                    ensemble = EnsembleModel({
                        "isolation_forest": isolation_model,
                        "xgboost": xgboost_model
                    })
                    
                    # Evaluate ensemble
                    y_pred_proba = ensemble.predict_proba(X_test)[:, 1]
                    y_pred = ensemble.predict(X_test)
                    
                    auc_score = roc_auc_score(y_test, y_pred_proba)
                    precision = np.mean(y_test[y_pred == 1] == 1) if sum(y_pred) > 0 else 0
                    recall = np.mean(y_pred[y_test == 1] == 1) if sum(y_test == 1) > 0 else 0
                    
                    # Log metrics
                    mlflow.log_metric("auc", auc_score)
                    mlflow.log_metric("precision", precision)
                    mlflow.log_metric("recall", recall)
                    
                    # Save model
                    mlflow.sklearn.log_model(ensemble, "model")
                    
                    return {
                        "model": ensemble,
                        "auc": auc_score,
                        "precision": precision,
                        "recall": recall,
                        "params": {"ensemble_type": "weighted_voting"}
                    }
                else:
                    raise ValueError("Required models not available for ensemble")
                    
        except Exception as e:
            self.logger.error(f"Ensemble training failed: {str(e)}")
            raise
    
    async def _save_models_to_mlflow(self, models_results: Dict[str, Any]):
        """Save trained models to MLflow registry"""
        try:
            for model_name, result in models_results.items():
                if "model" in result:
                    # Register model
                    model_uri = f"runs:/{mlflow.active_run().info.run_id}/model"
                    mlflow.register_model(model_uri, f"fraud_detection_{model_name}")
                    
                    self.logger.info(f"Registered model: fraud_detection_{model_name}")
            
            # Save scalers
            scaler_uri = f"runs:/{mlflow.active_run().info.run_id}/scalers"
            mlflow.sklearn.log_model(self.scalers, "scalers")
            mlflow.register_model(scaler_uri, "fraud_scalers")
            
        except Exception as e:
            self.logger.error(f"Failed to save models to MLflow: {str(e)}")
    
    async def get_model_status(self) -> Dict[str, Any]:
        """Get status of loaded models"""
        status = {}
        for model_name, model in self.models.items():
            status[model_name] = {
                "loaded": model is not None,
                "type": type(model).__name__ if model else None
            }
        return status
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information"""
        return {
            "models": await self.get_model_status(),
            "scalers_loaded": len(self.scalers) > 0,
            "training_jobs": list(self.training_jobs.keys()),
            "last_updated": datetime.now().isoformat()
        }
    
    async def trigger_retraining(self) -> str:
        """Trigger model retraining job"""
        job_id = f"retrain_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start training in background
        asyncio.create_task(self._background_training(job_id))
        
        return job_id
    
    async def _background_training(self, job_id: str):
        """Background training task"""
        try:
            self.training_jobs[job_id] = {"status": "running", "started": datetime.now()}
            
            result = await self.train_models()
            
            self.training_jobs[job_id] = {
                "status": "completed",
                "started": self.training_jobs[job_id]["started"],
                "completed": datetime.now(),
                "result": result
            }
            
        except Exception as e:
            self.training_jobs[job_id] = {
                "status": "failed",
                "started": self.training_jobs[job_id]["started"],
                "failed": datetime.now(),
                "error": str(e)
            }


class EnsembleModel:
    """Ensemble model combining multiple fraud detection models"""
    
    def __init__(self, models: Dict[str, Any]):
        self.models = models
        self.weights = {"isolation_forest": 0.3, "xgboost": 0.7}
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make ensemble predictions"""
        predictions = []
        
        for model_name, model in self.models.items():
            if model_name == "isolation_forest":
                pred = model.predict(X)
                pred = [1 if p == -1 else 0 for p in pred]  # Convert to binary
            else:
                pred = model.predict(X)
            
            predictions.append(pred)
        
        # Weighted voting
        weighted_pred = np.zeros(len(X))
        for i, pred in enumerate(predictions):
            model_name = list(self.models.keys())[i]
            weight = self.weights.get(model_name, 1.0 / len(predictions))
            weighted_pred += pred * weight
        
        return (weighted_pred > 0.5).astype(int)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get ensemble prediction probabilities"""
        probabilities = []
        
        for model_name, model in self.models.items():
            if model_name == "isolation_forest":
                # Convert isolation forest scores to probabilities
                scores = model.decision_function(X)
                prob = 1 / (1 + np.exp(scores))  # Convert to probability-like scores
                prob = np.column_stack([1 - prob, prob])
            else:
                prob = model.predict_proba(X)
            
            probabilities.append(prob)
        
        # Weighted average of probabilities
        weighted_prob = np.zeros_like(probabilities[0])
        for i, prob in enumerate(probabilities):
            model_name = list(self.models.keys())[i]
            weight = self.weights.get(model_name, 1.0 / len(probabilities))
            weighted_prob += prob * weight
        
        return weighted_prob
