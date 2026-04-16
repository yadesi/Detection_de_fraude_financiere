import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import pandas as pd
import numpy as np

# Import the main application
from src.main import app
from src.prediction_service import PredictionService
from src.data_processor import DataProcessor
from src.model_service import ModelService
from src.monitoring import MetricsCollector

# Create test client
client = TestClient(app)

class TestAPIEndpoints:
    """Test suite for API endpoints"""
    
    @pytest.fixture
    def mock_services(self):
        """Mock all services for testing"""
        with patch('src.main.prediction_service') as mock_pred, \
             patch('src.main.data_processor') as mock_data, \
             patch('src.main.model_service') as mock_model, \
             patch('src.main.metrics') as mock_metrics:
            
            # Setup mock prediction service
            mock_pred.initialize = AsyncMock()
            mock_pred.predict = AsyncMock(return_value={
                "is_fraud": False,
                "fraud_probability": 0.1,
                "confidence": 0.9,
                "model_version": "1.0.0",
                "prediction_timestamp": "2024-01-01T12:00:00"
            })
            mock_pred.get_kafka_status = AsyncMock(return_value={"status": "connected"})
            mock_pred.get_redis_status = AsyncMock(return_value={"status": "connected"})
            mock_pred.get_prediction_history = AsyncMock(return_value=[])
            mock_pred.cleanup = AsyncMock()
            
            # Setup mock data processor
            mock_data.process_transaction = AsyncMock(return_value={
                "amount": 1000,
                "type": "TRANSFER",
                "transaction_type_encoded": 5,
                "amount_log": 6.9,
                "balance_change_orig": -1000,
                "error_orig": 0,
                "hour_of_day": 12,
                "day_of_week": 3
            })
            
            # Setup mock model service
            mock_model.load_models = AsyncMock()
            mock_model.get_model_status = AsyncMock(return_value={
                "isolation_forest": {"loaded": True, "type": "IsolationForest"},
                "xgboost": {"loaded": True, "type": "XGBClassifier"}
            })
            mock_model.get_model_info = AsyncMock(return_value={
                "models": {"isolation_forest": {"loaded": True}},
                "last_updated": "2024-01-01T12:00:00"
            })
            mock_model.trigger_retraining = AsyncMock(return_value="job_123")
            
            # Setup mock metrics
            mock_metrics.start_collection = MagicMock()
            mock_metrics.stop_collection = MagicMock()
            mock_metrics.record_prediction_latency = MagicMock()
            mock_metrics.record_prediction = MagicMock()
            mock_metrics.get_all_metrics = AsyncMock(return_value={
                "prediction_stats": {"total_predictions": 100, "fraud_rate": 0.02},
                "performance": {"avg_prediction_latency_ms": 50}
            })
            
            yield {
                'prediction': mock_pred,
                'data': mock_data,
                'model': mock_model,
                'metrics': mock_metrics
            }
    
    def test_root_endpoint(self, mock_services):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Fraud Detection API"
        assert data["version"] == "1.0.0"
    
    def test_health_check(self, mock_services):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
        assert data["services"]["models"]["isolation_forest"]["loaded"] == True
    
    def test_predict_single_valid(self, mock_services):
        """Test single prediction with valid data"""
        transaction_data = {
            "transaction_id": "TXN123",
            "type": "TRANSFER",
            "amount": 1000,
            "oldbalanceOrg": 5000,
            "newbalanceOrig": 4000,
            "oldbalanceDest": 2000,
            "newbalanceDest": 3000,
            "nameOrig": "C123456",
            "nameDest": "M789012"
        }
        
        response = client.post("/predict/single", json=transaction_data)
        assert response.status_code == 200
        data = response.json()
        assert "transaction_id" in data
        assert "prediction" in data
        assert "latency_ms" in data
        assert "timestamp" in data
        assert data["prediction"]["is_fraud"] == False
        assert data["prediction"]["fraud_probability"] == 0.1
    
    def test_predict_single_invalid(self, mock_services):
        """Test single prediction with invalid data"""
        invalid_data = {
            "type": "INVALID_TYPE",
            "amount": -100  # Negative amount
        }
        
        response = client.post("/predict/single", json=invalid_data)
        # Should still process but with validation errors handled in processing
        assert response.status_code in [200, 422]
    
    def test_predict_batch(self, mock_services):
        """Test batch prediction"""
        transactions = [
            {
                "transaction_id": "TXN1",
                "type": "TRANSFER",
                "amount": 1000,
                "oldbalanceOrg": 5000,
                "newbalanceOrig": 4000
            },
            {
                "transaction_id": "TXN2",
                "type": "PAYMENT",
                "amount": 500,
                "oldbalanceOrg": 2000,
                "newbalanceOrig": 1500
            }
        ]
        
        response = client.post("/predict/batch", json=transactions)
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "total_transactions" in data
        assert "latency_ms" in data
        assert len(data["predictions"]) == 2
        assert data["total_transactions"] == 2
    
    def test_predict_file_csv(self, mock_services):
        """Test file prediction with CSV"""
        # Create a mock CSV content
        csv_content = """transaction_id,type,amount,oldbalanceOrg,newbalanceOrig
TXN1,TRANSFER,1000,5000,4000
TXN2,PAYMENT,500,2000,1500"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        response = client.post("/predict/file", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "file_size" in data
        assert "predictions" in data
        assert data["filename"] == "test.csv"
    
    def test_predict_file_json(self, mock_services):
        """Test file prediction with JSON"""
        json_content = json.dumps([
            {
                "transaction_id": "TXN1",
                "type": "TRANSFER",
                "amount": 1000,
                "oldbalanceOrg": 5000,
                "newbalanceOrig": 4000
            }
        ])
        
        files = {"file": ("test.json", json_content, "application/json")}
        response = client.post("/predict/file", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "predictions" in data
        assert data["filename"] == "test.json"
    
    def test_predict_file_invalid_format(self, mock_services):
        """Test file prediction with invalid format"""
        files = {"file": ("test.txt", "invalid content", "text/plain")}
        response = client.post("/predict/file", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "Only CSV and JSON files are supported" in data["detail"]
    
    def test_get_metrics(self, mock_services):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "prediction_stats" in data
        assert "performance" in data
    
    def test_get_model_info(self, mock_services):
        """Test model info endpoint"""
        response = client.get("/model/info")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "last_updated" in data
    
    def test_trigger_retrain(self, mock_services):
        """Test model retraining trigger"""
        response = client.post("/model/retrain")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "job_id" in data
        assert "timestamp" in data
        assert data["message"] == "Retraining started"
    
    def test_get_prediction_history(self, mock_services):
        """Test prediction history endpoint"""
        response = client.get("/predictions/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_prediction_history_with_limit(self, mock_services):
        """Test prediction history endpoint with limit"""
        response = client.get("/predictions/history?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAPIPerformance:
    """Performance tests for API endpoints"""
    
    def test_single_prediction_latency(self, mock_services):
        """Test that single prediction meets latency requirements"""
        import time
        
        transaction_data = {
            "transaction_id": "TXN_PERF",
            "type": "TRANSFER",
            "amount": 1000,
            "oldbalanceOrg": 5000,
            "newbalanceOrig": 4000
        }
        
        start_time = time.time()
        response = client.post("/predict/single", json=transaction_data)
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert latency_ms < 100  # Should be under 100ms
    
    def test_batch_prediction_throughput(self, mock_services):
        """Test batch prediction throughput"""
        import time
        
        # Create a batch of 100 transactions
        transactions = [
            {
                "transaction_id": f"TXN_{i}",
                "type": "TRANSFER",
                "amount": 1000 + i,
                "oldbalanceOrg": 5000,
                "newbalanceOrig": 4000
            }
            for i in range(100)
        ]
        
        start_time = time.time()
        response = client.post("/predict/batch", json=transactions)
        end_time = time.time()
        
        throughput = len(transactions) / (end_time - start_time)
        
        assert response.status_code == 200
        assert throughput > 10  # Should handle at least 10 transactions per second


class TestAPIErrorHandling:
    """Test error handling in API endpoints"""
    
    def test_service_unavailable_handling(self, mock_services):
        """Test handling when services are unavailable"""
        # Mock service to raise an exception
        mock_services['prediction'].predict.side_effect = Exception("Service unavailable")
        
        transaction_data = {
            "transaction_id": "TXN_ERROR",
            "type": "TRANSFER",
            "amount": 1000
        }
        
        response = client.post("/predict/single", json=transaction_data)
        assert response.status_code == 500
        data = response.json()
        assert "Prediction failed" in data["detail"]
    
    def test_missing_required_fields(self, mock_services):
        """Test handling of missing required fields"""
        incomplete_data = {
            "transaction_id": "TXN_INCOMPLETE"
            # Missing required fields like type, amount
        }
        
        response = client.post("/predict/single", json=incomplete_data)
        # Should still process but with defaults or validation errors
        assert response.status_code in [200, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
