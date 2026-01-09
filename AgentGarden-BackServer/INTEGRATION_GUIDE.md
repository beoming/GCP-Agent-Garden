# AgentGarden 백엔드 API 통합 가이드

이 가이드는 Travel Concierge Agent Garden에 백엔드 API 서버를 통합하는 방법을 설명합니다.

## 개요

기존에는 항공편 검색과 호텔 검색이 LLM Agent를 통해 데모용 데이터를 생성했습니다. 이제는 실제 백엔드 API 서버를 통해 데이터를 제공하도록 변경되었습니다.

## 구조

```
AgentGarden-BackServer/
├── flight_search_api/          # 항공편 검색 API 서버
│   ├── main.py
│   └── requirements.txt
├── hotel_search_api/            # 호텔 검색 API 서버
│   ├── main.py
│   └── requirements.txt
└── INTEGRATION_GUIDE.md         # 이 파일

travel-concierge/
└── travel_concierge/
    └── tools/
        └── backend_apis.py       # 백엔드 API를 호출하는 FunctionTool
```

## 설정 단계

### 1. 백엔드 API 서버 실행

#### 항공편 검색 API 서버

```bash
cd /Users/Shared/Files\ From\ d.localized/GSNeotek/Work/GCP/AgentGarden-BackServer/flight_search_api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

#### 호텔 검색 API 서버

```bash
cd /Users/Shared/Files\ From\ d.localized/GSNeotek/Work/GCP/AgentGarden-BackServer/hotel_search_api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8002
```

### 2. 환경 변수 설정

Travel Concierge 프로젝트의 `.env` 파일에 다음 환경 변수를 추가하거나 수정합니다:

```bash
# 백엔드 API 서버 URL (기본값: localhost)
FLIGHT_SEARCH_API_URL=http://localhost:8001
HOTEL_SEARCH_API_URL=http://localhost:8002
```

프로덕션 환경에서는 실제 서버 URL로 변경하세요:
```bash
FLIGHT_SEARCH_API_URL=https://api.example.com/flight-search
HOTEL_SEARCH_API_URL=https://api.example.com/hotel-search
```

### 3. Travel Concierge 실행

```bash
cd /Users/Shared/Files\ From\ d.localized/GSNeotek/Work/GCP/gcp-adk-samples-main/python/agents/travel-concierge
adk run travel_concierge
```

또는 웹 인터페이스:

```bash
adk web
```

## 변경 사항

### 기존 구조

- `flight_search_agent`: LLM Agent가 프롬프트를 통해 데모용 항공편 데이터 생성
- `hotel_search_agent`: LLM Agent가 프롬프트를 통해 데모용 호텔 데이터 생성

### 새로운 구조

- `flight_search_tool`: 백엔드 API (`http://localhost:8001/search`)를 호출하는 FunctionTool
- `hotel_search_tool`: 백엔드 API (`http://localhost:8002/search`)를 호출하는 FunctionTool

### 코드 변경

`travel_concierge/sub_agents/planning/agent.py`에서:

```python
# 기존
tools=[
    AgentTool(agent=flight_search_agent),  # LLM Agent
    AgentTool(agent=hotel_search_agent),    # LLM Agent
    ...
]

# 변경 후
from travel_concierge.tools.backend_apis import flight_search_tool, hotel_search_tool

tools=[
    flight_search_tool,  # FunctionTool (백엔드 API 호출)
    hotel_search_tool,    # FunctionTool (백엔드 API 호출)
    ...
]
```

## API 스펙

### 항공편 검색 API

**Endpoint**: `POST /search`

**Request Body**:
```json
{
  "origin": "San Diego",
  "destination": "Seattle",
  "departure_date": "2024-04-20",
  "return_date": "2024-04-24"  // 선택사항
}
```

**Response**:
```json
{
  "flights": [
    {
      "flight_number": "AA1234",
      "departure": {
        "city_name": "San Diego",
        "airport_code": "SAN",
        "timestamp": "2024-04-20T08:00:00"
      },
      "arrival": {
        "city_name": "Seattle",
        "airport_code": "SEA",
        "timestamp": "2024-04-20T10:30:00"
      },
      "airlines": ["American Airlines"],
      "airline_logo": "/images/american.png",
      "price_in_usd": 450,
      "number_of_stops": 0
    }
  ]
}
```

### 호텔 검색 API

**Endpoint**: `POST /search`

**Request Body**:
```json
{
  "location": "Seattle",
  "check_in_date": "2024-04-20",
  "check_out_date": "2024-04-24"
}
```

**Response**:
```json
{
  "hotels": [
    {
      "name": "Seattle Marriott Waterfront",
      "address": "2100 Alaskan Wy, Seattle, WA 98121, United States",
      "check_in_time": "16:00",
      "check_out_time": "11:00",
      "thumbnail": "/src/images/mariott.png",
      "price": 250
    }
  ]
}
```

## 테스트

### 백엔드 API 테스트

#### 항공편 검색 API 테스트

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "San Diego",
    "destination": "Seattle",
    "departure_date": "2024-04-20",
    "return_date": "2024-04-24"
  }'
```

#### 호텔 검색 API 테스트

```bash
curl -X POST http://localhost:8002/search \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Seattle",
    "check_in_date": "2024-04-20",
    "check_out_date": "2024-04-24"
  }'
```

### Agent 통합 테스트

1. 백엔드 API 서버들이 실행 중인지 확인
2. Travel Concierge 실행
3. 다음과 같은 요청을 시도:
   - "Find flights from San Diego to Seattle on April 20th"
   - "Search for hotels in Seattle from April 20th to April 24th"

## 문제 해결

### 백엔드 API 연결 실패

**증상**: Agent가 항공편/호텔 검색 시 오류 발생

**해결 방법**:
1. 백엔드 API 서버가 실행 중인지 확인
2. 환경 변수 `FLIGHT_SEARCH_API_URL`, `HOTEL_SEARCH_API_URL`이 올바르게 설정되었는지 확인
3. 네트워크 연결 확인 (방화벽, 포트 등)

### 포트 충돌

**증상**: `Address already in use` 오류

**해결 방법**:
- 다른 포트 사용: `uvicorn main:app --port 8003`
- 환경 변수에서 해당 포트로 URL 업데이트

## 향후 개선 사항

1. **실제 항공편/호텔 API 연동**: Amadeus, Sabre, Booking.com 등의 실제 API 연동
2. **인증 추가**: API 키 기반 인증 구현
3. **에러 핸들링 강화**: 재시도 로직, 폴백 메커니즘
4. **로깅 및 모니터링**: 요청/응답 로깅, 성능 모니터링
5. **캐싱**: 자주 검색되는 경로에 대한 캐싱


