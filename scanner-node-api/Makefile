# Makefile for Scanner Node + Tools
# For VM2 (Kali - 10.102.199.37)

.PHONY: help build-scanner build-tools build-all push deploy logs clean test

REGISTRY := nguyenminhnguyen
TAG      := latest
NAMESPACE := scan-system

help:
	@echo "Scanner Node + Tools Build & Deploy"
	@echo "=================================="
	@echo "Available commands:"
	@echo "  make build-scanner   Build scanner-node-api image"
	@echo "  make build-tools     Build all scan tool images"
	@echo "  make build-all       Build scanner + tools"
	@echo "  make push           Push all images to Docker Hub"
	@echo "  make deploy         Deploy scanner node to K8s"
	@echo "  make logs           View scanner node logs"
	@echo "  make clean          Clean scanner resources"
	@echo "  make test           Test scanner node"

build-scanner:
	@echo "🔨 Building Scanner Node API..."
	docker build -t $(REGISTRY)/scanner-node-api:$(TAG) .
	@echo "✅ Scanner Node API built"

build-tools:
	@echo "🔨 Building scan tools..."
	docker build -t $(REGISTRY)/dns-lookup:$(TAG) ../scan-node-tools/dns-lookup
	docker build -t $(REGISTRY)/port-scan:$(TAG) ../scan-node-tools/port-scan
	docker build -t $(REGISTRY)/httpx-scan:$(TAG) ../scan-node-tools/httpx-scan
	@echo "✅ All scan tools built"

build-all: build-scanner build-tools
	@echo "✅ All Scanner Node components built"

push: build-all
	@echo "🚀 Pushing Scanner Node images..."
	docker push $(REGISTRY)/scanner-node-api:$(TAG)
	docker push $(REGISTRY)/dns-lookup:$(TAG)
	docker push $(REGISTRY)/port-scan:$(TAG)
	docker push $(REGISTRY)/httpx-scan:$(TAG)
	@echo "✅ All images pushed"

deploy:
	@echo "🚀 Deploying Scanner Node to Kubernetes..."
	kubectl apply -f ../manifests/namespace.yaml
	kubectl apply -f ../manifests/scanner-node-rbac.yaml
	kubectl apply -f ../manifests/scanner-node-api-deployment.yaml
	kubectl apply -f ../manifests/scanner-node-api-service.yaml
	@echo "⏳ Waiting for Scanner Node to be ready..."
	kubectl wait --for=condition=available --timeout=300s deployment/scanner-node-api -n $(NAMESPACE)
	@echo "✅ Scanner Node deployed successfully"

logs:
	@echo "📋 Scanner Node logs:"
	kubectl logs -n $(NAMESPACE) deployment/scanner-node-api -f

clean:
	@echo "🧹 Cleaning Scanner Node resources..."
	kubectl delete deployment scanner-node-api -n $(NAMESPACE) --ignore-not-found
	kubectl delete service scanner-node-api -n $(NAMESPACE) --ignore-not-found
	kubectl delete jobs --all -n $(NAMESPACE) --ignore-not-found

test:
	@echo "🧪 Testing Scanner Node..."
	kubectl get pods -n $(NAMESPACE) -l app=scanner-node-api
	@echo "Service test:"
	kubectl exec -n $(NAMESPACE) deployment/scanner-node-api -- curl -f http://localhost:8000/health

health:
	@echo "🔍 Scanner Node health check..."
	kubectl get pods -n $(NAMESPACE) -l app=scanner-node-api
	kubectl get svc -n $(NAMESPACE) scanner-node-api

rebuild: clean build-all deploy
	@echo "✅ Scanner Node rebuilt and redeployed"
