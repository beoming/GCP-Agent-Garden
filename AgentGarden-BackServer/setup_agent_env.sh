#!/bin/bash

# Agent Engine 환경 변수 설정 스크립트
# 이 스크립트는 travel-concierge 프로젝트의 .env 파일에 환경 변수를 추가합니다.

set -e

TRAVEL_CONCIERGE_DIR="/Users/Shared/Files From d.localized/GSNeotek/Work/GCP/gcp-adk-samples-main/python/agents/travel-concierge"
ENV_FILE="${TRAVEL_CONCIERGE_DIR}/.env"

FLIGHT_API_URL="https://flight-search-api-nelifvy57a-uc.a.run.app"
HOTEL_API_URL="https://hotel-search-api-nelifvy57a-uc.a.run.app"

echo "🔧 Agent Engine 환경 변수 설정 중..."
echo ""

# .env 파일이 존재하는지 확인
if [ ! -f "${ENV_FILE}" ]; then
    echo "⚠️  .env 파일이 없습니다. 생성합니다..."
    touch "${ENV_FILE}"
fi

# 환경 변수 추가 (이미 존재하면 업데이트)
if grep -q "^FLIGHT_SEARCH_API_URL=" "${ENV_FILE}"; then
    # 이미 존재하면 업데이트
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^FLIGHT_SEARCH_API_URL=.*|FLIGHT_SEARCH_API_URL=${FLIGHT_API_URL}|" "${ENV_FILE}"
    else
        # Linux
        sed -i "s|^FLIGHT_SEARCH_API_URL=.*|FLIGHT_SEARCH_API_URL=${FLIGHT_API_URL}|" "${ENV_FILE}"
    fi
    echo "✅ FLIGHT_SEARCH_API_URL 업데이트됨"
else
    # 존재하지 않으면 추가
    echo "FLIGHT_SEARCH_API_URL=${FLIGHT_API_URL}" >> "${ENV_FILE}"
    echo "✅ FLIGHT_SEARCH_API_URL 추가됨"
fi

if grep -q "^HOTEL_SEARCH_API_URL=" "${ENV_FILE}"; then
    # 이미 존재하면 업데이트
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^HOTEL_SEARCH_API_URL=.*|HOTEL_SEARCH_API_URL=${HOTEL_API_URL}|" "${ENV_FILE}"
    else
        # Linux
        sed -i "s|^HOTEL_SEARCH_API_URL=.*|HOTEL_SEARCH_API_URL=${HOTEL_API_URL}|" "${ENV_FILE}"
    fi
    echo "✅ HOTEL_SEARCH_API_URL 업데이트됨"
else
    # 존재하지 않으면 추가
    echo "HOTEL_SEARCH_API_URL=${HOTEL_API_URL}" >> "${ENV_FILE}"
    echo "✅ HOTEL_SEARCH_API_URL 추가됨"
fi

echo ""
echo "🎉 환경 변수 설정 완료!"
echo ""
echo "📝 다음 단계:"
echo "1. Agent Engine을 재배포하세요:"
echo "   cd ${TRAVEL_CONCIERGE_DIR}"
echo "   uv run python deployment/deploy.py --create"
echo ""
echo "2. 또는 기존 Agent Engine을 업데이트하려면 deploy.py에 --update 옵션을 추가해야 합니다."


