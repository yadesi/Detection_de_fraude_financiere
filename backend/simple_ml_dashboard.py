import streamlit as st
import pandas as pd
import requests
import json
import time

# Configuration
st.set_page_config(
    page_title="Fraud Detection Dashboard - ML Models",
    page_icon=":shield:",
    layout="wide"
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
        margin-bottom: 1rem;
    }
    .model-info {
        background: #e8f5e8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class MLFraudDetectionDashboard:
    def __init__(self):
        self.api_url = "http://backend:8000"
        
    def render(self):
        self._render_header()
        self._render_sidebar()
        self._render_main_content()
        
    def _render_header(self):
        st.markdown('<h1 class="main-header">Fraud Detection Dashboard - ML Models</h1>', unsafe_allow_html=True)
        
        # Show ML model info
        try:
            model_info = requests.get(f"{self.api_url}/model/info", timeout=5)
            if model_info.status_code == 200:
                info = model_info.json()
                models = info.get('models', {})
                
                loaded_models = models.get('loaded_models', [])
                best_model = models.get('best_model', 'Unknown')
                feature_count = models.get('feature_count', 0)
                performance = models.get('model_performance', {})
                
                st.markdown(f"""
                <div class="model-info">
                    <h3>Active ML Models: {loaded_models}</h3>
                    <p>Best Model: <strong>{best_model}</strong></p>
                    <p>Features: {feature_count} | Model Performance: {performance}</p>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Could not load model info: {e}")
    
    def _render_sidebar(self):
        st.sidebar.title("Dashboard Controls")
        
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
        # Create tabs
        tab1, tab2, tab3 = st.tabs([
            "ML Overview", "Real-time Monitoring", "Test Predictions"
        ])
        
        with tab1:
            self._render_ml_overview()
        
        with tab2:
            self._render_realtime_monitoring()
        
        with tab3:
            self._render_test_predictions()
    
    def _render_ml_overview(self):
        st.subheader("ML Model Overview")
        
        try:
            model_info = requests.get(f"{self.api_url}/model/info", timeout=5)
            if model_info.status_code == 200:
                info = model_info.json()
                models = info.get('models', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("ML Model Information")
                    st.write(f"**Best Model:** {models.get('best_model', 'Unknown')}")
                    
                    loaded_models = models.get('loaded_models', [])
                    st.write(f"**Loaded Models:** {loaded_models}")
                    
                    st.write(f"**Feature Count:** {models.get('feature_count', 0)}")
                    
                    performance = models.get('model_performance', {})
                    if performance:
                        st.write("**Model Performance:**")
                        for model, auc in performance.items():
                            st.write(f"- {model}: AUC = {auc:.4f}")
                
                with col2:
                    st.subheader("System Health")
                    try:
                        health_response = requests.get(f"{self.api_url}/health", timeout=5)
                        if health_response.status_code == 200:
                            health = health_response.json()
                            st.json(health)
                    except Exception as e:
                        st.error(f"Health check failed: {e}")
        except Exception as e:
            st.error(f"Error loading model info: {e}")
    
    def _render_realtime_monitoring(self):
        st.subheader("Real-time ML Predictions")
        
        # Input form
        with st.form("prediction_form"):
            st.write("Test Transaction:")
            
            amount = st.number_input("Amount", min_value=0.0, value=1000.0)
            transaction_type = st.selectbox("Type", ["TRANSFER", "PAYMENT", "CASH_OUT", "CASH_IN", "DEBIT"])
            old_balance = st.number_input("Old Balance Orig", min_value=0.0, value=5000.0)
            new_balance = st.number_input("New Balance Orig", min_value=0.0, value=4000.0)
            
            submit_button = st.form_submit_button("Predict Fraud")
            
            if submit_button:
                transaction = {
                    'transaction_id': f'LIVE_TEST_{int(time.time())}',
                    'type': transaction_type,
                    'amount': amount,
                    'oldbalanceOrg': old_balance,
                    'newbalanceOrig': new_balance,
                    'nameOrig': 'C123456789',
                    'oldbalanceDest': 1000.0,
                    'newbalanceDest': 2000.0,
                    'nameDest': 'M987654321'
                }
                self._make_prediction(transaction)
    
    def _render_test_predictions(self):
        st.subheader("Test ML Predictions")
        
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
                
                button_key = f"test_{test_case['transaction']['transaction_id']}"
                if st.button(f"Test {test_case['name']}", key=button_key):
                    self._make_prediction(test_case["transaction"])
    
    def _make_prediction(self, transaction):
        try:
            with st.spinner("Making ML prediction..."):
                response = requests.post(f"{self.api_url}/predict/single", json=transaction, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    prediction = result.get('prediction', {})
                    
                    st.success("Prediction completed!")
                    
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
