# Makefile for Distributed Scanner System - Kubernetes Only

.PHONY: help start-cluster stop-cluster cluster-status dev-setup \
        build-dns build-port build-httpx push-tools \
        build build-local build-and-push push \
        deploy test monitor logs clean clear-db scan \
        view-jobs view-results health status follow-logs

REGISTRY := nguyenminhnguyen
TAG      := latest

help:
	@echo "Distributed Scanner System - Kubernetes"
	@echo "======================================="
	@echo "Available commands:"
	@echo "  make start-cluster      Start Minikube cluster"
	@echo "  make stop-cluster       Stop Minikube cluster"
	@echo "  make cluster-status     Check cluster status"
	@echo "  make dev-setup          Setup development environment"
	@echo "  make build-dns          Build dns-lookup image"
	@echo "  make build-port         Build port-scan image"
	@echo "  make build-httpx        Build httpx-scan image"
	@echo "  make push-tools         Push all tool images"
	@echo "  make build              Build all images in Minikube"
	@echo "  make build-local        Build all images locally"
	@echo "  make build-and-push     Build & push controller + tools"
	@echo "  make push               Push images only"
	@echo "  make deploy             Deploy to Kubernetes"
	@echo "  make test               Test Kubernetes deployment"
	@echo "  make monitor            Monitor K8s resources"
	@echo "  make logs               View Kubernetes logs"
	@echo "  make clean              Clean up Kubernetes resources"
	@echo "  make clear-db           Restart controller to clear DB"
	@echo "  make scan               Dispatch a custom scan job"
	@echo "  make view-jobs          List scanner Jobs/Pods"
	@echo "  make view-results       Show scan results"
	@echo "  make health             Health-check services"
	@echo "  make status             Show cluster status"
	@echo "  make follow-logs        Follow controller logs"
	@echo "  make test-manual        Manual test without docker-compose"
	@echo "  make test-k8s-full      Full K8s deployment test"
	@echo "  make stop-manual        Stop manual test containers"

start-cluster:
	@echo "🚀 Starting Minikube..."
	minikube start --driver=docker --memory=2200 --cpus=2

stop-cluster:
	@echo "🛑 Stopping Minikube..."
	minikube stop

cluster-status:
	@echo "🔍 Cluster status:"
	minikube status
	kubectl cluster-info

dev-setup:
	@echo "🛠️  Dev-setup..."
	@which kubectl >/dev/null || (echo "kubectl missing" && exit 1)
	@which docker  >/dev/null || (echo "docker missing"  && exit 1)
	@which minikube>/dev/null || (echo "minikube missing"&& exit 1)
	@minikube status | grep -q Running || minikube start --driver=docker
	@echo "✅ Dev environment ready"

# -------------------------------------------------------------------
# Tool images
# -------------------------------------------------------------------
build-dns:
	@echo "🔨 Building dns-lookup image..."
	docker build -t $(REGISTRY)/dns-lookup:$(TAG) ./scan-node-tools/dns-lookup

build-port:
	@echo "🔨 Building port-scan image..."
	docker build -t $(REGISTRY)/port-scan:$(TAG) ./scan-node-tools/port-scan

build-httpx:
	@echo "🔨 Building httpx-scan image..."
	docker build -t $(REGISTRY)/httpx-scan:$(TAG) ./scan-node-tools/httpx-scan

push-tools: build-dns build-port build-httpx
	@echo "🚀 Pushing tool images..."
	docker push $(REGISTRY)/dns-lookup:$(TAG)
	docker push $(REGISTRY)/port-scan:$(TAG)
	docker push $(REGISTRY)/httpx-scan:$(TAG)

# -------------------------------------------------------------------
# Build controller + tools
# -------------------------------------------------------------------
build: build-dns build-port build-httpx
	@echo "🔨 Building controller + scanner-node-api + tools in Minikube..."
	@eval $(minikube docker-env)
	docker build -f controller/Dockerfile -t $(REGISTRY)/controller:$(TAG) controller/
	docker build -t $(REGISTRY)/scanner-node-api:$(TAG) ./scanner-node-api
	docker build -t $(REGISTRY)/dns-lookup:$(TAG) ./scan-node-tools/dns-lookup
	docker build -t $(REGISTRY)/port-scan:$(TAG) ./scan-node-tools/port-scan
	docker build -t $(REGISTRY)/httpx-scan:$(TAG) ./scan-node-tools/httpx-scan

build-local:
	@echo "🔨 Building controller + scanner-node-api + tools locally..."
	docker build -f controller/Dockerfile -t $(REGISTRY)/controller:$(TAG) controller/
	docker build -t $(REGISTRY)/scanner-node-api:$(TAG) ./scanner-node-api
	docker build -t $(REGISTRY)/dns-lookup:$(TAG) ./scan-node-tools/dns-lookup
	docker build -t $(REGISTRY)/port-scan:$(TAG) ./scan-node-tools/port-scan
	docker build -t $(REGISTRY)/httpx-scan:$(TAG) ./scan-node-tools/httpx-scan

build-and-push: build-local
	@echo "🚀 Pushing controller + tools..."
	docker push $(REGISTRY)/controller:$(TAG)
	make push-tools

push: build-and-push

# -------------------------------------------------------------------
# Kubernetes workflows
# -------------------------------------------------------------------
deploy:
	@echo "🚀 Deploying to Kubernetes..."
	chmod +x test_k8s.sh
	./test_k8s.sh deploy

test:
	@echo "🧪 Testing Kubernetes deployment..."
	chmod +x test_k8s.sh
	./test_k8s.sh test

monitor:
	@echo "🔍 Monitoring Kubernetes resources..."
	chmod +x test_k8s.sh
	./test_k8s.sh monitor

logs:
	@echo "📋 Viewing Kubernetes logs..."
	chmod +x test_k8s.sh
	./test_k8s.sh logs

clean:
	@echo "🧹 Cleaning up Kubernetes resources..."
	chmod +x test_k8s.sh
	./test_k8s.sh cleanup

clear-db:
	@echo "🗑️  Clearing scan results DB..."
	kubectl delete pod -n scan-system -l app=controller

scan:
	@echo "🎯 Dispatching custom scan..."
	@read -p "Tool (dns-lookup/port-scan/httpx-scan): " tool && \
	 read -p "Targets (comma-separated): " t && \
	 targets=$$(echo "$$t" | sed 's/,/","/g' | sed 's/^/"/' | sed 's/$$/"/') && \
	 curl -s -X POST http://localhost:8000/api/scan \
	   -H "Content-Type: application/json" \
	   -d '{"tool":"'"$$tool"'","targets":["'"$${targets//\"/}"'"],"options":{},"scanner_node_url":"http://scanner-node-api.scan-system.svc.cluster.local:8080"}' && \
	 echo "✅ Scan submitted."

view-jobs:
	@echo "📋 Jobs & Pods in scan-system"
	kubectl get jobs,pods -n scan-system

view-results:
	@echo "📊 Latest scan results"
	kubectl port-forward -n scan-system deployment/controller 8000:8000 >/dev/null 2>&1 & \
	sleep 2; \
	curl -s http://localhost:8000/api/scan_results; \
	kill %1

health:
	@echo "🔍 Health check Controller"
	kubectl port-forward -n scan-system svc/controller 8000:8000 >/dev/null 2>&1 & \
	sleep 2; \
	curl -s http://localhost:8000/docs >/dev/null && echo "OK" || echo "DOWN"; \
	kill %1

status:
	@echo "🔍 Cluster status"
	kubectl get nodes; \
	kubectl get all -n scan-system

follow-logs:
	@echo "📋 Following Controller logs"
	kubectl logs -n scan-system deployment/controller -f

test-manual:
	@echo "🧪 Running manual test..."
	chmod +x test_manual.sh
	./test_manual.sh

test-k8s-full:
	@echo "🧪 Running full K8s test..."
	chmod +x test_k8s_full.sh
	./test_k8s_full.sh

stop-manual:
	@echo "🛑 Stopping manual test containers..."
	docker stop controller scanner-node-api 2>/dev/null || true
	docker rm controller scanner-node-api 2>/dev/null || true
