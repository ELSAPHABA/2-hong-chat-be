# Real-time Chat Server (FastAPI + Redis + MongoDB)

이 프로젝트는 FastAPI, Redis Pub/Sub, 그리고 MongoDB를 활용한 실시간 1:1 채팅 시스템 서버입니다.

## 핵심 기능
- **WebSocket**: `/ws/{room_id}/{user_id}`를 통한 실시간 양방향 통신.
- **Redis Pub/Sub**: 다중 서버 인스턴스 환경에서도 메시지 동기화를 지원하는 브로드캐스트 시스템.
- **MongoDB**: 비동기 처리를 통한 채팅 내역 영속성 저장.
- **History API**: 입장 시 최근 50개의 메시지를 불러오는 REST API.

## 운영 고려 사항 (Scale-up, Scale-out, K8s)

### 1. Scale-out (수평 확장)
- **Redis Pub/Sub의 역할**: 여러 개의 FastAPI 서버 인스턴스가 실행 중일 때, 클라이언트 A가 서버 1에 연결되어 있고 클라이언트 B가 서버 2에 연결되어 있어도 Redis를 통해 메시지가 공유됩니다.
- **Sticky Sessions (Optional)**: WebSocket의 특성상 로드 밸런서(Nginx, ALB 등)에서 특정 클라이언트가 동일한 서버 인스턴스에 유지되도록 설정할 수 있으나, Redis Pub/Sub 덕분에 필수는 아닙니다.

### 2. K8s (Kubernetes) 운영
- **Deployment**: FastAPI 앱을 Stateless Deployment로 관리하여 손쉽게 복제본(Replicas)을 늘릴 수 있습니다.
- **Service & Ingress**: Ingress Controller(Nginx 등)를 통해 WebSocket 업그레이드 설정을 추가해야 합니다.
- **ConfigMap & Secrets**: MongoDB, Redis 연결 정보를 환경 변수로 관리합니다.
- **Horizontal Pod Autoscaler (HPA)**: CPU/Memory 사용량에 따라 자동으로 Pod 개수를 조절합니다.

### 3. 고가용성 (HA)
- **Redis Sentinel/Cluster**: Redis 자체를 클러스터링하여 장애 대응력을 높입니다.
- **MongoDB Replica Set**: 데이터 가용성을 위해 MongoDB 복제셋을 구성합니다.

## 실행 방법
1. 종속성 설치: `pip install -r requirements.txt`
2. 환경 변수 설정: `.env` 파일 생성 (필요시 `app/config.py` 참조)
3. 서버 실행: `python -m app.main`
