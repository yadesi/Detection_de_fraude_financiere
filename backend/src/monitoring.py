import asyncio
import logging
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
import redis
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import json

class MetricsCollector:
    """Metrics collection and monitoring for fraud detection system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.metrics_collection_active = False
        
        # Prometheus metrics
        self.prediction_counter = Counter('fraud_predictions_total', 'Total predictions', ['result'])
        self.prediction_latency = Histogram('fraud_prediction_latency_seconds', 'Prediction latency')
        self.batch_prediction_latency = Histogram('fraud_batch_prediction_latency_seconds', 'Batch prediction latency')
        self.fraud_detection_counter = Counter('fraud_detections_total', 'Total fraud detections')
        self.false_positive_counter = Counter('false_positives_total', 'Total false positives')
        self.model_accuracy = Gauge('model_accuracy', 'Current model accuracy')
        self.system_health = Gauge('system_health', 'System health status')
        self.kafka_lag = Gauge('kafka_consumer_lag', 'Kafka consumer lag')
        self.redis_connections = Gauge('redis_connections', 'Active Redis connections')
        
        # Internal metrics storage
        self.prediction_history = deque(maxlen=10000)
        self.performance_metrics = defaultdict(list)
        self.alert_thresholds = {
            'prediction_latency': 0.1,  # 100ms
            'error_rate': 0.05,         # 5%
            'fraud_rate': 0.02,         # 2%
            'system_memory': 0.8        # 80%
        }
        
    async def start_collection(self):
        """Start metrics collection"""
        try:
            # Initialize Redis for metrics storage
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            # Start Prometheus HTTP server
            start_http_server(8001)  # Metrics endpoint
            
            self.metrics_collection_active = True
            
            # Start background metrics collection
            asyncio.create_task(self._collect_system_metrics())
            
            self.logger.info("Metrics collection started")
            
        except Exception as e:
            self.logger.error(f"Failed to start metrics collection: {str(e)}")
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.metrics_collection_active = False
    
    def record_prediction_latency(self, latency_ms: float):
        """Record prediction latency"""
        latency_seconds = latency_ms / 1000.0
        self.prediction_latency.observe(latency_seconds)
        self.performance_metrics['prediction_latency'].append(latency_seconds)
        
        # Keep only recent metrics
        if len(self.performance_metrics['prediction_latency']) > 1000:
            self.performance_metrics['prediction_latency'] = self.performance_metrics['prediction_latency'][-1000:]
    
    def record_batch_prediction_latency(self, latency_ms: float, batch_size: int):
        """Record batch prediction latency"""
        latency_seconds = latency_ms / 1000.0
        self.batch_prediction_latency.observe(latency_seconds)
        self.performance_metrics['batch_prediction_latency'].append(latency_seconds)
        
        # Keep only recent metrics
        if len(self.performance_metrics['batch_prediction_latency']) > 1000:
            self.performance_metrics['batch_prediction_latency'] = self.performance_metrics['batch_prediction_latency'][-1000:]
    
    def record_prediction(self, is_fraud: bool):
        """Record prediction result"""
        result = 'fraud' if is_fraud else 'legitimate'
        self.prediction_counter.labels(result=result).inc()
        
        if is_fraud:
            self.fraud_detection_counter.inc()
        
        # Store in history
        self.prediction_history.append({
            'timestamp': datetime.now().isoformat(),
            'is_fraud': is_fraud,
            'result': result
        })
    
    def record_false_positive(self):
        """Record false positive"""
        self.false_positive_counter.inc()
    
    def update_model_accuracy(self, accuracy: float):
        """Update model accuracy metric"""
        self.model_accuracy.set(accuracy)
    
    def update_system_health(self, health_score: float):
        """Update system health score (0-1)"""
        self.system_health.set(health_score)
    
    def update_kafka_lag(self, lag: int):
        """Update Kafka consumer lag"""
        self.kafka_lag.set(lag)
    
    def update_redis_connections(self, connections: int):
        """Update Redis connections count"""
        self.redis_connections.set(connections)
    
    async def _collect_system_metrics(self):
        """Background task to collect system metrics"""
        while self.metrics_collection_active:
            try:
                # Collect system metrics
                metrics = await self._get_system_metrics()
                
                # Store in Redis
                await self._store_metrics(metrics)
                
                # Check for alerts
                await self._check_alerts(metrics)
                
                # Sleep for collection interval
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        try:
            import psutil
            
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Performance metrics
            avg_latency = self._calculate_average_latency()
            error_rate = self._calculate_error_rate()
            fraud_rate = self._calculate_fraud_rate()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024**3)
                },
                'performance': {
                    'avg_prediction_latency_ms': avg_latency * 1000,
                    'error_rate': error_rate,
                    'fraud_rate': fraud_rate,
                    'predictions_per_second': self._calculate_predictions_per_second()
                },
                'services': {
                    'redis_status': await self._check_redis_status(),
                    'kafka_status': await self._check_kafka_status(),
                    'model_status': await self._check_model_status()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics in Redis"""
        try:
            key = f"metrics:{datetime.now().strftime('%Y%m%d_%H%M')}"
            self.redis_client.setex(key, 3600, json.dumps(metrics))  # 1 hour TTL
            
            # Store latest metrics
            self.redis_client.set("metrics:latest", json.dumps(metrics))
            
        except Exception as e:
            self.logger.error(f"Failed to store metrics: {str(e)}")
    
    async def _check_alerts(self, metrics: Dict[str, Any]):
        """Check for alert conditions"""
        try:
            alerts = []
            
            # Check prediction latency
            performance = metrics.get('performance', {})
            latency = performance.get('avg_prediction_latency_ms', 0) / 1000
            if latency > self.alert_thresholds['prediction_latency']:
                alerts.append({
                    'type': 'high_latency',
                    'message': f'Prediction latency {latency:.3f}s exceeds threshold {self.alert_thresholds["prediction_latency"]}s',
                    'severity': 'warning'
                })
            
            # Check error rate
            error_rate = performance.get('error_rate', 0)
            if error_rate > self.alert_thresholds['error_rate']:
                alerts.append({
                    'type': 'high_error_rate',
                    'message': f'Error rate {error_rate:.2%} exceeds threshold {self.alert_thresholds["error_rate"]:.2%}',
                    'severity': 'critical'
                })
            
            # Check system memory
            system = metrics.get('system', {})
            memory_percent = system.get('memory_percent', 0)
            if memory_percent > self.alert_thresholds['system_memory'] * 100:
                alerts.append({
                    'type': 'high_memory',
                    'message': f'Memory usage {memory_percent:.1f}% exceeds threshold {self.alert_thresholds["system_memory"]:.0%}',
                    'severity': 'warning'
                })
            
            # Store alerts
            if alerts:
                await self._store_alerts(alerts)
                
        except Exception as e:
            self.logger.error(f"Error checking alerts: {str(e)}")
    
    async def _store_alerts(self, alerts: List[Dict[str, Any]]):
        """Store alerts in Redis"""
        try:
            for alert in alerts:
                alert['timestamp'] = datetime.now().isoformat()
                key = f"alerts:{datetime.now().strftime('%Y%m%d_%H%M%S')}_{alert['type']}"
                self.redis_client.setex(key, 86400, json.dumps(alert))  # 24 hours TTL
                
        except Exception as e:
            self.logger.error(f"Failed to store alerts: {str(e)}")
    
    def _calculate_average_latency(self) -> float:
        """Calculate average prediction latency"""
        latencies = self.performance_metrics.get('prediction_latency', [])
        if latencies:
            return sum(latencies) / len(latencies)
        return 0.0
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate from recent predictions"""
        if not self.prediction_history:
            return 0.0
        
        recent_predictions = list(self.prediction_history)[-1000:]  # Last 1000 predictions
        # This would need actual error tracking - for now return 0
        return 0.0
    
    def _calculate_fraud_rate(self) -> float:
        """Calculate fraud rate from recent predictions"""
        if not self.prediction_history:
            return 0.0
        
        recent_predictions = list(self.prediction_history)[-1000:]  # Last 1000 predictions
        fraud_count = sum(1 for p in recent_predictions if p.get('is_fraud', False))
        return fraud_count / len(recent_predictions)
    
    def _calculate_predictions_per_second(self) -> float:
        """Calculate predictions per second"""
        if not self.prediction_history:
            return 0.0
        
        # Calculate rate from last minute of predictions
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_predictions = [
            p for p in self.prediction_history 
            if datetime.fromisoformat(p['timestamp']) > one_minute_ago
        ]
        
        return len(recent_predictions) / 60.0  # per second
    
    async def _check_redis_status(self) -> Dict[str, Any]:
        """Check Redis service status"""
        try:
            if self.redis_client:
                start_time = time.time()
                self.redis_client.ping()
                latency = (time.time() - start_time) * 1000
                
                info = self.redis_client.info()
                
                return {
                    'status': 'connected',
                    'latency_ms': latency,
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_mb': info.get('used_memory', 0) / (1024**2)
                }
            else:
                return {'status': 'disconnected', 'error': 'Redis client not initialized'}
                
        except Exception as e:
            return {'status': 'disconnected', 'error': str(e)}
    
    async def _check_kafka_status(self) -> Dict[str, Any]:
        """Check Kafka service status"""
        try:
            # This would require Kafka client instance
            # For now, return placeholder
            return {
                'status': 'connected',
                'brokers': 1,
                'topics': 3
            }
        except Exception as e:
            return {'status': 'disconnected', 'error': str(e)}
    
    async def _check_model_status(self) -> Dict[str, Any]:
        """Check ML models status"""
        try:
            # This would require model service instance
            # For now, return placeholder
            return {
                'status': 'loaded',
                'models': 3,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        try:
            # Get latest metrics from Redis
            latest_metrics = self.redis_client.get("metrics:latest")
            if latest_metrics:
                metrics = json.loads(latest_metrics)
            else:
                metrics = await self._get_system_metrics()
            
            # Add prediction statistics
            metrics['prediction_stats'] = self._get_prediction_stats()
            
            # Add recent alerts
            metrics['recent_alerts'] = await self._get_recent_alerts()
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_prediction_stats(self) -> Dict[str, Any]:
        """Get prediction statistics"""
        if not self.prediction_history:
            return {
                'total_predictions': 0,
                'fraud_predictions': 0,
                'legitimate_predictions': 0,
                'fraud_rate': 0.0
            }
        
        recent_predictions = list(self.prediction_history)
        total = len(recent_predictions)
        fraud_count = sum(1 for p in recent_predictions if p.get('is_fraud', False))
        
        return {
            'total_predictions': total,
            'fraud_predictions': fraud_count,
            'legitimate_predictions': total - fraud_count,
            'fraud_rate': fraud_count / total if total > 0 else 0.0
        }
    
    async def _get_recent_alerts(self) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            # Get recent alert keys from Redis
            alert_keys = self.redis_client.keys("alerts:*")
            alerts = []
            
            for key in alert_keys[-10:]:  # Last 10 alerts
                alert_data = self.redis_client.get(key)
                if alert_data:
                    alerts.append(json.loads(alert_data))
            
            return sorted(alerts, key=lambda x: x.get('timestamp', ''), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {str(e)}")
            return []
