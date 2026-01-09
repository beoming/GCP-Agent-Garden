# Zendesk Integration for Travel Concierge Agent

이 디렉토리는 Zendesk Connection을 사용하기 위한 Application Integration을 생성합니다.

## 설정 방법

1. 환경 변수 설정:
```bash
source env.sh
```

2. Application Integration 생성:
```bash
./create-integration.sh
```

이 스크립트는 `ExecuteConnection`이라는 이름의 Application Integration을 생성합니다.
이 Integration은 `ApplicationIntegrationToolset`에서 사용할 수 있습니다.

## 파일 구조

- `src/ExecuteConnection.json`: Application Integration 정의
- `overrides/overrides.json`: Integration 오버라이드 설정
- `env.sh`: 환경 변수 설정
- `create-integration.sh`: Integration 생성 스크립트
