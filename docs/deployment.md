# Guide de Déploiement

## Environnements

### 1. Développement

#### Prérequis
- Docker Desktop
- Git
- 8GB+ RAM
- 50GB+ disque

#### Installation
```bash
git clone <repository>
cd fraud-detection-system
docker-compose -f docker-compose.dev.yml up -d
```

#### Services
- Frontend: http://localhost:3000
- API: http://localhost:8000
- Dashboard: http://localhost:8501
- Grafana: http://localhost:3000
- MLflow: http://localhost:5000

### 2. Staging

#### Infrastructure
- **Cloud**: AWS/Azure/GCP
- **Instances**: 2x t3.large (4GB RAM)
- **Storage**: 100GB SSD
- **Network**: VPC privée

#### Configuration
```yaml
# docker-compose.staging.yml
version: '3.8'
services:
  backend:
    image: fraud-detection:staging
    environment:
      - ENV=staging
      - LOG_LEVEL=INFO
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

### 3. Production

#### Infrastructure Recommandée
- **Load Balancer**: Application Load Balancer
- **Instances**: 3x t3.xlarge (8GB RAM)
- **Database**: RDS PostgreSQL
- **Cache**: ElastiCache Redis
- **Streaming**: MSK Kafka
- **Storage**: S3 + EFS
- **Monitoring**: CloudWatch + Prometheus

#### Sécurité
- **SSL/TLS**: Certificat wildcard
- **WAF**: AWS WAF
- **VPC**: Réseau privé
- **IAM**: Rôles limités
- **Secrets**: AWS Secrets Manager

## Dockerisation

### Multi-stage Builds

#### Backend Dockerfile
```dockerfile
# Build stage
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile
```dockerfile
# Build stage
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Runtime stage
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### Optimisation Docker

#### Image Size Reduction
```dockerfile
# Use Alpine base
FROM python:3.9-alpine

# Multi-stage builds
# .dockerignore
node_modules/
*.pyc
.git/
.env
```

#### Security Hardening
```dockerfile
# Non-root user
RUN adduser -D -s /bin/sh appuser
USER appuser

# Minimal permissions
COPY --chown=appuser:appuser . .
```

## Kubernetes Deployment

### Namespace Configuration
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: fraud-detection
  labels:
    name: fraud-detection
```

### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fraud-detection-config
  namespace: fraud-detection
data:
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  KAFKA_BOOTSTRAP_SERVERS: "kafka:9092"
  REDIS_HOST: "redis"
  LOG_LEVEL: "INFO"
```

### Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: fraud-detection-secrets
  namespace: fraud-detection
type: Opaque
data:
  DATABASE_URL: <base64-encoded>
  API_KEY: <base64-encoded>
```

### Backend Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fraud-detection-backend
  namespace: fraud-detection
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fraud-detection-backend
  template:
    metadata:
      labels:
        app: fraud-detection-backend
    spec:
      containers:
      - name: backend
        image: fraud-detection:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: fraud-detection-config
        - secretRef:
            name: fraud-detection-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service Configuration
```yaml
apiVersion: v1
kind: Service
metadata:
  name: fraud-detection-backend-service
  namespace: fraud-detection
spec:
  selector:
    app: fraud-detection-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress Configuration
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fraud-detection-ingress
  namespace: fraud-detection
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.fraud-detection.com
    secretName: fraud-detection-tls
  rules:
  - host: api.fraud-detection.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fraud-detection-backend-service
            port:
              number: 80
```

### Horizontal Pod Autoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fraud-detection-hpa
  namespace: fraud-detection
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fraud-detection-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## CI/CD Pipeline

### GitHub Actions
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    - name: Run tests
      run: |
        cd backend
        pytest --cov=src tests/
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    - name: Build Docker images
      run: |
        docker build -t fraud-detection-backend:${{ github.sha }} ./backend
        docker build -t fraud-detection-frontend:${{ github.sha }} ./frontend
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push fraud-detection-backend:${{ github.sha }}
        docker push fraud-detection-frontend:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/fraud-detection-backend backend=fraud-detection-backend:${{ github.sha }}
        kubectl set image deployment/fraud-detection-frontend frontend=fraud-detection-frontend:${{ github.sha }}
```

### GitOps avec ArgoCD

#### Application Manifest
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: fraud-detection
  namespace: argocd
spec:
  project: default
  source:
    repoURL: 'https://github.com/your-org/fraud-detection-k8s'
    targetRevision: HEAD
    path: manifests
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: fraud-detection
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Monitoring & Logging

### Prometheus Configuration
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "fraud_detection_rules.yml"

scrape_configs:
  - job_name: 'fraud-detection-api'
    kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
        - fraud-detection
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: true
```

### Alerting Rules
```yaml
groups:
- name: fraud_detection_alerts
  rules:
  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(fraud_prediction_latency_seconds_bucket[5m])) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High prediction latency detected"
      description: "95th percentile latency is {{ $value }}s"

  - alert: HighErrorRate
    expr: rate(fraud_prediction_errors_total[5m]) / rate(fraud_prediction_total[5m]) > 0.05
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value | humanizePercentage }}"
```

### Grafana Dashboards
```json
{
  "dashboard": {
    "title": "Fraud Detection Overview",
    "panels": [
      {
        "title": "Prediction Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(fraud_predictions_total[5m])"
          }
        ]
      },
      {
        "title": "Fraud Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(fraud_fraud_predictions_total[5m]) / rate(fraud_predictions_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## Configuration Management

### Helm Charts

#### Chart Structure
```
helm-chart/
  Chart.yaml
  values.yaml
  values-dev.yaml
  values-staging.yaml
  values-prod.yaml
  templates/
    deployment.yaml
    service.yaml
    ingress.yaml
    configmap.yaml
    secret.yaml
```

#### Values.yaml
```yaml
replicaCount: 3

image:
  repository: fraud-detection
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  className: nginx
  annotations: {}
  hosts:
    - host: fraud-detection.local
      paths:
        - path: /
          pathType: Prefix
  tls: []

resources:
  limits:
    cpu: 500m
    memory: 1Gi
  requests:
    cpu: 250m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

## Sécurité

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fraud-detection-netpol
  namespace: fraud-detection
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 9092  # Kafka
    - protocol: TCP
      port: 6379  # Redis
```

### Pod Security Policy
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: fraud-detection-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## Backup & Recovery

### Database Backup
```bash
# PostgreSQL backup
pg_dump -h $DB_HOST -U $DB_USER -d fraud_detection > backup_$(date +%Y%m%d).sql

# Redis backup
redis-cli --rdb backup_$(date +%Y%m%d).rdb
```

### Kubernetes Backup
```bash
# Velero installation
velero install --provider aws --bucket velero-backups --secret-file ./credentials-velero

# Backup namespace
velero backup create fraud-detection-backup --include-namespaces fraud-detection

# Restore namespace
velero restore create --from-backup fraud-detection-backup
```

### Disaster Recovery Plan

#### RTO/RPO
- **RTO** (Recovery Time Objective): 1 heure
- **RPO** (Recovery Point Objective): 15 minutes

#### Procédures
1. **Détection**: Monitoring automatique
2. **Évaluation**: Impact assessment
3. **Basculement**: Traffic redirection
4. **Restauration**: Data recovery
5. **Validation**: Functional testing

## Performance Tuning

### Resource Optimization
```yaml
# JVM tuning for Spark
SPARK_EXECUTOR_MEMORY: 2g
SPARK_DRIVER_MEMORY: 1g
SPARK_EXECUTOR_CORES: 2
SPARK_DEFAULT_PARALLELISM: 4

# Python optimization
PYTHONUNBUFFERED: 1
PYTHONDONTWRITEBYTECODE: 1
```

### Database Optimization
```sql
-- Indexes for performance
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_predictions_fraud ON predictions(is_fraud);

-- Partitioning
CREATE TABLE transactions_2024_01 PARTITION OF transactions
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Caching Strategy
```python
# Redis caching configuration
CACHE_TTL_PREDICTIONS = 3600  # 1 hour
CACHE_TTL_FEATURES = 1800    # 30 minutes
CACHE_TTL_MODELS = 86400     # 24 hours
```

## Maintenance

### Rolling Updates
```bash
# Zero-downtime deployment
kubectl set image deployment/fraud-detection-backend backend=fraud-detection:v2.0.0
kubectl rollout status deployment/fraud-detection-backend
```

### Health Checks
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Log Management
```yaml
# Fluentd configuration
<source>
  @type tail
  path /var/log/containers/fraud-detection*.log
  pos_file /var/log/fluentd-containers.log.pos
  tag kubernetes.*
  format json
</source>

<match kubernetes.**>
  @type elasticsearch
  host elasticsearch.logging.svc.cluster.local
  port 9200
  index_name fraud-detection
</match>
```

## Conclusion

Ce guide de déploiement couvre tous les aspects nécessaires pour mettre en production le système de détection de fraude, de l'environnement de développement à la production en passant par le staging. Chaque étape inclut les meilleures pratiques pour garantir la sécurité, la performance et la fiabilité du système.

Pour un déploiement réussi, suivez les étapes dans l'ordre et adaptez les configurations à votre environnement spécifique.
