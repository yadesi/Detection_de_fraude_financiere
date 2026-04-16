#!/usr/bin/env python3
"""
Debug script to understand file upload issue
"""

import requests
import tempfile
import os

def debug_upload_issue():
    """Debug the file upload endpoint step by step"""
    
    print("🔍 DEBUG: Testing file upload endpoint...")
    
    # Test 1: Check if endpoint exists
    try:
        response = requests.get('http://localhost:8000/docs')
        print(f"✅ API Docs accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ API not accessible: {e}")
        return
    
    # Test 2: Try empty file
    try:
        response = requests.post('http://localhost:8000/predict/file', files={})
        print(f"📊 Empty file test: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Empty file test error: {e}")
    
    # Test 3: Try with minimal file
    try:
        minimal_csv = "id,type,amount\n1,TRANSFER,1000"
        files = {'file': ('test.csv', minimal_csv, 'text/csv')}
        response = requests.post('http://localhost:8000/predict/file', files=files)
        print(f"📊 Minimal file test: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Minimal file test error: {e}")
    
    # Test 4: Check endpoint with curl-like simulation
    try:
        import subprocess
        result = subprocess.run([
            'curl', '-X', 'POST', 
            '-F', 'file=@test.csv',
            'http://localhost:8000/predict/file'
        ], capture_output=True, text=True, input="id,type,amount\n1,TRANSFER,1000")
        
        print(f"📊 Curl test result: {result.returncode}")
        print(f"📊 Curl test output: {result.stdout}")
        print(f"📊 Curl test error: {result.stderr}")
    except Exception as e:
        print(f"❌ Curl test error: {e}")

if __name__ == "__main__":
    debug_upload_issue()
