# 돈만이 게시판

회원가입, 로그인, 게시판 기능이 있는 웹 앱입니다.

## 기술 스택

- **Backend**: Python (FastAPI)
- **Database**: PostgreSQL
- **Infra**: Docker / Docker Compose

## 실행 방법

### 1. 환경 변수 준비

```bash
cp .env.example .env
```

`.env` 파일에서 `SECRET_KEY`를 긴 랜덤 문자열로 바꿔 주세요.

### 2. Docker로 실행

```bash
docker compose up --build
```

### 3. 접속

브라우저에서 [http://localhost:8000](http://localhost:8000) 을 엽니다.

## 주요 기능

- 회원가입 / 로그인 / 로그아웃
- 게시글 목록 / 작성 / 상세 / 수정 / 삭제
- 본인 글만 수정·삭제 가능

## 프로젝트 구조

```
coding_syudy/
├── docker-compose.yml
├── .env.example
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── entrypoint.sh
    ├── alembic/
    └── app/
        ├── main.py
        ├── config.py
        ├── database.py
        ├── models.py
        ├── routers/
        ├── templates/
        └── static/
```

## 배포 시 참고

- `SECRET_KEY`는 프로덕션용 강한 값으로 변경
- `APP_ENV=production`, `DEBUG=false` 설정
- PostgreSQL은 Docker volume으로 데이터 유지
- `/health` 엔드포인트로 헬스체크 가능
