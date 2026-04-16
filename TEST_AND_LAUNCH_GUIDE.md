# Guide Complet de Test et Lancement

## Étape 1: Vérification Prérequis

### 1.1 Vérifier Docker
```bash
# Vérifier que Docker est installé
docker --version
docker-compose --version

# Si Docker n'est pas installé:
# 1. Télécharger Docker Desktop depuis https://www.docker.com/products/docker-desktop
# 2. Installer et démarrer Docker Desktop
# 3. Vérifier l'installation avec les commandes ci-dessus
```

### 1.2 Vérifier Python (optionnel si vous voulez lancer manuellement)
```bash
# Vérifier Python 3.9+
python --version
# ou
python3 --version

# Si besoin d'installer Python:
# https://www.python.org/downloads/
```

### 1.3 Vérifier Node.js (optionnel si vous voulez lancer manuellement)
```bash
# Vérifier Node.js 16+
node --version
npm --version

# Si besoin d'installer Node.js:
# https://nodejs.org/
```

## Étape 2: Lancement avec Docker Compose (Recommandé)

### 2.1 Lancer tous les services
```bash
# Ouvrir un terminal dans le répertoire du projet
cd C:\Users\sylla\CascadeProjects\fraud-detection-system

# Lancer tous les services
docker-compose up -d

# Vérifier que tous les services démarrent
docker-compose ps
```

### 2.2 Attendre le démarrage complet (2-3 minutes)
```bash
# Surveiller les logs pendant le démarrage
docker-compose logs -f

# Quand vous voyez que tous les services sont démarrés, appuyez sur Ctrl+C
```

### 2.3 Vérifier l'état des services
```bash
# Vérifier que tous les containers sont en cours d'exécution
docker-compose ps

# Vous devriez voir quelque chose comme:
# NAME                    COMMAND                  SERVICE             STATUS              PORTS
# fraud-detection-system-backend-1    "uvicorn src.main:ap..."   backend             running (healthy)   0.0.0.0:8000->8000/tcp
# fraud-detection-system-frontend-1    "npm start"               frontend            running             0.0.0.0:3000->3000/tcp
# fraud-detection-system-streamlit-1    "streamlit run src/d..."   streamlit           running             0.0.0.0:8501->8501/tcp
# fraud-detection-system-kafka-1        "/etc/confluent/dock..."   kafka               running             0.0.0.0:9092->9092/tcp
# fraud-detection-system-redis-1        "redis-server --appe..."   redis               running             0.0.0.0:6379->6379/tcp
# fraud-detection-system-grafana-1      "/run.sh"                 grafana             running             0.0.0.0:3000->3000/tcp
# fraud-detection-system-prometheus-1   "/bin/prometheus --c..."   prometheus          running             0.0.0.0:9090->9090/tcp
# fraud-detection-system-mlflow-1       "bash -c 'pip insta..."   mlflow              running             0.0.0.0:5000->5000/tcp
# fraud-detection-system-zookeeper-1    "/etc/confluent/dock..."   zookeeper           running             0.0.0.0:2181->2181/tcp
```

## Étape 3: Accès aux Services

### 3.1 Frontend React (Interface principale)
```
URL: http://localhost:3000
```

### 3.2 API Documentation
```
URL: http://localhost:8000/docs
```

### 3.3 Dashboard Streamlit
```
URL: http://localhost:8501
```

### 3.4 Grafana (Monitoring)
```
URL: http://localhost:3000
Username: admin
Password: admin
```

### 3.5 Prometheus (Métriques)
```
URL: http://localhost:9090
```

### 3.6 MLflow (Modèles ML)
```
URL: http://localhost:5000
```

## Étape 4: Tests de Base

### 4.1 Test Health Check API
```bash
# Test avec curl (ou ouvrir l'URL dans le navigateur)
curl http://localhost:8000/health

# Réponse attendue:
# {"status":"healthy","timestamp":"2024-01-01T12:00:00Z","services":{"models":{...},"kafka":{"status":"connected"},"redis":{"status":"connected"}}}
```

### 4.2 Test Prédiction Simple
```bash
# Test avec curl
curl -X POST http://localhost:8000/predict/single \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TEST_001",
    "type": "TRANSFER",
    "amount": 15000,
    "oldbalanceOrg": 50000,
    "newbalanceOrig": 35000,
    "oldbalanceDest": 20000,
    "newbalanceDest": 35000,
    "nameOrig": "C123456789",
    "nameDest": "M987654321"
  }'

# Réponse attendue:
# {"transaction_id":"TEST_001","prediction":{"is_fraud":false,"fraud_probability":0.15,"confidence":0.85,...},"latency_ms":45.2,...}
```

### 4.3 Test Interface Web

#### Frontend React:
1. Ouvrir http://localhost:3000
2. Vérifier que le dashboard s'affiche
3. Cliquer sur "File Upload" pour tester l'upload
4. Cliquer sur "Manual Entry" pour tester la saisie manuelle

#### Dashboard Streamlit:
1. Ouvrir http://localhost:8501
2. Vérifier que les métriques s'affichent
3. Vérifier les graphiques et alertes

## Étape 5: Tests Complets (Optionnel)

### 5.1 Script de Validation Automatique
```bash
# Lancer le script de performance
cd C:\Users\sylla\CascadeProjects\fraud-detection-system
python scripts/performance_validation.py --mode single --iterations 100

# Pour un test plus complet
python scripts/performance_validation.py --mode distributed --iterations 1000
```

### 5.2 Tests Unitaires Backend
```bash
# Si vous voulez lancer les tests manuellement
cd C:\Users\sylla\CascadeProjects\fraud-detection-system\backend
pip install -r requirements.txt
pytest tests/ -v --cov=src
```

### 5.3 Tests de Charge avec Locust
```bash
# Installer Locust
pip install locust

# Lancer les tests de charge
cd C:\Users\sylla\CascadeProjects\fraud-detection-system\tests
locust -f locustfile.py --host=http://localhost:8000

# Ouvrir http://localhost:8089 dans le navigateur pour l'interface Locust
```

## Étape 6: Dépannage

### 6.1 Problèmes Communs

#### Docker ne démarre pas:
```bash
# Vérifier que Docker Desktop est en cours d'exécution
# Redémarrer Docker Desktop

# Nettoyer et relancer
docker-compose down -v
docker-compose up -d
```

#### Ports déjà utilisés:
```bash
# Vérifier les ports utilisés
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Tuer les processus si nécessaire
taskkill /PID <PID> /F
```

#### Services ne répondent pas:
```bash
# Vérifier les logs de chaque service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs kafka
docker-compose logs redis

# Redémarrer un service spécifique
docker-compose restart backend
```

#### Frontend ne se charge pas:
```bash
# Vérifier que le backend fonctionne
curl http://localhost:8000/health

# Si le backend fonctionne, redémarrer le frontend
docker-compose restart frontend
```

### 6.2 Logs Utiles

#### Voir tous les logs en temps réel:
```bash
docker-compose logs -f
```

#### Voir les logs d'un service spécifique:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f kafka
docker-compose logs -f redis
```

### 6.3 Réinitialisation Complète

Si rien ne fonctionne:
```bash
# Arrêter tout
docker-compose down -v

# Supprimer toutes les images (attention!)
docker system prune -a

# Relancer depuis le début
docker-compose up -d
```

## Étape 7: Vérification Finale

### 7.1 Checklist de Validation

- [ ] Docker Desktop est en cours d'exécution
- [ ] `docker-compose up -d` s'exécute sans erreur
- [ ] Tous les containers sont "running" avec `docker-compose ps`
- [ ] Frontend React accessible: http://localhost:3000
- [ ] API docs accessibles: http://localhost:8000/docs
- [ ] Dashboard Streamlit accessible: http://localhost:8501
- [ ] Grafana accessible: http://localhost:3000 (admin/admin)
- [ ] Test prédiction API fonctionne
- [ ] Interface web fonctionne correctement

### 7.2 Test Final Complet

```bash
# Script de test complet
curl http://localhost:8000/health && \
curl -X POST http://localhost:8000/predict/single -H "Content-Type: application/json" -d '{"transaction_id":"FINAL_TEST","type":"TRANSFER","amount":1000,"oldbalanceOrg":5000,"newbalanceOrig":4000,"oldbalanceDest":2000,"newbalanceDest":3000,"nameOrig":"C123456789","nameDest":"M987654321"}'
```

## Étape 8: Utilisation Quotidienne

### 8.1 Pour Arrêter le Système
```bash
docker-compose down
```

### 8.2 Pour Redémarrer
```bash
docker-compose up -d
```

### 8.3 Pour Mettre à Jour
```bash
# Arrêter
docker-compose down

# Pull les dernières images (si disponibles)
docker-compose pull

# Relancer
docker-compose up -d
```

## Support

Si vous rencontrez des problèmes:

1. **Vérifiez les logs**: `docker-compose logs <service>`
2. **Consultez la documentation**: `docs/` directory
3. **Testez les services individuellement**: curl les endpoints
4. **Redémarrez les services**: `docker-compose restart`

## Résumé Rapide

```bash
# Commandes essentielles
cd C:\Users\sylla\CascadeProjects\fraud-detection-system
docker-compose up -d                    # Démarrer
docker-compose ps                      # Vérifier état
docker-compose logs -f                  # Voir logs
docker-compose down                    # Arrêter

# URLs importantes
# Frontend: http://localhost:3000
# API: http://localhost:8000/docs
# Dashboard: http://localhost:8501
# Grafana: http://localhost:3000 (admin/admin)
```

Le système devrait maintenant être complètement opérationnel!
