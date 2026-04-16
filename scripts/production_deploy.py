#!/usr/bin/env python3
"""
Production Deployment Script for Fraud Detection System
Handles automated deployment, configuration, and monitoring setup
"""

import os
import sys
import json
import yaml
import subprocess
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionDeployer:
    """Production deployment automation"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.deploy_dir = self.project_root / "deploy"
        
        # Create directories
        self.config_dir.mkdir(exist_ok=True)
        self.deploy_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load environment-specific configuration"""
        
        config_file = self.config_dir / f"{self.environment}.yaml"
        
        if not config_file.exists():
            # Create default configuration
            default_config = self._create_default_config()
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            logger.info(f"Created default config: {config_file}")
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration for production"""
        
        return {
            "environment": self.environment,
            "cluster": {
                "provider": "kubernetes",
                "region": "us-west-2",
                "node_count": 3,
                "instance_type": "t3.medium"
            },
            "services": {
                "backend": {
                    "replicas": 3,
                    "cpu_limit": "500m",
                    "memory_limit": "1Gi",
                    "image": "fraud-detection-system-backend:latest"
                },
                "frontend": {
                    "replicas": 2,
                    "cpu_limit": "200m",
                    "memory_limit": "512Mi",
                    "image": "fraud-detection-system-frontend:latest"
                },
                "streamlit": {
                    "replicas": 1,
                    "cpu_limit": "300m",
                    "memory_limit": "1Gi",
                    "image": "fraud-detection-system-streamlit:latest"
                },
                "kafka": {
                    "replicas": 3,
                    "cpu_limit": "500m",
                    "memory_limit": "2Gi",
                    "storage": "20Gi"
                },
                "redis": {
                    "replicas": 1,
                    "cpu_limit": "200m",
                    "memory_limit": "1Gi",
                    "storage": "10Gi"
                },
                "prometheus": {
                    "replicas": 1,
                    "cpu_limit": "300m",
                    "memory_limit": "2Gi",
                    "storage": "50Gi"
                },
                "grafana": {
                    "replicas": 1,
                    "cpu_limit": "200m",
                    "memory_limit": "512Mi",
                    "storage": "10Gi"
                },
                "mlflow": {
                    "replicas": 1,
                    "cpu_limit": "500m",
                    "memory_limit": "2Gi",
                    "storage": "50Gi"
                }
            },
            "networking": {
                "domain": "fraud-detection.example.com",
                "ssl_enabled": True,
                "load_balancer_type": "application"
            },
            "monitoring": {
                "enabled": True,
                "alerting": True,
                "log_level": "INFO",
                "metrics_retention": "30d"
            },
            "security": {
                "rbac_enabled": True,
                "network_policies": True,
                "pod_security_policy": True,
                "image_pull_secrets": True
            },
            "backup": {
                "enabled": True,
                "schedule": "0 2 * * *",
                "retention": "7d",
                "storage_class": "standard"
            },
            "scaling": {
                "auto_scaling": True,
                "min_replicas": 2,
                "max_replicas": 10,
                "target_cpu_utilization": 70
            }
        }
    
    def create_kubernetes_manifests(self) -> Dict[str, str]:
        """Create Kubernetes manifests for all services"""
        
        manifests = {}
        
        # Namespace
        namespace = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": f"fraud-detection-{self.environment}"
            }
        }
        manifests["namespace.yaml"] = yaml.dump(namespace, default_flow_style=False)
        
        # ConfigMap
        config_map = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "fraud-detection-config",
                "namespace": f"fraud-detection-{self.environment}"
            },
            "data": {
                "API_HOST": "0.0.0.0",
                "API_PORT": "8000",
                "REDIS_HOST": "redis-service",
                "REDIS_PORT": "6379",
                "KAFKA_BOOTSTRAP_SERVERS": "kafka-service:9092",
                "MLFLOW_TRACKING_URI": "http://mlflow-service:5000",
                "LOG_LEVEL": "INFO",
                "ENVIRONMENT": self.environment
            }
        }
        manifests["configmap.yaml"] = yaml.dump(config_map, default_flow_style=False)
        
        # Secrets
        secrets = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": "fraud-detection-secrets",
                "namespace": f"fraud-detection-{self.environment}"
            },
            "type": "Opaque",
            "data": {
                "database-password": "cGFzc3dvcmQxMjM=",  # base64 encoded
                "api-key": "bW9ja2FwaWtleQ==",
                "redis-password": "cmVkaXNwYXNz"
            }
        }
        manifests["secrets.yaml"] = yaml.dump(secrets, default_flow_style=False)
        
        # Service manifests
        for service_name, service_config in self.config["services"].items():
            if service_name in ["backend", "frontend", "streamlit", "mlflow"]:
                service_manifest = self._create_service_manifest(service_name, service_config)
                manifests[f"{service_name}-service.yaml"] = yaml.dump(service_manifest, default_flow_style=False)
                
                deployment_manifest = self._create_deployment_manifest(service_name, service_config)
                manifests[f"{service_name}-deployment.yaml"] = yaml.dump(deployment_manifest, default_flow_style=False)
        
        # StatefulSets for stateful services
        for service_name in ["kafka", "redis", "prometheus", "grafana"]:
            service_config = self.config["services"][service_name]
            statefulset_manifest = self._create_statefulset_manifest(service_name, service_config)
            manifests[f"{service_name}-statefulset.yaml"] = yaml.dump(statefulset_manifest, default_flow_style=False)
            
            service_manifest = self._create_service_manifest(service_name, service_config)
            manifests[f"{service_name}-service.yaml"] = yaml.dump(service_manifest, default_flow_style=False)
        
        # Ingress
        ingress_manifest = self._create_ingress_manifest()
        manifests["ingress.yaml"] = yaml.dump(ingress_manifest, default_flow_style=False)
        
        # HorizontalPodAutoscaler
        if self.config["scaling"]["auto_scaling"]:
            hpa_manifest = self._create_hpa_manifest()
            manifests["hpa.yaml"] = yaml.dump(hpa_manifest, default_flow_style=False)
        
        # NetworkPolicy
        if self.config["security"]["network_policies"]:
            network_policy = self._create_network_policy_manifest()
            manifests["networkpolicy.yaml"] = yaml.dump(network_policy, default_flow_style=False)
        
        return manifests
    
    def _create_service_manifest(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Kubernetes Service manifest"""
        
        port_mapping = {
            "backend": 8000,
            "frontend": 3000,
            "streamlit": 8501,
            "mlflow": 5000,
            "kafka": 9092,
            "redis": 6379,
            "prometheus": 9090,
            "grafana": 3000
        }
        
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"{service_name}-service",
                "namespace": f"fraud-detection-{self.environment}",
                "labels": {
                    "app": "fraud-detection",
                    "component": service_name,
                    "environment": self.environment
                }
            },
            "spec": {
                "selector": {
                    "app": "fraud-detection",
                    "component": service_name
                },
                "ports": [
                    {
                        "name": "http",
                        "port": port_mapping.get(service_name, 80),
                        "targetPort": port_mapping.get(service_name, 80),
                        "protocol": "TCP"
                    }
                ],
                "type": "ClusterIP"
            }
        }
    
    def _create_deployment_manifest(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Kubernetes Deployment manifest"""
        
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"{service_name}-deployment",
                "namespace": f"fraud-detection-{self.environment}",
                "labels": {
                    "app": "fraud-detection",
                    "component": service_name,
                    "environment": self.environment
                }
            },
            "spec": {
                "replicas": config["replicas"],
                "selector": {
                    "matchLabels": {
                        "app": "fraud-detection",
                        "component": service_name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "fraud-detection",
                            "component": service_name,
                            "environment": self.environment
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": service_name,
                                "image": config["image"],
                                "ports": [
                                    {
                                        "containerPort": 8000 if service_name == "backend" else 3000 if service_name == "frontend" else 8501 if service_name == "streamlit" else 5000
                                    }
                                ],
                                "envFrom": [
                                    {
                                        "configMapRef": {
                                            "name": "fraud-detection-config"
                                        }
                                    }
                                ],
                                "resources": {
                                    "limits": {
                                        "cpu": config["cpu_limit"],
                                        "memory": config["memory_limit"]
                                    },
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": "128Mi"
                                    }
                                },
                                "livenessProbe": {
                                    "httpGet": {
                                        "path": "/health" if service_name == "backend" else "/",
                                        "port": 8000 if service_name == "backend" else 3000 if service_name == "frontend" else 8501
                                    },
                                    "initialDelaySeconds": 30,
                                    "periodSeconds": 10
                                },
                                "readinessProbe": {
                                    "httpGet": {
                                        "path": "/health" if service_name == "backend" else "/",
                                        "port": 8000 if service_name == "backend" else 3000 if service_name == "frontend" else 8501
                                    },
                                    "initialDelaySeconds": 5,
                                    "periodSeconds": 5
                                }
                            }
                        ]
                    }
                }
            }
        }
    
    def _create_statefulset_manifest(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Kubernetes StatefulSet manifest"""
        
        port_mapping = {
            "kafka": 9092,
            "redis": 6379,
            "prometheus": 9090,
            "grafana": 3000
        }
        
        manifest = {
            "apiVersion": "apps/v1",
            "kind": "StatefulSet",
            "metadata": {
                "name": f"{service_name}-statefulset",
                "namespace": f"fraud-detection-{self.environment}",
                "labels": {
                    "app": "fraud-detection",
                    "component": service_name,
                    "environment": self.environment
                }
            },
            "spec": {
                "serviceName": f"{service_name}-service",
                "replicas": config["replicas"],
                "selector": {
                    "matchLabels": {
                        "app": "fraud-detection",
                        "component": service_name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "fraud-detection",
                            "component": service_name,
                            "environment": self.environment
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": service_name,
                                "image": self._get_service_image(service_name),
                                "ports": [
                                    {
                                        "containerPort": port_mapping[service_name]
                                    }
                                ],
                                "resources": {
                                    "limits": {
                                        "cpu": config["cpu_limit"],
                                        "memory": config["memory_limit"]
                                    },
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": "128Mi"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        
        # Add volume claim template if storage is specified
        if "storage" in config:
            manifest["spec"]["volumeClaimTemplates"] = [
                {
                    "metadata": {
                        "name": f"{service_name}-data"
                    },
                    "spec": {
                        "accessModes": ["ReadWriteOnce"],
                        "resources": {
                            "requests": {
                                "storage": config["storage"]
                            }
                        }
                    }
                }
            ]
        
        return manifest
    
    def _get_service_image(self, service_name: str) -> str:
        """Get Docker image for service"""
        
        image_mapping = {
            "kafka": "confluentinc/cp-kafka:7.4.0",
            "redis": "redis:7.2-alpine",
            "prometheus": "prom/prometheus:v2.47.0",
            "grafana": "grafana/grafana:10.2.0"
        }
        
        return image_mapping.get(service_name, "nginx:latest")
    
    def _create_ingress_manifest(self) -> Dict[str, Any]:
        """Create Kubernetes Ingress manifest"""
        
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": "fraud-detection-ingress",
                "namespace": f"fraud-detection-{self.environment}",
                "annotations": {
                    "kubernetes.io/ingress.class": "nginx",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                    "nginx.ingress.kubernetes.io/ssl-redirect": "true"
                }
            },
            "spec": {
                "tls": [
                    {
                        "hosts": [self.config["networking"]["domain"]],
                        "secretName": "fraud-detection-tls"
                    }
                ],
                "rules": [
                    {
                        "host": self.config["networking"]["domain"],
                        "http": {
                            "paths": [
                                {
                                    "path": "/api",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": "backend-service",
                                            "port": {
                                                "number": 8000
                                            }
                                        }
                                    }
                                },
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": "frontend-service",
                                            "port": {
                                                "number": 3000
                                            }
                                        }
                                    }
                                },
                                {
                                    "path": "/dashboard",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": "streamlit-service",
                                            "port": {
                                                "number": 8501
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    
    def _create_hpa_manifest(self) -> Dict[str, Any]:
        """Create HorizontalPodAutoscaler manifest"""
        
        return {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": "fraud-detection-hpa",
                "namespace": f"fraud-detection-{self.environment}"
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": "backend-deployment"
                },
                "minReplicas": self.config["scaling"]["min_replicas"],
                "maxReplicas": self.config["scaling"]["max_replicas"],
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": self.config["scaling"]["target_cpu_utilization"]
                            }
                        }
                    }
                ]
            }
        }
    
    def _create_network_policy_manifest(self) -> Dict[str, Any]:
        """Create NetworkPolicy manifest"""
        
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": "fraud-detection-network-policy",
                "namespace": f"fraud-detection-{self.environment}"
            },
            "spec": {
                "podSelector": {
                    "matchLabels": {
                        "app": "fraud-detection"
                    }
                },
                "policyTypes": ["Ingress", "Egress"],
                "ingress": [
                    {
                        "from": [
                            {
                                "namespaceSelector": {
                                    "matchLabels": {
                                        "name": "ingress-nginx"
                                    }
                                }
                            }
                        ],
                        "ports": [
                            {
                                "protocol": "TCP",
                                "port": 8000
                            },
                            {
                                "protocol": "TCP",
                                "port": 3000
                            },
                            {
                                "protocol": "TCP",
                                "port": 8501
                            }
                        ]
                    }
                ],
                "egress": [
                    {
                        "to": [
                            {
                                "podSelector": {
                                    "matchLabels": {
                                        "app": "fraud-detection"
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
    
    def save_manifests(self, manifests: Dict[str, str]):
        """Save Kubernetes manifests to files"""
        
        manifest_dir = self.deploy_dir / "kubernetes" / self.environment
        manifest_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, content in manifests.items():
            file_path = manifest_dir / filename
            with open(file_path, 'w') as f:
                f.write(content)
        
        logger.info(f"Saved {len(manifests)} manifests to {manifest_dir}")
    
    def create_monitoring_config(self) -> Dict[str, str]:
        """Create monitoring configuration files"""
        
        configs = {}
        
        # Prometheus configuration
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "rule_files": ["/etc/prometheus/rules/*.yml"],
            "scrape_configs": [
                {
                    "job_name": "fraud-detection-backend",
                    "kubernetes_sd_configs": [
                        {
                            "role": "pod",
                            "namespaces": {
                                "names": [f"fraud-detection-{self.environment}"]
                            }
                        }
                    ],
                    "relabel_configs": [
                        {
                            "source_labels": ["__meta_kubernetes_pod_label_component"],
                            "target_label": "component",
                            "replacement": "backend"
                        }
                    ]
                },
                {
                    "job_name": "kafka",
                    "kubernetes_sd_configs": [
                        {
                            "role": "pod",
                            "namespaces": {
                                "names": [f"fraud-detection-{self.environment}"]
                            }
                        }
                    ],
                    "relabel_configs": [
                        {
                            "source_labels": ["__meta_kubernetes_pod_label_component"],
                            "target_label": "component",
                            "replacement": "kafka"
                        }
                    ]
                }
            ],
            "alerting": {
                "alertmanagers": [
                    {
                        "kubernetes_sd_configs": [
                            {
                                "role": "pod",
                                "namespaces": {
                                    "names": [f"fraud-detection-{self.environment}"]
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        configs["prometheus.yml"] = yaml.dump(prometheus_config, default_flow_style=False)
        
        # Alert rules
        alert_rules = {
            "groups": [
                {
                    "name": "fraud-detection.rules",
                    "rules": [
                        {
                            "alert": "HighErrorRate",
                            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) > 0.1",
                            "for": "5m",
                            "labels": {
                                "severity": "critical"
                            },
                            "annotations": {
                                "summary": "High error rate detected",
                                "description": "Error rate is {{ $value }} errors per second"
                            }
                        },
                        {
                            "alert": "HighLatency",
                            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High latency detected",
                                "description": "95th percentile latency is {{ $value }} seconds"
                            }
                        },
                        {
                            "alert": "PodCrashLooping",
                            "expr": "rate(kube_pod_container_status_restarts_total[15m]) > 0",
                            "for": "5m",
                            "labels": {
                                "severity": "critical"
                            },
                            "annotations": {
                                "summary": "Pod is crash looping",
                                "description": "Pod {{ $labels.pod }} is restarting frequently"
                            }
                        }
                    ]
                }
            ]
        }
        
        configs["alert-rules.yml"] = yaml.dump(alert_rules, default_flow_style=False)
        
        # Grafana dashboard
        grafana_dashboard = {
            "dashboard": {
                "title": "Fraud Detection System",
                "panels": [
                    {
                        "title": "Request Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(http_requests_total[5m])",
                                "legendFormat": "{{method}} {{status}}"
                            }
                        ]
                    },
                    {
                        "title": "Response Time",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                                "legendFormat": "95th percentile"
                            }
                        ]
                    },
                    {
                        "title": "Error Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
                                "legendFormat": "5xx errors"
                            }
                        ]
                    }
                ]
            }
        }
        
        configs["grafana-dashboard.json"] = json.dumps(grafana_dashboard, indent=2)
        
        return configs
    
    def create_ci_cd_pipeline(self) -> str:
        """Create CI/CD pipeline configuration"""
        
        pipeline_config = {
            "name": "fraud-detection-ci-cd",
            "on": {
                "push": {
                    "branches": ["main", "develop"]
                },
                "pull_request": {
                    "branches": ["main"]
                }
            },
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {
                            "name": "Checkout code",
                            "uses": "actions/checkout@v3"
                        },
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v4",
                            "with": {
                                "python-version": "3.9"
                            }
                        },
                        {
                            "name": "Install dependencies",
                            "run": "pip install -r requirements.txt"
                        },
                        {
                            "name": "Run tests",
                            "run": "pytest tests/ --cov=src --cov-report=xml"
                        },
                        {
                            "name": "Upload coverage",
                            "uses": "codecov/codecov-action@v3"
                        }
                    ]
                },
                "build": {
                    "needs": "test",
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {
                            "name": "Checkout code",
                            "uses": "actions/checkout@v3"
                        },
                        {
                            "name": "Build Docker images",
                            "run": "docker build -t fraud-detection-system-backend:${{ github.sha }} ./backend && docker build -t fraud-detection-system-frontend:${{ github.sha }} ./frontend && docker build -t fraud-detection-system-streamlit:${{ github.sha }} ./backend -f Dockerfile.streamlit"
                        },
                        {
                            "name": "Push to registry",
                            "run": "echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin && docker push fraud-detection-system-backend:${{ github.sha }} && docker push fraud-detection-system-frontend:${{ github.sha }} && docker push fraud-detection-system-streamlit:${{ github.sha }}"
                        }
                    ]
                },
                "deploy": {
                    "needs": "build",
                    "runs-on": "ubuntu-latest",
                    "if": "github.ref == 'refs/heads/main'",
                    "steps": [
                        {
                            "name": "Deploy to production",
                            "run": "kubectl apply -f deploy/kubernetes/production/ && kubectl rollout status deployment/backend-deployment -n fraud-detection-production"
                        }
                    ]
                }
            }
        }
        
        return yaml.dump(pipeline_config, default_flow_style=False)
    
    def deploy_to_kubernetes(self) -> bool:
        """Deploy application to Kubernetes"""
        
        try:
            logger.info("Starting Kubernetes deployment...")
            
            # Create namespace
            namespace_cmd = [
                "kubectl", "create", "namespace", 
                f"fraud-detection-{self.environment}", 
                "--dry-run=client", "-o", "yaml", "|", "kubectl", "apply", "-f", "-"
            ]
            
            # Apply manifests
            manifest_dir = self.deploy_dir / "kubernetes" / self.environment
            apply_cmd = f"kubectl apply -f {manifest_dir}"
            
            result = subprocess.run(apply_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Kubernetes deployment successful")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"Kubernetes deployment failed: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return False
    
    def verify_deployment(self) -> bool:
        """Verify that deployment is successful"""
        
        try:
            logger.info("Verifying deployment...")
            
            # Check pod status
            pod_cmd = f"kubectl get pods -n fraud-detection-{self.environment}"
            result = subprocess.run(pod_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Pod status:")
                logger.info(result.stdout)
                
                # Check services
                service_cmd = f"kubectl get services -n fraud-detection-{self.environment}"
                result = subprocess.run(service_cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("Service status:")
                    logger.info(result.stdout)
                    
                    return True
                else:
                    logger.error(f"Service check failed: {result.stderr}")
                    return False
            else:
                logger.error(f"Pod check failed: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return False
    
    def run_deployment(self) -> bool:
        """Run complete deployment process"""
        
        logger.info(f"Starting production deployment for {self.environment}")
        
        try:
            # 1. Create Kubernetes manifests
            logger.info("Creating Kubernetes manifests...")
            manifests = self.create_kubernetes_manifests()
            self.save_manifests(manifests)
            
            # 2. Create monitoring configuration
            logger.info("Creating monitoring configuration...")
            monitoring_configs = self.create_monitoring_config()
            monitoring_dir = self.deploy_dir / "monitoring" / self.environment
            monitoring_dir.mkdir(parents=True, exist_ok=True)
            
            for filename, content in monitoring_configs.items():
                with open(monitoring_dir / filename, 'w') as f:
                    f.write(content)
            
            # 3. Create CI/CD pipeline
            logger.info("Creating CI/CD pipeline...")
            pipeline_config = self.create_ci_cd_pipeline()
            with open(self.deploy_dir / "ci-cd.yml", 'w') as f:
                f.write(pipeline_config)
            
            # 4. Deploy to Kubernetes
            if self.deploy_to_kubernetes():
                # 5. Verify deployment
                if self.verify_deployment():
                    logger.info("Deployment completed successfully!")
                    return True
                else:
                    logger.error("Deployment verification failed")
                    return False
            else:
                logger.error("Deployment failed")
                return False
        
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return False

def main():
    """Main function to run production deployment"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Fraud Detection System Production Deployment")
    parser.add_argument("--environment", choices=["development", "staging", "production"], 
                       default="production", help="Target environment")
    parser.add_argument("--dry-run", action="store_true", help="Generate manifests without deploying")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing deployment")
    
    args = parser.parse_args()
    
    deployer = ProductionDeployer(args.environment)
    
    if args.verify_only:
        success = deployer.verify_deployment()
    elif args.dry_run:
        logger.info("Dry run mode - generating manifests only...")
        manifests = deployer.create_kubernetes_manifests()
        deployer.save_manifests(manifests)
        success = True
    else:
        success = deployer.run_deployment()
    
    if success:
        logger.info("Deployment operation completed successfully")
        sys.exit(0)
    else:
        logger.error("Deployment operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
