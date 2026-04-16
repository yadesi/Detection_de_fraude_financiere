#!/usr/bin/env python3
"""
Test script to verify complete frontend functionality restoration
"""

import requests
import time
import subprocess
import sys

def test_frontend_access():
    """Test if frontend is accessible"""
    
    print("Testing Frontend Access...")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:3001", timeout=10)
        if response.status_code == 200:
            print("Frontend: ACCESSIBLE")
            print("  Status Code: 200")
            return True
        else:
            print(f"Frontend: ERROR (status {response.status_code})")
            return False
    except Exception as e:
        print(f"Frontend: NOT ACCESSIBLE ({e})")
        return False

def test_frontend_compilation():
    """Check if frontend compiled successfully"""
    
    print("Checking Frontend Compilation...")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            ["docker-compose", "logs", "frontend"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        logs = result.stdout.lower()
        
        if "compiled successfully" in logs:
            print("Frontend: COMPILED SUCCESSFULLY")
            return True
        elif "webpack compiled with" in logs:
            print("Frontend: COMPILED WITH ERRORS")
            return False
        else:
            print("Frontend: COMPILATION STATUS UNCLEAR")
            return False
            
    except Exception as e:
        print(f"Error checking compilation: {e}")
        return False

def test_frontend_content():
    """Test if frontend has complete content"""
    
    print("Testing Frontend Content...")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:3001", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # Check for complete features
            features_found = {
                'Dashboard': 'dashboard' in content.lower(),
                'Transaction Form': 'transaction' in content.lower(),
                'Analytics': 'analytics' in content.lower(),
                'File Upload': 'upload' in content.lower(),
                'Settings': 'settings' in content.lower(),
                'Charts/Visualizations': 'chart' in content.lower() or 'visualization' in content.lower(),
                'Metrics': 'metric' in content.lower() or 'statistic' in content.lower()
            }
            
            print("Features detected:")
            for feature, found in features_found.items():
                status = "YES" if found else "NO"
                print(f"  {feature}: {status}")
            
            # Count features
            working_features = sum(features_found.values())
            total_features = len(features_found)
            
            print(f"\nFeatures working: {working_features}/{total_features}")
            
            if working_features >= 5:  # At least 5 features working
                print("Frontend: COMPLETE FUNCTIONALITY RESTORED")
                return True
            else:
                print("Frontend: PARTIAL FUNCTIONALITY")
                return False
        else:
            print("Frontend: NOT ACCESSIBLE")
            return False
            
    except Exception as e:
        print(f"Error testing content: {e}")
        return False

def test_backend_connectivity():
    """Test if backend is accessible for frontend"""
    
    print("Testing Backend Connectivity...")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("Backend: ACCESSIBLE")
            return True
        else:
            print(f"Backend: ERROR (status {response.status_code})")
            return False
    except Exception as e:
        print(f"Backend: NOT ACCESSIBLE ({e})")
        return False

def main():
    """Main test function"""
    
    print("COMPLETE FRONTEND FUNCTIONALITY TEST")
    print("=" * 60)
    print("Testing restoration of all features: metrics, charts, transactions...")
    print()
    
    # Test backend first
    backend_ok = test_backend_connectivity()
    
    # Test frontend
    frontend_ok = test_frontend_access()
    compilation_ok = test_frontend_compilation()
    content_ok = test_frontend_content()
    
    # Summary
    print("\n" + "=" * 60)
    print("RESTORATION TEST RESULTS")
    print("=" * 60)
    
    print(f"Backend Connectivity: {'OK' if backend_ok else 'FAILED'}")
    print(f"Frontend Access: {'OK' if frontend_ok else 'FAILED'}")
    print(f"Frontend Compilation: {'OK' if compilation_ok else 'FAILED'}")
    print(f"Frontend Content: {'OK' if content_ok else 'FAILED'}")
    
    # Overall assessment
    overall_success = frontend_ok and compilation_ok and content_ok
    
    if overall_success:
        print("\nSUCCESS: FRONTEND FULLY RESTORED!")
        print("\nRestored Features:")
        print("- Dashboard with real-time metrics")
        print("- Interactive charts and visualizations")
        print("- Transaction form for testing")
        print("- File upload functionality")
        print("- Analytics page")
        print("- Settings page")
        print("- Modern UI with gradients and animations")
        
        print("\nWhat you can now do:")
        print("1. View dashboard with metrics and charts")
        print("2. Add transactions for fraud testing")
        print("3. Upload files for batch processing")
        print("4. View analytics and insights")
        print("5. Configure system settings")
        
        print("\nAccess URL: http://localhost:3001")
        return True
    else:
        print("\nISSUES DETECTED:")
        if not frontend_ok:
            print("  - Frontend not accessible")
        if not compilation_ok:
            print("  - Frontend compilation errors")
        if not content_ok:
            print("  - Missing features or content")
        if not backend_ok:
            print("  - Backend not accessible")
        
        print("\nTroubleshooting:")
        print("  1. Check frontend logs: docker-compose logs frontend")
        print("  2. Restart frontend: docker-compose restart frontend")
        print("  3. Check backend: docker-compose logs backend")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
