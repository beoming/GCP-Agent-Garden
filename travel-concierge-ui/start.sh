#!/bin/bash
# Travel Concierge Chat UI 시작 스크립트

echo "Travel Concierge Chat UI 시작 중..."

# 가상 환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo "가상 환경 생성 중..."
    python3 -m venv venv
fi

# 가상 환경 활성화
source venv/bin/activate

# 의존성 설치
echo "의존성 설치 중..."
pip install -q -r requirements.txt

# 환경 변수 확인
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "경고: GOOGLE_CLOUD_PROJECT 환경 변수가 설정되지 않았습니다."
    echo "기본값(gsneotek-ncc-demo)을 사용합니다."
fi

# 서버 시작
echo ""
echo "=========================================="
echo "Travel Concierge Chat UI Backend Server"
echo "=========================================="
echo ""
echo "서버가 시작되었습니다!"
echo ""
echo "다음 단계:"
echo "1. 브라우저에서 index.html 파일을 엽니다"
echo "2. 또는 간단한 HTTP 서버를 실행합니다:"
echo "   python3 -m http.server 3000"
echo "   그 다음 http://localhost:3000 접속"
echo ""
echo "서버 종료: Ctrl+C"
echo ""

python server.py
