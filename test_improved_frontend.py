#!/usr/bin/env python3
"""
Test script for the improved frontend and dashboard
"""

import requests
import time
import subprocess
import sys
import json

def test_backend_connection():
    """Test if backend is accessible"""
    
    print("Testing Backend Connection...")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("Backend is running correctly")
            return True
        else:
            print(f"Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"Backend is not accessible: {e}")
        return False

def test_frontend_access():
    """Test if frontend is accessible"""
    
    print("\nTesting Frontend Access...")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:3001", timeout=10)
        if response.status_code == 200:
            print("Frontend is accessible")
            return True
        else:
            print(f"Frontend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"Frontend is not accessible: {e}")
        return False

def test_api_endpoints():
    """Test key API endpoints"""
    
    print("\nTesting API Endpoints...")
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

def test_frontend_backend_communication():
    """Test frontend-backend communication"""
    
    print("\nTesting Frontend-Backend Communication...")
    print("-" * 40)
    
    # Test a sample prediction
    test_transaction = {
        "transaction_id": "TEST_COMM_001",
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
    """Check Docker container status"""
    
    print("\nChecking Container Status...")
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
    
    print("FRONTEND AND BACKEND COMMUNICATION TEST")
    print("=" * 50)
    
    # Test container status
    containers_ok = check_container_status()
    
    if containers_ok:
        # Test backend connection
        backend_ok = test_backend_connection()
        
        # Test frontend access
        frontend_ok = test_frontend_access()
        
        # Test API endpoints
        api_results = test_api_endpoints()
        
        # Test frontend-backend communication
        comm_ok = test_frontend_backend_communication()
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        print(f"Containers: {'OK' if containers_ok else 'FAILED'}")
        print(f"Backend: {'OK' if backend_ok else 'FAILED'}")
        print(f"Frontend: {'OK' if frontend_ok else 'FAILED'}")
        print(f"API Endpoints: {sum(api_results.values())}/{len(api_results)} working")
        print(f"Communication: {'OK' if comm_ok else 'FAILED'}")
        
        if backend_ok and frontend_ok and comm_ok:
            print("\nSUCCESS: Frontend-Backend communication is working!")
            print("\nYou can access:")
            print("  - Frontend: http://localhost:3001")
            print("  - API Docs: http://localhost:8000/docs")
            print("  - Dashboard: http://localhost:8501")
            print("  - Grafana: http://localhost:3000 (admin/admin)")
            
            print("\nNew Features:")
            print("  - Modern dashboard with real-time updates")
            print("  - Beautiful UI with gradients and animations")
            print("  - Responsive design for mobile devices")
            print("  - Mock data when backend is not available")
            print("  - Connection status indicators")
            print("  - Enhanced charts and visualizations")
            
            return True
        else:
            print("\nISSUES DETECTED:")
            if not backend_ok:
                print("  - Backend is not accessible")
            if not frontend_ok:
                print("  - Frontend is not accessible")
            if not comm_ok:
                print("  - Frontend-Backend communication failed")
            
            print("\nTroubleshooting:")
            print("  1. Check container status: docker-compose ps")
            print("  2. Restart services: docker-compose restart")
            print("  3. Check logs: docker-compose logs frontend")
            print("  4. Rebuild if needed: docker-compose build frontend")
            
            return False
    else:
        print("\nERROR: Docker containers are not running properly")
        print("Try: docker-compose up -d")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
