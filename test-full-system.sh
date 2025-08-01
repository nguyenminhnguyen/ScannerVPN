#!/bin/bash
# Test script để verify full workflow
# Chạy từ VM1 hoặc bất kỳ máy nào có thể access both VMs

echo "=== Testing Scanner System ==="

VM1_IP="10.102.199.42"
VM2_IP="10.102.199.37"

echo "VM1 Controller: $VM1_IP:8000"
echo "VM2 Scanner Node: $VM2_IP:8002"

echo ""
echo "1. Testing Controller health..."
curl -s http://$VM1_IP:8000/health || echo "Controller health check failed"

echo ""
echo "2. Testing Scanner Node health..."
curl -s http://$VM2_IP:8002/health || echo "Scanner Node health check failed"

echo ""
echo "3. Testing Controller tools endpoint..."
curl -s http://$VM1_IP:8000/api/tools | jq .tools[].name || echo "Tools endpoint failed"

echo ""
echo "4. Running DNS lookup scan..."
curl -X POST http://$VM1_IP:8000/api/scan/dns-lookup \
  -H "Content-Type: application/json" \
  -d '{"targets": ["google.com"]}' \
  -s | jq . || echo "DNS scan failed"

echo ""
echo "5. Checking scan jobs..."
sleep 5
curl -s http://$VM1_IP:8000/api/scan_jobs | jq . || echo "Scan jobs check failed"

echo ""
echo "6. Checking scan results..."
sleep 10
curl -s http://$VM1_IP:8000/api/scan_results | jq . || echo "Scan results check failed"

echo ""
echo "=== Test complete ==="
