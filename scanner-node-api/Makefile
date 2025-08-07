# Makefile for Scanner Node + Tools
# For VM2 (Kali - 10.102.199.37)

.PHONY: help build-scanner build-tools build-all push deploy logs clean test health rebuild port-forward-external port-forward-external-bg test-external logs-jobs status clean-jobs

REGISTRY := nguyenminhnguyen
TAG      := latest
NAMESPACE := scan-system

help:
	@echo "Scanner Node + Tools Build & Deploy"
	@echo "=================================="
	@echo "Available commands:"
	@echo "  make build-scanner       Build scanner-node-api image"
	@echo "  make build-tools         Build all scan tool images"
	@echo "  make build-all           Build scanner + tools"
	@echo "  make push                Push all images to Docker Hub"
	@echo "  make deploy              Deploy scanner node to K8s"
	@echo "  make logs                View scanner node logs"
	@echo "  make logs-jobs           View recent scan job logs"
	@echo "  make clean               Clean scanner resources"
	@echo "  make clean-jobs          Clean old scan jobs"
	@echo "  make test                Test scanner node APIs"
	@echo "  make health              Health check scanner node"
	@echo "  make status              Show comprehensive system status"
	@echo "  make rebuild             Clean, build and redeploy"
	@echo "  make port-forward-external   External port forwarding"
	@echo "  make test-external       Test APIs via external access"

build-scanner:
	@echo "🔨 Building Scanner Node API..."
	@eval $$(minikube docker-env); docker build --no-cache -f Dockerfile -t $(REGISTRY)/scanner-node-api:$(TAG) .
	@echo "✅ Scanner Node API built: $(REGISTRY)/scanner-node-api:$(TAG)"

build-tools:
	@echo "🔨 Building scan tools..."
	@eval $$(minikube docker-env); docker build --no-cache -t $(REGISTRY)/dns-lookup:$(TAG) ../scan-node-tools/dns-lookup
	@eval $$(minikube docker-env); docker build --no-cache -t $(REGISTRY)/port-scan:$(TAG) ../scan-node-tools/port-scan
	@eval $$(minikube docker-env); docker build --no-cache -t $(REGISTRY)/httpx-scan:$(TAG) ../scan-node-tools/httpx-scan
	@echo "✅ All scan tools built"

build-all: build-scanner build-tools
	@echo "✅ All Scanner Node components built"

push: build-all
	@echo "🚀 Pushing Scanner Node images to Docker Hub..."
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
	kubectl delete rolebinding scanner-node-rolebinding -n $(NAMESPACE) --ignore-not-found
	kubectl delete role scanner-node-role -n $(NAMESPACE) --ignore-not-found
	kubectl delete serviceaccount scanner-node-sa -n $(NAMESPACE) --ignore-not-found

test:
	@echo "🧪 Testing Scanner Node APIs..."
	@echo "Health check:"
	curl -f http://10.102.199.37:8000/health || echo "Health check failed"
	@echo "\nPod status:"
	kubectl get pods -n $(NAMESPACE) -l app=scanner-node-api
	@echo "\nService test (internal):"
	kubectl exec -n $(NAMESPACE) deployment/scanner-node-api -- curl -f http://localhost:8000/health || echo "Internal health check failed"

health:
	@echo "🔍 Scanner Node health check..."
	kubectl get pods -n $(NAMESPACE) -l app=scanner-node-api
	@echo "Service status:"
	kubectl get svc -n $(NAMESPACE) scanner-node-api
	@echo "External access test:"
	curl -f http://10.102.199.37:8000/health && echo "✅ Scanner Node healthy" || echo "❌ Scanner Node not accessible"

rebuild: clean build-all deploy
	@echo "✅ Scanner Node rebuilt and redeployed"

port-forward-external:
	@echo "🌐 Setting up external port forwarding for Scanner Node..."
	@echo "Scanner Node API will be available at http://10.102.199.37:8000"
	kubectl port-forward --address 0.0.0.0 -n $(NAMESPACE) service/scanner-node-api 8000:8000

port-forward-external-bg:
	@echo "🌐 Setting up external background port forwarding for Scanner Node..."
	@echo "Scanner Node API will be available at http://10.102.199.37:8000"
	kubectl port-forward --address 0.0.0.0 -n $(NAMESPACE) service/scanner-node-api 8000:8000 &

test-external:
	@echo "🧪 Testing Scanner Node APIs via external port-forward..."
	@echo "Health check:"
	curl -f http://10.102.199.37:8000/health || echo "Health check failed"
	@echo "\nTest scan job creation:"
	curl -X POST http://10.102.199.37:8000/api/scan/execute \
		-H "Content-Type: application/json" \
		-d '{"tool":"dns-lookup","targets":["google.com"],"vpn_assignment":{"filename":"test.ovpn","hostname":"test-vpn"}}' \
		|| echo "Scan job creation failed"

logs-jobs:
	@echo "📋 Recent scan job logs:"
	@for job in $$(kubectl get jobs -n $(NAMESPACE) --sort-by=.metadata.creationTimestamp -o name | tail -5); do \
		echo "=== $$job ==="; \
		kubectl logs -n $(NAMESPACE) $$job --tail=20 || true; \
		echo ""; \
	done

status:
	@echo "📊 Scanner Node System Status:"
	@echo "Pods:"
	kubectl get pods -n $(NAMESPACE) -l app=scanner-node-api
	@echo "\nServices:"
	kubectl get svc -n $(NAMESPACE) scanner-node-api
	@echo "\nRecent Jobs:"
	kubectl get jobs -n $(NAMESPACE) --sort-by=.metadata.creationTimestamp | tail -10
	@echo "\nNode Resources:"
	kubectl top pods -n $(NAMESPACE) --no-headers | grep scanner-node || echo "Metrics not available"

clean-jobs:
	@echo "🧹 Cleaning old scan jobs..."
	kubectl delete jobs --field-selector status.successful=1 -n $(NAMESPACE) --ignore-not-found
	kubectl delete jobs --field-selector status.failed=1 -n $(NAMESPACE) --ignore-not-found
	@echo "✅ Old jobs cleaned"
