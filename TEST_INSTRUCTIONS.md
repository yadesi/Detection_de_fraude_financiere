# Instructions de Test Complet

## État Actuel : SYSTÈME OPÉRATIONNEL

### 1. Test de l'API Backend

#### Health Check
```bash
# Ouvrir dans le navigateur ou utiliser curl
http://localhost:8000/health
```

#### Test Prédiction Simple
```bash
# Ouvrir http://localhost:8000/docs dans le navigateur
# Utiliser l'interface Swagger pour tester :

POST /predict/single
{
  "transaction_id": "TEST_001",
  "type": "TRANSFER",
  "amount": 15000,
  "oldbalanceOrg": 50000,
  "newbalanceOrig": 35000,
  "oldbalanceDest": 20000,
  "newbalanceDest": 35000,
  "nameOrig": "C123456789",
  "nameDest": "M987654321"
}
```

#### Test Prédiction Batch
```bash
POST /predict/batch
[
  {
    "transaction_id": "BATCH_001",
    "type": "TRANSFER",
    "amount": 10000,
    "oldbalanceOrg": 30000,
    "newbalanceOrig": 20000,
    "oldbalanceDest": 15000,
    "newbalanceDest": 25000,
    "nameOrig": "C111111111",
    "nameDest": "M222222222"
  },
  {
    "transaction_id": "BATCH_002",
    "type": "PAYMENT",
    "amount": 500,
    "oldbalanceOrg": 5000,
    "newbalanceOrig": 4500,
    "oldbalanceDest": 8000,
    "newbalanceDest": 8500,
    "nameOrig": "C333333333",
    "nameDest": "M444444444"
  }
]
```

### 2. Test Frontend React

#### Accès Principal
```
URL: http://localhost:3001
```

#### Fonctionnalités à Tester
1. **Dashboard** : Voir les métriques en temps réel
2. **File Upload** : Uploader un fichier CSV/JSON
3. **Manual Entry** : Saisir une transaction manuellement
4. **Analytics** : Visualiser les graphiques et tendances
5. **Settings** : Configurer les paramètres système

#### Test Upload Fichier
```csv
# Créer un fichier test.csv avec ce contenu :
transaction_id,type,amount,oldbalanceOrg,newbalanceOrig,oldbalanceDest,newbalanceDest,nameOrig,nameDest
TEST001,TRANSFER,15000,50000,35000,20000,35000,C123456789,M987654321
TEST002,PAYMENT,500,5000,4500,8000,8500,C111111111,M222222222
```

### 3. Test Dashboard Streamlit

#### Accès
```
URL: http://localhost:8501
```

#### Fonctionnalités
- Métriques temps réel
- Graphiques interactifs
- Alertes système
- Statistiques de performance

### 4. Test Monitoring Grafana

#### Accès
```
URL: http://localhost:3000
Username: admin
Password: admin
```

#### Dashboards Disponibles
- System Metrics
- API Performance  
- Kafka Monitoring
- Redis Metrics

### 5. Test API Documentation

#### Swagger UI
```
URL: http://localhost:8000/docs
```

#### Endpoints Disponibles
- GET /health
- POST /predict/single
- POST /predict/batch  
- POST /predict/file
- GET /metrics
- GET /model/info
- POST /model/retrain
- GET /predictions/history

### 6. Tests de Performance

#### Script de Validation
```bash
cd C:\Users\sylla\CascadeProjects\fraud-detection-system
python scripts/performance_validation.py --mode single --iterations 100
```

#### Test de Charge (Optionnel)
```bash
cd tests
locust -f locustfile.py --host=http://localhost:8000
# Puis ouvrir http://localhost:8089
```

### 7. Vérification Services

#### Vérifier l'état de tous les services
```bash
docker-compose ps
```

#### Voir les logs d'un service spécifique
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs streamlit
```

### 8. Test Complet End-to-End

#### Scénario Complet
1. **Ouvrir le Frontend** : http://localhost:3001
2. **Vérifier le Dashboard** : Métriques visibles
3. **Tester Manual Entry** : Saisir une transaction
4. **Vérifier la prédiction** : Résultat affiché
5. **Ouvrir Streamlit** : http://localhost:8501
6. **Vérifier les graphiques** : Données synchronisées
7. **Ouvrir Grafana** : http://localhost:3000
8. **Vérifier monitoring** : Métriques système

### 9. Dépannage Rapide

#### Si un service ne répond pas
```bash
docker-compose restart <service_name>
# Exemple:
docker-compose restart backend
```

#### Si les ports sont occupés
```bash
netstat -ano | findstr :8000
# Tuer le processus si nécessaire
```

#### Pour tout réinitialiser
```bash
docker-compose down -v
docker-compose up -d
```

### 10. Checklist de Validation

- [ ] Frontend React accessible (http://localhost:3001)
- [ ] API répond (http://localhost:8000/health)
- [ ] Documentation API visible (http://localhost:8000/docs)
- [ ] Dashboard Streamlit fonctionnel (http://localhost:8501)
- [ ] Grafana accessible (http://localhost:3000)
- [ ] Prédiction simple fonctionne
- [ ] Upload de fichier fonctionne
- [ ] Graphiques se mettent à jour
- [ ] Monitoring actif dans Grafana

## Prochaines Étapes

1. **Explorer les fonctionnalités** : Tester chaque composant
2. **Personnaliser les paramètres** : Via Settings dans le frontend
3. **Charger des données réelles** : Via File Upload
4. **Monitorer les performances** : Via Grafana
5. **Tester les limites** : Via scripts de charge

## Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs avec `docker-compose logs <service>`
2. Redémarrez le service concerné
3. Consultez la documentation complète dans `docs/`

**Le système est prêt pour une démonstration complète !**
