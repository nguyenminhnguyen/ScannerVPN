# Makefile for Controller only
# For VM1 (Ubuntu - 10.102.199.42)

.PHONY: help build push deploy logs clean test

REGISTRY := nguyenminhnguyen
TAG      := latest
NAMESPACE := scan-system

help:
	@echo "Controller Build & Deploy"
	@echo "========================"
	@echo "Available commands:"
	@echo "  make build       Build controller image"
	@echo "  make push        Push controller to Docker Hub"
	@echo "  make deploy      Deploy controller to K8s"
	@echo "  make logs        View controller logs"
	@echo "  make clean       Clean controller resources"
	@echo "  make test        Test controller APIs"
	@echo "  make health      Health check controller"

build:
	@echo "🔨 Building Controller image..."
	@eval $$(minikube docker-env); docker build --no-cache -f Dockerfile -t $(REGISTRY)/controller:$(TAG) .
	@echo "✅ Controller image built: $(REGISTRY)/controller:$(TAG)"

push: build
	@echo "🚀 Pushing Controller to Docker Hub..."
	docker push $(REGISTRY)/controller:$(TAG)
	@echo "✅ Controller image pushed"

deploy:
	@echo "🚀 Deploying Controller to Kubernetes..."
	kubectl apply -f ../manifests/namespace.yaml
	kubectl apply -f ../manifests/controller-rbac.yaml
	kubectl apply -f ../manifests/controller-deployment.yaml
	kubectl apply -f ../manifests/controller-service.yaml
	kubectl apply -f ../manifests/controller-nodeport.yaml
	@echo "⏳ Waiting for Controller to be ready..."
	kubectl wait --for=condition=available --timeout=300s deployment/controller -n $(NAMESPACE)
	@echo "✅ Controller deployed successfully"

logs:
	@echo "📋 Controller logs:"
	kubectl logs -n $(NAMESPACE) deployment/controller -f

clean:
	@echo "🧹 Cleaning Controller resources..."
	kubectl delete deployment controller -n $(NAMESPACE) --ignore-not-found
	kubectl delete service controller -n $(NAMESPACE) --ignore-not-found
	kubectl delete service controller-nodeport -n $(NAMESPACE) --ignore-not-found

test:
	@echo "🧪 Testing Controller APIs..."
	@echo "Health check:"
	curl -f http://10.102.199.42:8000/health || echo "Health check failed"
	@echo "\nVPN API test:"
	curl -f http://10.102.199.42:8000/api/vpns || echo "VPN API failed"
	@echo "\nAPI docs:"
	curl -f http://10.102.199.42:8000/docs >/dev/null && echo "API docs OK" || echo "API docs failed"

health:
	@echo "🔍 Controller health check..."
	kubectl get pods -n $(NAMESPACE) -l app=controller
	@echo "Service status:"
	kubectl get svc -n $(NAMESPACE) controller controller-nodeport
	@echo "External access test:"
	curl -f http://10.102.199.42:8000/health && echo "✅ Controller healthy" || echo "❌ Controller not accessible"

rebuild: clean build deploy
	@echo "✅ Controller rebuilt and redeployed"

port-forward:
	@echo "🌐 Setting up port forwarding for Controller..."
	@echo "Controller API will be available at http://localhost:8000"
	kubectl port-forward -n $(NAMESPACE) service/controller 8000:8000

port-forward-bg:
	@echo "🌐 Setting up background port forwarding for Controller..."
	@echo "Controller API will be available at http://localhost:8000"
	kubectl port-forward -n $(NAMESPACE) service/controller 8000:8000 &

port-forward-external:
	@echo "🌐 Setting up external port forwarding for Controller..."
	@echo "Controller API will be available at http://10.102.199.42:8000"
	kubectl port-forward --address 0.0.0.0 -n $(NAMESPACE) service/controller 8000:8000

port-forward-external-bg:
	@echo "🌐 Setting up external background port forwarding for Controller..."
	@echo "Controller API will be available at http://10.102.199.42:8000"
	kubectl port-forward --address 0.0.0.0 -n $(NAMESPACE) service/controller 8000:8000 &

test-external:
	@echo "🧪 Testing Controller APIs via external port-forward..."
	@echo "Health check:"
	curl -f http://10.102.199.42:8000/health || echo "Health check failed"
	@echo "\nDebug info:"
	curl -f http://10.102.199.42:8000/debug/info || echo "Debug info failed"
	@echo "\nVPN API test (sync):"
	curl -f http://10.102.199.42:8000/api/vpns/test || echo "VPN API failed"
