# Cloud Run 배포 가이드

이 가이드는 백엔드 API 서버를 Google Cloud Run에 배포하는 방법을 설명합니다.

## 사전 요구사항

1. **Google Cloud SDK (gcloud) 설치 및 인증**
   ```bash
   # gcloud 설치 확인
   gcloud --version
   
   # 인증
   gcloud auth login
   gcloud auth application-default login
   ```

2. **프로젝트 설정**
   ```bash
   gcloud config set project gsneotek-ncc-demo
   ```

3. **필요한 API 활성화**
   ```bash
   # Cloud Run API
   gcloud services enable run.googleapis.com
   
   # Artifact Registry API
   gcloud services enable artifactregistry.googleapis.com
   
   # Cloud Build API
   gcloud services enable cloudbuild.googleapis.com
   ```

## 배포 방법

### 방법 1: 자동 배포 스크립트 사용 (권장)

```bash
cd /Users/Shared/Files\ From\ d.localized/GSNeotek/Work/GCP/AgentGarden-BackServer

# 실행 권한 부여
chmod +x deploy.sh

# 배포 실행
./deploy.sh
```

스크립트가 다음을 자동으로 수행합니다:
1. Docker 이미지 빌드
2. Container Registry에 이미지 푸시
3. Cloud Run에 서비스 배포
4. 서비스 URL 출력

### 방법 2: 수동 배포

#### 1. Artifact Registry 리포지토리 생성

```bash
# Artifact Registry 리포지토리 생성
gcloud artifacts repositories create backend-apis \
  --repository-format=docker \
  --location=us-central1 \
  --description="Backend APIs for Travel Concierge"
```

#### 2. 항공편 검색 API 배포

```bash
cd flight_search_api

# Docker 이미지 빌드 및 푸시
gcloud builds submit --tag us-central1-docker.pkg.dev/gsneotek-ncc-demo/backend-apis/flight-search-api --region=us-central1

# Cloud Run에 배포
gcloud run deploy flight-search-api \
  --image us-central1-docker.pkg.dev/gsneotek-ncc-demo/backend-apis/flight-search-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300
```

#### 3. 호텔 검색 API 배포

```bash
cd hotel_search_api

# Docker 이미지 빌드 및 푸시
gcloud builds submit --tag us-central1-docker.pkg.dev/gsneotek-ncc-demo/backend-apis/hotel-search-api --region=us-central1

# Cloud Run에 배포
gcloud run deploy hotel-search-api \
  --image us-central1-docker.pkg.dev/gsneotek-ncc-demo/backend-apis/hotel-search-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300
```

## 배포 후 확인

### 서비스 URL 확인

```bash
# 항공편 검색 API URL
gcloud run services describe flight-search-api \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'

# 호텔 검색 API URL
gcloud run services describe hotel-search-api \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

### 서비스 테스트

```bash
# 항공편 검색 API 테스트
FLIGHT_URL=$(gcloud run services describe flight-search-api \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')

curl -X POST ${FLIGHT_URL}/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "San Diego",
    "destination": "Seattle",
    "departure_date": "2024-04-20",
    "return_date": "2024-04-24"
  }'

# 호텔 검색 API 테스트
HOTEL_URL=$(gcloud run services describe hotel-search-api \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')

curl -X POST ${HOTEL_URL}/search \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Seattle",
    "check_in_date": "2024-04-20",
    "check_out_date": "2024-04-24"
  }'
```

## Cloud Run 설정 옵션

### 현재 설정
- **메모리**: 512Mi
- **CPU**: 1
- **최소 인스턴스**: 0 (콜드 스타트 허용)
- **최대 인스턴스**: 10
- **타임아웃**: 300초
- **인증**: 비인증 허용 (`--allow-unauthenticated`)

### 설정 변경

```bash
# 메모리 및 CPU 증가
gcloud run services update flight-search-api \
  --memory 1Gi \
  --cpu 2 \
  --region us-central1

# 최소 인스턴스 설정 (콜드 스타트 방지)
gcloud run services update flight-search-api \
  --min-instances 1 \
  --region us-central1
```

## 비용 최적화

- **최소 인스턴스 0**: 트래픽이 없을 때 인스턴스가 종료되어 비용 절감
- **적절한 메모리/CPU**: 사용량에 따라 조정 가능
- **리전**: `us-central1`은 Agent Engine과 같은 리전으로 지연 시간 최소화

## 보안 고려사항

### 인증이 필요한 경우

인증이 필요한 경우 `--allow-unauthenticated` 대신 IAM 기반 인증을 사용:

```bash
# 인증 필요로 변경
gcloud run services update flight-search-api \
  --no-allow-unauthenticated \
  --region us-central1

# Service Account에 권한 부여
gcloud run services add-iam-policy-binding flight-search-api \
  --member="serviceAccount:service-545259847156@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region us-central1
```

## 문제 해결

### 배포 실패

1. **API 활성화 확인**
   ```bash
   gcloud services list --enabled
   ```

2. **권한 확인**
   ```bash
   gcloud projects get-iam-policy gsneotek-ncc-demo
   ```

3. **로그 확인**
   ```bash
   gcloud run services logs read flight-search-api --region us-central1
   ```

### 서비스 접근 불가

1. **헬스 체크**
   ```bash
   curl ${FLIGHT_URL}/health
   ```

2. **서비스 상태 확인**
   ```bash
   gcloud run services describe flight-search-api --region us-central1
   ```

## 다음 단계

배포가 완료되면 [Agent Engine 통합 가이드](./AGENT_ENGINE_INTEGRATION.md)를 참고하여 Agent Engine에 환경 변수를 설정하세요.

