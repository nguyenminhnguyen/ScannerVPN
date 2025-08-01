#!/bin/bash

echo "=== Manual Testing Scanner System ==="

# Build images
echo "1. Building images..."
docker build -f controller/Dockerfile -t l4sttr4in/controller:latest controller/
docker build -t l4sttr4in/scanner-node-api:latest ./scanner-node-api
docker build -t l4sttr4in/dns-lookup:latest ./scan-node-tools/dns-lookup

# Stop existing containers
echo "2. Stopping existing containers..."
docker stop controller scanner-node-api 2>/dev/null || true
docker rm controller scanner-node-api 2>/dev/null || true

# Start Controller
echo "3. Starting Controller..."
docker run -d --name controller \
  -p 8001:8000 \
  -e DATABASE_URL=sqlite:///./data/scan_results.db \
  -e SCANNER_NODE_URL=http://host.docker.internal:8002 \
  -e CONTROLLER_CALLBACK_URL=http://host.docker.internal:8001 \
  l4sttr4in/controller:latest

# Start Scanner Node API
echo "4. Starting Scanner Node API..."
docker run -d --name scanner-node-api \
  -p 8002:8000 \
  -e REGISTRY=l4sttr4in \
  -e TAG=latest \
  -e NAMESPACE=scan-system \
  l4sttr4in/scanner-node-api:latest

# Wait for services to start
echo "5. Waiting for services to start..."
sleep 10

# Test Controller
echo "6. Testing Controller..."
curl -s http://localhost:8001/api/tools | jq . || echo "Controller not ready"

# Test Scanner Node API
echo "7. Testing Scanner Node API..."
curl -s http://localhost:8002/health | jq . || echo "Scanner Node API not ready"

# Test scan creation
echo "8. Creating test scan..."
SCAN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/scan/dns-lookup \
  -H "Content-Type: application/json" \
  -d '{"targets": ["google.com"], "options": {}}')
echo "Scan response: $SCAN_RESPONSE"

# Check scan jobs
echo "9. Checking scan jobs..."
curl -s http://localhost:8001/api/scan_jobs | jq .

echo "=== Manual test completed ==="
echo "Controller: http://localhost:8001"
echo "Scanner Node API: http://localhost:8002"
echo ""
echo "To stop:"
echo "docker stop controller scanner-node-api"
echo "docker rm controller scanner-node-api"
