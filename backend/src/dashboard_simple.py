import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
import time

# Configuration
st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .status-good {
        color: #2ecc71;
        font-weight: bold;
    }
    .status-warning {
        color: #f39c12;
        font-weight: bold;
    }
    .status-error {
        color: #e74c3c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def get_api_data(endpoint):
    """Get data from API with error handling"""
    import os
    api_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
    try:
        response = requests.get(f"{api_url}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None

def create_mock_data():
    """Create mock data when API is not available"""
    return {
        "prediction_stats": {
            "total_predictions": 15420,
            "fraud_predictions": 768,
            "legitimate_predictions": 14652,
            "fraud_rate": 0.0498
        },
        "performance": {
            "avg_prediction_latency_ms": 45.2,
            "error_rate": 0.002,
            "predictions_per_second": 156.8
        },
        "system": {
            "cpu_percent": 42.3,
            "memory_percent": 67.8,
            "memory_available_gb": 8.2,
            "disk_percent": 34.1
        },
        "recent_alerts": [
            {
                "id": "alert_001",
                "type": "warning",
                "message": "High value transaction detected",
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": "alert_002",
                "type": "info",
                "message": "System performance optimal",
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": "alert_003",
                "type": "error",
                "message": "Multiple fraud patterns detected",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }

def create_sample_predictions():
    """Create sample prediction data"""
    predictions = []
    for i in range(10):
        is_fraud = np.random.random() < 0.1
        predictions.append({
            "transaction_id": f"TXN_{i:03d}",
            "prediction": {
                "is_fraud": is_fraud,
                "fraud_probability": np.random.random(),
                "confidence": np.random.uniform(0.7, 0.95)
            },
            "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat()
        })
    return predictions

def create_chart_data():
    """Create data for charts"""
    # Time series data
    hours = list(range(24))
    time_data = []
    for hour in hours:
        time_data.append({
            "hour": f"{hour:02d}:00",
            "total": np.random.randint(50, 150),
            "fraud": np.random.randint(1, 15),
            "latency": np.random.uniform(30, 80)
        })
    
    # Transaction type data
    type_data = [
        {"type": "CASH-IN", "count": 450, "fraud": 9},
        {"type": "CASH-OUT", "count": 380, "fraud": 38},
        {"type": "TRANSFER", "count": 220, "fraud": 22},
        {"type": "PAYMENT", "count": 680, "fraud": 7},
        {"type": "DEBIT", "count": 180, "fraud": 2}
    ]
    
    return time_data, type_data

# Main Dashboard
def main():
    # Header
    st.markdown('<h1 class="main-header">:shield: Fraud Detection Dashboard</h1>', unsafe_allow_html=True)
    
    # Debug information
    import os
    api_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
    st.markdown(f"### 🔍 Debug Info")
    st.write(f"**Backend URL:** {api_url}")
    
    # Check API connection
    st.write("**Testing /health endpoint...**")
    api_status = get_api_data("/health")
    if api_status:
        st.success(f"✅ /health endpoint working: {api_status}")
        st.write("**Testing /metrics endpoint...**")
        data = get_api_data("/metrics")
        if data:
            st.success("✅ /metrics endpoint working")
            st.success("API Connection: Connected")
        else:
            st.error("❌ /metrics endpoint failed")
            data = create_mock_data()
            st.warning("Using mock data (metrics endpoint unavailable)")
    else:
        st.error("❌ /health endpoint failed")
        st.error("API Connection: Disconnected - Using mock data")
        data = create_mock_data()
    
    # Refresh button
    if st.button("Refresh Data", type="primary"):
        st.rerun()
    
    # Key Metrics
    st.markdown("## :bar_chart: Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_pred = data.get("prediction_stats", {}).get("total_predictions", 0)
        st.markdown(f"""
        <div class="metric-card">
            <h3>{total_pred:,}</h3>
            <p>Total Predictions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        fraud_rate = data.get("prediction_stats", {}).get("fraud_rate", 0) * 100
        st.markdown(f"""
        <div class="metric-card">
            <h3>{fraud_rate:.2f}%</h3>
            <p>Fraud Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        latency = data.get("performance", {}).get("avg_prediction_latency_ms", 0)
        st.markdown(f"""
        <div class="metric-card">
            <h3>{latency:.1f}ms</h3>
            <p>Avg Latency</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        throughput = data.get("performance", {}).get("predictions_per_second", 0)
        st.markdown(f"""
        <div class="metric-card">
            <h3>{throughput:.1f}</h3>
            <p>Predictions/sec</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts Section
    st.markdown("## :chart_with_upwards_trend: Analytics")
    
    # Get chart data
    time_data, type_data = create_chart_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Hourly Transaction Volume")
        df_time = pd.DataFrame(time_data)
        
        # Create bar chart using st.bar_chart
        st.bar_chart(df_time.set_index("hour")[["total", "fraud"]])
        
    with col2:
        st.markdown("### Transaction Types")
        df_type = pd.DataFrame(type_data)
        
        # Create bar chart for transaction types
        st.bar_chart(df_type.set_index("type")[["count", "fraud"]])
    
    # Performance Metrics
    st.markdown("## :gear: System Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### System Resources")
        cpu = data.get("system", {}).get("cpu_percent", 0)
        memory = data.get("system", {}).get("memory_percent", 0)
        disk = data.get("system", {}).get("disk_percent", 0)
        
        st.metric("CPU Usage", f"{cpu:.1f}%")
        st.metric("Memory Usage", f"{memory:.1f}%")
        st.metric("Disk Usage", f"{disk:.1f}%")
        
        # Progress bars
        st.progress(cpu / 100, f"CPU: {cpu:.1f}%")
        st.progress(memory / 100, f"Memory: {memory:.1f}%")
        st.progress(disk / 100, f"Disk: {disk:.1f}%")
    
    with col2:
        st.markdown("### Performance Metrics")
        error_rate = data.get("performance", {}).get("error_rate", 0) * 100
        latency = data.get("performance", {}).get("avg_prediction_latency_ms", 0)
        throughput = data.get("performance", {}).get("predictions_per_second", 0)
        
        st.metric("Error Rate", f"{error_rate:.3f}%")
        st.metric("Avg Latency", f"{latency:.1f}ms")
        st.metric("Throughput", f"{throughput:.1f}/sec")
        
        # Status indicators
        if error_rate < 1:
            st.markdown('<p class="status-good">Error Rate: Good</p>', unsafe_allow_html=True)
        elif error_rate < 5:
            st.markdown('<p class="status-warning">Error Rate: Warning</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-error">Error Rate: Critical</p>', unsafe_allow_html=True)
        
        if latency < 100:
            st.markdown('<p class="status-good">Latency: Good</p>', unsafe_allow_html=True)
        elif latency < 200:
            st.markdown('<p class="status-warning">Latency: Warning</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-error">Latency: Critical</p>', unsafe_allow_html=True)
    
    # Recent Predictions
    st.markdown("## :list: Recent Predictions")
    
    predictions = get_api_data("/predictions/history?limit=10")
    if not predictions:
        predictions = create_sample_predictions()
        st.info("Using sample prediction data")
    
    if predictions:
        df_pred = pd.DataFrame(predictions)
        
        # Format the data for display
        display_data = []
        for pred in predictions:
            display_data.append({
                "Transaction ID": pred.get("transaction_id"),
                "Is Fraud": "Yes" if pred.get("prediction", {}).get("is_fraud") else "No",
                "Fraud Probability": f"{pred.get('prediction', {}).get('fraud_probability', 0):.3f}",
                "Confidence": f"{pred.get('prediction', {}).get('confidence', 0):.3f}",
                "Time": pred.get("timestamp", "")[:19]
            })
        
        df_display = pd.DataFrame(display_data)
        st.dataframe(df_display, use_container_width=True)
    
    # Recent Alerts
    st.markdown("## :bell: Recent Alerts")
    
    alerts = data.get("recent_alerts", [])
    if alerts:
        for alert in alerts:
            alert_type = alert.get("type", "info")
            icon = "warning" if alert_type == "warning" else "error" if alert_type == "error" else "info"
            
            if alert_type == "error":
                st.error(f"**{alert.get('message', 'Unknown alert')}**\n{alert.get('timestamp', '')}")
            elif alert_type == "warning":
                st.warning(f"**{alert.get('message', 'Unknown alert')}**\n{alert.get('timestamp', '')}")
            else:
                st.info(f"**{alert.get('message', 'Unknown alert')}**\n{alert.get('timestamp', '')}")
    else:
        st.info("No recent alerts")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Fraud Detection Dashboard - Real-time Monitoring | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
