#!/bin/bash

echo "=== Testing Full K8s Deployment ==="

# 1. Build images
echo "1. Building all images for Minikube..."
eval $(minikube docker-env)
make build

# 2. Deploy to K8s
echo "2. Deploying to Kubernetes..."
make deploy

# 3. Wait for pods to be ready
echo "3. Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=controller -n scan-system --timeout=120s
kubectl wait --for=condition=ready pod -l app=scanner-node-api -n scan-system --timeout=120s

# 4. Port forward services
echo "4. Setting up port forwarding..."
kubectl port-forward -n scan-system svc/controller 8001:8000 &
CONTROLLER_PF=$!
kubectl port-forward -n scan-system svc/scanner-node-api 8002:8000 &
SCANNER_PF=$!

# Wait for port forwarding to be ready
sleep 5

# 5. Test services
echo "5. Testing services..."
echo "Testing Controller..."
curl -s http://localhost:8001/api/tools | jq . || echo "Controller not ready"

echo "Testing Scanner Node API..."
curl -s http://localhost:8002/health | jq . || echo "Scanner Node API not ready"

# 6. Test scan creation
echo "6. Creating test scan..."
SCAN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/scan/dns-lookup \
  -H "Content-Type: application/json" \
  -d '{"targets": ["google.com"], "options": {}}')
echo "Scan response: $SCAN_RESPONSE"

# 7. Check jobs and pods
echo "7. Checking Kubernetes jobs and pods..."
kubectl get jobs,pods -n scan-system

# 8. Check scan jobs in Controller
echo "8. Checking scan jobs in Controller..."
sleep 5
curl -s http://localhost:8001/api/scan_jobs | jq .

# 9. Wait and check results
echo "9. Waiting 30 seconds for scan completion..."
sleep 30

echo "Checking scan results..."
curl -s http://localhost:8001/api/scan_results | jq .

# Cleanup port forwarding
kill $CONTROLLER_PF $SCANNER_PF 2>/dev/null

echo "=== K8s test completed ==="
echo ""
echo "To access services:"
echo "Controller: kubectl port-forward -n scan-system svc/controller 8001:8000"
echo "Scanner Node API: kubectl port-forward -n scan-system svc/scanner-node-api 8002:8000"
echo ""
echo "To cleanup:"
echo "make clean"
