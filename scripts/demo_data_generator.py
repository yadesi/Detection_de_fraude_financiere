#!/usr/bin/env python3
"""
Demo Data Generator for Fraud Detection System
Creates realistic transaction data for demonstration purposes
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import csv
from faker import Faker
import uuid

class FraudDemoDataGenerator:
    """Generate realistic transaction data for fraud detection demo"""
    
    def __init__(self):
        self.fake = Faker()
        self.fraud_types = ['TRANSFER', 'CASH-OUT', 'DEBIT', 'CASH-IN', 'PAYMENT']
        self.customer_prefixes = ['C', 'CM']
        self.merchant_prefixes = ['M']
        
    def generate_customer_id(self) -> str:
        """Generate realistic customer ID"""
        prefix = random.choice(self.customer_prefixes)
        return f"{prefix}{random.randint(100000000, 999999999)}"
    
    def generate_merchant_id(self) -> str:
        """Generate realistic merchant ID"""
        return f"{random.choice(self.merchant_prefixes)}{random.randint(100000000, 999999999)}"
    
    def generate_transaction(self, is_fraud: bool = False, fraud_type: str = None) -> Dict[str, Any]:
        """Generate a single transaction with realistic patterns"""
        
        # Basic transaction data
        transaction_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
        transaction_type = random.choice(self.fraud_types)
        amount = round(random.uniform(50, 50000), 2)
        
        # Generate customer and merchant
        name_orig = self.generate_customer_id()
        name_dest = self.generate_merchant_id()
        
        # Generate balances
        old_balance_org = round(random.uniform(1000, 100000), 2)
        
        # Calculate new origin balance
        if transaction_type in ['TRANSFER', 'CASH-OUT', 'DEBIT']:
            new_balance_orig = round(old_balance_org - amount, 2)
        else:  # CASH-IN, PAYMENT
            new_balance_orig = round(old_balance_org + amount, 2)
        
        # Generate destination balances
        old_balance_dest = round(random.uniform(500, 80000), 2)
        
        if transaction_type in ['TRANSFER', 'CASH-IN']:
            new_balance_dest = round(old_balance_dest + amount, 2)
        else:  # CASH-OUT, DEBIT, PAYMENT
            new_balance_dest = old_balance_dest
        
        # Add fraud patterns if specified
        if is_fraud:
            if fraud_type == "high_amount":
                amount = round(random.uniform(50000, 200000), 2)
                # Adjust balances for high amount
                old_balance_org = amount * random.uniform(1.1, 2.0)
                new_balance_orig = round(old_balance_org - amount, 2)
                
            elif fraud_type == "balance_mismatch":
                # Create suspicious balance changes
                new_balance_orig = round(old_balance_org - amount * random.uniform(0.8, 1.2), 2)
                new_balance_dest = round(old_balance_dest + amount * random.uniform(0.5, 1.5), 2)
                
            elif fraud_type == "rapid_sequence":
                # Generate multiple transactions in short time
                pass  # Will be handled at batch level
                
            elif fraud_type == "suspicious_pattern":
                # Unusual transaction patterns
                if random.random() < 0.3:
                    # Round amounts (suspicious)
                    amount = round(amount / 100) * 100
                if random.random() < 0.2:
                    # Same destination multiple times
                    name_dest = "M999999999"  # Known suspicious merchant
        
        return {
            "transaction_id": transaction_id,
            "type": transaction_type,
            "amount": amount,
            "oldbalanceOrg": round(old_balance_org, 2),
            "newbalanceOrig": round(new_balance_orig, 2),
            "oldbalanceDest": round(old_balance_dest, 2),
            "newbalanceDest": round(new_balance_dest, 2),
            "nameOrig": name_orig,
            "nameDest": name_dest,
            "timestamp": datetime.now().isoformat(),
            "is_fraud": is_fraud,
            "fraud_type": fraud_type if is_fraud else None
        }
    
    def generate_batch(self, size: int = 100, fraud_rate: float = 0.05) -> List[Dict[str, Any]]:
        """Generate a batch of transactions with specified fraud rate"""
        
        transactions = []
        fraud_count = int(size * fraud_rate)
        legitimate_count = size - fraud_count
        
        # Generate legitimate transactions
        for _ in range(legitimate_count):
            transactions.append(self.generate_transaction(is_fraud=False))
        
        # Generate fraudulent transactions with different patterns
        fraud_types = ["high_amount", "balance_mismatch", "suspicious_pattern"]
        for i in range(fraud_count):
            fraud_type = random.choice(fraud_types)
            transactions.append(self.generate_transaction(is_fraud=True, fraud_type=fraud_type))
        
        # Shuffle the transactions
        random.shuffle(transactions)
        
        return transactions
    
    def generate_streaming_data(self, duration_minutes: int = 10, transactions_per_minute: int = 50) -> List[Dict[str, Any]]:
        """Generate streaming transaction data over time"""
        
        all_transactions = []
        start_time = datetime.now()
        
        for minute in range(duration_minutes):
            # Vary transaction rate throughout the day
            hour_factor = 1.0
            current_hour = start_time.hour
            if 9 <= current_hour <= 17:  # Business hours
                hour_factor = 1.5
            elif 22 <= current_hour or current_hour <= 6:  # Night hours
                hour_factor = 0.5
            
            # Calculate transactions for this minute
            minute_transactions = int(transactions_per_minute * hour_factor)
            
            # Generate transactions for this minute
            minute_batch = self.generate_batch(minute_transactions, fraud_rate=0.03)
            
            # Add timestamp for each transaction
            minute_start = start_time + timedelta(minutes=minute)
            for i, tx in enumerate(minute_batch):
                tx['timestamp'] = (minute_start + timedelta(seconds=i * (60 / minute_transactions))).isoformat()
            
            all_transactions.extend(minute_batch)
        
        return all_transactions
    
    def save_to_csv(self, transactions: List[Dict[str, Any]], filename: str):
        """Save transactions to CSV file"""
        
        # Remove internal fields
        clean_transactions = []
        for tx in transactions:
            clean_tx = tx.copy()
            clean_tx.pop('is_fraud', None)
            clean_tx.pop('fraud_type', None)
            clean_transactions.append(clean_tx)
        
        df = pd.DataFrame(clean_transactions)
        df.to_csv(filename, index=False)
        print(f"Saved {len(clean_transactions)} transactions to {filename}")
    
    def save_to_json(self, transactions: List[Dict[str, Any]], filename: str):
        """Save transactions to JSON file"""
        
        # Remove internal fields
        clean_transactions = []
        for tx in transactions:
            clean_tx = tx.copy()
            clean_tx.pop('is_fraud', None)
            clean_tx.pop('fraud_type', None)
            clean_transactions.append(clean_tx)
        
        with open(filename, 'w') as f:
            json.dump(clean_transactions, f, indent=2)
        print(f"Saved {len(clean_transactions)} transactions to {filename}")
    
    def create_demo_datasets(self):
        """Create multiple demo datasets for different scenarios"""
        
        print("Creating demo datasets...")
        
        # Scenario 1: Small batch for quick testing
        small_batch = self.generate_batch(size=50, fraud_rate=0.1)
        self.save_to_csv(small_batch, 'demo_small_batch.csv')
        self.save_to_json(small_batch, 'demo_small_batch.json')
        
        # Scenario 2: Medium batch with realistic fraud rate
        medium_batch = self.generate_batch(size=500, fraud_rate=0.05)
        self.save_to_csv(medium_batch, 'demo_medium_batch.csv')
        self.save_to_json(medium_batch, 'demo_medium_batch.json')
        
        # Scenario 3: Large batch for performance testing
        large_batch = self.generate_batch(size=2000, fraud_rate=0.03)
        self.save_to_csv(large_batch, 'demo_large_batch.csv')
        self.save_to_json(large_batch, 'demo_large_batch.json')
        
        # Scenario 4: Streaming data simulation
        streaming_data = self.generate_streaming_data(duration_minutes=30, transactions_per_minute=100)
        self.save_to_csv(streaming_data, 'demo_streaming_data.csv')
        self.save_to_json(streaming_data, 'demo_streaming_data.json')
        
        # Scenario 5: High fraud concentration for alert testing
        high_fraud_batch = self.generate_batch(size=100, fraud_rate=0.3)
        self.save_to_csv(high_fraud_batch, 'demo_high_fraud.csv')
        self.save_to_json(high_fraud_batch, 'demo_high_fraud.json')
        
        # Create summary report
        self.create_summary_report([
            ('Small Batch', small_batch),
            ('Medium Batch', medium_batch),
            ('Large Batch', large_batch),
            ('Streaming Data', streaming_data),
            ('High Fraud', high_fraud_batch)
        ])
        
        print("Demo datasets created successfully!")
    
    def create_summary_report(self, datasets: List[tuple]):
        """Create a summary report of all generated datasets"""
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "datasets": []
        }
        
        for name, transactions in datasets:
            fraud_count = sum(1 for tx in transactions if tx.get('is_fraud', False))
            total_amount = sum(tx['amount'] for tx in transactions)
            fraud_amount = sum(tx['amount'] for tx in transactions if tx.get('is_fraud', False))
            
            # Transaction type distribution
            type_counts = {}
            for tx in transactions:
                tx_type = tx['type']
                type_counts[tx_type] = type_counts.get(tx_type, 0) + 1
            
            report["datasets"].append({
                "name": name,
                "total_transactions": len(transactions),
                "fraud_transactions": fraud_count,
                "fraud_rate": round(fraud_count / len(transactions) * 100, 2),
                "total_amount": round(total_amount, 2),
                "fraud_amount": round(fraud_amount, 2),
                "average_amount": round(total_amount / len(transactions), 2),
                "transaction_types": type_counts
            })
        
        with open('demo_summary_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("Summary report created: demo_summary_report.json")

def main():
    """Main function to run demo data generation"""
    
    print("Fraud Detection System - Demo Data Generator")
    print("=" * 50)
    
    generator = FraudDemoDataGenerator()
    generator.create_demo_datasets()
    
    print("\nDemo files created:")
    print("- demo_small_batch.csv/json (50 transactions, 10% fraud)")
    print("- demo_medium_batch.csv/json (500 transactions, 5% fraud)")
    print("- demo_large_batch.csv/json (2000 transactions, 3% fraud)")
    print("- demo_streaming_data.csv/json (30 min streaming, 3% fraud)")
    print("- demo_high_fraud.csv/json (100 transactions, 30% fraud)")
    print("- demo_summary_report.json (summary statistics)")

if __name__ == "__main__":
    main()
