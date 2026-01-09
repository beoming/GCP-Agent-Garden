#!/bin/bash

# Cloud Run 배포 스크립트
# 사용법: ./deploy.sh

set -e

# 프로젝트 설정
PROJECT_ID="gsneotek-ncc-demo"
REGION="us-central1"

# Artifact Registry 리포지토리 이름
REPOSITORY_NAME="backend-apis"

# 서비스 이름
FLIGHT_SERVICE_NAME="flight-search-api"
HOTEL_SERVICE_NAME="hotel-search-api"

# Artifact Registry 이미지 이름
FLIGHT_IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${FLIGHT_SERVICE_NAME}"
HOTEL_IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${HOTEL_SERVICE_NAME}"

echo "🚀 Cloud Run 배포를 시작합니다..."
echo "프로젝트: ${PROJECT_ID}"
echo "리전: ${REGION}"
echo ""

# gcloud 프로젝트 설정
echo "📋 GCP 프로젝트 설정 중..."
gcloud config set project ${PROJECT_ID}

# Artifact Registry API 활성화
echo "🔧 Artifact Registry API 활성화 중..."
gcloud services enable artifactregistry.googleapis.com

# Artifact Registry 리포지토리 생성 (이미 존재하면 무시)
echo "📦 Artifact Registry 리포지토리 확인/생성 중..."
gcloud artifacts repositories create ${REPOSITORY_NAME} \
  --repository-format=docker \
  --location=${REGION} \
  --description="Backend APIs for Travel Concierge" \
  || echo "리포지토리가 이미 존재합니다."

# 항공편 검색 API 배포
echo ""
echo "✈️  항공편 검색 API 배포 중..."
cd flight_search_api

# Docker 이미지 빌드 및 푸시
echo "  📦 Docker 이미지 빌드 및 푸시 중..."
gcloud builds submit --tag ${FLIGHT_IMAGE_NAME} --region=${REGION}

# Cloud Run에 배포
echo "  🚀 Cloud Run에 배포 중..."
gcloud run deploy ${FLIGHT_SERVICE_NAME} \
  --image ${FLIGHT_IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300

# 서비스 URL 가져오기
FLIGHT_URL=$(gcloud run services describe ${FLIGHT_SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)')

echo "  ✅ 항공편 검색 API 배포 완료!"
echo "  📍 URL: ${FLIGHT_URL}"
cd ..

# 호텔 검색 API 배포
echo ""
echo "🏨 호텔 검색 API 배포 중..."
cd hotel_search_api

# Docker 이미지 빌드 및 푸시
echo "  📦 Docker 이미지 빌드 및 푸시 중..."
gcloud builds submit --tag ${HOTEL_IMAGE_NAME} --region=${REGION}

# Cloud Run에 배포
echo "  🚀 Cloud Run에 배포 중..."
gcloud run deploy ${HOTEL_SERVICE_NAME} \
  --image ${HOTEL_IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300

# 서비스 URL 가져오기
HOTEL_URL=$(gcloud run services describe ${HOTEL_SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)')

echo "  ✅ 호텔 검색 API 배포 완료!"
echo "  📍 URL: ${HOTEL_URL}"
cd ..

echo ""
echo "🎉 모든 서비스 배포가 완료되었습니다!"
echo ""
echo "📝 다음 단계:"
echo "1. Agent Engine의 환경 변수를 설정하세요:"
echo "   FLIGHT_SEARCH_API_URL=${FLIGHT_URL}"
echo "   HOTEL_SEARCH_API_URL=${HOTEL_URL}"
echo ""
echo "2. 또는 .env 파일에 다음을 추가하세요:"
echo "   FLIGHT_SEARCH_API_URL=${FLIGHT_URL}"
echo "   HOTEL_SEARCH_API_URL=${HOTEL_URL}"
echo ""
echo "3. Agent Engine을 재배포하거나 환경 변수를 업데이트하세요."

