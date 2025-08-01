#!/bin/bash
# Setup script cho VM2 (Scanner Node + Kubernetes)
# IP VM1: 10.102.199.42
# IP VM2: 10.102.199.37

echo "=== Setting up Scanner Node on VM2 ==="

# Setup Minikube environment
echo "Setting up Minikube environment..."
eval $(minikube docker-env)

# Build all images
echo "Building tool images..."
docker build -t nguyenminhnguyen/dns-lookup:latest scan-node-tools/dns-lookup/
docker build -t nguyenminhnguyen/port-scan:latest scan-node-tools/port-scan/
docker build -t nguyenminhnguyen/httpx-scan:latest scan-node-tools/httpx-scan/

echo "Building Scanner Node API image..."
docker build -t nguyenminhnguyen/scanner-node-api:latest scanner-node-api/

# Deploy Kubernetes manifests
echo "Deploying Kubernetes manifests..."
kubectl apply -f manifests/namespace.yaml
kubectl apply -f manifests/controller-rbac.yaml
kubectl apply -f manifests/scanner-node-api-deployment.yaml
kubectl apply -f manifests/scanner-node-api-service.yaml

# Wait for deployment
echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/scanner-node-api -n scan-system

# Port forward Scanner Node API
echo "Setting up port forwarding..."
kubectl port-forward -n scan-system svc/scanner-node-api 8002:8000 --address=0.0.0.0 &
PORT_FORWARD_PID=$!

# Check status
echo "Checking deployment status..."
kubectl get all -n scan-system

echo "=== Scanner Node setup complete ==="
echo "Scanner Node API URL: http://10.102.199.37:8002"
echo "Port forward PID: $PORT_FORWARD_PID"

# Test commands
echo ""
echo "Test commands:"
echo "curl http://localhost:8002/health"
echo "kubectl get pods -n scan-system"

# Save port forward PID for later cleanup
echo $PORT_FORWARD_PID > /tmp/scanner-port-forward.pid
echo "Port forward PID saved to /tmp/scanner-port-forward.pid"
