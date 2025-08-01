# Testing Scanner System with Kubernetes

## 🏗️ Architecture

```
Kubernetes Cluster
├── Controller Pod (Port 8000)
│   ├── FastAPI
│   ├── SQLite Database  
│   ├── Business Logic
│   └── HTTP calls to Scanner Node API
│
└── Scanner Node API Pod (Port 8000)
    ├── FastAPI
    ├── Kubernetes Client
    ├── Job Creation
    └── Tool Container Management
```

## 🚀 Full Kubernetes Deployment

### 1. Build & Deploy
```bash
# Start Minikube
minikube start --driver=docker --memory=4096 --cpus=2

# Build all images
make build

# Deploy to K8s
make deploy

# Test full deployment  
make test-k8s-full
```

### 2. Manual K8s Testing
```bash
# Build images in Minikube context
eval $(minikube docker-env)
make build

# Deploy services
kubectl apply -f manifests/

# Check deployment
kubectl get all -n scan-system

# Port forward for testing
kubectl port-forward -n scan-system svc/controller 8001:8000 &
kubectl port-forward -n scan-system svc/scanner-node-api 8002:8000 &
```

## 🧪 Manual Testing

### Controller API (Port 8001)
```bash
# List available tools
curl http://localhost:8001/api/tools

# Create DNS scan
curl -X POST http://localhost:8001/api/scan/dns-lookup \
  -H "Content-Type: application/json" \
  -d '{"targets": ["google.com"], "options": {}}'

# Check scan jobs
curl http://localhost:8001/api/scan_jobs

# Check scan results  
curl http://localhost:8001/api/scan_results
```

### Scanner Node API (Port 8002)
```bash
# Health check
curl http://localhost:8002/health

# Direct scan execution (for testing)
curl -X POST http://localhost:8002/api/scan/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "dns-lookup",
    "targets": ["github.com"],
    "job_id": "test-123",
    "controller_callback_url": "http://controller:8000"
  }'
```

## 🔧 Production Deployment

### VM1 - Controller
```bash
# Build and run Controller
docker build -f controller/Dockerfile -t scanner-controller .
docker run -d -p 8001:8000 \
  -e SCANNER_NODE_URL=http://vm2:8002 \
  -e DATABASE_URL=sqlite:///./data/scan_results.db \
  -v /data/scanner:/app/data \
  scanner-controller
```

### VM2 - Scanner Node + Kubernetes
```bash
# Setup Kubernetes cluster
minikube start

# Build Scanner Node API
docker build -t scanner-node-api ./scanner-node-api

# Deploy to Kubernetes
kubectl create namespace scan-system
kubectl apply -f manifests/scanner-node-api-deployment.yaml

# Load tool images
docker build -t l4sttr4in/dns-lookup:latest ./scan-node-tools/dns-lookup
docker build -t l4sttr4in/port-scan:latest ./scan-node-tools/port-scan
docker build -t l4sttr4in/httpx-scan:latest ./scan-node-tools/httpx-scan
```

## 📋 API Flow

1. **User** → Controller `/api/scan/dns-lookup`
2. **Controller** → Scanner Node API `/api/scan/execute`  
3. **Scanner Node API** → Kubernetes Job with tool container
4. **Tool Container** → Executes scan and sends results back
5. **Controller** → Stores results in database

## 🎯 Key Features

- ✅ **Separation of Concerns**: Controller (business) vs Scanner Node (execution)
- ✅ **Scalability**: Multiple Scanner Nodes supported  
- ✅ **Resource Isolation**: Scanning workloads isolated in K8s
- ✅ **API-driven**: RESTful communication between components
- ✅ **Database Tracking**: Job status and results persistence
