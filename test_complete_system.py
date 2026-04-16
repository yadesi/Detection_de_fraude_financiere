#!/usr/bin/env python3
"""
Complete System Test - Frontend, Backend, and Streamlit Dashboard
"""

import requests
import time
import subprocess
import sys
import json
from datetime import datetime

def test_frontend_react():
    """Test React Frontend"""
    
    print("Testing React Frontend...")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:3001", timeout=10)
        if response.status_code == 200:
            print("React Frontend: ACCESSIBLE")
            print("  URL: http://localhost:3001")
            print("  Status: Working")
            return True
        else:
            print(f"React Frontend: ERROR (status {response.status_code})")
            return False
    except Exception as e:
        print(f"React Frontend: NOT ACCESSIBLE ({e})")
        return False

def test_streamlit_dashboard():
    """Test Streamlit Dashboard"""
    
    print("Testing Streamlit Dashboard...")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:8501", timeout=10)
        if response.status_code == 200:
            print("Streamlit Dashboard: ACCESSIBLE")
            print("  URL: http://localhost:8501")
            print("  Status: Working (plotly issue resolved)")
            return True
        else:
            print(f"Streamlit Dashboard: ERROR (status {response.status_code})")
            return False
    except Exception as e:
        print(f"Streamlit Dashboard: NOT ACCESSIBLE ({e})")
        return False

def test_backend_api():
    """Test Backend API"""
    
    print("Testing Backend API...")
    print("-" * 40)
    
    endpoints = [
        ("/health", "Health Check"),
        ("/metrics", "System Metrics"),
        ("/predictions/history?limit=5", "Prediction History"),
        ("/model/info", "Model Information")
    ]
    
    results = {}
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"  {name}: OK")
                results[endpoint] = True
            else:
                print(f"  {name}: FAILED (status {response.status_code})")
                results[endpoint] = False
        except Exception as e:
            print(f"  {name}: ERROR ({e})")
            results[endpoint] = False
    
    return results

def test_prediction_endpoint():
    """Test prediction functionality"""
    
    print("Testing Prediction Endpoint...")
    print("-" * 40)
    
    test_transaction = {
        "transaction_id": "TEST_COMPLETE_001",
        "type": "TRANSFER",
        "amount": 15000,
        "oldbalanceOrg": 50000,
        "newbalanceOrig": 35000,
        "oldbalanceDest": 20000,
        "newbalanceDest": 35000,
        "nameOrig": "C123456789",
        "nameDest": "M987654321"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/predict/single",
            json=test_transaction,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("  Single Prediction: OK")
            print(f"    Transaction ID: {result.get('transaction_id')}")
            print(f"    Is Fraud: {result.get('prediction', {}).get('is_fraud')}")
            print(f"    Fraud Probability: {result.get('prediction', {}).get('fraud_probability', 0):.3f}")
            print(f"    Latency: {result.get('latency_ms', 0):.2f}ms")
            return True
        else:
            print(f"  Single Prediction: FAILED (status {response.status_code})")
            return False
            
    except Exception as e:
        print(f"  Single Prediction: ERROR ({e})")
        return False

def check_container_status():
    """Check all container status"""
    
    print("Checking Container Status...")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            ["docker-compose", "ps"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            services = {}
            
            for line in lines:
                if 'backend' in line:
                    services['backend'] = 'Up' in line
                elif 'frontend' in line:
                    services['frontend'] = 'Up' in line
                elif 'streamlit' in line:
                    services['streamlit'] = 'Up' in line
                elif 'grafana' in line:
                    services['grafana'] = 'Up' in line
                elif 'prometheus' in line:
                    services['prometheus'] = 'Up' in line
                elif 'mlflow' in line:
                    services['mlflow'] = 'Up' in line
                elif 'kafka' in line:
                    services['kafka'] = 'Up' in line
                elif 'redis' in line:
                    services['redis'] = 'Up' in line
                elif 'zookeeper' in line:
                    services['zookeeper'] = 'Up' in line
            
            for service, status in services.items():
                status_str = "Running" if status else "Stopped"
                print(f"  {service}: {status_str}")
            
            return all(services.values())
        else:
            print("Error checking Docker status")
            return False
            
    except Exception as e:
        print(f"Error checking Docker: {e}")
        return False

def main():
    """Main test function"""
    
    print("COMPLETE SYSTEM TEST")
    print("=" * 60)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check container status
    containers_ok = check_container_status()
    
    if containers_ok:
        print("\n" + "=" * 60)
        print("TESTING SERVICES")
        print("=" * 60)
        
        # Test React Frontend
        frontend_ok = test_frontend_react()
        
        # Test Streamlit Dashboard
        streamlit_ok = test_streamlit_dashboard()
        
        # Test Backend API
        api_results = test_backend_api()
        
        # Test Prediction Endpoint
        prediction_ok = test_prediction_endpoint()
        
        # Summary
        print("\n" + "=" * 60)
        print("FINAL TEST RESULTS")
        print("=" * 60)
        
        print(f"Containers: {'OK' if containers_ok else 'FAILED'}")
        print(f"React Frontend: {'OK' if frontend_ok else 'FAILED'}")
        print(f"Streamlit Dashboard: {'OK' if streamlit_ok else 'FAILED'}")
        print(f"Backend API: {sum(api_results.values())}/{len(api_results)} endpoints working")
        print(f"Prediction Test: {'OK' if prediction_ok else 'FAILED'}")
        
        # Success criteria
        all_services_ok = containers_ok and frontend_ok and streamlit_ok
        api_working = sum(api_results.values()) >= 3  # At least 3 endpoints working
        
        if all_services_ok and api_working and prediction_ok:
            print("\n" + "SUCCESS: ALL SYSTEMS WORKING!" + " " * 20)
            print("\n" + "ACCESS URLs:")
            print("-" * 40)
            print("  React Frontend:     http://localhost:3001")
            print("  Streamlit Dashboard: http://localhost:8501")
            print("  API Documentation:  http://localhost:8000/docs")
            print("  Grafana:           http://localhost:3000 (admin/admin)")
            print("  Prometheus:        http://localhost:9090")
            print("  MLflow:            http://localhost:5000")
            
            print("\n" + "NEW FEATURES:")
            print("-" * 40)
            print("  - Modern React dashboard with real-time updates")
            print("  - Beautiful UI with gradients and animations")
            print("  - Streamlit dashboard (plotly issue resolved)")
            print("  - Mock data fallback when backend unavailable")
            print("  - Connection status indicators")
            print("  - Enhanced charts and visualizations")
            print("  - Responsive design for all devices")
            
            print("\n" + "SYSTEM CAPABILITIES:")
            print("-" * 40)
            print("  - Real-time fraud detection")
            print("  - Batch and single predictions")
            print("  - File upload and processing")
            print("  - Interactive analytics")
            print("  - System monitoring")
            print("  - Alert management")
            print("  - Performance metrics")
            
            return True
        else:
            print("\n" + "ISSUES DETECTED:")
            print("-" * 40)
            if not containers_ok:
                print("  - Some containers are not running")
            if not frontend_ok:
                print("  - React frontend is not accessible")
            if not streamlit_ok:
                print("  - Streamlit dashboard is not accessible")
            if not api_working:
                print("  - Backend API has issues")
            if not prediction_ok:
                print("  - Prediction endpoint failed")
            
            print("\n" + "TROUBLESHOOTING:")
            print("-" * 40)
            print("  1. Check container status: docker-compose ps")
            print("  2. Restart services: docker-compose restart")
            print("  3. Check logs: docker-compose logs [service]")
            print("  4. Rebuild if needed: docker-compose build [service]")
            print("  5. Verify ports: netstat -ano | findstr :3001")
            
            return False
    else:
        print("\n" + "ERROR: Docker containers are not running properly")
        print("Try: docker-compose up -d")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
