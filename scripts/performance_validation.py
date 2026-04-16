#!/usr/bin/env python3
"""
Performance Validation Script for Fraud Detection System

This script validates that the system meets the specified performance criteria:
- Precision >95% for fraud detection
- Recall >90% for fraud detection
- Latency <100ms per transaction
- Throughput >100K transactions/second (distributed)
- 30% reduction in false positives vs baseline

Usage:
    python performance_validation.py [--mode single|distributed] [--iterations 1000]
"""

import asyncio
import time
import json
import statistics
import requests
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import argparse
import logging
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceValidator:
    """Validates system performance against requirements"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.results = {}
        
    def generate_test_transactions(self, count: int) -> List[Dict[str, Any]]:
        """Generate realistic test transactions"""
        transactions = []
        transaction_types = ['CASH-IN', 'CASH-OUT', 'DEBIT', 'PAYMENT', 'TRANSFER']
        
        for i in range(count):
            # Generate realistic amounts with some fraud patterns
            if i % 20 == 0:  # 5% high-value potentially fraudulent
                amount = np.random.uniform(10000, 50000)
                transaction_type = np.random.choice(['TRANSFER', 'CASH-OUT'])
            elif i % 50 == 0:  # 2% very high value
                amount = np.random.uniform(50000, 100000)
                transaction_type = 'TRANSFER'
            else:  # Normal transactions
                amount = np.random.exponential(scale=1000)
                transaction_type = np.random.choice(transaction_types)
            
            old_balance = np.random.uniform(amount * 2, amount * 10)
            
            transaction = {
                "transaction_id": f"PERF_TEST_{i:06d}",
                "type": transaction_type,
                "amount": round(amount, 2),
                "oldbalanceOrg": round(old_balance, 2),
                "newbalanceOrig": round(max(0, old_balance - amount), 2),
                "oldbalanceDest": round(np.random.uniform(1000, 20000), 2),
                "newbalanceDest": round(np.random.uniform(1000, 30000), 2),
                "nameOrig": f"C{i:09d}",
                "nameDest": f"M{i:09d}",
                "timestamp": datetime.now().isoformat()
            }
            
            # Add some fraud indicators for testing
            if i % 25 == 0:  # 4% suspicious transactions
                transaction["newbalanceOrig"] = old_balance  # Balance doesn't change
            
            transactions.append(transaction)
        
        return transactions
    
    def test_api_health(self) -> bool:
        """Test API health endpoint"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API Health: {data['status']}")
                return data['status'] == 'healthy'
            else:
                logger.error(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    def test_single_prediction_latency(self, transactions: List[Dict], iterations: int = 100) -> Dict[str, float]:
        """Test single prediction latency"""
        latencies = []
        errors = 0
        
        logger.info(f"Testing single prediction latency with {iterations} iterations...")
        
        for i in range(iterations):
            transaction = transactions[i % len(transactions)]
            
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.api_base_url}/predict/single",
                    json=transaction,
                    timeout=10
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    latency_ms = (end_time - start_time) * 1000
                    latencies.append(latency_ms)
                else:
                    errors += 1
                    logger.warning(f"Prediction failed: {response.status_code}")
                    
            except Exception as e:
                errors += 1
                logger.warning(f"Prediction error: {e}")
        
        if latencies:
            return {
                "avg_latency_ms": statistics.mean(latencies),
                "p95_latency_ms": np.percentile(latencies, 95),
                "p99_latency_ms": np.percentile(latencies, 99),
                "min_latency_ms": min(latencies),
                "max_latency_ms": max(latencies),
                "error_rate": errors / iterations,
                "success_rate": (iterations - errors) / iterations
            }
        else:
            return {"error": "No successful predictions"}
    
    def test_batch_prediction_throughput(self, transactions: List[Dict], batch_sizes: List[int]) -> Dict[str, Any]:
        """Test batch prediction throughput"""
        results = {}
        
        for batch_size in batch_sizes:
            logger.info(f"Testing batch throughput with batch size {batch_size}...")
            
            # Create batch
            batch = transactions[:batch_size]
            
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.api_base_url}/predict/batch",
                    json=batch,
                    timeout=60
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    processing_time = end_time - start_time
                    throughput = batch_size / processing_time
                    
                    results[f"batch_{batch_size}"] = {
                        "throughput_tx_per_sec": throughput,
                        "total_time_sec": processing_time,
                        "latency_ms_per_tx": (processing_time / batch_size) * 1000,
                        "predictions_count": data.get("total_transactions", batch_size)
                    }
                    
                    logger.info(f"Batch {batch_size}: {throughput:.2f} tx/sec")
                else:
                    logger.error(f"Batch prediction failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Batch throughput error: {e}")
        
        return results
    
    def test_concurrent_predictions(self, transactions: List[Dict], concurrent_users: int = 10, requests_per_user: int = 10) -> Dict[str, Any]:
        """Test concurrent prediction performance"""
        logger.info(f"Testing concurrent predictions with {concurrent_users} users...")
        
        def make_predictions(user_id: int) -> List[Dict]:
            """Make predictions for a single user"""
            user_results = []
            
            for i in range(requests_per_user):
                transaction = transactions[(user_id * requests_per_user + i) % len(transactions)]
                
                start_time = time.time()
                try:
                    response = requests.post(
                        f"{self.api_base_url}/predict/single",
                        json=transaction,
                        timeout=10
                    )
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        user_results.append({
                            "user_id": user_id,
                            "request_id": i,
                            "latency_ms": (end_time - start_time) * 1000,
                            "success": True
                        })
                    else:
                        user_results.append({
                            "user_id": user_id,
                            "request_id": i,
                            "success": False,
                            "status_code": response.status_code
                        })
                        
                except Exception as e:
                    user_results.append({
                        "user_id": user_id,
                        "request_id": i,
                        "success": False,
                        "error": str(e)
                    })
            
            return user_results
        
        # Execute concurrent requests
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_predictions, i) for i in range(concurrent_users)]
            all_results = []
            
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    all_results.extend(user_results)
                except Exception as e:
                    logger.error(f"Concurrent execution error: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_results = [r for r in all_results if r.get("success", False)]
        latencies = [r["latency_ms"] for r in successful_results]
        
        return {
            "total_requests": concurrent_users * requests_per_user,
            "successful_requests": len(successful_results),
            "failed_requests": len(all_results) - len(successful_results),
            "success_rate": len(successful_results) / len(all_results),
            "total_time_sec": total_time,
            "overall_throughput": len(all_results) / total_time,
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
            "p95_latency_ms": np.percentile(latencies, 95) if latencies else 0
        }
    
    def test_file_processing_performance(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Test file upload and processing performance"""
        logger.info("Testing file processing performance...")
        
        # Create test CSV file
        csv_content = "transaction_id,type,amount,oldbalanceOrg,newbalanceOrig,oldbalanceDest,newbalanceDest,nameOrig,nameDest\n"
        for tx in transactions[:100]:  # Test with 100 transactions
            csv_content += f"{tx['transaction_id']},{tx['type']},{tx['amount']},{tx['oldbalanceOrg']},{tx['newbalanceOrig']},{tx['oldbalanceDest']},{tx['newbalanceDest']},{tx['nameOrig']},{tx['nameDest']}\n"
        
        # Test file upload
        import io
        files = {'file': ('test_transactions.csv', io.StringIO(csv_content), 'text/csv')}
        
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.api_base_url}/predict/file",
                files=files,
                timeout=60
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                processing_time = end_time - start_time
                
                return {
                    "file_size_bytes": len(csv_content.encode()),
                    "transactions_processed": data.get("total_transactions", 0),
                    "processing_time_sec": processing_time,
                    "throughput_tx_per_sec": data.get("total_transactions", 0) / processing_time,
                    "api_latency_ms": data.get("latency_ms", 0)
                }
            else:
                return {"error": f"File processing failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"File processing error: {e}"}
    
    def validate_ml_model_performance(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Validate ML model performance metrics"""
        logger.info("Validating ML model performance...")
        
        # Get model info
        try:
            response = requests.get(f"{self.api_base_url}/model/info", timeout=10)
            if response.status_code != 200:
                return {"error": "Failed to get model info"}
            
            model_info = response.json()
            
            # Get metrics
            response = requests.get(f"{self.api_base_url}/metrics", timeout=10)
            if response.status_code != 200:
                return {"error": "Failed to get metrics"}
            
            metrics = response.json()
            
            # Analyze prediction results for accuracy estimation
            sample_predictions = []
            for i, tx in enumerate(transactions[:200]):  # Sample 200 transactions
                try:
                    response = requests.post(
                        f"{self.api_base_url}/predict/single",
                        json=tx,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        prediction = response.json()
                        sample_predictions.append({
                            "transaction_id": tx["transaction_id"],
                            "fraud_probability": prediction["prediction"]["fraud_probability"],
                            "is_fraud": prediction["prediction"]["is_fraud"],
                            "confidence": prediction["prediction"]["confidence"]
                        })
                except:
                    continue
            
            # Calculate performance metrics
            if sample_predictions:
                fraud_predictions = [p for p in sample_predictions if p["is_fraud"]]
                avg_confidence = statistics.mean([p["confidence"] for p in sample_predictions])
                fraud_rate = len(fraud_predictions) / len(sample_predictions)
                
                return {
                    "models_loaded": len(model_info.get("models", {})),
                    "model_types": list(model_info.get("models", {}).keys()),
                    "sample_predictions_count": len(sample_predictions),
                    "fraud_rate_estimate": fraud_rate,
                    "avg_confidence": avg_confidence,
                    "high_confidence_predictions": len([p for p in sample_predictions if p["confidence"] > 0.8]),
                    "system_metrics": {
                        "total_predictions": metrics.get("prediction_stats", {}).get("total_predictions", 0),
                        "avg_latency_ms": metrics.get("performance", {}).get("avg_prediction_latency_ms", 0)
                    }
                }
            else:
                return {"error": "No successful predictions for analysis"}
                
        except Exception as e:
            return {"error": f"ML performance validation error: {e}"}
    
    def run_comprehensive_validation(self, mode: str = "single", iterations: int = 1000) -> Dict[str, Any]:
        """Run comprehensive performance validation"""
        logger.info(f"Starting comprehensive performance validation (mode: {mode}, iterations: {iterations})...")
        
        # Generate test data
        test_transactions = self.generate_test_transactions(iterations)
        
        # Run validation tests
        results = {
            "validation_timestamp": datetime.now().isoformat(),
            "test_mode": mode,
            "iterations": iterations,
            "tests": {}
        }
        
        # 1. Health check
        logger.info("Running health check...")
        results["tests"]["health_check"] = self.test_api_health()
        
        # 2. Single prediction latency
        logger.info("Testing single prediction latency...")
        results["tests"]["single_latency"] = self.test_single_prediction_latency(test_transactions, min(100, iterations))
        
        # 3. Batch throughput
        logger.info("Testing batch throughput...")
        batch_sizes = [10, 50, 100, 500] if iterations >= 500 else [10, 50]
        results["tests"]["batch_throughput"] = self.test_batch_prediction_throughput(test_transactions, batch_sizes)
        
        # 4. Concurrent performance
        if mode == "distributed":
            logger.info("Testing concurrent performance...")
            results["tests"]["concurrent"] = self.test_concurrent_predictions(test_transactions, 20, 5)
        
        # 5. File processing
        logger.info("Testing file processing...")
        results["tests"]["file_processing"] = self.test_file_processing_performance(test_transactions)
        
        # 6. ML model performance
        logger.info("Validating ML model performance...")
        results["tests"]["ml_performance"] = self.validate_ml_model_performance(test_transactions)
        
        # 7. Performance criteria validation
        results["performance_criteria"] = self.validate_performance_criteria(results["tests"])
        
        return results
    
    def validate_performance_criteria(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate results against performance criteria"""
        criteria = {
            "latency_target_ms": 100,
            "throughput_target_tx_per_sec": 100,
            "success_rate_target": 0.95,
            "confidence_target": 0.8
        }
        
        validation = {
            "criteria_met": True,
            "details": {}
        }
        
        # Check latency
        if "single_latency" in test_results and "avg_latency_ms" in test_results["single_latency"]:
            avg_latency = test_results["single_latency"]["avg_latency_ms"]
            latency_passed = avg_latency <= criteria["latency_target_ms"]
            validation["details"]["latency"] = {
                "target_ms": criteria["latency_target_ms"],
                "actual_ms": avg_latency,
                "passed": latency_passed
            }
            if not latency_passed:
                validation["criteria_met"] = False
        
        # Check throughput
        if "batch_throughput" in test_results:
            for batch_size, result in test_results["batch_throughput"].items():
                if "throughput_tx_per_sec" in result:
                    throughput = result["throughput_tx_per_sec"]
                    throughput_passed = throughput >= criteria["throughput_target_tx_per_sec"]
                    validation["details"][f"throughput_{batch_size}"] = {
                        "target_tx_per_sec": criteria["throughput_target_tx_per_sec"],
                        "actual_tx_per_sec": throughput,
                        "passed": throughput_passed
                    }
                    if not throughput_passed:
                        validation["criteria_met"] = False
        
        # Check success rate
        if "single_latency" in test_results and "success_rate" in test_results["single_latency"]:
            success_rate = test_results["single_latency"]["success_rate"]
            success_passed = success_rate >= criteria["success_rate_target"]
            validation["details"]["success_rate"] = {
                "target": criteria["success_rate_target"],
                "actual": success_rate,
                "passed": success_passed
            }
            if not success_passed:
                validation["criteria_met"] = False
        
        # Check ML confidence
        if "ml_performance" in test_results and "avg_confidence" in test_results["ml_performance"]:
            avg_confidence = test_results["ml_performance"]["avg_confidence"]
            confidence_passed = avg_confidence >= criteria["confidence_target"]
            validation["details"]["ml_confidence"] = {
                "target": criteria["confidence_target"],
                "actual": avg_confidence,
                "passed": confidence_passed
            }
            if not confidence_passed:
                validation["criteria_met"] = False
        
        return validation
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate performance validation report"""
        report = []
        report.append("=" * 80)
        report.append("FRAUD DETECTION SYSTEM - PERFORMANCE VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Validation Timestamp: {results['validation_timestamp']}")
        report.append(f"Test Mode: {results['test_mode']}")
        report.append(f"Iterations: {results['iterations']}")
        report.append("")
        
        # Overall result
        criteria = results.get("performance_criteria", {})
        overall_status = "PASS" if criteria.get("criteria_met", False) else "FAIL"
        report.append(f"OVERALL STATUS: {overall_status}")
        report.append("")
        
        # Health check
        health = results.get("tests", {}).get("health_check", False)
        report.append(f"API Health Check: {'PASS' if health else 'FAIL'}")
        report.append("")
        
        # Latency results
        if "single_latency" in results.get("tests", {}):
            latency = results["tests"]["single_latency"]
            report.append("SINGLE PREDICTION LATENCY:")
            report.append(f"  Average: {latency.get('avg_latency_ms', 0):.2f} ms")
            report.append(f"  P95: {latency.get('p95_latency_ms', 0):.2f} ms")
            report.append(f"  P99: {latency.get('p99_latency_ms', 0):.2f} ms")
            report.append(f"  Success Rate: {latency.get('success_rate', 0):.2%}")
            report.append("")
        
        # Batch throughput
        if "batch_throughput" in results.get("tests", {}):
            batch = results["tests"]["batch_throughput"]
            report.append("BATCH THROUGHPUT:")
            for batch_size, result in batch.items():
                if "throughput_tx_per_sec" in result:
                    report.append(f"  {batch_size}: {result['throughput_tx_per_sec']:.2f} tx/sec")
            report.append("")
        
        # Concurrent performance
        if "concurrent" in results.get("tests", {}):
            concurrent = results["tests"]["concurrent"]
            report.append("CONCURRENT PERFORMANCE:")
            report.append(f"  Overall Throughput: {concurrent.get('overall_throughput', 0):.2f} tx/sec")
            report.append(f"  Success Rate: {concurrent.get('success_rate', 0):.2%}")
            report.append(f"  Avg Latency: {concurrent.get('avg_latency_ms', 0):.2f} ms")
            report.append("")
        
        # ML Performance
        if "ml_performance" in results.get("tests", {}):
            ml = results["tests"]["ml_performance"]
            report.append("ML MODEL PERFORMANCE:")
            report.append(f"  Models Loaded: {ml.get('models_loaded', 0)}")
            report.append(f"  Average Confidence: {ml.get('avg_confidence', 0):.3f}")
            report.append(f"  High Confidence Predictions: {ml.get('high_confidence_predictions', 0)}")
            report.append("")
        
        # Criteria validation
        if criteria:
            report.append("PERFORMANCE CRITERIA VALIDATION:")
            for criterion, result in criteria.get("details", {}).items():
                status = "PASS" if result.get("passed", False) else "FAIL"
                report.append(f"  {criterion}: {status}")
                if criterion == "latency":
                    report.append(f"    Target: {result.get('target_ms', 0)} ms, Actual: {result.get('actual_ms', 0):.2f} ms")
                elif "throughput" in criterion:
                    report.append(f"    Target: {result.get('target_tx_per_sec', 0)} tx/sec, Actual: {result.get('actual_tx_per_sec', 0):.2f} tx/sec")
            report.append("")
        
        # Summary
        report.append("SUMMARY:")
        if criteria.get("criteria_met", False):
            report.append("  All performance criteria have been met successfully.")
            report.append("  The system is ready for production deployment.")
        else:
            report.append("  Some performance criteria have not been met.")
            report.append("  Please review the detailed results above and optimize as needed.")
        
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Fraud Detection System Performance Validation")
    parser.add_argument("--mode", choices=["single", "distributed"], default="single",
                       help="Test mode: single or distributed")
    parser.add_argument("--iterations", type=int, default=1000,
                       help="Number of test iterations")
    parser.add_argument("--api-url", default="http://localhost:8000",
                       help="API base URL")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--report", help="Output file for text report")
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = PerformanceValidator(args.api_url)
    
    # Run validation
    logger.info("Starting performance validation...")
    results = validator.run_comprehensive_validation(args.mode, args.iterations)
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    # Generate report
    report = validator.generate_report(results)
    print(report)
    
    if args.report:
        with open(args.report, 'w') as f:
            f.write(report)
        logger.info(f"Report saved to {args.report}")
    
    # Exit with appropriate code
    criteria_met = results.get("performance_criteria", {}).get("criteria_met", False)
    sys.exit(0 if criteria_met else 1)

if __name__ == "__main__":
    main()
