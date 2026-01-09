# Agent Engine 통합 가이드

이 가이드는 Cloud Run에 배포된 백엔드 API 서버를 Agent Engine의 Travel Concierge 에이전트와 통합하는 방법을 설명합니다.

## 현재 Agent Engine 정보

- **이름**: travel-concierge-17738
- **Resource Name**: `projects/545259847156/locations/us-central1/reasoningEngines/484511893407399936`
- **Service Account**: `service-545259847156@gcp-sa-aiplatform-re.iam.gserviceaccount.com`
- **프로젝트 ID**: `gsneotek-ncc-demo`
- **프로젝트 번호**: `545259847156`

## 통합 단계

### 1. Cloud Run 서비스 URL 확인

배포 후 서비스 URL을 확인합니다:

```bash
# 항공편 검색 API URL
FLIGHT_URL=$(gcloud run services describe flight-search-api \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')
echo "항공편 검색 API: ${FLIGHT_URL}"

# 호텔 검색 API URL
HOTEL_URL=$(gcloud run services describe hotel-search-api \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')
echo "호텔 검색 API: ${HOTEL_URL}"
```

### 2. Agent Engine 환경 변수 설정

Agent Engine에 환경 변수를 설정하는 방법은 두 가지가 있습니다:

#### 방법 1: Agent Config 파일 수정 (권장)

Travel Concierge 프로젝트의 Agent Config 파일을 수정합니다:

```yaml
# agent_config.yaml 또는 유사한 파일
runtime_config:
  environment_variables:
    FLIGHT_SEARCH_API_URL: "https://flight-search-api-xxxxx-uc.a.run.app"
    HOTEL_SEARCH_API_URL: "https://hotel-search-api-xxxxx-uc.a.run.app"
```

#### 방법 2: gcloud CLI를 통한 업데이트

```bash
# Agent Engine 업데이트
gcloud ai reasoning-engines update 484511893407399936 \
  --region=us-central1 \
  --update-env-vars=FLIGHT_SEARCH_API_URL=https://flight-search-api-xxxxx-uc.a.run.app,HOTEL_SEARCH_API_URL=https://hotel-search-api-xxxxx-uc.a.run.app
```

### 3. Agent Engine 재배포

환경 변수를 변경한 후 Agent Engine을 재배포합니다:

```bash
cd /Users/Shared/Files\ From\ d.localized/GSNeotek/Work/GCP/gcp-adk-samples-main/python/agents/travel-concierge

# Agent Engine에 재배포
uv run python deployment/deploy.py --update --resource_id=484511893407399936
```

또는 Agent Starter Pack을 사용하는 경우:

```bash
make deploy
```

### 4. IAM 권한 설정 (인증이 필요한 경우)

Cloud Run 서비스가 인증을 요구하는 경우, Agent Engine의 Service Account에 권한을 부여해야 합니다:

```bash
# 항공편 검색 API 권한 부여
gcloud run services add-iam-policy-binding flight-search-api \
  --member="serviceAccount:service-545259847156@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region us-central1

# 호텔 검색 API 권한 부여
gcloud run services add-iam-policy-binding hotel-search-api \
  --member="serviceAccount:service-545259847156@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region us-central1
```

## 코드 수정 확인

`travel_concierge/tools/backend_apis.py` 파일이 환경 변수를 올바르게 읽는지 확인:

```python
# 환경 변수에서 백엔드 API URL 가져오기 (기본값: localhost)
FLIGHT_SEARCH_API_URL = os.getenv(
    "FLIGHT_SEARCH_API_URL", "http://localhost:8001"
)
HOTEL_SEARCH_API_URL = os.getenv(
    "HOTEL_SEARCH_API_URL", "http://localhost:8002"
)
```

이 코드는 Agent Engine의 환경 변수를 자동으로 읽습니다.

## 테스트

### 1. Agent Engine 테스트

Agent Engine이 백엔드 API를 올바르게 호출하는지 테스트:

```bash
# Agent Engine 테스트
gcloud ai reasoning-engines query 484511893407399936 \
  --region=us-central1 \
  --query="Find flights from San Diego to Seattle on April 20th"
```

### 2. 로그 확인

Cloud Run 서비스 로그를 확인하여 요청이 도착하는지 확인:

```bash
# 항공편 검색 API 로그
gcloud run services logs read flight-search-api --region us-central1 --limit 50

# 호텔 검색 API 로그
gcloud run services logs read hotel-search-api --region us-central1 --limit 50
```

### 3. Agent Engine 로그 확인

Agent Engine의 로그도 확인:

```bash
# Cloud Logging에서 Agent Engine 로그 확인
gcloud logging read "resource.type=aiplatform.googleapis.com/ReasoningEngine AND resource.labels.reasoning_engine_id=484511893407399936" --limit 50
```

## 문제 해결

### 환경 변수가 적용되지 않는 경우

1. **환경 변수 확인**
   ```bash
   gcloud ai reasoning-engines describe 484511893407399936 \
     --region=us-central1 \
     --format="yaml(runtimeConfig.environmentVariables)"
   ```

2. **Agent 재배포**
   - 환경 변수 변경 후 반드시 재배포 필요

### API 호출 실패

1. **네트워크 연결 확인**
   - Agent Engine이 Cloud Run 서비스에 접근할 수 있는지 확인
   - VPC 설정 확인 (필요한 경우)

2. **인증 오류**
   - Service Account 권한 확인
   - IAM 바인딩 확인

3. **타임아웃**
   - Cloud Run 타임아웃 설정 확인 (현재 300초)
   - 필요시 증가 가능

### CORS 오류 (웹 UI 사용 시)

Cloud Run 서비스에 CORS 헤더 추가가 필요할 수 있습니다. `main.py`에 CORS 미들웨어 추가:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 모니터링

### Cloud Run 메트릭

```bash
# 서비스 메트릭 확인
gcloud run services describe flight-search-api \
  --region us-central1 \
  --format="yaml(status)"
```

### Agent Engine Telemetry

Agent Engine의 Telemetry collection이 활성화되어 있으므로, BigQuery와 Cloud Logging에서 데이터를 확인할 수 있습니다.

## 다음 단계

1. ✅ Cloud Run 서비스 배포 완료
2. ✅ Agent Engine 환경 변수 설정
3. ✅ Agent Engine 재배포
4. ✅ 테스트 및 검증
5. 🔄 프로덕션 모니터링 설정

## 참고 자료

- [Agent Engine 문서](https://cloud.google.com/vertex-ai/docs/reasoning-engines)
- [Cloud Run 문서](https://cloud.google.com/run/docs)
- [ADK 문서](https://google.github.io/adk-docs/)


