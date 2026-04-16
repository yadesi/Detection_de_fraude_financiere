#!/usr/bin/env python3
"""
Real-time Alerts System for Fraud Detection
Monitors transactions and triggers alerts for suspicious patterns
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import requests
from collections import defaultdict, deque
import threading
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    HIGH_AMOUNT = "high_amount"
    RAPID_TRANSACTIONS = "rapid_transactions"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    BALANCE_MISMATCH = "balance_mismatch"
    UNUSUAL_LOCATION = "unusual_location"
    MULTIPLE_FRAUDS = "multiple_frauds"
    SYSTEM_PERFORMANCE = "system_performance"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    transaction_id: Optional[str]
    customer_id: Optional[str]
    timestamp: datetime
    details: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

class AlertManager:
    """Manages fraud detection alerts and notifications"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.alerts: deque = deque(maxlen=1000)  # Keep last 1000 alerts
        self.alert_rules = self._initialize_rules()
        self.transaction_history: Dict[str, List[Dict]] = defaultdict(list)
        self.customer_patterns: Dict[str, Dict] = defaultdict(dict)
        self.alert_queue = queue.Queue()
        self.running = False
        
        # Statistics
        self.stats = {
            "total_alerts": 0,
            "alerts_by_type": defaultdict(int),
            "alerts_by_severity": defaultdict(int),
            "resolved_alerts": 0,
            "false_positives": 0
        }
    
    def _initialize_rules(self) -> Dict[AlertType, Dict]:
        """Initialize alert rules and thresholds"""
        return {
            AlertType.HIGH_AMOUNT: {
                "threshold": 50000,
                "severity": AlertSeverity.HIGH,
                "title": "High Value Transaction",
                "message": "Transaction amount exceeds threshold"
            },
            AlertType.RAPID_TRANSACTIONS: {
                "max_transactions": 5,
                "time_window": 300,  # 5 minutes
                "severity": AlertSeverity.MEDIUM,
                "title": "Rapid Transaction Sequence",
                "message": "Multiple transactions detected in short time period"
            },
            AlertType.SUSPICIOUS_PATTERN: {
                "round_amount_threshold": 0.95,
                "same_destination_threshold": 3,
                "severity": AlertSeverity.MEDIUM,
                "title": "Suspicious Transaction Pattern",
                "message": "Unusual transaction pattern detected"
            },
            AlertType.BALANCE_MISMATCH: {
                "threshold": 0.1,  # 10% mismatch
                "severity": AlertSeverity.HIGH,
                "title": "Balance Mismatch",
                "message": "Transaction balance calculation appears incorrect"
            },
            AlertType.MULTIPLE_FRAUDS: {
                "threshold": 2,
                "time_window": 3600,  # 1 hour
                "severity": AlertSeverity.CRITICAL,
                "title": "Multiple Fraudulent Transactions",
                "message": "Multiple fraud predictions for same customer"
            },
            AlertType.SYSTEM_PERFORMANCE: {
                "latency_threshold": 1000,  # 1 second
                "error_rate_threshold": 0.05,  # 5%
                "severity": AlertSeverity.MEDIUM,
                "title": "System Performance Issue",
                "message": "System performance degradation detected"
            }
        }
    
    def create_alert(self, alert_type: AlertType, severity: AlertSeverity, 
                    title: str, message: str, transaction_id: str = None,
                    customer_id: str = None, details: Dict[str, Any] = None) -> Alert:
        """Create a new alert"""
        
        alert_id = f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.alerts):04d}"
        
        alert = Alert(
            id=alert_id,
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            transaction_id=transaction_id,
            customer_id=customer_id,
            timestamp=datetime.now(),
            details=details or {}
        )
        
        # Store alert
        self.alerts.append(alert)
        self.stats["total_alerts"] += 1
        self.stats["alerts_by_type"][alert_type] += 1
        self.stats["alerts_by_severity"][severity] += 1
        
        # Queue for notification
        self.alert_queue.put(alert)
        
        logger.warning(f"ALERT CREATED: {alert.title} - {alert.message}")
        
        return alert
    
    def analyze_transaction(self, transaction: Dict[str, Any]) -> List[Alert]:
        """Analyze a single transaction for alert conditions"""
        
        alerts = []
        customer_id = transaction.get('nameOrig')
        transaction_id = transaction.get('transaction_id')
        
        # Store transaction for pattern analysis
        self.transaction_history[customer_id].append(transaction)
        
        # Rule 1: High Amount Alert
        amount = transaction.get('amount', 0)
        if amount > self.alert_rules[AlertType.HIGH_AMOUNT]["threshold"]:
            alert = self.create_alert(
                AlertType.HIGH_AMOUNT,
                self.alert_rules[AlertType.HIGH_AMOUNT]["severity"],
                self.alert_rules[AlertType.HIGH_AMOUNT]["title"],
                f"Transaction amount ${amount:,.2f} exceeds threshold",
                transaction_id=transaction_id,
                customer_id=customer_id,
                details={"amount": amount, "threshold": self.alert_rules[AlertType.HIGH_AMOUNT]["threshold"]}
            )
            alerts.append(alert)
        
        # Rule 2: Balance Mismatch Alert
        old_balance = transaction.get('oldbalanceOrg', 0)
        new_balance = transaction.get('newbalanceOrig', 0)
        tx_type = transaction.get('type')
        
        if tx_type in ['TRANSFER', 'CASH-OUT', 'DEBIT']:
            expected_balance = old_balance - amount
            mismatch = abs(new_balance - expected_balance) / max(old_balance, 1)
            
            if mismatch > self.alert_rules[AlertType.BALANCE_MISMATCH]["threshold"]:
                alert = self.create_alert(
                    AlertType.BALANCE_MISMATCH,
                    self.alert_rules[AlertType.BALANCE_MISMATCH]["severity"],
                    self.alert_rules[AlertType.BALANCE_MISMATCH]["title"],
                    f"Balance mismatch detected: expected ${expected_balance:,.2f}, got ${new_balance:,.2f}",
                    transaction_id=transaction_id,
                    customer_id=customer_id,
                    details={
                        "expected_balance": expected_balance,
                        "actual_balance": new_balance,
                        "mismatch_percentage": mismatch * 100
                    }
                )
                alerts.append(alert)
        
        # Rule 3: Suspicious Pattern Alert
        pattern_alerts = self._check_suspicious_patterns(transaction)
        alerts.extend(pattern_alerts)
        
        # Rule 4: Rapid Transactions Alert
        rapid_alerts = self._check_rapid_transactions(customer_id, transaction_id)
        alerts.extend(rapid_alerts)
        
        # Rule 5: Multiple Frauds Alert
        fraud_alerts = self._check_multiple_frauds(customer_id, transaction_id)
        alerts.extend(fraud_alerts)
        
        return alerts
    
    def _check_suspicious_patterns(self, transaction: Dict[str, Any]) -> List[Alert]:
        """Check for suspicious transaction patterns"""
        
        alerts = []
        customer_id = transaction.get('nameOrig')
        transaction_id = transaction.get('transaction_id')
        amount = transaction.get('amount', 0)
        
        # Check for round amounts (suspicious)
        if amount > 1000:
            roundness = 1 - (amount % 1000) / 1000
            if roundness > self.alert_rules[AlertType.SUSPICIOUS_PATTERN]["round_amount_threshold"]:
                alert = self.create_alert(
                    AlertType.SUSPICIOUS_PATTERN,
                    self.alert_rules[AlertType.SUSPICIOUS_PATTERN]["severity"],
                    self.alert_rules[AlertType.SUSPICIOUS_PATTERN]["title"],
                    f"Round amount transaction detected: ${amount:,.2f}",
                    transaction_id=transaction_id,
                    customer_id=customer_id,
                    details={"amount": amount, "roundness": roundness}
                )
                alerts.append(alert)
        
        # Check for same destination multiple times
        customer_txs = self.transaction_history[customer_id]
        destination_counts = defaultdict(int)
        
        for tx in customer_txs:
            dest = tx.get('nameDest')
            if dest:
                destination_counts[dest] += 1
        
        for dest, count in destination_counts.items():
            if count >= self.alert_rules[AlertType.SUSPICIOUS_PATTERN]["same_destination_threshold"]:
                alert = self.create_alert(
                    AlertType.SUSPICIOUS_PATTERN,
                    self.alert_rules[AlertType.SUSPICIOUS_PATTERN]["severity"],
                    self.alert_rules[AlertType.SUSPICIOUS_PATTERN]["title"],
                    f"Multiple transactions to same destination: {dest} ({count} times)",
                    transaction_id=transaction_id,
                    customer_id=customer_id,
                    details={"destination": dest, "count": count}
                )
                alerts.append(alert)
                break  # Only create one alert per transaction
        
        return alerts
    
    def _check_rapid_transactions(self, customer_id: str, transaction_id: str) -> List[Alert]:
        """Check for rapid transaction sequences"""
        
        alerts = []
        customer_txs = self.transaction_history[customer_id]
        
        if len(customer_txs) < self.alert_rules[AlertType.RAPID_TRANSACTIONS]["max_transactions"]:
            return alerts
        
        # Get recent transactions
        now = datetime.now()
        time_window = self.alert_rules[AlertType.RAPID_TRANSACTIONS]["time_window"]
        max_tx = self.alert_rules[AlertType.RAPID_TRANSACTIONS]["max_transactions"]
        
        recent_txs = []
        for tx in customer_txs:
            tx_time = datetime.fromisoformat(tx.get('timestamp', now.isoformat()))
            if (now - tx_time).total_seconds() <= time_window:
                recent_txs.append(tx)
        
        if len(recent_txs) >= max_tx:
            alert = self.create_alert(
                AlertType.RAPID_TRANSACTIONS,
                self.alert_rules[AlertType.RAPID_TRANSACTIONS]["severity"],
                self.alert_rules[AlertType.RAPID_TRANSACTIONS]["title"],
                f"{len(recent_txs)} transactions in {time_window/60:.0f} minutes",
                transaction_id=transaction_id,
                customer_id=customer_id,
                details={
                    "transaction_count": len(recent_txs),
                    "time_window": time_window,
                    "transactions": recent_txs
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_multiple_frauds(self, customer_id: str, transaction_id: str) -> List[Alert]:
        """Check for multiple fraudulent transactions"""
        
        alerts = []
        customer_txs = self.transaction_history[customer_id]
        
        # Count fraud predictions (assuming we have prediction results)
        fraud_count = 0
        time_window = self.alert_rules[AlertType.MULTIPLE_FRAUDS]["time_window"]
        threshold = self.alert_rules[AlertType.MULTIPLE_FRAUDS]["threshold"]
        
        now = datetime.now()
        recent_fraud_txs = []
        
        for tx in customer_txs:
            tx_time = datetime.fromisoformat(tx.get('timestamp', now.isoformat()))
            if (now - tx_time).total_seconds() <= time_window:
                # Check if this transaction was predicted as fraud
                # This would require integration with prediction results
                # For demo purposes, we'll simulate some fraud predictions
                if tx.get('amount', 0) > 10000 and tx.get('type') in ['TRANSFER', 'CASH-OUT']:
                    fraud_count += 1
                    recent_fraud_txs.append(tx)
        
        if fraud_count >= threshold:
            alert = self.create_alert(
                AlertType.MULTIPLE_FRAUDS,
                self.alert_rules[AlertType.MULTIPLE_FRAUDS]["severity"],
                self.alert_rules[AlertType.MULTIPLE_FRAUDS]["title"],
                f"{fraud_count} fraudulent transactions detected in last hour",
                transaction_id=transaction_id,
                customer_id=customer_id,
                details={
                    "fraud_count": fraud_count,
                    "time_window": time_window,
                    "transactions": recent_fraud_txs
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def check_system_performance(self) -> List[Alert]:
        """Check system performance and create alerts if needed"""
        
        alerts = []
        
        try:
            # Get system metrics
            response = requests.get(f"{self.api_base_url}/metrics", timeout=10)
            
            if response.status_code == 200:
                metrics = response.json()
                
                # Check latency
                avg_latency = metrics['performance'].get('avg_prediction_latency_ms', 0)
                if avg_latency > self.alert_rules[AlertType.SYSTEM_PERFORMANCE]["latency_threshold"]:
                    alert = self.create_alert(
                        AlertType.SYSTEM_PERFORMANCE,
                        self.alert_rules[AlertType.SYSTEM_PERFORMANCE]["severity"],
                        self.alert_rules[AlertType.SYSTEM_PERFORMANCE]["title"],
                        f"High latency detected: {avg_latency:.2f}ms",
                        details={"latency_ms": avg_latency, "threshold": self.alert_rules[AlertType.SYSTEM_PERFORMANCE]["latency_threshold"]}
                    )
                    alerts.append(alert)
                
                # Check error rate
                error_rate = metrics['performance'].get('error_rate', 0)
                if error_rate > self.alert_rules[AlertType.SYSTEM_PERFORMANCE]["error_rate_threshold"]:
                    alert = self.create_alert(
                        AlertType.SYSTEM_PERFORMANCE,
                        self.alert_rules[AlertType.SYSTEM_PERFORMANCE]["severity"],
                        self.alert_rules[AlertType.SYSTEM_PERFORMANCE]["title"],
                        f"High error rate detected: {error_rate*100:.2f}%",
                        details={"error_rate": error_rate, "threshold": self.alert_rules[AlertType.SYSTEM_PERFORMANCE]["error_rate_threshold"]}
                    )
                    alerts.append(alert)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get system metrics: {e}")
        
        return alerts
    
    def resolve_alert(self, alert_id: str, resolved_by: str = "system", notes: str = "") -> bool:
        """Resolve an alert"""
        
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                alert.resolved_by = resolved_by
                alert.details["resolution_notes"] = notes
                
                self.stats["resolved_alerts"] += 1
                
                logger.info(f"ALERT RESOLVED: {alert_id} by {resolved_by}")
                return True
        
        return False
    
    def get_active_alerts(self, severity: AlertSeverity = None) -> List[Alert]:
        """Get active (unresolved) alerts"""
        
        active_alerts = [alert for alert in self.alerts if not alert.resolved]
        
        if severity:
            active_alerts = [alert for alert in active_alerts if alert.severity == severity]
        
        return sorted(active_alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        
        active_alerts = self.get_active_alerts()
        
        return {
            "total_alerts": self.stats["total_alerts"],
            "active_alerts": len(active_alerts),
            "resolved_alerts": self.stats["resolved_alerts"],
            "resolution_rate": self.stats["resolved_alerts"] / max(self.stats["total_alerts"], 1),
            "alerts_by_type": dict(self.stats["alerts_by_type"]),
            "alerts_by_severity": dict(self.stats["alerts_by_severity"]),
            "active_by_severity": {
                severity.value: len([a for a in active_alerts if a.severity == severity])
                for severity in AlertSeverity
            },
            "false_positive_rate": self.stats["false_positives"] / max(self.stats["total_alerts"], 1)
        }
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous monitoring"""
        
        self.running = True
        
        def monitor_loop():
            while self.running:
                try:
                    # Check system performance
                    self.check_system_performance()
                    
                    # Process alert queue (send notifications)
                    while not self.alert_queue.empty():
                        alert = self.alert_queue.get()
                        self._send_notification(alert)
                    
                    time.sleep(interval_seconds)
                    
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(interval_seconds)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        logger.info(f"Alert monitoring started with {interval_seconds}s interval")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.running = False
        logger.info("Alert monitoring stopped")
    
    def _send_notification(self, alert: Alert):
        """Send alert notification (placeholder for actual notification system)"""
        
        # In a real system, this would send emails, SMS, push notifications, etc.
        logger.info(f"NOTIFICATION: {alert.title} - {alert.message}")
        
        # Store for demo purposes
        notification = {
            "alert_id": alert.id,
            "sent_at": datetime.now().isoformat(),
            "channels": ["log", "webhook"]  # Example channels
        }
        
        # Could integrate with email services, Slack, etc.
        return notification

class AlertDashboard:
    """Simple dashboard for displaying alerts"""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
    
    def display_active_alerts(self):
        """Display active alerts in a formatted way"""
        
        active_alerts = self.alert_manager.get_active_alerts()
        
        if not active_alerts:
            print("No active alerts")
            return
        
        print(f"\nACTIVE ALERTS ({len(active_alerts)}):")
        print("-" * 80)
        
        for i, alert in enumerate(active_alerts[:10]):  # Show top 10
            print(f"{i+1}. [{alert.severity.value.upper()}] {alert.title}")
            print(f"   ID: {alert.id}")
            print(f"   Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Message: {alert.message}")
            if alert.transaction_id:
                print(f"   Transaction: {alert.transaction_id}")
            if alert.customer_id:
                print(f"   Customer: {alert.customer_id}")
            print()
    
    def display_statistics(self):
        """Display alert statistics"""
        
        stats = self.alert_manager.get_alert_statistics()
        
        print(f"\nALERT STATISTICS:")
        print("-" * 40)
        print(f"Total Alerts: {stats['total_alerts']}")
        print(f"Active Alerts: {stats['active_alerts']}")
        print(f"Resolved Alerts: {stats['resolved_alerts']}")
        print(f"Resolution Rate: {stats['resolution_rate']*100:.1f}%")
        print(f"False Positive Rate: {stats['false_positive_rate']*100:.1f}%")
        
        print(f"\nBy Type:")
        for alert_type, count in stats['alerts_by_type'].items():
            print(f"  {alert_type}: {count}")
        
        print(f"\nBy Severity:")
        for severity, count in stats['alerts_by_severity'].items():
            print(f"  {severity}: {count}")
        
        print(f"\nActive by Severity:")
        for severity, count in stats['active_by_severity'].items():
            print(f"  {severity}: {count}")

def main():
    """Main function to demonstrate the alert system"""
    
    print("FRAUD DETECTION - REAL-TIME ALERTS SYSTEM")
    print("=" * 50)
    
    # Initialize alert manager
    alert_manager = AlertManager()
    dashboard = AlertDashboard(alert_manager)
    
    # Start monitoring
    alert_manager.start_monitoring(interval_seconds=30)
    
    try:
        print("Alert monitoring started. Press Ctrl+C to stop.")
        print()
        
        # Demo with some test transactions
        from demo_data_generator import FraudDemoDataGenerator
        generator = FraudDemoDataGenerator()
        
        # Generate some test transactions
        print("Generating test transactions...")
        for i in range(20):
            transaction = generator.generate_transaction(
                is_fraud=(i % 5 == 0),  # Every 5th transaction is fraud
                fraud_type="high_amount" if i % 3 == 0 else "suspicious_pattern"
            )
            
            # Analyze transaction
            alerts = alert_manager.analyze_transaction(transaction)
            
            if alerts:
                print(f"Transaction {transaction['transaction_id']} generated {len(alerts)} alerts")
            
            time.sleep(1)  # Simulate transaction flow
        
        # Display results
        dashboard.display_active_alerts()
        dashboard.display_statistics()
        
        print("\nMonitoring continues... Press Ctrl+C to stop.")
        
        # Keep monitoring running
        while True:
            time.sleep(10)
            dashboard.display_active_alerts()
    
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
        alert_manager.stop_monitoring()
        print("Alert system stopped.")

if __name__ == "__main__":
    main()
