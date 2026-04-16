# Système de Détection de Fraude Financière en Temps Réel

## Architecture du Projet

Ce projet implémente un système complet de détection de fraude financière en temps réel avec les composants suivants :

### Stack Technique
- **Streaming**: PySpark Structured Streaming + Kafka
- **ML**: Isolation Forest, XGBoost (MLlib + scikit-learn)
- **Cache**: Redis pour features temps réel
- **MLOps**: MLflow tracking + model registry
- **Monitoring**: Grafana + Prometheus
- **API**: FastAPI
- **Dashboard**: Streamlit
- **Frontend**: React
- **Tests**: pytest + locust

### Structure des Répertoires

```
fraud-detection-system/
|
|-- backend/                 # Services backend
|   |-- src/                # Code source principal
|   |-- models/             # Modèles ML entraînés
|   |-- utils/              # Utilitaires et helpers
|   |-- tests/              # Tests backend
|   |-- config/             # Configuration
|
|-- frontend/               # Interface utilisateur React
|   |-- src/                # Code source React
|   |-- public/             # Assets publics
|   |-- components/         # Composants React
|
|-- data/                   # Datasets et données
|   |-- raw/                # Données brutes
|   |-- processed/          # Données traitées
|
|-- docker/                 # Configurations Docker
|   |-- kafka/              # Configuration Kafka
|   |-- redis/              # Configuration Redis
|   -- monitoring/          # Config monitoring
|
|-- monitoring/             # Configuration monitoring
|   |-- grafana/            # Dashboards Grafana
|   |-- prometheus/         # Configuration Prometheus
|
|-- docs/                   # Documentation
|-- tests/                  # Tests d'intégration
```

## Objectifs de Performance

- **Précision**: >95% détection de fraude
- **Rappel**: >90% 
- **Latence**: <100ms par transaction
- **Débit**: 100K transactions/seconde
- **Réduction faux positifs**: 30%

## Datasets

1. **PaySim** - Synthetic Financial Fraud (186 MB)
   - 6.3M transactions sur 30 jours
   - 5 types de transactions
   - Source: Kaggle

2. **Credit Card Fraud ULB** (69 MB)
   - 284K transactions
   - Source: Kaggle

## Installation et Démarrage

Voir `docs/installation.md` pour les instructions détaillées.

## API Documentation

L'API documentation est disponible via OpenAPI une fois le service démarré.

## Monitoring

Accès au monitoring:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
