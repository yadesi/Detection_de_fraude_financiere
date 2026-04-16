# Installation Guide

## Prérequis

- Docker & Docker Compose
- Python 3.9+
- Node.js 16+
- Git

## Installation rapide avec Docker

1. **Cloner le repository**
```bash
git clone <repository-url>
cd fraud-detection-system
```

2. **Lancer tous les services**
```bash
docker-compose up -d
```

3. **Vérifier l'installation**
```bash
# API Health Check
curl http://localhost:8000/health

# Frontend
http://localhost:3000

# Dashboard Streamlit
http://localhost:8501

# Grafana
http://localhost:3000 (admin/admin)

# MLflow
http://localhost:5000
```

## Installation manuelle

### Backend

1. **Créer l'environnement virtuel**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Démarrer les services externes**
```bash
# Kafka & Zookeeper
docker-compose up -d zookeeper kafka

# Redis
docker-compose up -d redis

# MLflow
docker-compose up -d mlflow
```

4. **Lancer l'API**
```bash
cd src
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

1. **Installer les dépendances**
```bash
cd frontend
npm install
```

2. **Lancer l'application**
```bash
npm start
```

### Dashboard Streamlit

1. **Lancer le dashboard**
```bash
cd backend
streamlit run src/dashboard.py --server.port 8501
```

## Configuration

### Variables d'environnement

Créer un fichier `.env` à la racine du projet:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_TRANSACTIONS=transactions
KAFKA_TOPIC_PREDICTIONS=fraud_predictions

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=fraud_detection

# Monitoring
PROMETHEUS_PORT=8001
GRAFANA_PORT=3000
```

### Configuration des datasets

1. **Télécharger PaySim dataset**
```bash
mkdir -p data/raw
cd data/raw
wget https://storage.googleapis.com/kaggle-datasets/123456/paysim1/PS_20174392719_1491204439457_log.csv
```

2. **Télécharger Credit Card Fraud dataset**
```bash
wget https://storage.googleapis.com/kaggle-datasets/123456/creditcardfraud/creditcard.csv
```

## Vérification de l'installation

### 1. Test de l'API

```bash
# Health check
curl http://localhost:8000/health

# Test prédiction
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
```

### 2. Test du frontend

Accéder à http://localhost:3000 et vérifier que:
- Le dashboard s'affiche
- Les métriques système sont visibles
- L'upload de fichiers fonctionne

### 3. Test des services de monitoring

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **MLflow**: http://localhost:5000

## Dépannage

### Problèmes courants

1. **Port déjà utilisé**
```bash
# Vérifier les ports utilisés
netstat -tulpn | grep :8000
# Tuer le processus
kill -9 <PID>
```

2. **Kafka ne démarre pas**
```bash
# Nettoyer les données Kafka
docker-compose down -v
docker-compose up -d zookeeper kafka
```

3. **Redis connection refusée**
```bash
# Vérifier Redis
docker-compose logs redis
# Redémarrer Redis
docker-compose restart redis
```

4. **MLflow inaccessible**
```bash
# Vérifier MLflow
docker-compose logs mlflow
# Recréer le conteneur MLflow
docker-compose up -d --force-recreate mlflow
```

### Logs et monitoring

- **API logs**: `docker-compose logs backend`
- **Frontend logs**: `docker-compose logs frontend`
- **Kafka logs**: `docker-compose logs kafka`
- **Redis logs**: `docker-compose logs redis`
- **MLflow logs**: `docker-compose logs mlflow`

### Performance

1. **Optimisation Docker**
```bash
# Allouer plus de mémoire à Docker
# Dans Docker Desktop: Settings > Resources > Memory (4GB+ recommandé)
```

2. **Optimisation Spark**
```bash
# Configurer Spark dans src/main.py
spark.conf.set("spark.executor.memory", "2g")
spark.conf.set("spark.driver.memory", "1g")
```

## Mise à jour

### Mettre à jour les dépendances

```bash
# Backend
cd backend
pip install --upgrade -r requirements.txt

# Frontend
cd frontend
npm update
```

### Mettre à jour les modèles

```bash
# Retrigger l'entraînement des modèles
curl -X POST http://localhost:8000/model/retrain
```

## Sécurité

### Configuration SSL

Pour la production, configurer SSL:

```bash
# Générer certificats
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# Configurer nginx ou utiliser HTTPS directement dans FastAPI
```

### Variables sensibles

Utiliser Docker secrets ou un gestionnaire de secrets pour:
- Clés API
- Credentials base de données
- Certificats SSL

## Support

Pour toute question ou problème:
1. Vérifier les logs Docker
2. Consulter la documentation technique
3. Créer une issue sur le repository
