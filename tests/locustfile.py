from locust import HttpUser, task, between, events
import json
import random
import time
from datetime import datetime

class FraudDetectionLoadTest(HttpUser):
    """Load testing for Fraud Detection API"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts"""
        print(f"User started: {self.environment.parsed_options.host}")
    
    @task(3)  # Weight 3 - most common operation
    def predict_single_transaction(self):
        """Test single transaction prediction"""
        # Generate realistic transaction data
        transaction_types = ['CASH-IN', 'CASH-OUT', 'DEBIT', 'PAYMENT', 'TRANSFER']
        
        transaction_data = {
            "transaction_id": f"TXN_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
            "type": random.choice(transaction_types),
            "amount": round(random.uniform(10, 50000), 2),
            "oldbalanceOrg": round(random.uniform(0, 100000), 2),
            "newbalanceOrig": round(random.uniform(0, 100000), 2),
            "oldbalanceDest": round(random.uniform(0, 100000), 2),
            "newbalanceDest": round(random.uniform(0, 100000), 2),
            "nameOrig": f"C{random.randint(100000000, 999999999)}",
            "nameDest": f"C{random.randint(100000000, 999999999)}",
            "timestamp": datetime.now().isoformat()
        }
        
        # Ensure balance changes make sense
        amount = transaction_data["amount"]
        old_balance_orig = transaction_data["oldbalanceOrg"]
        transaction_data["newbalanceOrig"] = max(0, old_balance_orig - amount)
        
        with self.client.post(
            "/predict/single",
            json=transaction_data,
            catch_response=True,
            name="Single Prediction"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Validate response structure
                if "prediction" in data and "fraud_probability" in data["prediction"]:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)  # Weight 2 - batch predictions
    def predict_batch_transactions(self):
        """Test batch transaction prediction"""
        batch_size = random.randint(5, 20)
        transactions = []
        
        for i in range(batch_size):
            transaction_types = ['CASH-IN', 'CASH-OUT', 'DEBIT', 'PAYMENT', 'TRANSFER']
            
            transaction_data = {
                "transaction_id": f"TXN_BATCH_{int(time.time() * 1000)}_{i}_{random.randint(1000, 9999)}",
                "type": random.choice(transaction_types),
                "amount": round(random.uniform(10, 50000), 2),
                "oldbalanceOrg": round(random.uniform(0, 100000), 2),
                "newbalanceOrig": round(random.uniform(0, 100000), 2),
                "oldbalanceDest": round(random.uniform(0, 100000), 2),
                "newbalanceDest": round(random.uniform(0, 100000), 2),
                "nameOrig": f"C{random.randint(100000000, 999999999)}",
                "nameDest": f"C{random.randint(100000000, 999999999)}"
            }
            
            # Ensure balance changes make sense
            amount = transaction_data["amount"]
            old_balance_orig = transaction_data["oldbalanceOrg"]
            transaction_data["newbalanceOrig"] = max(0, old_balance_orig - amount)
            
            transactions.append(transaction_data)
        
        with self.client.post(
            "/predict/batch",
            json=transactions,
            catch_response=True,
            name="Batch Prediction"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Validate response structure
                if "predictions" in data and "total_transactions" in data:
                    if len(data["predictions"]) == batch_size:
                        response.success()
                    else:
                        response.failure(f"Expected {batch_size} predictions, got {len(data['predictions'])}")
                else:
                    response.failure("Invalid response structure")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)  # Weight 1 - health checks
    def health_check(self):
        """Test health check endpoint"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="Health Check"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "healthy":
                    response.success()
                else:
                    response.failure("Unhealthy status")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)  # Weight 1 - metrics endpoint
    def get_metrics(self):
        """Test metrics endpoint"""
        with self.client.get(
            "/metrics",
            catch_response=True,
            name="Get Metrics"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "prediction_stats" in data:
                    response.success()
                else:
                    response.failure("Missing prediction stats")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)  # Weight 1 - model info
    def get_model_info(self):
        """Test model info endpoint"""
        with self.client.get(
            "/model/info",
            catch_response=True,
            name="Model Info"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "models" in data:
                    response.success()
                else:
                    response.failure("Missing models info")
            else:
                response.failure(f"HTTP {response.status_code}")


class FraudDetectionStressTest(HttpUser):
    """Stress testing for Fraud Detection API"""
    
    wait_time = between(0.1, 0.5)  # Very short wait time for stress testing
    
    @task
    def high_volume_predictions(self):
        """High volume single predictions for stress testing"""
        transaction_data = {
            "transaction_id": f"STRESS_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
            "type": random.choice(['CASH-IN', 'CASH-OUT', 'TRANSFER']),
            "amount": round(random.uniform(100, 10000), 2),
            "oldbalanceOrg": round(random.uniform(1000, 50000), 2),
            "newbalanceOrig": round(random.uniform(0, 50000), 2),
            "oldbalanceDest": round(random.uniform(1000, 50000), 2),
            "newbalanceDest": round(random.uniform(0, 50000), 2),
            "nameOrig": f"C{random.randint(100000000, 999999999)}",
            "nameDest": f"C{random.randint(100000000, 999999999)}"
        }
        
        self.client.post("/predict/single", json=transaction_data, name="Stress Prediction")


# Event handlers for reporting
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, **kwargs):
    """Log request events"""
    if response.status_code >= 400:
        print(f"Error: {name} - Status: {response.status_code} - Response time: {response_time}ms")

@events.spawning_complete.add_listener
def on_spawning_complete(user_count):
    """Called when all users have been spawned"""
    print(f"Spawning complete. {user_count} users started.")

@events.quitting.add_listener
def on_quitting(environment):
    """Called when the test is quitting"""
    print("Test quitting. Generating final report...")

# Custom statistics for performance criteria
class PerformanceValidator:
    """Validate performance against requirements"""
    
    def __init__(self):
        self.latency_threshold = 100  # 100ms latency requirement
        self.throughput_threshold = 100  # 100 transactions/second
    
    def validate_latency(self, response_time):
        """Check if response time meets latency requirement"""
        return response_time <= self.latency_threshold
    
    def validate_throughput(self, requests_per_second):
        """Check if throughput meets requirement"""
        return requests_per_second >= self.throughput_threshold


# Performance monitoring
performance_validator = PerformanceValidator()

@events.request.add_listener
def validate_performance(request_type, name, response_time, response_length, response, **kwargs):
    """Validate performance against requirements"""
    if name == "Single Prediction":
        if not performance_validator.validate_latency(response_time):
            print(f"PERFORMANCE WARNING: {name} took {response_time}ms (threshold: {performance_validator.latency_threshold}ms)")


if __name__ == "__main__":
    # Example of how to run the tests
    print("To run load tests:")
    print("locust -f locustfile.py --host=http://localhost:8000")
    print("\nTo run stress tests:")
    print("locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10 --run-time=60s --stress-test")
