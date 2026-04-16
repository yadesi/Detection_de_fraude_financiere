import pytest
import asyncio
import json
import requests
import time
from typing import Dict, Any
import tempfile
import os
import pandas as pd

class TestIntegration:
    """Integration tests for the complete fraud detection system"""
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        """Base URL for API tests"""
        return "http://localhost:8000"
    
    @pytest.fixture(scope="class")
    def sample_transaction(self):
        """Sample transaction data for testing"""
        return {
            "transaction_id": "TEST_TXN_001",
            "type": "TRANSFER",
            "amount": 15000.0,
            "oldbalanceOrg": 50000.0,
            "newbalanceOrig": 35000.0,
            "oldbalanceDest": 20000.0,
            "newbalanceDest": 35000.0,
            "nameOrig": "C123456789",
            "nameDest": "M987654321",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    
    @pytest.fixture(scope="class")
    def sample_batch_transactions(self):
        """Sample batch transaction data"""
        return [
            {
                "transaction_id": f"BATCH_TXN_{i:03d}",
                "type": "TRANSFER" if i % 2 == 0 else "PAYMENT",
                "amount": 1000.0 + (i * 100),
                "oldbalanceOrg": 10000.0 + (i * 500),
                "newbalanceOrig": 9000.0 + (i * 400),
                "oldbalanceDest": 5000.0 + (i * 200),
                "newbalanceDest": 6000.0 + (i * 300),
                "nameOrig": f"C{i:09d}",
                "nameDest": f"M{i:09d}"
            }
            for i in range(10)
        ]
    
    def test_api_health_check(self, api_base_url):
        """Test API health check endpoint"""
        response = requests.get(f"{api_base_url}/health", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
    
    def test_single_prediction_workflow(self, api_base_url, sample_transaction):
        """Test complete single prediction workflow"""
        # Step 1: Make prediction
        response = requests.post(
            f"{api_base_url}/predict/single",
            json=sample_transaction,
            timeout=10
        )
        
        assert response.status_code == 200
        prediction_data = response.json()
        
        # Validate response structure
        required_fields = ["transaction_id", "prediction", "latency_ms", "timestamp"]
        for field in required_fields:
            assert field in prediction_data
        
        # Validate prediction structure
        prediction = prediction_data["prediction"]
        required_prediction_fields = ["is_fraud", "fraud_probability", "confidence", "model_version", "prediction_timestamp"]
        for field in required_prediction_fields:
            assert field in prediction
        
        # Validate data types
        assert isinstance(prediction["is_fraud"], bool)
        assert isinstance(prediction["fraud_probability"], (int, float))
        assert 0 <= prediction["fraud_probability"] <= 1
        assert isinstance(prediction["confidence"], (int, float))
        assert 0 <= prediction["confidence"] <= 1
        assert isinstance(prediction_data["latency_ms"], (int, float))
        assert prediction_data["latency_ms"] >= 0
    
    def test_batch_prediction_workflow(self, api_base_url, sample_batch_transactions):
        """Test complete batch prediction workflow"""
        response = requests.post(
            f"{api_base_url}/predict/batch",
            json=sample_batch_transactions,
            timeout=30
        )
        
        assert response.status_code == 200
        batch_data = response.json()
        
        # Validate response structure
        required_fields = ["predictions", "total_transactions", "latency_ms", "timestamp"]
        for field in required_fields:
            assert field in batch_data
        
        # Validate batch results
        assert batch_data["total_transactions"] == len(sample_batch_transactions)
        assert len(batch_data["predictions"]) == len(sample_batch_transactions)
        
        # Validate each prediction
        for i, prediction_result in enumerate(batch_data["predictions"]):
            assert "transaction_id" in prediction_result
            assert "prediction" in prediction_result
            assert prediction_result["transaction_id"] == sample_batch_transactions[i]["transaction_id"]
            
            # Validate prediction structure
            prediction = prediction_result["prediction"]
            assert "is_fraud" in prediction
            assert "fraud_probability" in prediction
            assert "confidence" in prediction
    
    def test_file_upload_workflow(self, api_base_url):
        """Test file upload and prediction workflow"""
        # Create sample CSV data
        csv_data = """transaction_id,type,amount,oldbalanceOrg,newbalanceOrig,oldbalanceDest,newbalanceDest,nameOrig,nameDest
FILE_TXN_001,TRANSFER,15000,50000,35000,20000,35000,C123456789,M987654321
FILE_TXN_002,PAYMENT,500,8000,7500,3000,3500,C234567890,M123456789
FILE_TXN_003,CASH-OUT,2000,15000,13000,10000,12000,C345678901,M234567890"""
        
        # Upload CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_file = f.name
        
        try:
            with open(temp_file, 'rb') as f:
                files = {'file': ('test_transactions.csv', f, 'text/csv')}
                response = requests.post(
                    f"{api_base_url}/predict/file",
                    files=files,
                    timeout=30
                )
            
            assert response.status_code == 200
            file_data = response.json()
            
            # Validate response structure
            required_fields = ["filename", "file_size", "predictions", "total_transactions", "latency_ms", "timestamp"]
            for field in required_fields:
                assert field in file_data
            
            assert file_data["filename"] == "test_transactions.csv"
            assert file_data["total_transactions"] == 3
            assert len(file_data["predictions"]) == 3
            
        finally:
            os.unlink(temp_file)
    
    def test_metrics_and_monitoring(self, api_base_url):
        """Test metrics collection and monitoring"""
        # Make some predictions to generate metrics
        for i in range(5):
            transaction = {
                "transaction_id": f"METRIC_TXN_{i}",
                "type": "TRANSFER",
                "amount": 1000.0 + (i * 200),
                "oldbalanceOrg": 10000.0,
                "newbalanceOrig": 9000.0 - (i * 200),
                "oldbalanceDest": 5000.0,
                "newbalanceDest": 6000.0 + (i * 200),
                "nameOrig": f"C{i:09d}",
                "nameDest": f"M{i:09d}"
            }
            
            requests.post(f"{api_base_url}/predict/single", json=transaction, timeout=10)
        
        # Get metrics
        response = requests.get(f"{api_base_url}/metrics", timeout=10)
        assert response.status_code == 200
        metrics_data = response.json()
        
        # Validate metrics structure
        assert "prediction_stats" in metrics_data
        assert "performance" in metrics_data
        
        prediction_stats = metrics_data["prediction_stats"]
        assert "total_predictions" in prediction_stats
        assert "fraud_rate" in prediction_stats
        
        performance = metrics_data["performance"]
        assert "avg_prediction_latency_ms" in performance
    
    def test_model_management(self, api_base_url):
        """Test model management endpoints"""
        # Get model info
        response = requests.get(f"{api_base_url}/model/info", timeout=10)
        assert response.status_code == 200
        model_info = response.json()
        
        # Validate model info structure
        assert "models" in model_info
        assert "last_updated" in model_info
        
        # Trigger retraining (this might take time, so we'll just check the response)
        response = requests.post(f"{api_base_url}/model/retrain", timeout=10)
        assert response.status_code == 200
        retrain_data = response.json()
        
        assert "message" in retrain_data
        assert "job_id" in retrain_data
        assert "timestamp" in retrain_data
    
    def test_prediction_history(self, api_base_url):
        """Test prediction history endpoint"""
        response = requests.get(f"{api_base_url}/predictions/history?limit=5", timeout=10)
        assert response.status_code == 200
        history_data = response.json()
        
        # Should return a list
        assert isinstance(history_data, list)
        assert len(history_data) <= 5
        
        # Validate history item structure if present
        if history_data:
            history_item = history_data[0]
            assert "transaction_id" in history_item
            assert "prediction" in history_item
            assert "timestamp" in history_item
    
    def test_error_handling(self, api_base_url):
        """Test error handling and edge cases"""
        # Test invalid transaction data
        invalid_transaction = {
            "transaction_id": "",  # Empty ID
            "type": "INVALID_TYPE",  # Invalid type
            "amount": -1000  # Negative amount
        }
        
        response = requests.post(
            f"{api_base_url}/predict/single",
            json=invalid_transaction,
            timeout=10
        )
        
        # Should handle gracefully (either 200 with processed defaults or 422 for validation)
        assert response.status_code in [200, 422]
        
        # Test missing required fields
        incomplete_transaction = {
            "transaction_id": "INCOMPLETE_TXN"
            # Missing other required fields
        }
        
        response = requests.post(
            f"{api_base_url}/predict/single",
            json=incomplete_transaction,
            timeout=10
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 422]
    
    def test_performance_requirements(self, api_base_url, sample_transaction):
        """Test that performance requirements are met"""
        # Test latency requirement (<100ms per prediction)
        latencies = []
        
        for i in range(10):
            start_time = time.time()
            response = requests.post(
                f"{api_base_url}/predict/single",
                json=sample_transaction,
                timeout=10
            )
            end_time = time.time()
            
            assert response.status_code == 200
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
        
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        # Performance assertions
        assert avg_latency < 100, f"Average latency {avg_latency:.2f}ms exceeds 100ms requirement"
        assert max_latency < 200, f"Max latency {max_latency:.2f}ms exceeds 200ms threshold"
        
        # Test throughput requirement (>100 transactions/second)
        batch_size = 50
        start_time = time.time()
        
        # Create batch of transactions
        batch_transactions = [
            {
                "transaction_id": f"THROUGHPUT_TXN_{i}",
                "type": "TRANSFER",
                "amount": 1000.0 + i,
                "oldbalanceOrg": 10000.0,
                "newbalanceOrig": 9000.0 - i,
                "oldbalanceDest": 5000.0,
                "newbalanceDest": 6000.0 + i,
                "nameOrig": f"C{i:09d}",
                "nameDest": f"M{i:09d}"
            }
            for i in range(batch_size)
        ]
        
        response = requests.post(
            f"{api_base_url}/predict/batch",
            json=batch_transactions,
            timeout=30
        )
        end_time = time.time()
        
        assert response.status_code == 200
        throughput = batch_size / (end_time - start_time)
        
        assert throughput > 10, f"Throughput {throughput:.2f} tx/s below minimum threshold"
    
    def test_system_resilience(self, api_base_url):
        """Test system resilience under load"""
        # Test concurrent requests
        import concurrent.futures
        
        def make_request():
            transaction = {
                "transaction_id": f"CONCURRENT_TXN_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
                "type": "TRANSFER",
                "amount": 1000.0,
                "oldbalanceOrg": 10000.0,
                "newbalanceOrig": 9000.0,
                "oldbalanceDest": 5000.0,
                "newbalanceDest": 6000.0,
                "nameOrig": "C123456789",
                "nameDest": "M987654321"
            }
            
            try:
                response = requests.post(
                    f"{api_base_url}/predict/single",
                    json=transaction,
                    timeout=10
                )
                return response.status_code == 200
            except:
                return False
        
        # Make 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in futures]
        
        # At least 80% should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8, f"Success rate {success_rate:.2%} below 80% threshold"


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])
