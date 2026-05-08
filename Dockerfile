# 1. Base Image: Python 3.10-slim (경량화 버전)
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 환경 변수 설정
# Python이 pyc 파일을 생성하지 않도록 설정
ENV PYTHONDONTWRITEBYTECODE 1
# 로그가 버퍼링 없이 즉시 출력되도록 설정 (K8s 로그 확인 용이)
ENV PYTHONUNBUFFERED 1

# 4. 종속성 설치를 위한 시스템 패키지 설치 (필요시)
# build-essential 등은 컴파일이 필요한 패키지가 있을 때 추가
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 5. 종속성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. 소스 코드 복사
# .dockerignore가 있다면 app/, main.py 등을 선택적으로 복사
COPY . .

# 7. 포트 노출
EXPOSE 8000

# 8. 실행 명령 (Uvicorn)
# --host 0.0.0.0은 컨테이너 외부 접속을 위해 필수
# --proxy-headers 및 --forwarded-allow-ips는 K8s Ingress/LoadBalancer 환경 대응
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
