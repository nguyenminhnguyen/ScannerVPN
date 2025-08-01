#!/bin/bash
# Setup script cho VM1 (Controller)
# IP VM1: 10.102.199.42
# IP VM2: 10.102.199.37

echo "=== Setting up Controller on VM1 ==="

# Build Controller image
echo "Building Controller image..."
docker build -f controller/Dockerfile -t scanner-controller .

# Create data directory
echo "Creating data directory..."
mkdir -p $HOME/scanner-data

# Stop existing container if running
echo "Stopping existing container..."
docker stop scanner-controller 2>/dev/null || true
docker rm scanner-controller 2>/dev/null || true

# Run Controller container
echo "Running Controller container..."
docker run -d \
  --name scanner-controller \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./data/scan_results.db \
  -e SCANNER_NODE_URL=http://10.102.199.37:8002 \
  -v $HOME/scanner-data:/app/data \
  --restart unless-stopped \
  scanner-controller

# Check status
echo "Checking container status..."
docker ps | grep scanner-controller
docker logs scanner-controller --tail 10

echo "=== Controller setup complete ==="
echo "Controller URL: http://10.102.199.42:8000"
echo "Scanner Node URL: http://10.102.199.37:8002"

# Test commands
echo ""
echo "Test commands:"
echo "curl http://localhost:8000/health"
echo "curl http://localhost:8000/api/tools"
