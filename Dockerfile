# 영화 추천 API 이미지. 원본 CSV와 준비된 추천 데이터(artifacts)는 이미지에 넣지 않고
# 실행할 때 볼륨으로 연결한다. (docker-compose.yml 참고)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 검증에 사용한 패키지 버전 그대로 설치한다. 코드보다 먼저 복사해 의존성 층을 캐시한다.
COPY requirements.lock.txt .
RUN pip install -r requirements.lock.txt

# 서비스에 필요한 코드만 복사한다. 제외 대상은 .dockerignore에 있다.
COPY *.py ./
COPY static ./static

EXPOSE 8000

# 컨테이너 안에서는 0.0.0.0으로 받아야 호스트에서 접근할 수 있다.
# 데이터가 준비되지 않았으면 서버 시작 단계에서 중단된다.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
