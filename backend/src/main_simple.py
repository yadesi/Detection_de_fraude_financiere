"""
Simplified FastAPI application for testing
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import random
import time
import uuid
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="Fraud Detection API - Simple Version",
    description="Simplified API for testing purposes",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Transaction(BaseModel):
    transaction_id: str
    type: str
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float
    nameOrig: str
    nameDest: str
    timestamp: Optional[str] = None

class PredictionResult(BaseModel):
    is_fraud: bool
    fraud_probability: float
    confidence: float
    model_version: str
    prediction_timestamp: str

class PredictionResponse(BaseModel):
    transaction_id: str
    prediction: PredictionResult
    latency_ms: float
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, Any]

class MetricsResponse(BaseModel):
    prediction_stats: Dict[str, Any]
    performance: Dict[str, Any]
    system: Dict[str, Any]
    services: Dict[str, Any]
    recent_alerts: List[Dict[str, Any]]

# Simple mock model for testing
def predict_fraud_simple(transaction: Transaction) -> PredictionResult:
    """Simple mock prediction for testing"""
    start_time = time.time()
    
    # Simple rule-based logic for demo
    fraud_indicators = 0
    
    # High amount indicator
    if transaction.amount > 10000:
        fraud_indicators += 1
    
    # Balance mismatch indicator
    expected_new_balance = transaction.oldbalanceOrg - transaction.amount
    if abs(transaction.newbalanceOrig - expected_new_balance) > 100:
        fraud_indicators += 1
    
    # Risky transaction types
    if transaction.type in ['TRANSFER', 'CASH-OUT']:
        fraud_indicators += 1
    
    # Calculate probability based on indicators
    base_probability = 0.05  # 5% base fraud rate
    indicator_weight = 0.25  # Each indicator adds 25%
    fraud_probability = min(0.95, base_probability + (fraud_indicators * indicator_weight))
    
    # Add some randomness for testing
    fraud_probability += random.uniform(-0.1, 0.1)
    fraud_probability = max(0.0, min(1.0, fraud_probability))
    
    is_fraud = fraud_probability > 0.5
    confidence = max(0.5, 1.0 - abs(fraud_probability - 0.5))
    
    processing_time = time.time() - start_time
    
    return PredictionResult(
        is_fraud=is_fraud,
        fraud_probability=fraud_probability,
        confidence=confidence,
        model_version="simple_demo_v1.0",
        prediction_timestamp=datetime.now().isoformat()
    )

# API endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Fraud Detection API - Simple Version",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        services={
            "models": {
                "simple_model": {"loaded": True, "type": "RuleBased"}
            },
            "kafka": {"status": "simulated"},
            "redis": {"status": "simulated"}
        }
    )

@app.post("/predict/single", response_model=PredictionResponse)
async def predict_single(transaction: Transaction):
    """Predict fraud for a single transaction"""
    start_time = time.time()
    
    # Validate transaction
    if not transaction.transaction_id:
        transaction.transaction_id = f"TXN_{uuid.uuid4().hex[:8]}"
    
    # Make prediction
    prediction = predict_fraud_simple(transaction)
    
    # Calculate latency
    latency_ms = (time.time() - start_time) * 1000
    
    return PredictionResponse(
        transaction_id=transaction.transaction_id,
        prediction=prediction,
        latency_ms=latency_ms,
        timestamp=datetime.now().isoformat()
    )

@app.post("/predict/batch")
async def predict_batch(transactions: List[Transaction]):
    """Predict fraud for multiple transactions"""
    start_time = time.time()
    
    predictions = []
    for transaction in transactions:
        if not transaction.transaction_id:
            transaction.transaction_id = f"TXN_{uuid.uuid4().hex[:8]}"
        
        prediction = predict_fraud_simple(transaction)
        predictions.append({
            "transaction_id": transaction.transaction_id,
            "prediction": prediction.dict()
        })
    
    latency_ms = (time.time() - start_time) * 1000
    
    return {
        "predictions": predictions,
        "total_transactions": len(transactions),
        "latency_ms": latency_ms,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/predict/file")
async def predict_file(file_content: str = None):
    """Predict fraud from uploaded file (simplified)"""
    if not file_content:
        raise HTTPException(status_code=400, detail="No file content provided")
    
    # Simple CSV parsing for demo
    lines = file_content.strip().split('\n')
    if len(lines) < 2:
        raise HTTPException(status_code=400, detail="Invalid CSV format")
    
    headers = lines[0].split(',')
    transactions = []
    
    for line in lines[1:]:
        values = line.split(',')
        if len(values) >= len(headers):
            transaction_data = dict(zip(headers, values))
            
            # Convert to proper types
            try:
                transaction = Transaction(
                    transaction_id=transaction_data.get('transaction_id', f"FILE_{uuid.uuid4().hex[:8]}"),
                    type=transaction_data.get('type', 'TRANSFER'),
                    amount=float(transaction_data.get('amount', 0)),
                    oldbalanceOrg=float(transaction_data.get('oldbalanceOrg', 0)),
                    newbalanceOrig=float(transaction_data.get('newbalanceOrig', 0)),
                    oldbalanceDest=float(transaction_data.get('oldbalanceDest', 0)),
                    newbalanceDest=float(transaction_data.get('newbalanceDest', 0)),
                    nameOrig=transaction_data.get('nameOrig', 'C123456789'),
                    nameDest=transaction_data.get('nameDest', 'M987654321')
                )
                transactions.append(transaction)
            except (ValueError, KeyError):
                continue
    
    if not transactions:
        raise HTTPException(status_code=400, detail="No valid transactions found")
    
    # Process batch
    start_time = time.time()
    predictions = []
    for transaction in transactions:
        prediction = predict_fraud_simple(transaction)
        predictions.append({
            "transaction_id": transaction.transaction_id,
            "prediction": prediction.dict()
        })
    
    latency_ms = (time.time() - start_time) * 1000
    
    return {
        "filename": "uploaded_file.csv",
        "file_size": len(file_content),
        "predictions": predictions,
        "total_transactions": len(transactions),
        "latency_ms": latency_ms,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics"""
    return MetricsResponse(
        prediction_stats={
            "total_predictions": random.randint(1000, 5000),
            "fraud_predictions": random.randint(50, 200),
            "legitimate_predictions": random.randint(950, 4800),
            "fraud_rate": round(random.uniform(0.02, 0.08), 3)
        },
        performance={
            "avg_prediction_latency_ms": round(random.uniform(20, 80), 2),
            "error_rate": round(random.uniform(0.001, 0.01), 4),
            "fraud_rate": round(random.uniform(0.02, 0.08), 3),
            "predictions_per_second": round(random.uniform(50, 150), 1)
        },
        system={
            "cpu_percent": round(random.uniform(20, 60), 1),
            "memory_percent": round(random.uniform(30, 70), 1),
            "memory_available_gb": round(random.uniform(4, 12), 1),
            "disk_percent": round(random.uniform(40, 80), 1),
            "disk_free_gb": round(random.uniform(20, 100), 1)
        },
        services={
            "redis": {"status": "simulated", "latency_ms": round(random.uniform(1, 5), 2)},
            "kafka": {"status": "simulated", "brokers": 1},
            "models": {"status": "loaded", "models": 1}
        },
        recent_alerts=[
            {
                "id": "alert_001",
                "type": "info",
                "message": "System operating normally",
                "timestamp": datetime.now().isoformat()
            }
        ]
    )

@app.get("/model/info")
async def get_model_info():
    """Get model information"""
    return {
        "models": {
            "simple_model": {"loaded": True, "type": "RuleBased"}
        },
        "scalers_loaded": False,
        "training_jobs": [],
        "last_updated": datetime.now().isoformat()
    }

@app.post("/model/retrain")
async def trigger_retraining():
    """Trigger model retraining (simulated)"""
    job_id = f"retrain_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return {
        "message": "Retraining started (simulated)",
        "job_id": job_id,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/predictions/history")
async def get_prediction_history(limit: int = 100):
    """Get prediction history (simulated)"""
    history = []
    for i in range(min(limit, 50)):
        history.append({
            "transaction_id": f"HIST_TXN_{i:03d}",
            "prediction": {
                "is_fraud": random.choice([True, False]),
                "fraud_probability": round(random.uniform(0, 1), 3),
                "confidence": round(random.uniform(0.5, 1.0), 3)
            },
            "timestamp": datetime.now().isoformat()
        })
    
    return history

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
