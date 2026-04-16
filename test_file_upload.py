#!/usr/bin/env python3
"""
Test script to verify file upload functionality
"""

import requests
import json
import tempfile
import os

def test_file_upload():
    """Test file upload endpoint with a real file"""
    
    # Create a temporary CSV file
    csv_content = """transaction_id,type,amount,oldbalanceOrg,newbalanceOrig,nameOrig,oldbalanceDest,newbalanceDest,nameDest
TEST_001,TRANSFER,5000,10000,5000,C123456789,2000,7000,M987654321
TEST_002,PAYMENT,100,5000,4900,C123456789,1000,1100,M987654321
TEST_003,CASH_OUT,2000,8000,6000,C987654321,5000,7000,M123456789
TEST_004,TRANSFER,15000,25000,10000,C555555555,10000,25000,D999888888
"""
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_file_path = f.name
    
    try:
        # Test file upload with real file
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('test_transactions.csv', f, 'text/csv')}
            response = requests.post('http://localhost:8000/predict/file', files=files, timeout=30)
        
        print(f'✅ File Upload Status: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            print('🎯 File Upload SUCCESS!')
            print('📊 Results:')
            print(f'  - Filename: {result.get("filename")}')
            print(f'  - File Size: {result.get("file_size")} bytes')
            print(f'  - Transactions: {result.get("total_transactions")}')
            print(f'  - Predictions: {len(result.get("predictions", []))}')
            print('🚀 File upload is WORKING!')
        else:
            print('❌ File Upload Error:')
            print(f'  Status: {response.status_code}')
            print(f'  Response: {response.text}')
            
    except Exception as e:
        print(f'❌ Test Error: {e}')
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

if __name__ == "__main__":
    test_file_upload()
