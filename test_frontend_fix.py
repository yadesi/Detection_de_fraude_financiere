#!/usr/bin/env python3
"""
Test script to verify frontend fix
"""

import requests
import time
import subprocess
import sys

def test_frontend():
    """Test if frontend is accessible"""
    
    print("Testing Frontend Fix...")
    print("=" * 40)
    
    # Test backend first
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running correctly")
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend is not accessible: {e}")
        return False
    
    # Test frontend
    try:
        response = requests.get("http://localhost:3001", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            print("✅ Frontend fix successful!")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend is not accessible: {e}")
        return False

def check_docker_status():
    """Check Docker container status"""
    
    print("\nChecking Docker Container Status...")
    print("=" * 40)
    
    try:
        result = subprocess.run(
            ["docker-compose", "ps"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'frontend' in line and 'Up' in line:
                    print("✅ Frontend container is running")
                    return True
                elif 'frontend' in line:
                    print(f"❌ Frontend container status: {line}")
                    return False
            
            print("❌ Frontend container not found")
            return False
        else:
            print(f"❌ Error checking Docker status: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False

def main():
    """Main test function"""
    
    print("FRONTEND FIX VERIFICATION")
    print("=" * 50)
    
    # Check Docker status
    docker_ok = check_docker_status()
    
    if docker_ok:
        # Wait a bit for frontend to fully start
        print("\nWaiting for frontend to fully start...")
        time.sleep(5)
        
        # Test frontend accessibility
        frontend_ok = test_frontend()
        
        if frontend_ok:
            print("\n🎉 SUCCESS: Frontend is now working!")
            print("\nYou can access:")
            print("  - Frontend: http://localhost:3001")
            print("  - API Docs: http://localhost:8000/docs")
            print("  - Dashboard: http://localhost:8501")
            print("  - Grafana: http://localhost:3000 (admin/admin)")
            return True
        else:
            print("\n❌ Frontend is still not accessible")
            print("\nTroubleshooting steps:")
            print("1. Check frontend logs: docker-compose logs frontend")
            print("2. Restart frontend: docker-compose restart frontend")
            print("3. Rebuild frontend: docker-compose build frontend")
            return False
    else:
        print("\n❌ Docker containers are not running properly")
        print("\nTry: docker-compose up -d")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
