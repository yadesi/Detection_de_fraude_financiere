#!/usr/bin/env python3
"""
Script to download and prepare the fraud detection datasets
"""

import os
import requests
import zipfile
import pandas as pd
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_directories():
    """Create necessary directories"""
    directories = [
        "data/raw",
        "data/processed",
        "data/samples"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def download_paysim():
    """Download PaySim dataset (simulated for demo)"""
    logger.info("Creating sample PaySim dataset...")
    
    # Generate sample data similar to PaySim
    np.random.seed(42)
    n_samples = 100000  # 100K sample for demo
    
    data = {
        'step': np.random.randint(1, 744, n_samples),  # 1 month of hours
        'type': np.random.choice(['CASH_IN', 'CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER'], n_samples),
        'amount': np.random.exponential(scale=1000, size=n_samples),
        'nameOrig': [f'C{np.random.randint(100000, 999999)}' for _ in range(n_samples)],
        'oldbalanceOrg': np.random.exponential(scale=5000, size=n_samples),
        'newbalanceOrig': np.random.exponential(scale=4500, size=n_samples),
        'nameDest': [f'M{np.random.randint(100000, 999999)}' for _ in range(n_samples)],
        'oldbalanceDest': np.random.exponential(scale=3000, size=n_samples),
        'newbalanceDest': np.random.exponential(scale=3500, size=n_samples),
        'isFraud': np.zeros(n_samples, dtype=int),
        'isFlaggedFraud': np.zeros(n_samples, dtype=int)
    }
    
    df = pd.DataFrame(data)
    
    # Add fraud patterns (similar to PaySim)
    fraud_mask = (
        (df['amount'] > 10000) & 
        (df['type'].isin(['TRANSFER', 'CASH_OUT'])) &
        (df['oldbalanceOrg'] - df['newbalanceOrig'] == df['amount']) &
        (df['newbalanceDest'] - df['oldbalanceDest'] == df['amount'])
    )
    
    # Add fraud to about 0.1% of transactions
    fraud_indices = np.random.choice(df.index, size=int(0.001 * n_samples), replace=False)
    df.loc[fraud_indices, 'isFraud'] = 1
    
    # Save to CSV
    df.to_csv('data/raw/paysim.csv', index=False)
    logger.info(f"Created PaySim sample dataset with {n_samples:,} transactions")
    logger.info(f"Fraud transactions: {df['isFraud'].sum():,} ({df['isFraud'].mean():.3%})")

def download_creditcard():
    """Download Credit Card Fraud dataset (simulated for demo)"""
    logger.info("Creating sample Credit Card dataset...")
    
    # Generate sample data similar to Credit Card Fraud dataset
    np.random.seed(123)
    n_samples = 50000  # 50K sample for demo
    
    # Generate V1-V28 features (PCA transformed features)
    v_features = {}
    for i in range(1, 29):
        v_features[f'V{i}'] = np.random.normal(0, 1, n_samples)
    
    data = {
        'Time': np.arange(n_samples),
        'Amount': np.random.exponential(scale=100, size=n_samples),
        **v_features,
        'Class': np.zeros(n_samples, dtype=int)
    }
    
    df = pd.DataFrame(data)
    
    # Add fraud patterns (about 0.17% like original dataset)
    fraud_indices = np.random.choice(df.index, size=int(0.0017 * n_samples), replace=False)
    df.loc[fraud_indices, 'Class'] = 1
    
    # Adjust fraud transactions to have different patterns
    for col in ['Amount', 'V1', 'V2', 'V3', 'V4']:
        df.loc[fraud_indices, col] *= np.random.uniform(1.5, 3.0, len(fraud_indices))
    
    # Save to CSV
    df.to_csv('data/raw/creditcard.csv', index=False)
    logger.info(f"Created Credit Card sample dataset with {n_samples:,} transactions")
    logger.info(f"Fraud transactions: {df['Class'].sum():,} ({df['Class'].mean():.3%})")

def create_sample_files():
    """Create smaller sample files for testing"""
    logger.info("Creating sample files for testing...")
    
    # Read full datasets
    paysim_df = pd.read_csv('data/raw/paysim.csv')
    creditcard_df = pd.read_csv('data/raw/creditcard.csv')
    
    # Create samples
    paysim_sample = paysim_df.sample(n=10000, random_state=42)
    creditcard_sample = creditcard_df.sample(n=5000, random_state=42)
    
    # Save samples
    paysim_sample.to_csv('data/samples/paysim_sample.csv', index=False)
    creditcard_sample.to_csv('data/samples/creditcard_sample.csv', index=False)
    
    logger.info("Created sample files in data/samples/")

def main():
    """Main function to download and prepare datasets"""
    logger.info("Starting dataset preparation...")
    
    try:
        # Create directories
        create_directories()
        
        # Download/create datasets
        download_paysim()
        download_creditcard()
        
        # Create sample files
        create_sample_files()
        
        logger.info("Dataset preparation completed successfully!")
        logger.info("Files created:")
        logger.info("  - data/raw/paysim.csv (100K transactions)")
        logger.info("  - data/raw/creditcard.csv (50K transactions)")
        logger.info("  - data/samples/paysim_sample.csv (10K transactions)")
        logger.info("  - data/samples/creditcard_sample.csv (5K transactions)")
        
    except Exception as e:
        logger.error(f"Error in dataset preparation: {str(e)}")
        raise

if __name__ == "__main__":
    import numpy as np
    main()
