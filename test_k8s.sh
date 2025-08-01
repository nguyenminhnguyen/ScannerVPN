#!/bin/bash
#
# Kubernetes test script for distributed scanning system
#
set -e

# Màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE="scan-system"
CONTROLLER_SERVICE="http://controller.scan-system.svc.cluster.local"

usage() {
  cat <<EOF
Usage: $0 {deploy|test|monitor|logs|cleanup|cleanup all}

  deploy        Triển khai Controller và các resource cần thiết
  test          Chạy end-to-end test suite
  monitor       Xem pod & service trong namespace
  logs          Xem logs của controller
  cleanup       Xóa deployment/controller, service/controller, jobs trong namespace
  cleanup all   Xóa toàn bộ resources trong namespace, bao gồm cả namespace
EOF
}

case "$1" in
  deploy)
    echo -e "${BLUE}🔨 Deploying Controller and Scanner Node API${NC}"
    kubectl apply -f manifests/namespace.yaml
    kubectl apply -f manifests/controller-rbac.yaml
    kubectl apply -f manifests/scanner-node-rbac.yaml
    kubectl apply -f manifests/controller-deployment.yaml
    kubectl apply -f manifests/controller-service.yaml
    kubectl apply -f manifests/scanner-node-api-deployment.yaml
    kubectl apply -f manifests/scanner-node-api-service.yaml
    
    echo -e "${BLUE}⏳ Waiting for deployments to be ready...${NC}"
    kubectl wait --for=condition=available --timeout=300s deployment/controller -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/scanner-node-api -n $NAMESPACE

    echo -e "${GREEN}✔️ Deploy completed${NC}"
    kubectl get all -n $NAMESPACE
    ;;

  test)
    echo -e "${BLUE}🧪 Chạy test suite end-to-end${NC}"
    # Giả sử bạn có script chạy test, ví dụ ./run_tests.sh
    ./run_tests.sh
    ;;

  monitor)
    echo -e "${BLUE}📊 Hiện trạng cluster${NC}"
    kubectl get pods,svc -n $NAMESPACE
    ;;

  logs)
    echo -e "${BLUE}📋 Following Controller logs${NC}"
    kubectl logs -n $NAMESPACE deployment/controller -f
    ;;

  cleanup)
    echo -e "${YELLOW}🧹 Xóa các resource chung${NC}"
    kubectl delete deployment controller -n $NAMESPACE  --ignore-not-found
    kubectl delete service controller -n $NAMESPACE     --ignore-not-found
    kubectl delete job --all -n $NAMESPACE              --ignore-not-found
    ;;

  "cleanup all")
    echo -e "${YELLOW}🧹 Xóa toàn bộ namespace và resources${NC}"
    kubectl delete namespace $NAMESPACE                  --ignore-not-found
    ;;

  *)
    usage
    ;;
esac
