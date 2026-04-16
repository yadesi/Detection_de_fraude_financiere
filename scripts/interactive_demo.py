#!/usr/bin/env python3
"""
Interactive Demo Script for Fraud Detection System
Provides a comprehensive demonstration of all system features
"""

import requests
import json
import time
import pandas as pd
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
import os
from demo_data_generator import FraudDemoDataGenerator

class FraudDetectionDemo:
    """Interactive demo for the fraud detection system"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.demo_generator = FraudDemoDataGenerator()
        self.session = requests.Session()
        
    def check_api_health(self) -> bool:
        """Check if API is healthy"""
        try:
            response = self.session.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                print("API Status: HEALTHY")
                health_data = response.json()
                print(f"Services: {health_data.get('services', {})}")
                return True
            else:
                print(f"API Status: ERROR - Status code {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"API Status: ERROR - {e}")
            return False
    
    def demo_single_prediction(self) -> Dict[str, Any]:
        """Demonstrate single transaction prediction"""
        
        print("\n" + "="*50)
        print("DEMO 1: Single Transaction Prediction")
        print("="*50)
        
        # Generate test transaction
        transaction = self.demo_generator.generate_transaction(is_fraud=False)
        
        print("Input Transaction:")
        print(f"  ID: {transaction['transaction_id']}")
        print(f"  Type: {transaction['type']}")
        print(f"  Amount: ${transaction['amount']:,.2f}")
        print(f"  From: {transaction['nameOrig']} (${transaction['oldbalanceOrg']:,.2f} -> ${transaction['newbalanceOrig']:,.2f})")
        print(f"  To: {transaction['nameDest']} (${transaction['oldbalanceDest']:,.2f} -> ${transaction['newbalanceDest']:,.2f})")
        
        # Make prediction
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.api_base_url}/predict/single",
                json=transaction,
                timeout=10
            )
            prediction_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                print(f"\nPrediction Results:")
                print(f"  Fraud Detected: {result['prediction']['is_fraud']}")
                print(f"  Fraud Probability: {result['prediction']['fraud_probability']:.3f}")
                print(f"  Confidence: {result['prediction']['confidence']:.3f}")
                print(f"  Model Version: {result['prediction']['model_version']}")
                print(f"  Latency: {result['latency_ms']:.2f}ms")
                print(f"  Total Time: {prediction_time:.2f}ms")
                
                return result
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network Error: {e}")
            return None
    
    def demo_batch_prediction(self) -> Dict[str, Any]:
        """Demonstrate batch transaction prediction"""
        
        print("\n" + "="*50)
        print("DEMO 2: Batch Transaction Prediction")
        print("="*50)
        
        # Generate batch of transactions
        batch_size = 10
        transactions = self.demo_generator.generate_batch(size=batch_size, fraud_rate=0.2)
        
        print(f"Processing batch of {batch_size} transactions...")
        
        # Count expected frauds
        expected_frauds = sum(1 for tx in transactions if tx.get('is_fraud', False))
        print(f"Expected frauds in batch: {expected_frauds}")
        
        # Make batch prediction
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.api_base_url}/predict/batch",
                json=transactions,
                timeout=30
            )
            prediction_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                predictions = result['predictions']
                
                # Analyze results
                detected_frauds = sum(1 for pred in predictions if pred['prediction']['is_fraud'])
                avg_probability = sum(pred['prediction']['fraud_probability'] for pred in predictions) / len(predictions)
                avg_confidence = sum(pred['prediction']['confidence'] for pred in predictions) / len(predictions)
                
                print(f"\nBatch Results:")
                print(f"  Total Processed: {result['total_transactions']}")
                print(f"  Detected Frauds: {detected_frauds}")
                print(f"  Expected Frauds: {expected_frauds}")
                print(f"  Average Probability: {avg_probability:.3f}")
                print(f"  Average Confidence: {avg_confidence:.3f}")
                print(f"  Batch Latency: {result['latency_ms']:.2f}ms")
                print(f"  Total Time: {prediction_time:.2f}ms")
                print(f"  Throughput: {batch_size / (result['latency_ms']/1000):.1f} tx/sec")
                
                # Show individual predictions
                print(f"\nIndividual Predictions:")
                for i, pred in enumerate(predictions[:5]):  # Show first 5
                    tx_id = pred['transaction_id']
                    is_fraud = pred['prediction']['is_fraud']
                    probability = pred['prediction']['fraud_probability']
                    print(f"  {i+1}. {tx_id}: {'FRAUD' if is_fraud else 'LEGIT'} ({probability:.3f})")
                
                if len(predictions) > 5:
                    print(f"  ... and {len(predictions)-5} more")
                
                return result
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network Error: {e}")
            return None
    
    def demo_file_upload(self) -> Dict[str, Any]:
        """Demonstrate file upload prediction"""
        
        print("\n" + "="*50)
        print("DEMO 3: File Upload Prediction")
        print("="*50)
        
        # Generate test file
        transactions = self.demo_generator.generate_batch(size=50, fraud_rate=0.1)
        
        # Convert to CSV format
        csv_content = "transaction_id,type,amount,oldbalanceOrg,newbalanceOrig,oldbalanceDest,newbalanceDest,nameOrig,nameDest\n"
        for tx in transactions:
            csv_content += f"{tx['transaction_id']},{tx['type']},{tx['amount']},{tx['oldbalanceOrg']},{tx['newbalanceOrig']},{tx['oldbalanceDest']},{tx['newbalanceDest']},{tx['nameOrig']},{tx['nameDest']}\n"
        
        print(f"Uploading file with {len(transactions)} transactions...")
        
        # Make file prediction
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.api_base_url}/predict/file",
                data=csv_content,
                timeout=60
            )
            prediction_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                predictions = result['predictions']
                
                # Analyze results
                detected_frauds = sum(1 for pred in predictions if pred['prediction']['is_fraud'])
                
                print(f"\nFile Upload Results:")
                print(f"  Filename: {result['filename']}")
                print(f"  File Size: {result['file_size']} bytes")
                print(f"  Total Processed: {result['total_transactions']}")
                print(f"  Detected Frauds: {detected_frauds}")
                print(f"  Fraud Rate: {detected_frauds/result['total_transactions']*100:.1f}%")
                print(f"  Processing Latency: {result['latency_ms']:.2f}ms")
                print(f"  Total Time: {prediction_time:.2f}ms")
                
                return result
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network Error: {e}")
            return None
    
    def demo_system_metrics(self) -> Dict[str, Any]:
        """Demonstrate system metrics monitoring"""
        
        print("\n" + "="*50)
        print("DEMO 4: System Metrics")
        print("="*50)
        
        try:
            response = self.session.get(f"{self.api_base_url}/metrics", timeout=10)
            
            if response.status_code == 200:
                metrics = response.json()
                
                print("System Performance Metrics:")
                print(f"  Total Predictions: {metrics['prediction_stats']['total_predictions']:,}")
                print(f"  Fraud Predictions: {metrics['prediction_stats']['fraud_predictions']:,}")
                print(f"  Fraud Rate: {metrics['prediction_stats']['fraud_rate']*100:.2f}%")
                print(f"  Avg Latency: {metrics['performance']['avg_prediction_latency_ms']:.2f}ms")
                print(f"  Error Rate: {metrics['performance']['error_rate']*100:.3f}%")
                print(f"  Throughput: {metrics['performance']['predictions_per_second']:.1f} tx/sec")
                
                print("\nSystem Resources:")
                print(f"  CPU Usage: {metrics['system']['cpu_percent']:.1f}%")
                print(f"  Memory Usage: {metrics['system']['memory_percent']:.1f}%")
                print(f"  Memory Available: {metrics['system']['memory_available_gb']:.1f}GB")
                print(f"  Disk Usage: {metrics['system']['disk_percent']:.1f}%")
                print(f"  Disk Free: {metrics['system']['disk_free_gb']:.1f}GB")
                
                print("\nService Status:")
                for service, status in metrics['services'].items():
                    print(f"  {service.capitalize()}: {status}")
                
                print("\nRecent Alerts:")
                for alert in metrics['recent_alerts']:
                    print(f"  [{alert['type'].upper()}] {alert['message']}")
                
                return metrics
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network Error: {e}")
            return None
    
    def demo_model_info(self) -> Dict[str, Any]:
        """Demonstrate model information"""
        
        print("\n" + "="*50)
        print("DEMO 5: Model Information")
        print("="*50)
        
        try:
            response = self.session.get(f"{self.api_base_url}/model/info", timeout=10)
            
            if response.status_code == 200:
                model_info = response.json()
                
                print("Loaded Models:")
                for model_name, model_data in model_info['models'].items():
                    print(f"  {model_name}: {model_data}")
                
                print(f"\nScalers Loaded: {model_info['scalers_loaded']}")
                print(f"Training Jobs: {len(model_info['training_jobs'])}")
                print(f"Last Updated: {model_info['last_updated']}")
                
                return model_info
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network Error: {e}")
            return None
    
    def demo_prediction_history(self) -> Dict[str, Any]:
        """Demonstrate prediction history"""
        
        print("\n" + "="*50)
        print("DEMO 6: Prediction History")
        print("="*50)
        
        try:
            response = self.session.get(f"{self.api_base_url}/predictions/history?limit=10", timeout=10)
            
            if response.status_code == 200:
                history = response.json()
                
                print("Recent Predictions:")
                for i, pred in enumerate(history[:5]):  # Show last 5
                    tx_id = pred['transaction_id']
                    is_fraud = pred['prediction']['is_fraud']
                    probability = pred['prediction']['fraud_probability']
                    timestamp = pred['timestamp']
                    
                    print(f"  {i+1}. {tx_id}: {'FRAUD' if is_fraud else 'LEGIT'} ({probability:.3f}) at {timestamp}")
                
                return history
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network Error: {e}")
            return None
    
    def demo_stress_test(self, duration_seconds: int = 30) -> Dict[str, Any]:
        """Demonstrate stress testing"""
        
        print("\n" + "="*50)
        print("DEMO 7: Stress Testing")
        print("="*50)
        
        print(f"Running stress test for {duration_seconds} seconds...")
        
        results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency": 0,
            "min_latency": float('inf'),
            "max_latency": 0,
            "start_time": time.time()
        }
        
        end_time = time.time() + duration_seconds
        
        while time.time() < end_time:
            # Generate random transaction
            transaction = self.demo_generator.generate_transaction(is_fraud=random.random() < 0.1)
            
            # Make prediction
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{self.api_base_url}/predict/single",
                    json=transaction,
                    timeout=5
                )
                latency = (time.time() - start_time) * 1000
                
                results["total_requests"] += 1
                
                if response.status_code == 200:
                    results["successful_requests"] += 1
                    results["total_latency"] += latency
                    results["min_latency"] = min(results["min_latency"], latency)
                    results["max_latency"] = max(results["max_latency"], latency)
                else:
                    results["failed_requests"] += 1
                    
            except requests.exceptions.RequestException:
                results["failed_requests"] += 1
            
            # Small delay to prevent overwhelming
            time.sleep(0.1)
        
        # Calculate statistics
        duration = time.time() - results["start_time"]
        if results["successful_requests"] > 0:
            avg_latency = results["total_latency"] / results["successful_requests"]
        else:
            avg_latency = 0
        
        print(f"\nStress Test Results:")
        print(f"  Duration: {duration:.1f} seconds")
        print(f"  Total Requests: {results['total_requests']}")
        print(f"  Successful: {results['successful_requests']}")
        print(f"  Failed: {results['failed_requests']}")
        print(f"  Success Rate: {results['successful_requests']/results['total_requests']*100:.1f}%")
        print(f"  Requests/sec: {results['total_requests']/duration:.1f}")
        print(f"  Avg Latency: {avg_latency:.2f}ms")
        print(f"  Min Latency: {results['min_latency']:.2f}ms")
        print(f"  Max Latency: {results['max_latency']:.2f}ms")
        
        return results
    
    def run_complete_demo(self):
        """Run complete demonstration of all features"""
        
        print("FRAUD DETECTION SYSTEM - INTERACTIVE DEMO")
        print("=" * 60)
        print(f"API Endpoint: {self.api_base_url}")
        print(f"Demo Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check API health first
        if not self.check_api_health():
            print("\nERROR: API is not responding. Please ensure the system is running.")
            return
        
        # Run all demos
        demos = [
            ("Single Prediction", self.demo_single_prediction),
            ("Batch Prediction", self.demo_batch_prediction),
            ("File Upload", self.demo_file_upload),
            ("System Metrics", self.demo_system_metrics),
            ("Model Information", self.demo_model_info),
            ("Prediction History", self.demo_prediction_history),
            ("Stress Test", lambda: self.demo_stress_test(10))  # 10-second stress test
        ]
        
        results = {}
        
        for demo_name, demo_func in demos:
            try:
                print(f"\n{'='*60}")
                print(f"STARTING: {demo_name}")
                print(f"{'='*60}")
                
                result = demo_func()
                results[demo_name] = result
                
                print(f"\nCOMPLETED: {demo_name}")
                
                # Pause between demos
                if demo_name != demos[-1][0]:
                    print("Pausing 2 seconds before next demo...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"ERROR in {demo_name}: {e}")
                results[demo_name] = {"error": str(e)}
        
        # Final summary
        print(f"\n{'='*60}")
        print("DEMO SUMMARY")
        print(f"{'='*60}")
        
        for demo_name, result in results.items():
            if "error" in result:
                print(f"  {demo_name}: FAILED - {result['error']}")
            else:
                print(f"  {demo_name}: SUCCESS")
        
        print(f"\nDemo Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nSystem URLs:")
        print(f"  - API Documentation: {self.api_base_url}/docs")
        print(f"  - Frontend: http://localhost:3001")
        print(f"  - Dashboard: http://localhost:8501")
        print(f"  - Grafana: http://localhost:3000 (admin/admin)")

def main():
    """Main function to run the demo"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Fraud Detection System Interactive Demo")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--demo", choices=["all", "single", "batch", "file", "metrics", "model", "history", "stress"], 
                       default="all", help="Specific demo to run")
    parser.add_argument("--stress-duration", type=int, default=30, help="Stress test duration in seconds")
    
    args = parser.parse_args()
    
    demo = FraudDetectionDemo(args.api_url)
    
    if args.demo == "all":
        demo.run_complete_demo()
    elif args.demo == "single":
        demo.demo_single_prediction()
    elif args.demo == "batch":
        demo.demo_batch_prediction()
    elif args.demo == "file":
        demo.demo_file_upload()
    elif args.demo == "metrics":
        demo.demo_system_metrics()
    elif args.demo == "model":
        demo.demo_model_info()
    elif args.demo == "history":
        demo.demo_prediction_history()
    elif args.demo == "stress":
        demo.demo_stress_test(args.stress_duration)

if __name__ == "__main__":
    main()
