#!/bin/bash

echo "=== Testing Scanner System với Scanner Node API ==="

# 1. Test Controller health
echo "1. Testing Controller health..."
curl -s http://localhost:8001/api/tools | jq .

# 2. Test Scanner Node API health  
echo "2. Testing Scanner Node API health..."
curl -s http://localhost:8002/health

# 3. Test DNS lookup scan
echo "3. Creating DNS lookup scan..."
SCAN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/scan/dns-lookup \
  -H "Content-Type: application/json" \
  -d '{
    "targets": ["google.com", "github.com"],
    "options": {}
  }')
echo "Scan response: $SCAN_RESPONSE"

# Extract job_id từ response
JOB_ID=$(echo $SCAN_RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# 4. Check scan job status
echo "4. Checking scan job status..."
curl -s http://localhost:8001/api/scan_jobs/$JOB_ID | jq .

# 5. Wait và check scan results
echo "5. Waiting 30 seconds for scan completion..."
sleep 30

echo "6. Checking scan results..."
curl -s http://localhost:8001/api/scan_results | jq .

echo "=== Test completed ==="
