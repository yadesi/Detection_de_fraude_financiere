import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import asyncio
import time

# Configuration
st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-high {
        border-left-color: #ff4444;
    }
    .alert-medium {
        border-left-color: #ffaa00;
    }
    .alert-low {
        border-left-color: #44ff44;
    }
</style>
""", unsafe_allow_html=True)

class FraudDetectionDashboard:
    """Streamlit dashboard for fraud detection monitoring"""
    
    def __init__(self):
        import os
        self.api_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        self.refresh_interval = 30  # seconds
        
    def run(self):
        """Main dashboard application"""
        st.markdown('<h1 class="main-header">:shield: Fraud Detection Dashboard</h1>', unsafe_allow_html=True)
        
        # Version check - to ensure we're running updated code
        st.warning("🔧 DEBUG MODE - Updated Code v2.0")
        
        # Debug info - visible in main content
        st.markdown("### 🔍 Debug Information")
        st.write(f"**API URL:** {self.api_url}")
        st.write(f"**Code Version:** Updated with connection fix")
        
        # Test API connection
        try:
            import requests
            response = requests.get(f"{self.api_url}/health", timeout=5)
            st.success(f"✅ API Connected! Status: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json()
                st.write(f"**Health Response:** {health_data}")
        except Exception as e:
            st.error(f"❌ API Connection Failed: {str(e)}")
            st.write(f"**Failed URL:** {self.api_url}/health")
        
        st.markdown("---")
        
        # Sidebar
        self._render_sidebar()
        
        # Main content
        self._render_main_content()
        
        # Auto-refresh
        if st.session_state.get('auto_refresh', True):
            time.sleep(self.refresh_interval)
            st.rerun()
    
    def _render_sidebar(self):
        """Render sidebar controls"""
        st.sidebar.title("Controls")
        
        # Auto-refresh toggle
        auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
        st.session_state.auto_refresh = auto_refresh
        
        if auto_refresh:
            refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 30)
            self.refresh_interval = refresh_interval
        
        # Manual refresh button
        if st.sidebar.button("Refresh Now"):
            st.rerun()
        
        # API health check
        st.sidebar.markdown("---")
        st.sidebar.subheader("System Status")
        
        try:
            st.sidebar.write(f"Trying to connect to: {self.api_url}/health")
            response = requests.get(f"{self.api_url}/health", timeout=5)
            st.sidebar.write(f"Response status: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json()
                st.sidebar.success("API Healthy")
                
                # Service status
                services = health_data.get('services', {})
                for service, status in services.items():
                    if status.get('status') == 'connected':
                        st.sidebar.success(f" {service}: Connected")
                    else:
                        st.sidebar.error(f" {service}: Disconnected")
            else:
                st.sidebar.error(f"API Unhealthy - Status: {response.status_code}")
        except Exception as e:
            st.sidebar.error(f"API Connection Failed: {str(e)}")
            st.sidebar.write(f"API URL: {self.api_url}")
        
        # Quick actions
        st.sidebar.markdown("---")
        st.sidebar.subheader("Quick Actions")
        
        if st.sidebar.button("Retrain Models"):
            self._trigger_retraining()
        
        if st.sidebar.button("Clear Cache"):
            self._clear_cache()
    
    def _render_main_content(self):
        """Render main dashboard content"""
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Overview", "Real-time Monitoring", "Model Performance", 
            "Transaction Analysis", "System Metrics"
        ])
        
        with tab1:
            self._render_overview()
        
        with tab2:
            self._render_realtime_monitoring()
        
        with tab3:
            self._render_model_performance()
        
        with tab4:
            self._render_transaction_analysis()
        
        with tab5:
            self._render_system_metrics()
    
    def _render_overview(self):
        """Render overview dashboard"""
        st.subheader("System Overview")
        
        # Get metrics
        metrics = self._get_metrics()
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._render_metric_card(
                "Total Predictions", 
                metrics.get('prediction_stats', {}).get('total_predictions', 0),
                "transactions"
            )
        
        with col2:
            fraud_rate = metrics.get('prediction_stats', {}).get('fraud_rate', 0) * 100
            self._render_metric_card(
                "Fraud Rate", 
                f"{fraud_rate:.2f}%",
                "percentage"
            )
        
        with col3:
            avg_latency = metrics.get('performance', {}).get('avg_prediction_latency_ms', 0)
            self._render_metric_card(
                "Avg Latency", 
                f"{avg_latency:.1f}ms",
                "time"
            )
        
        with col4:
            predictions_per_sec = metrics.get('performance', {}).get('predictions_per_second', 0)
            self._render_metric_card(
                "Throughput", 
                f"{predictions_per_sec:.1f}/s",
                "rate"
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Prediction Trends")
            self._render_prediction_trends()
        
        with col2:
            st.subheader("Fraud Detection Pattern")
            self._render_fraud_patterns()
        
        # Recent alerts
        st.subheader("Recent Alerts")
        self._render_recent_alerts(metrics.get('recent_alerts', []))
    
    def _render_realtime_monitoring(self):
        """Render real-time monitoring"""
        st.subheader("Real-time Transaction Monitoring")
        
        # Live predictions stream
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Live Predictions")
            self._render_live_predictions()
        
        with col2:
            st.subheader("Fraud Score Distribution")
            self._render_fraud_score_distribution()
        
        # Recent transactions table
        st.subheader("Recent Transactions")
        self._render_recent_transactions()
    
    def _render_model_performance(self):
        """Render model performance metrics"""
        st.subheader("Model Performance Analysis")
        
        # Model metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Accuracy")
            self._render_accuracy_gauge()
        
        with col2:
            st.subheader("Precision")
            self._render_precision_gauge()
        
        with col3:
            st.subheader("Recall")
            self._render_recall_gauge()
        
        # Performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Model Comparison")
            self._render_model_comparison()
        
        with col2:
            st.subheader("Feature Importance")
            self._render_feature_importance()
        
        # Training history
        st.subheader("Training History")
        self._render_training_history()
    
    def _render_transaction_analysis(self):
        """Render transaction analysis"""
        st.subheader("Transaction Analysis")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_range = st.date_input(
                "Date Range",
                value=[datetime.now().date() - timedelta(days=7), datetime.now().date()]
            )
        
        with col2:
            transaction_type = st.selectbox(
                "Transaction Type",
                ["All", "CASH-IN", "CASH-OUT", "DEBIT", "PAYMENT", "TRANSFER"]
            )
        
        with col3:
            amount_range = st.slider(
                "Amount Range ($)",
                0, 100000, (0, 10000)
            )
        
        # Analysis charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Transaction Volume by Type")
            self._render_transaction_volume()
        
        with col2:
            st.subheader("Fraud by Transaction Type")
            self._render_fraud_by_type()
        
        # Amount analysis
        st.subheader("Amount Distribution Analysis")
        self._render_amount_distribution()
        
        # Time analysis
        st.subheader("Temporal Analysis")
        self._render_temporal_analysis()
    
    def _render_system_metrics(self):
        """Render system metrics"""
        st.subheader("System Performance Metrics")
        
        # Get system metrics
        metrics = self._get_metrics()
        system_metrics = metrics.get('system', {})
        
        # System resources
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Resource Usage")
            self._render_resource_usage(system_metrics)
        
        with col2:
            st.subheader("Service Status")
            self._render_service_status(metrics.get('services', {}))
        
        # Performance metrics
        st.subheader("Performance Metrics")
        self._render_performance_metrics(metrics.get('performance', {}))
        
        # Logs
        st.subheader("System Logs")
        self._render_system_logs()
    
    def _render_metric_card(self, title, value, unit):
        """Render a metric card"""
        st.markdown(f"""
        <div class="metric-card">
            <h3>{title}</h3>
            <p style="font-size: 2rem; font-weight: bold; margin: 0;">{value}</p>
            <p style="color: #666; margin: 0;">{unit}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_prediction_trends(self):
        """Render prediction trends chart"""
        # Generate sample data
        dates = pd.date_range(start=datetime.now() - timedelta(days=7), periods=168, freq='H')
        predictions = np.random.poisson(50, 168)
        fraud_predictions = np.random.poisson(2, 168)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=predictions, name='Total Predictions', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=dates, y=fraud_predictions, name='Fraud Predictions', line=dict(color='red')))
        
        fig.update_layout(
            title='Prediction Trends (Last 7 Days)',
            xaxis_title='Time',
            yaxis_title='Predictions per Hour',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_fraud_patterns(self):
        """Render fraud patterns chart"""
        # Sample data
        hours = list(range(24))
        fraud_rates = [0.01 + 0.02 * np.sin(h/3) for h in hours]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=hours, y=fraud_rates, name='Fraud Rate', marker_color='red'))
        
        fig.update_layout(
            title='Fraud Rate by Hour of Day',
            xaxis_title='Hour',
            yaxis_title='Fraud Rate',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_recent_alerts(self, alerts):
        """Render recent alerts"""
        if not alerts:
            st.info("No recent alerts")
            return
        
        for alert in alerts[:5]:  # Show last 5 alerts
            alert_type = alert.get('type', 'info')
            severity = alert.get('severity', 'low')
            
            alert_class = f"alert-{severity}"
            
            st.markdown(f"""
            <div class="metric-card {alert_class}">
                <h4>{alert.get('type', 'Alert').replace('_', ' ').title()}</h4>
                <p>{alert.get('message', 'No message')}</p>
                <small>{alert.get('timestamp', '')}</small>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_live_predictions(self):
        """Render live predictions stream"""
        # Sample live data
        transactions = [
            {"id": "TXN001", "amount": 1500, "fraud_prob": 0.15, "status": "Legitimate"},
            {"id": "TXN002", "amount": 25000, "fraud_prob": 0.85, "status": "Fraud"},
            {"id": "TXN003", "amount": 500, "fraud_prob": 0.05, "status": "Legitimate"},
            {"id": "TXN004", "amount": 12000, "fraud_prob": 0.65, "status": "Suspicious"},
            {"id": "TXN005", "amount": 300, "fraud_prob": 0.02, "status": "Legitimate"},
        ]
        
        df = pd.DataFrame(transactions)
        
        # Color code based on fraud probability
        def color_status(val):
            if val == "Fraud":
                return 'background-color: #ffcccc'
            elif val == "Suspicious":
                return 'background-color: #fff3cd'
            else:
                return 'background-color: #d4edda'
        
        styled_df = df.style.applymap(color_status, subset=['status'])
        st.dataframe(styled_df, use_container_width=True)
    
    def _render_fraud_score_distribution(self):
        """Render fraud score distribution"""
        # Sample data
        scores = np.random.beta(2, 8, 1000)  # Most scores low, some high
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=scores, nbinsx=20, name='Fraud Scores'))
        
        fig.update_layout(
            title='Fraud Score Distribution',
            xaxis_title='Fraud Probability',
            yaxis_title='Count',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_recent_transactions(self):
        """Render recent transactions table"""
        # Sample data
        transactions = []
        for i in range(10):
            transactions.append({
                "Transaction ID": f"TXN{1000+i}",
                "Amount": np.random.randint(100, 50000),
                "Type": np.random.choice(["CASH-IN", "CASH-OUT", "TRANSFER", "PAYMENT"]),
                "Fraud Probability": round(np.random.random(), 3),
                "Status": "Fraud" if np.random.random() > 0.9 else "Legitimate",
                "Timestamp": datetime.now() - timedelta(minutes=np.random.randint(1, 60))
            })
        
        df = pd.DataFrame(transactions)
        st.dataframe(df, use_container_width=True)
    
    def _render_accuracy_gauge(self):
        """Render accuracy gauge"""
        accuracy = 0.95  # Sample value
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = accuracy,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Accuracy"},
            gauge = {
                'axis': {'range': [None, 1]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 0.5], 'color': "lightgray"},
                    {'range': [0.5, 0.8], 'color': "gray"},
                    {'range': [0.8, 1], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0.9
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_precision_gauge(self):
        """Render precision gauge"""
        precision = 0.92  # Sample value
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = precision,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Precision"},
            gauge = {
                'axis': {'range': [None, 1]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 0.5], 'color': "lightgray"},
                    {'range': [0.5, 0.8], 'color': "gray"},
                    {'range': [0.8, 1], 'color': "lightgreen"}
                ]
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_recall_gauge(self):
        """Render recall gauge"""
        recall = 0.88  # Sample value
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = recall,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Recall"},
            gauge = {
                'axis': {'range': [None, 1]},
                'bar': {'color': "darkorange"},
                'steps': [
                    {'range': [0, 0.5], 'color': "lightgray"},
                    {'range': [0.5, 0.8], 'color': "gray"},
                    {'range': [0.8, 1], 'color': "lightgreen"}
                ]
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_model_comparison(self):
        """Render model comparison chart"""
        models = ['Isolation Forest', 'XGBoost', 'Ensemble']
        accuracy = [0.85, 0.94, 0.96]
        precision = [0.82, 0.92, 0.95]
        recall = [0.88, 0.89, 0.94]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Accuracy', x=models, y=accuracy))
        fig.add_trace(go.Bar(name='Precision', x=models, y=precision))
        fig.add_trace(go.Bar(name='Recall', x=models, y=recall))
        
        fig.update_layout(
            title='Model Performance Comparison',
            xaxis_title='Models',
            yaxis_title='Score',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_feature_importance(self):
        """Render feature importance chart"""
        features = [
            'Amount', 'Amount Log', 'Balance Change', 'Error Indicator',
            'Transaction Type', 'Time of Day', 'Day of Week', 'Account History'
        ]
        importance = [0.25, 0.20, 0.15, 0.12, 0.10, 0.08, 0.06, 0.04]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=importance, y=features, orientation='h'))
        
        fig.update_layout(
            title='Feature Importance',
            xaxis_title='Importance',
            yaxis_title='Features',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_training_history(self):
        """Render training history"""
        # Sample training history
        training_data = [
            {"date": "2024-01-01", "model": "XGBoost", "accuracy": 0.92, "duration": 45},
            {"date": "2024-01-08", "model": "XGBoost", "accuracy": 0.93, "duration": 48},
            {"date": "2024-01-15", "model": "XGBoost", "accuracy": 0.94, "duration": 52},
            {"date": "2024-01-22", "model": "Ensemble", "accuracy": 0.95, "duration": 65},
            {"date": "2024-01-29", "model": "Ensemble", "accuracy": 0.96, "duration": 68},
        ]
        
        df = pd.DataFrame(training_data)
        st.dataframe(df, use_container_width=True)
    
    def _render_transaction_volume(self):
        """Render transaction volume by type"""
        types = ["CASH-IN", "CASH-OUT", "DEBIT", "PAYMENT", "TRANSFER"]
        volumes = [1200, 800, 600, 1500, 400]
        fraud_volumes = [12, 80, 6, 15, 40]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Total', x=types, y=volumes))
        fig.add_trace(go.Bar(name='Fraud', x=types, y=fraud_volumes))
        
        fig.update_layout(
            title='Transaction Volume by Type',
            xaxis_title='Transaction Type',
            yaxis_title='Count',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_fraud_by_type(self):
        """Render fraud by transaction type"""
        types = ["CASH-IN", "CASH-OUT", "DEBIT", "PAYMENT", "TRANSFER"]
        fraud_rates = [0.01, 0.10, 0.01, 0.01, 0.10]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=types, y=fraud_rates, marker_color='red'))
        
        fig.update_layout(
            title='Fraud Rate by Transaction Type',
            xaxis_title='Transaction Type',
            yaxis_title='Fraud Rate',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_amount_distribution(self):
        """Render amount distribution"""
        # Sample data
        amounts_legitimate = np.random.lognormal(8, 1, 1000)
        amounts_fraud = np.random.lognormal(9, 1.5, 100)
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=amounts_legitimate, name='Legitimate', opacity=0.7))
        fig.add_trace(go.Histogram(x=amounts_fraud, name='Fraud', opacity=0.7))
        
        fig.update_layout(
            title='Amount Distribution by Transaction Type',
            xaxis_title='Amount ($)',
            yaxis_title='Count',
            barmode='overlay',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_temporal_analysis(self):
        """Render temporal analysis"""
        # Sample data
        hours = list(range(24))
        volumes = [100 + 50 * np.sin(h/3) for h in hours]
        fraud_rates = [0.01 + 0.02 * np.sin(h/4) for h in hours]
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Transaction Volume by Hour', 'Fraud Rate by Hour'),
            vertical_spacing=0.1
        )
        
        fig.add_trace(go.Scatter(x=hours, y=volumes, name='Volume'), row=1, col=1)
        fig.add_trace(go.Scatter(x=hours, y=fraud_rates, name='Fraud Rate'), row=2, col=1)
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_resource_usage(self, system_metrics):
        """Render resource usage"""
        cpu = system_metrics.get('cpu_percent', 0)
        memory = system_metrics.get('memory_percent', 0)
        disk = system_metrics.get('disk_percent', 0)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=['CPU', 'Memory', 'Disk'],
            y=[cpu, memory, disk],
            marker_color=['blue', 'green', 'orange']
        ))
        
        fig.update_layout(
            title='System Resource Usage',
            yaxis_title='Usage (%)',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_service_status(self, services):
        """Render service status"""
        for service_name, service_data in services.items():
            status = service_data.get('status', 'unknown')
            
            if status == 'connected':
                st.success(f" {service_name}: Connected")
            else:
                st.error(f" {service_name}: Disconnected")
    
    def _render_performance_metrics(self, performance_metrics):
        """Render performance metrics"""
        metrics_data = {
            'Metric': ['Avg Latency', 'Error Rate', 'Fraud Rate', 'Throughput'],
            'Value': [
                f"{performance_metrics.get('avg_prediction_latency_ms', 0):.1f}ms",
                f"{performance_metrics.get('error_rate', 0):.2%}",
                f"{performance_metrics.get('fraud_rate', 0):.2%}",
                f"{performance_metrics.get('predictions_per_second', 0):.1f}/s"
            ]
        }
        
        df = pd.DataFrame(metrics_data)
        st.dataframe(df, use_container_width=True)
    
    def _render_system_logs(self):
        """Render system logs"""
        # Sample logs
        logs = [
            {"timestamp": datetime.now() - timedelta(minutes=5), "level": "INFO", "message": "Model prediction completed successfully"},
            {"timestamp": datetime.now() - timedelta(minutes=10), "level": "WARNING", "message": "High latency detected: 150ms"},
            {"timestamp": datetime.now() - timedelta(minutes=15), "level": "INFO", "message": "New model loaded: version 1.2.0"},
            {"timestamp": datetime.now() - timedelta(minutes=20), "level": "ERROR", "message": "Redis connection timeout"},
            {"timestamp": datetime.now() - timedelta(minutes=25), "level": "INFO", "message": "Batch processing completed: 1000 transactions"},
        ]
        
        df = pd.DataFrame(logs)
        st.dataframe(df, use_container_width=True)
    
    def _get_metrics(self):
        """Get metrics from API"""
        try:
            response = requests.get(f"{self.api_url}/metrics", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        # Return default metrics if API fails
        return {
            'prediction_stats': {'total_predictions': 0, 'fraud_rate': 0},
            'performance': {'avg_prediction_latency_ms': 0, 'predictions_per_second': 0},
            'system': {'cpu_percent': 0, 'memory_percent': 0},
            'services': {},
            'recent_alerts': []
        }
    
    def _trigger_retraining(self):
        """Trigger model retraining"""
        try:
            response = requests.post(f"{self.api_url}/model/retrain", timeout=10)
            if response.status_code == 200:
                st.success("Model retraining triggered successfully!")
            else:
                st.error("Failed to trigger retraining")
        except Exception as e:
            st.error(f"Error triggering retraining: {str(e)}")
    
    def _clear_cache(self):
        """Clear application cache"""
        st.cache_data.clear()
        st.success("Cache cleared successfully!")

# Main application
if __name__ == "__main__":
    dashboard = FraudDetectionDashboard()
    dashboard.run()
