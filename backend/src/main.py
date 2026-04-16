from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime

# Import our modules
from .prediction_service import PredictionService
try:
    from .ml_prediction_service import predict_fraud_ml, get_ml_model_info
    ML_MODELS_AVAILABLE = True
except ImportError:
    ML_MODELS_AVAILABLE = False
    def predict_fraud_ml(transaction):
        # Fallback to simple prediction
        from .main_simple import predict_fraud_simple
        return predict_fraud_simple(transaction)
    def get_ml_model_info():
        return {'loaded_models': [], 'best_model': 'fallback', 'feature_count': 0}

from .data_processor import DataProcessor
from .model_service import ModelService
from .monitoring import MetricsCollector

# Initialize FastAPI app
app = FastAPI(
    title="Fraud Detection API",
    description="Real-time fraud detection system for financial transactions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
prediction_service = PredictionService()
data_processor = DataProcessor()
model_service = ModelService()
metrics = MetricsCollector()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await model_service.load_models()
    await prediction_service.initialize()
    metrics.start_collection()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await prediction_service.cleanup()
    metrics.stop_collection()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Fraud Detection API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        model_status = await model_service.get_model_status()
        kafka_status = await prediction_service.get_kafka_status()
        redis_status = await prediction_service.get_redis_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "models": model_status,
                "kafka": kafka_status,
                "redis": redis_status
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/model/info")
async def get_model_info():
    """
    Get information about loaded ML models
    """
    try:
        ml_info = get_ml_model_info()
        return {
            "status": "active",
            "models": ml_info,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@app.post("/predict/single")
async def predict_single(transaction: Dict[str, Any]):
    """
    Predict fraud for a single transaction using ML models
    """
    try:
        start_time = time.time()
        
        # Use ML-based prediction
        prediction = predict_fraud_ml(transaction)
        
        latency = (time.time() - start_time) * 1000
        
        return {
            "transaction_id": transaction.get("transaction_id", "unknown"),
            "prediction": prediction,
            "latency_ms": latency,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict/batch")
async def predict_batch(transactions: List[Dict[str, Any]]):
    """
    Predict fraud for multiple transactions
    """
    try:
        start_time = datetime.now()
        
        predictions = []
        for transaction in transactions:
            processed_data = await data_processor.process_transaction(transaction)
            prediction = await prediction_service.predict(processed_data)
            predictions.append({
                "transaction_id": transaction.get("transaction_id"),
                "prediction": prediction
            })
        
        latency = (datetime.now() - start_time).total_seconds() * 1000
        metrics.record_batch_prediction_latency(latency, len(transactions))
        
        return {
            "predictions": predictions,
            "total_transactions": len(transactions),
            "latency_ms": latency,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.post("/predict/file")
async def predict_file(file: UploadFile = File(...)):
    """
    Predict fraud for transactions uploaded via file
    """
    try:
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
            
        if not file.filename.endswith(('.csv', '.json')):
            raise HTTPException(status_code=400, detail="Only CSV and JSON files are supported")
        
        # Read file with better error handling
        try:
            contents = await file.read()
            if not contents:
                raise HTTPException(status_code=400, detail="No file content provided")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
        
        # Parse file content
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(pd.io.common.StringIO(contents.decode('utf-8')))
                transactions = df.to_dict('records')
            else:
                transactions = json.loads(contents.decode('utf-8'))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")
        
        # Process predictions
        result = await predict_batch(transactions)
        
        return {
            "filename": file.filename,
            "file_size": len(contents),
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    try:
        return await metrics.get_all_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@app.get("/model/info")
async def get_model_info():
    """Get model information"""
    try:
        return await model_service.get_model_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@app.post("/model/retrain")
async def trigger_retrain():
    """Trigger model retraining"""
    try:
        job_id = await model_service.trigger_retraining()
        return {
            "message": "Retraining started",
            "job_id": job_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")

@app.get("/predictions/history")
async def get_prediction_history(limit: int = 100):
    """Get prediction history"""
    try:
        history = await prediction_service.get_prediction_history(limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prediction history: {str(e)}")

@app.get("/alerts")
async def get_alerts(limit: int = 10):
    """Get system alerts"""
    try:
        # Get recent predictions to generate alerts
        history = await prediction_service.get_prediction_history(50)
        alerts = []
        
        # Generate alerts based on recent predictions
        fraud_count = 0
        high_value_count = 0
        
        for pred in history:
            if pred.get("prediction", {}).get("is_fraud"):
                fraud_count += 1
                alerts.append({
                    "id": f"fraud_{pred.get('transaction_id')}",
                    "type": "error",
                    "message": f"Fraud detected in transaction {pred.get('transaction_id')}",
                    "timestamp": pred.get("timestamp", datetime.now().isoformat())
                })
            
            # Check for high value transactions
            if pred.get("amount", 0) > 10000:
                high_value_count += 1
                alerts.append({
                    "id": f"high_value_{pred.get('transaction_id')}",
                    "type": "warning",
                    "message": f"High value transaction detected: {pred.get('transaction_id')}",
                    "timestamp": pred.get("timestamp", datetime.now().isoformat())
                })
        
        # Add system performance alerts
        if fraud_count > 5:
            alerts.append({
                "id": "multiple_frauds",
                "type": "error",
                "message": f"Multiple fraud patterns detected: {fraud_count} transactions",
                "timestamp": datetime.now().isoformat()
            })
        
        if high_value_count > 3:
            alerts.append({
                "id": "high_activity",
                "type": "warning",
                "message": f"High value transaction activity: {high_value_count} transactions",
                "timestamp": datetime.now().isoformat()
            })
        
        # Add system status alert
        alerts.append({
            "id": "system_status",
            "type": "info",
            "message": "System performance optimal",
            "timestamp": datetime.now().isoformat()
        })
        
        # Sort by timestamp and limit
        alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return alerts[:limit]
        
    except Exception as e:
        # Fallback alerts
        return [
            {
                "id": "system_error",
                "type": "error",
                "message": f"Error generating alerts: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        ]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
