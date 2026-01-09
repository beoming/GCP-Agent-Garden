# 다음 단계: Agent Engine 통합

배포가 완료되었습니다! 이제 Agent Engine에 환경 변수를 설정해야 합니다.

## 배포된 서비스 URL

✅ **항공편 검색 API**: `https://flight-search-api-nelifvy57a-uc.a.run.app`
✅ **호텔 검색 API**: `https://hotel-search-api-nelifvy57a-uc.a.run.app`

## Agent Engine 정보

- **이름**: travel-concierge-17738
- **Resource ID**: `484511893407399936`
- **프로젝트**: `gsneotek-ncc-demo`
- **리전**: `us-central1`

## 환경 변수 설정 방법

### 방법 1: gcloud CLI로 직접 업데이트 (권장)

```bash
gcloud ai reasoning-engines update 484511893407399936 \
  --region=us-central1 \
  --update-env-vars=FLIGHT_SEARCH_API_URL=https://flight-search-api-nelifvy57a-uc.a.run.app,HOTEL_SEARCH_API_URL=https://hotel-search-api-nelifvy57a-uc.a.run.app
```

### 방법 2: Agent Config 파일 수정 후 재배포

1. Travel Concierge 프로젝트의 Agent Config 파일을 찾습니다:
   ```bash
   cd /Users/Shared/Files\ From\ d.localized/GSNeotek/Work/GCP/gcp-adk-samples-main/python/agents/travel-concierge
   ```

2. 환경 변수를 추가합니다. `agent_config.yaml` 또는 유사한 파일에:
   ```yaml
   runtime_config:
     environment_variables:
       FLIGHT_SEARCH_API_URL: "https://flight-search-api-nelifvy57a-uc.a.run.app"
       HOTEL_SEARCH_API_URL: "https://hotel-search-api-nelifvy57a-uc.a.run.app"
   ```

3. Agent Engine을 재배포합니다:
   ```bash
   uv run python deployment/deploy.py --update --resource_id=484511893407399936
   ```

## 서비스 테스트

### 1. 백엔드 API 직접 테스트

```bash
# 항공편 검색 API 테스트
curl -X POST https://flight-search-api-nelifvy57a-uc.a.run.app/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "San Diego",
    "destination": "Seattle",
    "departure_date": "2024-04-20",
    "return_date": "2024-04-24"
  }'

# 호텔 검색 API 테스트
curl -X POST https://hotel-search-api-nelifvy57a-uc.a.run.app/search \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Seattle",
    "check_in_date": "2024-04-20",
    "check_out_date": "2024-04-24"
  }'
```

### 2. Agent Engine 테스트

환경 변수 설정 후:

```bash
# Agent Engine 쿼리 테스트
gcloud ai reasoning-engines query 484511893407399936 \
  --region=us-central1 \
  --query="Find flights from San Diego to Seattle on April 20th"
```

## 환경 변수 확인

설정한 환경 변수가 올바르게 적용되었는지 확인:

```bash
gcloud ai reasoning-engines describe 484511893407399936 \
  --region=us-central1 \
  --format="yaml(runtimeConfig.environmentVariables)"
```

## 문제 해결

### 환경 변수가 적용되지 않는 경우

1. **재배포 확인**: 환경 변수 변경 후 반드시 재배포 필요
2. **형식 확인**: 환경 변수는 `KEY=VALUE` 형식으로 쉼표로 구분
3. **로그 확인**: Agent Engine 로그에서 환경 변수 로드 확인

### API 호출 실패

1. **서비스 상태 확인**:
   ```bash
   gcloud run services describe flight-search-api --region us-central1
   gcloud run services describe hotel-search-api --region us-central1
   ```

2. **로그 확인**:
   ```bash
   # Cloud Run 로그
   gcloud run services logs read flight-search-api --region us-central1 --limit 50
   
   # Agent Engine 로그
   gcloud logging read "resource.type=aiplatform.googleapis.com/ReasoningEngine AND resource.labels.reasoning_engine_id=484511893407399936" --limit 50
   ```

## 완료 체크리스트

- [x] Cloud Run 서비스 배포 완료
- [ ] Agent Engine 환경 변수 설정
- [ ] Agent Engine 재배포/업데이트
- [ ] 백엔드 API 테스트
- [ ] Agent Engine 통합 테스트

## 다음 작업

환경 변수 설정이 완료되면 Agent가 실제 백엔드 API를 호출하여 항공편과 호텔 정보를 가져올 수 있습니다!


