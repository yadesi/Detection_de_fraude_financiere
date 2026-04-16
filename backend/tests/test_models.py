import pytest
import asyncio
import numpy as np
import pandas as pd
from unittest.mock import AsyncMock, patch, MagicMock
from sklearn.ensemble import IsolationForest
from sklearn.datasets import make_classification
import mlflow
import tempfile
import os

# Import model service
from src.model_service import ModelService, EnsembleModel

class TestModelService:
    """Test suite for Model Service"""
    
    @pytest.fixture
    def model_service(self):
        """Create model service instance"""
        return ModelService()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample training data"""
        # Generate synthetic data
        X, y = make_classification(
            n_samples=1000,
            n_features=10,
            n_informative=5,
            n_redundant=2,
            n_clusters_per_class=1,
            random_state=42
        )
        
        # Convert to DataFrame with realistic column names
        feature_names = [
            'amount', 'amount_log', 'balance_change_orig', 'balance_change_dest',
            'error_orig', 'error_dest', 'hour_of_day', 'day_of_week',
            'is_weekend', 'is_night'
        ]
        
        df = pd.DataFrame(X, columns=feature_names)
        df['is_fraud'] = y
        
        # Add some categorical features
        df['type'] = np.random.choice(['CASH-IN', 'CASH-OUT', 'TRANSFER', 'PAYMENT'], len(df))
        
        return df
    
    @pytest.fixture
    def mock_mlflow(self):
        """Mock MLflow for testing"""
        with patch('src.model_service.mlflow') as mock_mlflow:
            mock_mlflow.set_tracking_uri = MagicMock()
            mock_mlflow.start_run = MagicMock()
            mock_mlflow.log_params = MagicMock()
            mock_mlflow.log_metric = MagicMock()
            mock_mlflow.sklearn.log_model = MagicMock()
            mock_mlflow.xgboost.log_model = MagicMock()
            mock_mlflow.register_model = MagicMock()
            mock_mlflow.pyfunc.load_model = MagicMock()
            mock_mlflow.active_run = MagicMock()
            mock_mlflow.active_run.info.run_id = "test_run_id"
            
            yield mock_mlflow
    
    @pytest.mark.asyncio
    async def test_load_models_success(self, model_service, mock_mlflow):
        """Test successful model loading"""
        # Mock successful model loading
        mock_isolation = IsolationForest(contamination=0.1, random_state=42)
        mock_mlflow.sklearn.load_model.return_value = mock_isolation
        
        await model_service.load_models()
        
        assert "isolation_forest" in model_service.models
        assert model_service.models["isolation_forest"] is not None
        assert model_service.scalers is not None
    
    @pytest.mark.asyncio
    async def test_load_models_failure(self, model_service, mock_mlflow):
        """Test model loading failure handling"""
        # Mock loading failure
        mock_mlflow.sklearn.load_model.side_effect = Exception("Model not found")
        
        await model_service.load_models()
        
        # Should create fallback models
        assert "isolation_forest" in model_service.models
        assert "xgboost_classifier" in model_service.models
        assert model_service.scalers is not None
    
    @pytest.mark.asyncio
    async def test_train_models_with_sample_data(self, model_service, sample_data, mock_mlflow):
        """Test model training with sample data"""
        # Mock MLflow tracking
        mock_mlflow.start_run.return_value.__enter__ = MagicMock()
        mock_mlflow.start_run.return_value.__exit__ = MagicMock()
        
        # Create temporary file for sample data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_data.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            result = await model_service.train_models(temp_file)
            
            assert result["status"] == "success"
            assert "models_trained" in result
            assert "results" in result
            assert "isolation_forest" in result["models_trained"]
            assert "xgboost" in result["models_trained"]
            assert "ensemble" in result["models_trained"]
            
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_train_models_without_data(self, model_service, mock_mlflow):
        """Test model training with generated sample data"""
        # Mock MLflow tracking
        mock_mlflow.start_run.return_value.__enter__ = MagicMock()
        mock_mlflow.start_run.return_value.__exit__ = MagicMock()
        
        result = await model_service.train_models()
        
        assert result["status"] == "success"
        assert "models_trained" in result
        assert len(result["models_trained"]) > 0
    
    @pytest.mark.asyncio
    async def test_train_models_failure(self, model_service, mock_mlflow):
        """Test model training failure handling"""
        # Mock training failure
        mock_mlflow.start_run.side_effect = Exception("Training failed")
        
        result = await model_service.train_models()
        
        assert result["status"] == "error"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_model_status(self, model_service):
        """Test getting model status"""
        # Add some mock models
        model_service.models["isolation_forest"] = IsolationForest()
        model_service.models["xgboost_classifier"] = None
        
        status = await model_service.get_model_status()
        
        assert "isolation_forest" in status
        assert "xgboost_classifier" in status
        assert status["isolation_forest"]["loaded"] == True
        assert status["isolation_forest"]["type"] == "IsolationForest"
        assert status["xgboost_classifier"]["loaded"] == False
    
    @pytest.mark.asyncio
    async def test_get_model_info(self, model_service):
        """Test getting detailed model information"""
        # Add mock models and training jobs
        model_service.models["isolation_forest"] = IsolationForest()
        model_service.training_jobs["job_1"] = {"status": "completed"}
        
        info = await model_service.get_model_info()
        
        assert "models" in info
        assert "training_jobs" in info
        assert "last_updated" in info
        assert len(info["training_jobs"]) == 1
    
    @pytest.mark.asyncio
    async def test_trigger_retraining(self, model_service):
        """Test triggering model retraining"""
        job_id = await model_service.trigger_retraining()
        
        assert job_id.startswith("retrain_job_")
        assert job_id in model_service.training_jobs
        assert model_service.training_jobs[job_id]["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_background_training_success(self, model_service, mock_mlflow):
        """Test background training job success"""
        # Mock successful training
        mock_mlflow.start_run.return_value.__enter__ = MagicMock()
        mock_mlflow.start_run.return_value.__exit__ = MagicMock()
        
        job_id = await model_service.trigger_retraining()
        
        # Wait a bit for background task to complete
        await asyncio.sleep(0.1)
        
        assert model_service.training_jobs[job_id]["status"] == "completed"
        assert "result" in model_service.training_jobs[job_id]
    
    def test_engineer_features(self, model_service):
        """Test feature engineering"""
        # Create sample raw data
        raw_data = pd.DataFrame({
            'amount': [1000, 2000],
            'oldbalanceOrg': [5000, 3000],
            'newbalanceOrig': [4000, 1000],
            'oldbalanceDest': [2000, 1500],
            'newbalanceDest': [3000, 2500],
            'type': ['TRANSFER', 'PAYMENT'],
            'hour_of_day': [12, 14],
            'day_of_week': [3, 4]
        })
        
        features = asyncio.run(model_service._engineer_features(raw_data))
        
        # Check that engineered features are present
        assert 'amount_log' in features.columns
        assert 'amount_sqrt' in features.columns
        assert 'balance_change_orig' in features.columns
        assert 'balance_change_dest' in features.columns
        assert 'error_orig' in features.columns
        assert 'error_dest' in features.columns
        assert 'is_weekend' in features.columns
        assert 'is_night' in features.columns
        
        # Check feature values
        assert features['amount_log'].iloc[0] == np.log1p(1000)
        assert features['balance_change_orig'].iloc[0] == -1000
        assert features['is_weekend'].iloc[0] == 0  # Wednesday


class TestEnsembleModel:
    """Test suite for Ensemble Model"""
    
    @pytest.fixture
    def ensemble_model(self):
        """Create ensemble model with mock base models"""
        # Create mock models
        isolation_model = IsolationForest(contamination=0.1, random_state=42)
        xgboost_model = MagicMock()
        xgboost_model.predict.return_value = np.array([0, 1, 0, 1])
        xgboost_model.predict_proba.return_value = np.array([[0.8, 0.2], [0.3, 0.7], [0.9, 0.1], [0.4, 0.6]])
        
        models = {
            "isolation_forest": isolation_model,
            "xgboost": xgboost_model
        }
        
        return EnsembleModel(models)
    
    def test_ensemble_predict(self, ensemble_model):
        """Test ensemble prediction"""
        # Create sample features
        X = np.random.rand(4, 5)
        
        predictions = ensemble_model.predict(X)
        
        assert len(predictions) == 4
        assert all(pred in [0, 1] for pred in predictions)
    
    def test_ensemble_predict_proba(self, ensemble_model):
        """Test ensemble probability prediction"""
        # Create sample features
        X = np.random.rand(4, 5)
        
        probabilities = ensemble_model.predict_proba(X)
        
        assert probabilities.shape == (4, 2)  # Binary classification
        assert np.allclose(probabilities.sum(axis=1), 1.0)  # Probabilities sum to 1
    
    def test_ensemble_weights(self, ensemble_model):
        """Test ensemble model weights"""
        assert "isolation_forest" in ensemble_model.weights
        assert "xgboost" in ensemble_model.weights
        assert sum(ensemble_model.weights.values()) == 1.0


class TestModelPerformance:
    """Performance tests for model service"""
    
    @pytest.mark.asyncio
    async def test_training_performance(self):
        """Test that model training completes in reasonable time"""
        import time
        
        model_service = ModelService()
        
        start_time = time.time()
        result = await model_service.train_models()
        end_time = time.time()
        
        training_time = end_time - start_time
        
        assert result["status"] == "success"
        assert training_time < 300  # Should complete within 5 minutes
    
    @pytest.mark.asyncio
    async def test_prediction_performance(self):
        """Test that model predictions are fast enough"""
        import time
        
        # Create sample model
        model_service = ModelService()
        await model_service.load_models()
        
        # Create sample features
        features = {
            'amount': 1000,
            'amount_log': 6.9,
            'transaction_type_encoded': 5,
            'balance_change_orig': -1000,
            'balance_change_dest': 1000,
            'balance_ratio_orig': 0.8,
            'balance_ratio_dest': 1.2,
            'error_orig': 0,
            'error_dest': 0,
            'is_merchant': 0,
            'hour_of_day': 12,
            'day_of_week': 3,
            'is_weekend': 0,
            'is_night': 0,
            'amount_to_balance_ratio': 0.2,
            'is_large_amount': 0,
            'is_small_amount': 0,
            'amount_category': 2,
            'transaction_count_24h': 5,
            'avg_amount_24h': 800,
            'max_amount_24h': 1500,
            'last_transaction_hours': 2,
            'is_new_account': 0
        }
        
        # Test multiple predictions
        start_time = time.time()
        for _ in range(100):
            # This would normally call the prediction service
            # For testing, we'll just simulate the feature preparation
            model_service._prepare_features(features)
        end_time = time.time()
        
        avg_time_per_prediction = (end_time - start_time) / 100 * 1000  # Convert to ms
        
        assert avg_time_per_prediction < 10  # Should be under 10ms per prediction


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
