import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import time

# Configuration
st.set_page_config(
    page_title="Fraud Detection Dashboard - ML Models",
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
    .model-info {
        background: #e8f5e8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

class MLFraudDetectionDashboard:
    """Streamlit dashboard for ML-based fraud detection monitoring"""
    
    def __init__(self):
        self.api_url = "http://backend:8000"
        self.refresh_interval = 30
        
    def render(self):
        """Render the complete dashboard"""
        self._render_header()
        self._render_sidebar()
        self._render_main_content()
        
    def _render_header(self):
        """Render dashboard header"""
        st.markdown('<h1 class="main-header">Fraud Detection Dashboard - ML Models</h1>', unsafe_allow_html=True)
        
        # Show ML model info
        try:
            model_info = requests.get(f"{self.api_url}/model/info", timeout=5)
            if model_info.status_code == 200:
                info = model_info.json()
                models = info.get('models', {})
                
                st.markdown(f"""
                <div class="model-info">
                    <h3>Active ML Models: {models.get('loaded_models', [])}</h3>
                    <p>Best Model: <strong>{models.get('best_model', 'Unknown')}</strong></p>
                    <p>Features: {models.get('feature_count', 0)} | Model Performance: {models.get('model_performance', {})}</p>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Could not load model info: {e}")
    
    def _render_sidebar(self):
        """Render sidebar controls"""
        st.sidebar.title("Dashboard Controls")
        
        # Auto-refresh
        auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
        if auto_refresh:
            refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 30)
            self.refresh_interval = refresh_interval
        
        # Manual refresh
        if st.sidebar.button("Refresh Now"):
            st.rerun()
        
        # API status
        st.sidebar.markdown("---")
        st.sidebar.subheader("System Status")
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                st.sidebar.success("API Healthy")
                st.sidebar.json(health_data)
            else:
                st.sidebar.error(f"API Unhealthy: {response.status_code}")
        except Exception as e:
            st.sidebar.error(f"API Connection Failed: {e}")
        
        # Test ML prediction
        st.sidebar.markdown("---")
        st.sidebar.subheader("Test ML Prediction")
        
        if st.sidebar.button("Test ML Models"):
            self._test_ml_prediction()
    
    def _render_main_content(self):
        """Render main dashboard content"""
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "ML Overview", "Real-time Monitoring", "Model Performance", "Test Predictions"
        ])
        
        with tab1:
            self._render_ml_overview()
        
        with tab2:
            self._render_realtime_monitoring()
        
        with tab3:
            self._render_model_performance()
        
        with tab4:
            self._render_test_predictions()
    
    def _render_ml_overview(self):
        """Render ML model overview"""
        st.subheader("ML Model Overview")
        
        # Get metrics
        try:
            metrics_response = requests.get(f"{self.api_url}/metrics", timeout=5)
            if metrics_response.status_code == 200:
                metrics = metrics_response.json()
            else:
                metrics = {}
        except:
            metrics = {}
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_predictions = metrics.get('total_predictions', 0)
            self._render_metric_card("Total Predictions", f"{total_predictions:,}", "predictions")
        
        with col2:
            fraud_detected = metrics.get('fraud_detected', 0)
            self._render_metric_card("Fraud Detected", f"{fraud_detected:,}", "fraud")
        
        with col3:
            avg_latency = metrics.get('avg_latency_ms', 0)
            self._render_metric_card("Avg Latency", f"{avg_latency:.2f}ms", "speed")
        
        with col4:
            accuracy = metrics.get('accuracy', 0.95)
            self._render_metric_card("Accuracy", f"{accuracy:.1%}", "accuracy")
        
        # ML Model Info
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("ML Model Information")
            try:
                model_info = requests.get(f"{self.api_url}/model/info", timeout=5)
                if model_info.status_code == 200:
                    info = model_info.json()
                    models = info.get('models', {})
                    
                    st.write(f"**Best Model:** {models.get('best_model', 'Unknown')}")
                    st.write(f"**Loaded Models:** {', '.join(models.get('loaded_models', []))}")
                    st.write(f"**Feature Count:** {models.get('feature_count', 0)}")
                    
                    # Performance metrics
                    performance = models.get('model_performance', {})
                    if performance:
                        st.write("**Model Performance:**")
                        for model, auc in performance.items():
                            st.write(f"- {model}: AUC = {auc:.4f}")
            except Exception as e:
                st.error(f"Could not load model info: {e}")
        
        with col2:
            st.subheader("System Health")
            try:
                health_response = requests.get(f"{self.api_url}/health", timeout=5)
                if health_response.status_code == 200:
                    health = health_response.json()
                    st.json(health)
            except Exception as e:
                st.error(f"Health check failed: {e}")
    
    def _render_realtime_monitoring(self):
        """Render real-time monitoring"""
        st.subheader("Real-time ML Predictions")
        
        # Test live predictions
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Live Prediction Test")
            
            # Input form
            with st.form("prediction_form"):
                st.write("Test Transaction:")
                
                amount = st.number_input("Amount", min_value=0.0, value=1000.0)
                transaction_type = st.selectbox("Type", ["TRANSFER", "PAYMENT", "CASH_OUT", "CASH_IN", "DEBIT"])
                old_balance = st.number_input("Old Balance Orig", min_value=0.0, value=5000.0)
                new_balance = st.number_input("New Balance Orig", min_value=0.0, value=4000.0)
                
                submit_button = st.form_submit_button("Predict Fraud")
                
                if submit_button:
                    self._make_prediction({
                        'transaction_id': f'LIVE_TEST_{int(time.time())}',
                        'type': transaction_type,
                        'amount': amount,
                        'oldbalanceOrg': old_balance,
                        'newbalanceOrig': new_balance,
                        'nameOrig': 'C123456789',
                        'oldbalanceDest': 1000.0,
                        'newbalanceDest': 2000.0,
                        'nameDest': 'M987654321'
                    })
        
        with col2:
            st.subheader("Recent Predictions")
            
            # Get prediction history
            try:
                history_response = requests.get(f"{self.api_url}/predictions/history", timeout=5)
                if history_response.status_code == 200:
                    history = history_response.json()
                    if isinstance(history, list) and history:
                        df = pd.DataFrame(history[:10])  # Last 10 predictions
                        
                        if not df.empty:
                            # Format for display
                            if 'prediction' in df.columns:
                                df['fraud_prob'] = df['prediction'].apply(lambda x: x.get('fraud_probability', 0))
                                df['is_fraud'] = df['prediction'].apply(lambda x: x.get('is_fraud', False))
                                df['model_used'] = df['prediction'].apply(lambda x: x.get('model_used', 'Unknown'))
                            
                            display_cols = ['transaction_id', 'fraud_prob', 'is_fraud', 'model_used', 'timestamp']
                            available_cols = [col for col in display_cols if col in df.columns]
                            
                            if available_cols:
                                st.dataframe(df[available_cols], use_container_width=True)
                    else:
                        st.info("No prediction history available")
                else:
                    st.error("Could not fetch prediction history")
            except Exception as e:
                st.error(f"Error fetching history: {e}")
    
    def _render_model_performance(self):
        """Render model performance metrics"""
        st.subheader("ML Model Performance")
        
        try:
            model_info = requests.get(f"{self.api_url}/model/info", timeout=5)
            if model_info.status_code == 200:
                info = model_info.json()
                models = info.get('models', {})
                performance = models.get('model_performance', {})
                
                if performance:
                    # Performance comparison
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Model AUC Scores")
                        
                        model_names = list(performance.keys())
                        auc_scores = list(performance.values())
                        
                        fig = go.Figure(data=[
                            go.Bar(x=model_names, y=auc_scores, text=[f"{score:.4f}" for score in auc_scores])
                        ])
                        
                        fig.update_layout(
                            title="Model Performance Comparison",
                            xaxis_title="Model",
                            yaxis_title="AUC Score",
                            yaxis=dict(range=[0, 1])
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.subheader("Feature Information")
                        
                        st.write(f"**Total Features:** {models.get('feature_count', 0)}")
                        st.write(f"**Feature Columns:** {models.get('features', [])}")
                        
                        # Training date
                        training_date = models.get('training_metadata', {}).get('training_date')
                        if training_date:
                            st.write(f"**Training Date:** {training_date}")
                else:
                    st.info("No performance data available")
            else:
                st.error("Could not fetch model information")
        except Exception as e:
            st.error(f"Error loading model performance: {e}")
    
    def _render_test_predictions(self):
        """Render test predictions section"""
        st.subheader("Test ML Predictions")
        
        # Predefined test cases
        test_cases = [
            {
                "name": "Low Risk Transaction",
                "transaction": {
                    'transaction_id': 'TEST_LOW_001',
                    'type': 'PAYMENT',
                    'amount': 50,
                    'oldbalanceOrg': 1000,
                    'newbalanceOrig': 950,
                    'nameOrig': 'C123456789',
                    'oldbalanceDest': 2000,
                    'newbalanceDest': 2050,
                    'nameDest': 'M987654321'
                }
            },
            {
                "name": "High Risk Transaction",
                "transaction": {
                    'transaction_id': 'TEST_HIGH_001',
                    'type': 'TRANSFER',
                    'amount': 25000,
                    'oldbalanceOrg': 50000,
                    'newbalanceOrig': 25000,
                    'nameOrig': 'C987654321',
                    'oldbalanceDest': 10000,
                    'newbalanceDest': 35000,
                    'nameDest': 'M123456789'
                }
            },
            {
                "name": "Medium Risk Transaction",
                "transaction": {
                    'transaction_id': 'TEST_MED_001',
                    'type': 'CASH_OUT',
                    'amount': 5000,
                    'oldbalanceOrg': 8000,
                    'newbalanceOrig': 3000,
                    'nameOrig': 'C555555555',
                    'oldbalanceDest': 2000,
                    'newbalanceDest': 7000,
                    'nameDest': 'D999888888'
                }
            }
        ]
        
        for test_case in test_cases:
            with st.expander(test_case["name"]):
                st.write("**Transaction Details:**")
                st.json(test_case["transaction"])
                
                if st.button(f"Test {test_case['name']}", key=f"test_{test_case['transaction']['transaction_id']}"):
                    self._make_prediction(test_case["transaction"])
    
    def _render_metric_card(self, title, value, icon):
        """Render a metric card"""
        st.markdown(f"""
        <div class="metric-card">
            <h3>{title}</h3>
            <h2>{value}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    def _make_prediction(self, transaction):
        """Make a prediction and display results"""
        try:
            with st.spinner("Making ML prediction..."):
                response = requests.post(f"{self.api_url}/predict/single", json=transaction, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    prediction = result.get('prediction', {})
                    
                    st.success("Prediction completed!")
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Prediction Results:**")
                        st.write(f"- **Is Fraud:** {prediction.get('is_fraud', False)}")
                        st.write(f"- **Fraud Probability:** {prediction.get('fraud_probability', 0):.4f}")
                        st.write(f"- **Confidence:** {prediction.get('confidence', 0):.4f}")
                        st.write(f"- **Model Used:** {prediction.get('model_used', 'Unknown')}")
                    
                    with col2:
                        st.write("**Technical Details:**")
                        st.write(f"- **Transaction ID:** {result.get('transaction_id')}")
                        st.write(f"- **Latency:** {result.get('latency_ms', 0):.2f} ms")
                        st.write(f"- **Model Version:** {prediction.get('model_version', 'Unknown')}")
                        st.write(f"- **Timestamp:** {result.get('timestamp')}")
                    
                    # Show all model predictions if available
                    all_predictions = prediction.get('all_predictions', {})
                    if all_predictions:
                        st.write("**All Model Predictions:**")
                        for model, prob in all_predictions.items():
                            st.write(f"- {model}: {prob:.4f}")
                    
                else:
                    st.error(f"Prediction failed: {response.text}")
                    
        except Exception as e:
            st.error(f"Error making prediction: {e}")
    
    def _test_ml_prediction(self):
        """Test ML prediction with sample data"""
        sample_transaction = {
            'transaction_id': f'SIDEBAR_TEST_{int(time.time())}',
            'type': 'TRANSFER',
            'amount': 10000,
            'oldbalanceOrg': 20000,
            'newbalanceOrig': 10000,
            'nameOrig': 'C123456789',
            'oldbalanceDest': 5000,
            'newbalanceDest': 15000,
            'nameDest': 'M987654321'
        }
        
        self._make_prediction(sample_transaction)

# Main execution
if __name__ == "__main__":
    dashboard = MLFraudDetectionDashboard()
    dashboard.render()
