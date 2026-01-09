# AgentGarden Backend Server

이 프로젝트는 Travel Concierge Agent Garden에 연결되는 백엔드 API 서버입니다.

## 구조

```
AgentGarden-BackServer/
├── flight_search_api/          # 항공편 검색 API 서버
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── hotel_search_api/            # 호텔 검색 API 서버
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── deploy.sh                    # Cloud Run 자동 배포 스크립트
├── CLOUD_RUN_DEPLOYMENT.md      # Cloud Run 배포 가이드
├── AGENT_ENGINE_INTEGRATION.md  # Agent Engine 통합 가이드
└── README.md
```

## 빠른 시작

### 로컬 개발

#### 항공편 검색 API 서버

```bash
cd flight_search_api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

#### 호텔 검색 API 서버

```bash
cd hotel_search_api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8002
```

### Cloud Run 배포

#### 자동 배포 (권장)

```bash
chmod +x deploy.sh
./deploy.sh
```

#### 수동 배포

자세한 내용은 [CLOUD_RUN_DEPLOYMENT.md](./CLOUD_RUN_DEPLOYMENT.md)를 참고하세요.

### Agent Engine 통합

배포 후 Agent Engine과 통합하는 방법은 [AGENT_ENGINE_INTEGRATION.md](./AGENT_ENGINE_INTEGRATION.md)를 참고하세요.

## API 엔드포인트

### 항공편 검색 API

- **URL**: `http://localhost:8001/search`
- **Method**: `POST`
- **Request Body**:
```json
{
  "origin": "San Diego",
  "destination": "Seattle",
  "departure_date": "2024-04-20",
  "return_date": "2024-04-24"
}
```

### 호텔 검색 API

- **URL**: `http://localhost:8002/search`
- **Method**: `POST`
- **Request Body**:
```json
{
  "location": "Seattle",
  "check_in_date": "2024-04-20",
  "check_out_date": "2024-04-24"
}
```

