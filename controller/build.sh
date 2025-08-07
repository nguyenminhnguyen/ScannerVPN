#!/bin/bash
#
# Controller Build Script for VM1 (Ubuntu - 10.102.199.42)
#
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REGISTRY="nguyenminhnguyen"
TAG="latest"

usage() {
  cat <<EOF
Usage: $0 {build|push|deploy|full|clean|test}

  build     Build controller image only
  push      Build and push to Docker Hub
  deploy    Deploy controller to K8s
  full      Build + Push + Deploy
  clean     Clean controller resources
  test      Test controller APIs

EOF
}

case "$1" in
  build)
    echo -e "${BLUE}🔨 Building Controller image...${NC}"
    docker build -f Dockerfile -t $REGISTRY/controller:$TAG .
    echo -e "${GREEN}✅ Controller image built: $REGISTRY/controller:$TAG${NC}"
    ;;

  push)
    echo -e "${BLUE}🔨 Building and pushing Controller...${NC}"
    docker build -f Dockerfile -t $REGISTRY/controller:$TAG .
    docker push $REGISTRY/controller:$TAG
    echo -e "${GREEN}✅ Controller image pushed to Docker Hub${NC}"
    ;;

  deploy)
    echo -e "${BLUE}🚀 Deploying Controller to Kubernetes...${NC}"
    kubectl apply -f ../manifests/namespace.yaml
    kubectl apply -f ../manifests/controller-rbac.yaml
    kubectl apply -f ../manifests/controller-deployment.yaml
    kubectl apply -f ../manifests/controller-service.yaml
    kubectl apply -f ../manifests/controller-nodeport.yaml
    
    echo -e "${YELLOW}⏳ Waiting for Controller to be ready...${NC}"
    kubectl wait --for=condition=available --timeout=300s deployment/controller -n scan-system
    
    echo -e "${GREEN}✅ Controller deployed successfully${NC}"
    echo -e "${BLUE}📋 Controller status:${NC}"
    kubectl get pods,svc -n scan-system -l app=controller
    ;;

  full)
    echo -e "${BLUE}🚀 Full deployment: Build + Push + Deploy${NC}"
    $0 push
    $0 deploy
    echo -e "${GREEN}✅ Full Controller deployment completed${NC}"
    ;;

  clean)
    echo -e "${YELLOW}🧹 Cleaning Controller resources...${NC}"
    kubectl delete deployment controller -n scan-system --ignore-not-found
    kubectl delete service controller controller-nodeport -n scan-system --ignore-not-found
    echo -e "${GREEN}✅ Controller resources cleaned${NC}"
    ;;

  test)
    echo -e "${BLUE}🧪 Testing Controller APIs...${NC}"
    echo "Health check:"
    curl -f http://10.102.199.42:8000/health && echo -e "${GREEN}✅ Health OK${NC}" || echo -e "${RED}❌ Health failed${NC}"
    
    echo "VPN API test:"
    curl -f http://10.102.199.42:8000/api/vpns >/dev/null 2>&1 && echo -e "${GREEN}✅ VPN API OK${NC}" || echo -e "${RED}❌ VPN API failed${NC}"
    
    echo "Pod status:"
    kubectl get pods -n scan-system -l app=controller
    ;;

  *)
    usage
    ;;
esac
