import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import redis
import numpy as np
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import mlflow
import mlflow.pyfunc
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

class PredictionService:
    """Real-time prediction service for fraud detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.kafka_producer = None
        self.spark = None
        self.model = None
        self.model_version = None
        self.is_streaming = False
        self.prediction_history = []
        
    async def initialize(self):
        """Initialize prediction service components"""
        try:
            # Initialize Redis
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            # Initialize Kafka producer
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            
            # Initialize Spark session
            self.spark = SparkSession.builder \
                .appName("FraudPrediction") \
                .config("spark.sql.streaming.checkpointLocation", "/tmp/prediction_checkpoint") \
                .getOrCreate()
            
            # Load latest model from MLflow
            await self.load_latest_model()
            
            self.logger.info("Prediction service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize prediction service: {str(e)}")
            raise
    
    async def load_latest_model(self):
        """Load the latest model from MLflow"""
        try:
            # Get latest model version from MLflow
            model_uri = "models:/fraud_detection_model/latest"
            self.model = mlflow.pyfunc.load_model(model_uri)
            
            # Get model version info
            client = mlflow.tracking.MlflowClient()
            model_version_info = client.get_latest_versions("fraud_detection_model", stages=["Production"])
            if model_version_info:
                self.model_version = model_version_info[0].version
            
            self.logger.info(f"Loaded model version {self.model_version}")
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
            # Fallback to dummy model for development
            self.model = self._create_dummy_model()
    
    def _create_dummy_model(self):
        """Create a dummy model for development/testing"""
        class DummyModel:
            def predict(self, features):
                # Simple rule-based prediction for development
                if isinstance(features, dict):
                    amount = features.get('amount', 0)
                    amount_log = features.get('amount_log', 0)
                    error_orig = features.get('error_orig', 0)
                    
                    # Simple heuristic
                    fraud_score = 0.1  # Base probability
                    if amount > 10000:
                        fraud_score += 0.3
                    if error_orig == 1:
                        fraud_score += 0.4
                    if amount_log > 10:
                        fraud_score += 0.2
                    
                    return np.array([fraud_score])
                return np.array([0.1])
        
        return DummyModel()
    
    async def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make prediction for a single transaction
        """
        try:
            start_time = datetime.now()
            
            # Prepare features for model
            model_features = self._prepare_features(features)
            
            # Make prediction
            if hasattr(self.model, 'predict'):
                prediction_proba = self.model.predict(model_features)
            else:
                prediction_proba = np.array([0.1])  # Default
            
            # Convert to fraud prediction
            fraud_probability = float(prediction_proba[0]) if len(prediction_proba) > 0 else 0.1
            is_fraud = fraud_probability > 0.5  # Threshold can be adjusted
            
            # Create result
            result = {
                "is_fraud": bool(is_fraud),
                "fraud_probability": fraud_probability,
                "confidence": max(fraud_probability, 1 - fraud_probability),
                "model_version": self.model_version,
                "prediction_timestamp": datetime.now().isoformat()
            }
            
            # Store prediction in Redis for real-time monitoring
            await self._store_prediction(features.get('transaction_id'), result)
            
            # Send to Kafka for streaming analytics
            await self._send_to_kafka(features, result)
            
            # Add to history
            self.prediction_history.append({
                'transaction_id': features.get('transaction_id'),
                'prediction': result,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep history size manageable
            if len(self.prediction_history) > 1000:
                self.prediction_history = self.prediction_history[-1000:]
            
            # Log prediction metrics
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.info(f"Prediction completed in {latency:.2f}ms")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Prediction failed: {str(e)}")
            # Return default prediction on error
            return {
                "is_fraud": False,
                "fraud_probability": 0.1,
                "confidence": 0.9,
                "model_version": self.model_version,
                "prediction_timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _prepare_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Prepare features for model input"""
        # Define feature order (must match training)
        feature_order = [
            'amount', 'amount_log', 'amount_sqrt', 'transaction_type_encoded',
            'balance_change_orig', 'balance_change_dest', 'balance_ratio_orig',
            'balance_ratio_dest', 'error_orig', 'error_dest', 'is_merchant',
            'hour_of_day', 'day_of_week', 'is_weekend', 'is_night',
            'amount_to_balance_ratio', 'is_large_amount', 'is_small_amount',
            'amount_category', 'transaction_count_24h', 'avg_amount_24h',
            'max_amount_24h', 'last_transaction_hours', 'is_new_account'
        ]
        
        # Create feature vector
        feature_vector = []
        for feature in feature_order:
            value = features.get(feature, 0)
            if isinstance(value, str) and value.lower() in ['true', 'false']:
                value = 1 if value.lower() == 'true' else 0
            feature_vector.append(float(value) if value is not None else 0.0)
        
        return np.array([feature_vector])
    
    async def _store_prediction(self, transaction_id: str, prediction: Dict[str, Any]):
        """Store prediction in Redis for real-time access"""
        try:
            if transaction_id:
                key = f"prediction:{transaction_id}"
                self.redis_client.setex(key, 3600, json.dumps(prediction))  # 1 hour TTL
        except Exception as e:
            self.logger.error(f"Failed to store prediction in Redis: {str(e)}")
    
    async def _send_to_kafka(self, features: Dict[str, Any], prediction: Dict[str, Any]):
        """Send prediction to Kafka for streaming analytics"""
        try:
            message = {
                "transaction_id": features.get('transaction_id'),
                "timestamp": datetime.now().isoformat(),
                "features": features,
                "prediction": prediction
            }
            
            # Send to predictions topic
            future = self.kafka_producer.send('fraud_predictions', value=message)
            
            # Block for a short time to ensure message is sent
            record_metadata = future.get(timeout=10)
            
            self.logger.debug(f"Message sent to Kafka: {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset}")
            
        except Exception as e:
            self.logger.error(f"Failed to send message to Kafka: {str(e)}")
    
    async def start_streaming_predictions(self):
        """Start streaming predictions from Kafka"""
        try:
            # Define schema for incoming transactions
            schema = StructType([
                StructField("transaction_id", StringType(), True),
                StructField("timestamp", TimestampType(), True),
                StructField("features", StringType(), True)  # JSON string
            ])
            
            # Create streaming DataFrame
            transactions_stream = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "localhost:9092") \
                .option("subscribe", "transactions") \
                .option("startingOffsets", "latest") \
                .load() \
                .select(from_json(col("value").cast("string"), schema).alias("data")) \
                .select("data.*")
            
            # Process each transaction
            def process_batch(batch_df, batch_id):
                """Process each micro-batch of transactions"""
                try:
                    # Collect transactions
                    transactions = batch_df.collect()
                    
                    # Process each transaction
                    for row in transactions:
                        features = json.loads(row.features)
                        # Use sync prediction in batch context
                        prediction = self._predict_sync(features)
                        
                        # Send prediction to output topic (sync version)
                        self._send_to_kafka_sync(features, prediction)
                        
                except Exception as e:
                    self.logger.error(f"Error processing batch {batch_id}: {str(e)}")
            
            # Start the streaming query
            query = transactions_stream \
                .writeStream \
                .foreachBatch(process_batch) \
                .option("checkpointLocation", "/tmp/streaming_checkpoint") \
                .start()
            
            self.is_streaming = True
            self.logger.info("Streaming predictions started")
            
            return query
            
        except Exception as e:
            self.logger.error(f"Failed to start streaming predictions: {str(e)}")
            raise
    
    async def get_prediction_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent prediction history"""
        return self.prediction_history[-limit:]
    
    async def get_kafka_status(self) -> Dict[str, Any]:
        """Get Kafka connection status"""
        try:
            if self.kafka_producer:
                # Test connection
                future = self.kafka_producer.send('test_topic', value={'test': 'message'})
                record_metadata = future.get(timeout=5)
                return {"status": "connected", "topic": record_metadata.topic}
            else:
                return {"status": "disconnected", "error": "Producer not initialized"}
        except Exception as e:
            return {"status": "disconnected", "error": str(e)}
    
    async def get_redis_status(self) -> Dict[str, Any]:
        """Get Redis connection status"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return {"status": "connected"}
            else:
                return {"status": "disconnected", "error": "Redis client not initialized"}
        except Exception as e:
            return {"status": "disconnected", "error": str(e)}
    
    def _predict_sync(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous version of predict for batch processing"""
        try:
            start_time = datetime.now()
            
            # Prepare features for model
            model_features = self._prepare_features(features)
            
            # Make prediction
            if hasattr(self.model, 'predict'):
                prediction_proba = self.model.predict(model_features)
            else:
                prediction_proba = np.array([0.1])  # Default
            
            # Convert to fraud prediction
            fraud_probability = float(prediction_proba[0]) if len(prediction_proba) > 0 else 0.1
            is_fraud = fraud_probability > 0.5  # Threshold can be adjusted
            
            # Create result
            result = {
                "is_fraud": bool(is_fraud),
                "fraud_probability": fraud_probability,
                "confidence": max(fraud_probability, 1 - fraud_probability),
                "model_version": self.model_version,
                "prediction_timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Sync prediction failed: {str(e)}")
            # Return default prediction on error
            return {
                "is_fraud": False,
                "fraud_probability": 0.1,
                "confidence": 0.9,
                "model_version": self.model_version,
                "prediction_timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _send_to_kafka_sync(self, features: Dict[str, Any], prediction: Dict[str, Any]):
        """Synchronous version of send_to_kafka for batch processing"""
        try:
            message = {
                "transaction_id": features.get('transaction_id'),
                "timestamp": datetime.now().isoformat(),
                "features": features,
                "prediction": prediction
            }
            
            # Send to predictions topic
            future = self.kafka_producer.send('fraud_predictions', value=message)
            
            # Block for a short time to ensure message is sent
            record_metadata = future.get(timeout=10)
            
            self.logger.debug(f"Message sent to Kafka: {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset}")
            
        except Exception as e:
            self.logger.error(f"Failed to send message to Kafka: {str(e)}")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.kafka_producer:
                self.kafka_producer.close()
            if self.redis_client:
                self.redis_client.close()
            if self.spark:
                self.spark.stop()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
