# API Documentation - Fraud Detection System

## Overview

L'API REST du système de détection de fraude fournit des endpoints pour la prédiction en temps réel, le monitoring et la gestion des modèles.

**Base URL**: `http://localhost:8000`

**Authentication**: Aucune (pour le développement)

## Endpoints

### Health & Status

#### GET /health

Vérifie l'état de santé du système et des services connectés.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "models": {
      "isolation_forest": {"loaded": true, "type": "IsolationForest"},
      "xgboost": {"loaded": true, "type": "XGBClassifier"}
    },
    "kafka": {"status": "connected"},
    "redis": {"status": "connected"}
  }
}
```

#### GET /

Endpoint racine avec informations sur l'API.

**Response**:
```json
{
  "message": "Fraud Detection API",
  "version": "1.0.0"
}
```

### Predictions

#### POST /predict/single

Prédit la fraude pour une seule transaction.

**Request Body**:
```json
{
  "transaction_id": "TXN123456",
  "type": "TRANSFER",
  "amount": 15000.0,
  "oldbalanceOrg": 50000.0,
  "newbalanceOrig": 35000.0,
  "oldbalanceDest": 20000.0,
  "newbalanceDest": 35000.0,
  "nameOrig": "C123456789",
  "nameDest": "M987654321",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Response**:
```json
{
  "transaction_id": "TXN123456",
  "prediction": {
    "is_fraud": false,
    "fraud_probability": 0.15,
    "confidence": 0.85,
    "model_version": "1.0.0",
    "prediction_timestamp": "2024-01-01T12:00:00Z"
  },
  "latency_ms": 45.2,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### POST /predict/batch

Prédit la fraude pour plusieurs transactions.

**Request Body**:
```json
[
  {
    "transaction_id": "TXN001",
    "type": "TRANSFER",
    "amount": 1000.0,
    "oldbalanceOrg": 5000.0,
    "newbalanceOrig": 4000.0,
    "oldbalanceDest": 2000.0,
    "newbalanceDest": 3000.0,
    "nameOrig": "C123456789",
    "nameDest": "M987654321"
  },
  {
    "transaction_id": "TXN002",
    "type": "PAYMENT",
    "amount": 500.0,
    "oldbalanceOrg": 2000.0,
    "newbalanceOrig": 1500.0,
    "oldbalanceDest": 1000.0,
    "newbalanceDest": 1500.0,
    "nameOrig": "C234567890",
    "nameDest": "M123456789"
  }
]
```

**Response**:
```json
{
  "predictions": [
    {
      "transaction_id": "TXN001",
      "prediction": {
        "is_fraud": false,
        "fraud_probability": 0.12,
        "confidence": 0.88
      }
    },
    {
      "transaction_id": "TXN002",
      "prediction": {
        "is_fraud": false,
        "fraud_probability": 0.08,
        "confidence": 0.92
      }
    }
  ],
  "total_transactions": 2,
  "latency_ms": 120.5,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### POST /predict/file

Prédit la fraude pour les transactions à partir d'un fichier uploadé.

**Request**: `multipart/form-data`
- `file`: Fichier CSV ou JSON

**CSV Format**:
```csv
transaction_id,type,amount,oldbalanceOrg,newbalanceOrig,oldbalanceDest,newbalanceDest,nameOrig,nameDest
TXN001,TRANSFER,1000,5000,4000,2000,3000,C123456789,M987654321
TXN002,PAYMENT,500,2000,1500,1000,1500,C234567890,M123456789
```

**JSON Format**:
```json
[
  {
    "transaction_id": "TXN001",
    "type": "TRANSFER",
    "amount": 1000,
    "oldbalanceOrg": 5000,
    "newbalanceOrig": 4000,
    "oldbalanceDest": 2000,
    "newbalanceDest": 3000,
    "nameOrig": "C123456789",
    "nameDest": "M987654321"
  }
]
```

**Response**:
```json
{
  "filename": "transactions.csv",
  "file_size": 1024,
  "predictions": [...],
  "total_transactions": 100,
  "latency_ms": 2500.0,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Metrics & Monitoring

#### GET /metrics

Récupère les métriques système et de performance.

**Response**:
```json
{
  "prediction_stats": {
    "total_predictions": 10000,
    "fraud_predictions": 150,
    "legitimate_predictions": 9850,
    "fraud_rate": 0.015
  },
  "performance": {
    "avg_prediction_latency_ms": 45.2,
    "error_rate": 0.001,
    "fraud_rate": 0.015,
    "predictions_per_second": 125.5
  },
  "system": {
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "memory_available_gb": 8.5,
    "disk_percent": 60.1,
    "disk_free_gb": 40.2
  },
  "services": {
    "redis": {"status": "connected", "latency_ms": 2.1},
    "kafka": {"status": "connected", "brokers": 1},
    "models": {"status": "loaded", "models": 3}
  },
  "recent_alerts": [...]
}
```

#### GET /predictions/history

Récupère l'historique des prédictions récentes.

**Query Parameters**:
- `limit` (optional): Nombre de prédictions à retourner (défaut: 100)

**Response**:
```json
[
  {
    "transaction_id": "TXN001",
    "prediction": {
      "is_fraud": false,
      "fraud_probability": 0.12,
      "confidence": 0.88
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
]
```

### Model Management

#### GET /model/info

Récupère des informations détaillées sur les modèles chargés.

**Response**:
```json
{
  "models": {
    "isolation_forest": {"loaded": true, "type": "IsolationForest"},
    "xgboost": {"loaded": true, "type": "XGBClassifier"},
    "ensemble": {"loaded": true, "type": "EnsembleModel"}
  },
  "scalers_loaded": true,
  "training_jobs": ["job_123"],
  "last_updated": "2024-01-01T12:00:00Z"
}
```

#### POST /model/retrain

Déclenche le réentraînement des modèles.

**Response**:
```json
{
  "message": "Retraining started",
  "job_id": "retrain_job_20240101_120000",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Schéma de données

### Transaction Schema

| Champ | Type | Requis | Description |
|-------|------|---------|-------------|
| transaction_id | string | Oui | Identifiant unique de la transaction |
| type | string | Oui | Type de transaction (CASH-IN, CASH-OUT, DEBIT, PAYMENT, TRANSFER) |
| amount | float | Oui | Montant de la transaction |
| oldbalanceOrg | float | Oui | Solde du compte origine avant transaction |
| newbalanceOrig | float | Oui | Solde du compte origine après transaction |
| oldbalanceDest | float | Oui | Solde du compte destination avant transaction |
| newbalanceDest | float | Oui | Solde du compte destination après transaction |
| nameOrig | string | Oui | Identifiant du compte origine |
| nameDest | string | Oui | Identifiant du compte destination |
| timestamp | string | Non | Timestamp ISO 8601 |

### Prediction Response Schema

| Champ | Type | Description |
|-------|------|-------------|
| is_fraud | boolean | True si la transaction est frauduleuse |
| fraud_probability | float | Probabilité de fraude (0-1) |
| confidence | float | Confiance de la prédiction (0-1) |
| model_version | string | Version du modèle utilisé |
| prediction_timestamp | string | Timestamp de la prédiction |

## Codes d'erreur

| Code | Description |
|------|-------------|
| 200 | Succès |
| 400 | Requête invalide |
| 422 | Validation échouée |
| 500 | Erreur interne du serveur |
| 503 | Service indisponible |

## Exemples d'utilisation

### Python

```python
import requests

# Prédiction simple
transaction = {
    "transaction_id": "TEST_001",
    "type": "TRANSFER",
    "amount": 1000,
    "oldbalanceOrg": 5000,
    "newbalanceOrig": 4000,
    "oldbalanceDest": 2000,
    "newbalanceDest": 3000,
    "nameOrig": "C123456789",
    "nameDest": "M987654321"
}

response = requests.post(
    "http://localhost:8000/predict/single",
    json=transaction
)

if response.status_code == 200:
    result = response.json()
    print(f"Fraud probability: {result['prediction']['fraud_probability']}")
    print(f"Is fraud: {result['prediction']['is_fraud']}")
```

### JavaScript

```javascript
// Prédiction avec fetch
const transaction = {
    transaction_id: "TEST_001",
    type: "TRANSFER",
    amount: 1000,
    oldbalanceOrg: 5000,
    newbalanceOrig: 4000,
    oldbalanceDest: 2000,
    newbalanceDest: 3000,
    nameOrig: "C123456789",
    nameDest: "M987654321"
};

fetch('http://localhost:8000/predict/single', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(transaction)
})
.then(response => response.json())
.then(data => {
    console.log('Fraud probability:', data.prediction.fraud_probability);
    console.log('Is fraud:', data.prediction.is_fraud);
});
```

### cURL

```bash
# Prédiction simple
curl -X POST http://localhost:8000/predict/single \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TEST_001",
    "type": "TRANSFER",
    "amount": 1000,
    "oldbalanceOrg": 5000,
    "newbalanceOrig": 4000,
    "oldbalanceDest": 2000,
    "newbalanceDest": 3000,
    "nameOrig": "C123456789",
    "nameDest": "M987654321"
  }'

# Upload de fichier
curl -X POST http://localhost:8000/predict/file \
  -F "file=@transactions.csv"
```

## Performance

### Objectifs de performance

- **Latence**: <100ms par prédiction
- **Débit**: >100 prédictions/seconde
- **Disponibilité**: >99.9%

### Monitoring

Les métriques de performance sont disponibles via:
- Endpoint `/metrics`
- Prometheus (port 8001)
- Grafana dashboard

## Rate Limiting

Pour la production, implémenter un rate limiting:
- 1000 requêtes/minute par IP
- 10000 requêtes/minute par API key

## Sécurité

### HTTPS

Configurer SSL/TLS pour la production:

```python
# Dans main.py
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem"
    )
```

### Authentication

Implémenter JWT ou OAuth2 pour la production.

## Support

Pour toute question sur l'API:
1. Consulter cette documentation
2. Vérifier les logs de l'application
3. Contacter l'équipe de développement
