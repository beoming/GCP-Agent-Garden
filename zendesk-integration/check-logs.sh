#!/bin/bash
# Zendesk 티켓 조회 로그 확인 스크립트

PROJECT_ID="gsneotek-ncc-demo"
REGION="us-east4"
INTEGRATION_NAME="ExecuteConnection"
CONNECTION_NAME="ncczendesk"

echo "=== Zendesk 티켓 조회 로그 확인 ==="
echo ""

echo "1. Agent Engine 로그 (최근 20개):"
echo "-----------------------------------"
gcloud logging read "resource.type=aiplatform.googleapis.com/ReasoningEngine AND jsonPayload.message=~\"zendesk\"" \
  --project=$PROJECT_ID \
  --limit=20 \
  --format="table(timestamp,jsonPayload.message)" \
  2>/dev/null || echo "로그를 찾을 수 없습니다."

echo ""
echo "2. Application Integration 로그 (최근 20개):"
echo "-----------------------------------"
gcloud logging read "resource.type=integrations.googleapis.com/Integration AND resource.labels.integration_name=$INTEGRATION_NAME" \
  --project=$PROJECT_ID \
  --limit=20 \
  --format="table(timestamp,jsonPayload.message)" \
  2>/dev/null || echo "로그를 찾을 수 없습니다."

echo ""
echo "3. Integration Connector 로그 (최근 20개):"
echo "-----------------------------------"
gcloud logging read "resource.type=connectors.googleapis.com/Connection AND resource.labels.connection_name=$CONNECTION_NAME" \
  --project=$PROJECT_ID \
  --limit=20 \
  --format="table(timestamp,jsonPayload.message)" \
  2>/dev/null || echo "로그를 찾을 수 없습니다."

echo ""
echo "4. 모든 Zendesk 관련 로그 (최근 50개):"
echo "-----------------------------------"
gcloud logging read "jsonPayload.message=~\"zendesk\" OR jsonPayload.message=~\"Zendesk\" OR jsonPayload.message=~\"ticket\" OR jsonPayload.message=~\"Ticket\"" \
  --project=$PROJECT_ID \
  --limit=50 \
  --format="table(timestamp,resource.type,jsonPayload.message)" \
  2>/dev/null || echo "로그를 찾을 수 없습니다."
