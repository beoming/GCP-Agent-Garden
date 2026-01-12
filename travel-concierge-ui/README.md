# Travel Concierge Chat UI

Travel Concierge Agent Engine을 위한 실시간 채팅 UI 및 로그 모니터링 도구입니다.

## 기능

- **왼쪽 패널**: Agent Engine과의 실시간 채팅
- **오른쪽 패널**: 실시간 로그 모니터링
- **스트리밍 응답**: Agent의 응답을 실시간으로 스트리밍
- **자동 로그 폴링**: 최근 로그를 자동으로 조회

## 사전 요구사항

1. Python 3.10 이상
2. Google Cloud 인증 설정:
   ```bash
   gcloud auth application-default login
   ```
3. Agent Engine이 배포되어 있어야 함

## 설치 및 실행

### 1. 의존성 설치

```bash
cd travel-concierge-ui
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (선택사항)

```bash
export GOOGLE_CLOUD_PROJECT=gsneotek-ncc-demo
export GOOGLE_CLOUD_LOCATION=us-central1
```

### 3. 서버 실행

```bash
python server.py
```

서버가 `http://localhost:8080`에서 실행되며, **정적 파일(HTML, CSS, JS)도 함께 서빙**합니다.

### 4. 브라우저에서 접속

서버가 실행되면 브라우저에서 다음 URL을 열어주세요:

```
http://localhost:8080
```

**중요**: `file://` 프로토콜로 직접 `index.html`을 열면 CORS 오류가 발생합니다. 반드시 서버를 통해 접속해야 합니다.

## 사용 방법

1. **Agent Engine Resource ID 입력**
   - 페이지를 열면 Resource ID를 입력하라는 프롬프트가 나타납니다
   - Agent Engine의 Resource ID를 입력하세요 (숫자만 입력 가능)

2. **채팅 시작**
   - 왼쪽 패널에서 메시지를 입력하고 전송
   - Agent의 응답이 실시간으로 표시됩니다

3. **로그 확인**
   - 오른쪽 패널에서 실시간 로그를 확인할 수 있습니다
   - 자동 스크롤 버튼으로 최신 로그 자동 스크롤
   - 지우기 버튼으로 로그 초기화

## 설정

### Agent Engine Resource ID 확인

Agent Engine의 Resource ID는 다음 방법으로 확인할 수 있습니다:

1. **GCP Console**:
   - Vertex AI > Agent Engines에서 확인

2. **gcloud CLI**:
   ```bash
   gcloud ai reasoning-engines list --region=us-central1
   ```

3. **배포 스크립트 출력**:
   - `deploy.py --create` 실행 시 출력되는 Resource ID

### 백엔드 서버 포트 변경

`server.py`의 마지막 줄에서 포트를 변경할 수 있습니다:

```python
port = int(os.getenv("PORT", 8080))
```

또는 환경 변수로 설정:

```bash
export PORT=3000
python server.py
```

### 프론트엔드 API URL 변경

`app.js`의 `CONFIG` 객체에서 API URL을 변경할 수 있습니다:

```javascript
const CONFIG = {
    apiUrl: 'http://localhost:8080',  // 여기 변경
    // ...
};
```

## 문제 해결

### 연결 오류

- `gcloud auth application-default login` 실행 확인
- Agent Engine Resource ID가 올바른지 확인
- 백엔드 서버가 실행 중인지 확인

### 로그가 보이지 않음

- Cloud Logging API가 활성화되어 있는지 확인
- IAM 권한 확인 (`roles/logging.viewer` 필요)

### CORS 오류

- 백엔드 서버의 `flask-cors`가 제대로 설치되어 있는지 확인
- 브라우저 콘솔에서 오류 메시지 확인

## 아키텍처

```
┌─────────────┐      HTTP/SSE      ┌──────────────┐      API      ┌─────────────┐
│   Browser   │ ◄────────────────► │  Flask      │ ◄───────────► │ Agent       │
│  (index.html)│                   │  Server     │              │ Engine      │
│             │                    │  (server.py)│              │             │
└─────────────┘                    └──────────────┘              └─────────────┘
                                            │
                                            │ Cloud Logging API
                                            ▼
                                    ┌──────────────┐
                                    │ Cloud        │
                                    │ Logging      │
                                    └──────────────┘
```

## 라이선스

Apache 2.0
