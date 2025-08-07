#!/bin/bash
# Setup script cho VM1 (Controller trên Kubernetes)
# IP VM1: 10.102.199.42
# IP VM2: 10.102.199.37

echo "=== Setting up Controller on VM1 with Kubernetes ==="

# Setup Minikube environment
echo "Setting up Minikube environment..."
eval $(minikube docker-env)

# Build Controller image
echo "Building Controller image..."
docker build -t nguyenminhnguyen/controller:latest controller/

# Deploy Kubernetes manifests for Controller
echo "Deploying Controller to Kubernetes..."
kubectl apply -f manifests/namespace.yaml
kubectl apply -f manifests/controller-rbac.yaml
kubectl apply -f manifests/controller-deployment.yaml
kubectl apply -f manifests/controller-service.yaml

# Wait for deployment
echo "Waiting for Controller deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/controller -n scan-system

# Port forward Controller API
echo "Setting up port forwarding for Controller..."
kubectl port-forward -n scan-system svc/controller 8000:8000 --address=0.0.0.0 &
CONTROLLER_PORT_FORWARD_PID=$!

# Check status
echo "Checking deployment status..."
kubectl get all -n scan-system

echo "=== Controller setup complete ==="
echo "Controller API URL: http://10.102.199.42:8000"
echo "Controller Port forward PID: $CONTROLLER_PORT_FORWARD_PID"

# Test Controller API
echo ""
echo "Testing Controller API..."
sleep 5
curl -s http://localhost:8000/health | jq . || echo "Controller not ready yet"

echo ""
echo "Available API endpoints:"
echo "- Health check: curl http://10.102.199.42:8000/health"
echo "- VPN endpoints: curl http://10.102.199.42:8000/api/vpns"
echo "- Scan endpoints: curl -X POST http://10.102.199.42:8000/api/scan/dns-lookup"

# Save port forward PID for later cleanup
echo $CONTROLLER_PORT_FORWARD_PID > /tmp/controller-port-forward.pid
echo "Controller port forward PID saved to /tmp/controller-port-forward.pid"

echo ""
echo "=== Environment Variables for testing ==="
echo "export CONTROLLER_URL=http://10.102.199.42:8000"
echo "export SCANNER_NODE_URL=http://10.102.199.37:8002"
