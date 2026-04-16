import pandas as pd
import numpy as np
from typing import Dict, Any, List
import asyncio
from datetime import datetime, timedelta
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, count, sum as spark_sum, avg, max, min
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
import redis
import logging

class DataProcessor:
    """Data processing and feature engineering for fraud detection"""
    
    def __init__(self):
        self.spark = None
        self.redis_client = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize Spark session and Redis connection"""
        # Initialize Spark session
        self.spark = SparkSession.builder \
            .appName("FraudDetection") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
            .getOrCreate()
        
        # Initialize Redis
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
    async def process_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single transaction and extract features
        """
        try:
            # Convert to DataFrame for processing
            df = pd.DataFrame([transaction])
            
            # Feature engineering
            features = await self._extract_features(df, transaction)
            
            # Add time-based features
            features.update(self._extract_time_features(transaction))
            
            # Add amount-based features
            features.update(self._extract_amount_features(transaction))
            
            # Add behavioral features from cache
            features.update(await self._extract_behavioral_features(transaction))
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error processing transaction: {str(e)}")
            raise
    
    async def _extract_features(self, df: pd.DataFrame, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic features from transaction"""
        features = {}
        
        # Transaction type encoding
        transaction_type = transaction.get('type', 'UNKNOWN')
        type_mapping = {
            'CASH-IN': 1, 'CASH-OUT': 2, 'DEBIT': 3, 
            'PAYMENT': 4, 'TRANSFER': 5, 'UNKNOWN': 0
        }
        features['transaction_type_encoded'] = type_mapping.get(transaction_type, 0)
        
        # Amount features
        amount = float(transaction.get('amount', 0))
        features['amount_log'] = np.log1p(amount)
        features['amount_sqrt'] = np.sqrt(amount)
        
        # Balance features
        old_balance_orig = float(transaction.get('oldbalanceOrg', 0))
        new_balance_orig = float(transaction.get('newbalanceOrig', 0))
        old_balance_dest = float(transaction.get('oldbalanceDest', 0))
        new_balance_dest = float(transaction.get('newbalanceDest', 0))
        
        features['balance_change_orig'] = new_balance_orig - old_balance_orig
        features['balance_change_dest'] = new_balance_dest - old_balance_dest
        features['balance_ratio_orig'] = new_balance_orig / (old_balance_orig + 1)
        features['balance_ratio_dest'] = new_balance_dest / (old_balance_dest + 1)
        
        # Error indicators (potential fraud signals)
        features['error_orig'] = 1 if (old_balance_orig - new_balance_orig != amount) and amount > 0 else 0
        features['error_dest'] = 1 if (new_balance_dest - old_balance_dest != amount) and amount > 0 else 0
        
        # Merchant/customer indicator
        name_dest = transaction.get('nameDest', '')
        features['is_merchant'] = 1 if name_dest.startswith('M') else 0
        
        return features
    
    def _extract_time_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Extract time-based features"""
        features = {}
        
        # Parse timestamp
        timestamp_str = transaction.get('timestamp', '')
        if timestamp_str:
            try:
                timestamp = pd.to_datetime(timestamp_str)
                features['hour_of_day'] = timestamp.hour
                features['day_of_week'] = timestamp.dayofweek
                features['is_weekend'] = 1 if timestamp.dayofweek >= 5 else 0
                features['is_night'] = 1 if timestamp.hour < 6 or timestamp.hour > 22 else 0
            except:
                features['hour_of_day'] = 12  # Default
                features['day_of_week'] = 3   # Default
                features['is_weekend'] = 0
                features['is_night'] = 0
        else:
            # Default values if no timestamp
            features['hour_of_day'] = 12
            features['day_of_week'] = 3
            features['is_weekend'] = 0
            features['is_night'] = 0
            
        return features
    
    def _extract_amount_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Extract amount-based features"""
        features = {}
        
        amount = float(transaction.get('amount', 0))
        old_balance_orig = float(transaction.get('oldbalanceOrg', 0))
        
        # Amount ratios
        features['amount_to_balance_ratio'] = amount / (old_balance_orig + 1)
        features['is_large_amount'] = 1 if amount > 10000 else 0  # Threshold for large transactions
        features['is_small_amount'] = 1 if amount < 100 else 1    # Threshold for small transactions
        
        # Amount categories
        if amount < 100:
            features['amount_category'] = 0  # Very small
        elif amount < 1000:
            features['amount_category'] = 1  # Small
        elif amount < 10000:
            features['amount_category'] = 2  # Medium
        elif amount < 100000:
            features['amount_category'] = 3  # Large
        else:
            features['amount_category'] = 4  # Very large
            
        return features
    
    async def _extract_behavioral_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Extract behavioral features using cached historical data"""
        features = {}
        
        try:
            # Get account history from Redis
            account_id = transaction.get('nameOrig', '')
            if account_id:
                account_data = self.redis_client.hgetall(f"account:{account_id}")
                
                if account_data:
                    # Historical features
                    features['transaction_count_24h'] = int(account_data.get('count_24h', 0))
                    features['avg_amount_24h'] = float(account_data.get('avg_amount_24h', 0))
                    features['max_amount_24h'] = float(account_data.get('max_amount_24h', 0))
                    features['last_transaction_hours'] = self._hours_since_last_transaction(account_data.get('last_transaction'))
                    features['is_new_account'] = 1 if int(account_data.get('total_transactions', 0)) < 5 else 0
                else:
                    # Default values for new accounts
                    features['transaction_count_24h'] = 0
                    features['avg_amount_24h'] = 0
                    features['max_amount_24h'] = 0
                    features['last_transaction_hours'] = 999  # Large value indicating no history
                    features['is_new_account'] = 1
            
            # Update account data in Redis
            await self._update_account_history(account_id, transaction)
            
        except Exception as e:
            self.logger.error(f"Error extracting behavioral features: {str(e)}")
            # Default values on error
            features.update({
                'transaction_count_24h': 0,
                'avg_amount_24h': 0,
                'max_amount_24h': 0,
                'last_transaction_hours': 999,
                'is_new_account': 1
            })
            
        return features
    
    def _hours_since_last_transaction(self, last_transaction_str: str) -> int:
        """Calculate hours since last transaction"""
        try:
            if last_transaction_str:
                last_time = pd.to_datetime(last_transaction_str)
                hours_ago = (datetime.now() - last_time).total_seconds() / 3600
                return int(hours_ago)
            return 999
        except:
            return 999
    
    async def _update_account_history(self, account_id: str, transaction: Dict[str, Any]):
        """Update account history in Redis cache"""
        try:
            if not account_id:
                return
                
            amount = float(transaction.get('amount', 0))
            current_time = datetime.now().isoformat()
            
            # Get current data
            account_data = self.redis_client.hgetall(f"account:{account_id}")
            
            # Update counters
            total_transactions = int(account_data.get('total_transactions', 0)) + 1
            count_24h = int(account_data.get('count_24h', 0)) + 1
            
            # Update amount statistics
            total_amount = float(account_data.get('total_amount', 0)) + amount
            avg_amount_24h = total_amount / count_24h if count_24h > 0 else amount
            max_amount_24h = max(float(account_data.get('max_amount_24h', 0)), amount)
            
            # Update account data
            updated_data = {
                'total_transactions': total_transactions,
                'total_amount': total_amount,
                'count_24h': count_24h,
                'avg_amount_24h': avg_amount_24h,
                'max_amount_24h': max_amount_24h,
                'last_transaction': current_time,
                'last_update': current_time
            }
            
            # Save to Redis with expiration (24 hours for behavioral data)
            self.redis_client.hset(f"account:{account_id}", mapping=updated_data)
            self.redis_client.expire(f"account:{account_id}", 86400)  # 24 hours
            
        except Exception as e:
            self.logger.error(f"Error updating account history: {str(e)}")
    
    async def process_batch(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple transactions in batch"""
        processed_data = []
        
        for transaction in transactions:
            try:
                processed = await self.process_transaction(transaction)
                processed_data.append(processed)
            except Exception as e:
                self.logger.error(f"Error processing transaction {transaction.get('transaction_id')}: {str(e)}")
                # Add default processed data for failed transactions
                processed_data.append({})
                
        return processed_data
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.spark:
            self.spark.stop()
        if self.redis_client:
            self.redis_client.close()
