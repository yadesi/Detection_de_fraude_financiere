#!/usr/bin/env python3
"""
Simple test to fix file upload issue
"""

import requests
import json

def test_simple_upload():
    """Test the simplest possible file upload"""
    
    print("🔍 Testing simple file upload...")
    
    # Create a test CSV file content
    csv_data = "transaction_id,type,amount\nTEST_001,TRANSFER,1000\nTEST_002,PAYMENT,500"
    
    # Test with multipart form data exactly like frontend would send
    try:
        # Method 1: Direct multipart
        files = {
            'file': ('transactions.csv', csv_data, 'text/csv')
        }
        
        response = requests.post(
            'http://localhost:8000/predict/file',
            files=files,
            timeout=30
        )
        
        print(f"✅ Upload Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("🎉 FILE UPLOAD SUCCESS!")
            print(f"📊 Filename: {result.get('filename')}")
            print(f"📊 File Size: {result.get('file_size')} bytes")
            print(f"📊 Transactions: {result.get('total_transactions')}")
            print(f"🎯 Predictions: {len(result.get('predictions', []))}")
        else:
            print(f"❌ Upload Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Test Error: {e}")

if __name__ == "__main__":
    test_simple_upload()
