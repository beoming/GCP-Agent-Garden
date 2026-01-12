# GCP 콘솔 설정 가이드

Pub/Sub 기반 스트리밍을 사용하기 위한 GCP 설정 가이드입니다.

## 1. Pub/Sub API 활성화

### 방법 1: GCP 콘솔에서 활성화
1. [GCP 콘솔](https://console.cloud.google.com) 접속
2. 프로젝트 선택: `gsneotek-ncc-demo`
3. 왼쪽 메뉴에서 **"API 및 서비스"** → **"라이브러리"** 클릭
4. 검색창에 `Pub/Sub API` 입력
5. **"Cloud Pub/Sub API"** 선택 후 **"사용 설정"** 클릭

### 방법 2: gcloud CLI로 활성화
```bash
gcloud services enable pubsub.googleapis.com --project=gsneotek-ncc-demo
```

## 2. IAM 권한 설정

### 로컬에서 실행하는 경우 (개인 계정 사용)

#### 2-1. 현재 사용자에게 권한 부여
1. [IAM 및 관리자](https://console.cloud.google.com/iam-admin/iam) 페이지로 이동
2. 프로젝트: `gsneotek-ncc-demo` 선택
3. 상단의 **"권한 부여"** 버튼 클릭
4. **"새 주 구성원"**에 본인 이메일 주소 입력
5. **"역할 선택"**에서 다음 역할 추가:
   - `Pub/Sub Publisher` (roles/pubsub.publisher)
   - `Pub/Sub Subscriber` (roles/pubsub.subscriber)
   - 또는 `Pub/Sub Admin` (roles/pubsub.admin) - 모든 권한 포함
6. **"저장"** 클릭

#### 2-2. gcloud CLI로 권한 부여
```bash
# 본인 이메일로 교체
YOUR_EMAIL="your-email@example.com"

# Publisher 권한
gcloud projects add-iam-policy-binding gsneotek-ncc-demo \
  --member="user:${YOUR_EMAIL}" \
  --role="roles/pubsub.publisher"

# Subscriber 권한
gcloud projects add-iam-policy-binding gsneotek-ncc-demo \
  --member="user:${YOUR_EMAIL}" \
  --role="roles/pubsub.subscriber"
```

### Cloud Run에서 실행하는 경우 (서비스 계정 사용)

#### 2-1. 서비스 계정 생성 (필요한 경우)
1. [서비스 계정](https://console.cloud.google.com/iam-admin/serviceaccounts) 페이지로 이동
2. 프로젝트: `gsneotek-ncc-demo` 선택
3. **"서비스 계정 만들기"** 클릭
4. 서비스 계정 이름: `travel-concierge-server` (또는 원하는 이름)
5. **"만들고 계속하기"** 클릭
6. 역할 추가:
   - `Pub/Sub Publisher`
   - `Pub/Sub Subscriber`
   - `Vertex AI User` (Agent Engine 접근용)
   - `Cloud Logging Viewer` (로그 조회용)
7. **"완료"** 클릭

#### 2-2. 기존 서비스 계정에 권한 추가
1. [서비스 계정](https://console.cloud.google.com/iam-admin/serviceaccounts) 페이지로 이동
2. 사용할 서비스 계정 클릭 (예: `travel-concierge-server`)
3. **"권한"** 탭 클릭
4. **"역할 부여"** 클릭
5. 다음 역할 추가:
   - `Pub/Sub Publisher`
   - `Pub/Sub Subscriber`
6. **"저장"** 클릭

## 3. Topic 확인 및 생성

### 방법 1: 자동 생성 (권장)
코드에서 자동으로 Topic을 생성하므로 별도 작업 불필요합니다.
서버를 실행하면 자동으로 `agent-engine-responses` Topic이 생성됩니다.

### 방법 2: 수동 생성 (선택사항)
1. [Pub/Sub Topics](https://console.cloud.google.com/cloudpubsub/topic/list) 페이지로 이동
2. 프로젝트: `gsneotek-ncc-demo` 선택
3. **"토픽 만들기"** 클릭
4. Topic ID: `agent-engine-responses` 입력
5. **"만들기"** 클릭

### gcloud CLI로 생성
```bash
gcloud pubsub topics create agent-engine-responses --project=gsneotek-ncc-demo
```

## 4. 인증 설정 (로컬 실행 시)

### Application Default Credentials (ADC) 설정
로컬에서 실행하는 경우, 다음 명령어로 인증 정보를 설정합니다:

```bash
gcloud auth application-default login --project=gsneotek-ncc-demo
```

이 명령어는 다음을 수행합니다:
- 사용자 인증 정보를 로컬에 저장
- `GOOGLE_APPLICATION_CREDENTIALS` 환경 변수 자동 설정
- Pub/Sub API 호출 시 자동으로 인증 정보 사용

## 5. Subscription 관리 (선택사항)

### 생성된 Subscription 확인
1. [Pub/Sub Subscriptions](https://console.cloud.google.com/cloudpubsub/subscription/list) 페이지로 이동
2. 프로젝트: `gsneotek-ncc-demo` 선택
3. `agent-response-*` 패턴의 Subscription들이 자동 생성됨

### 오래된 Subscription 정리
세션이 종료되어도 Subscription이 자동으로 삭제되지 않으므로, 주기적으로 정리하는 것을 권장합니다:

```bash
# 모든 agent-response-* Subscription 삭제
gcloud pubsub subscriptions list --project=gsneotek-ncc-demo \
  --filter="name:agent-response-" \
  --format="value(name)" | \
  xargs -I {} gcloud pubsub subscriptions delete {} --project=gsneotek-ncc-demo
```

## 6. 모니터링 설정 (선택사항)

### Pub/Sub 모니터링 대시보드 생성
1. [Monitoring](https://console.cloud.google.com/monitoring) 페이지로 이동
2. **"대시보드"** → **"대시보드 만들기"** 클릭
3. 다음 메트릭 추가:
   - Pub/Sub Topic 메시지 수
   - Pub/Sub Subscription 메시지 지연 시간
   - Pub/Sub Subscription 미처리 메시지 수

## 7. 비용 최적화 (선택사항)

### Subscription 자동 삭제 정책 설정
오래된 Subscription을 자동으로 삭제하려면 Cloud Functions를 사용할 수 있습니다:

1. [Cloud Functions](https://console.cloud.google.com/functions) 페이지로 이동
2. **"함수 만들기"** 클릭
3. 함수 이름: `cleanup-old-subscriptions`
4. 트리거: Cloud Scheduler (매일 실행)
5. 코드에서 24시간 이상 사용되지 않은 Subscription 삭제

## 확인 체크리스트

다음 항목들을 확인하세요:

- [ ] Pub/Sub API 활성화됨
- [ ] IAM 권한 부여됨 (Publisher, Subscriber)
- [ ] Application Default Credentials 설정됨 (로컬 실행 시)
- [ ] Topic `agent-engine-responses` 존재 확인
- [ ] 서버 실행 시 Topic 자동 생성 확인

## 문제 해결

### 권한 오류가 발생하는 경우
```bash
# 현재 사용자 확인
gcloud auth list

# 프로젝트 설정 확인
gcloud config get-value project

# 권한 확인
gcloud projects get-iam-policy gsneotek-ncc-demo \
  --flatten="bindings[].members" \
  --filter="bindings.members:YOUR_EMAIL"
```

### Topic 생성 오류가 발생하는 경우
1. Pub/Sub API가 활성화되었는지 확인
2. IAM 권한이 올바르게 부여되었는지 확인
3. 프로젝트 ID가 올바른지 확인 (`gsneotek-ncc-demo`)

### Subscription 생성 오류가 발생하는 경우
1. Topic이 존재하는지 확인
2. Subscription 이름에 특수문자가 없는지 확인 (코드에서 `/`를 `-`로 변환)
3. IAM 권한이 올바르게 부여되었는지 확인

## 참고 링크

- [Pub/Sub 문서](https://cloud.google.com/pubsub/docs)
- [IAM 권한 가이드](https://cloud.google.com/pubsub/docs/access-control)
- [Pub/Sub 모범 사례](https://cloud.google.com/pubsub/docs/best-practices)
