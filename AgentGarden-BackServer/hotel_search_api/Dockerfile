FROM python:3.11-slim

WORKDIR /app

# 의존성 파일 복사
COPY requirements.txt .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY main.py .

# 포트 노출
EXPOSE 8080

# 환경 변수 설정 (Cloud Run은 PORT 환경 변수를 사용)
ENV PORT=8080

# 애플리케이션 실행
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}


