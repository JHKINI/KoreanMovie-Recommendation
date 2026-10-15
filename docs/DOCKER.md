# Docker로 실행하기

기준일: 2026-10-09

> **검증 상태:** 이 파일들은 작성만 했고 **실제로 빌드·실행해 보지 않았다.** 작성한 PC에 Docker가 설치되어 있지 않았다.
> 처음 실행할 때 오류가 나면 아래 "문제 해결"을 먼저 보고, 해결한 내용을 이 문서에 반영한다.

## 구성 원칙

- 이미지에는 **코드와 패키지만** 넣는다. Python 3.12, `requirements.lock.txt`의 검증된 버전.
- 원본 `Koreanmovie_review.csv`와 준비된 추천 데이터 `artifacts/`는 이미지에 넣지 않고 **볼륨으로 연결**한다.
  이유: 데이터 재배포 조건이 확인되지 않았고, 데이터를 갱신할 때마다 이미지를 다시 만들 필요가 없다.
- 서버는 `127.0.0.1:8000`에만 열린다. 같은 네트워크의 다른 PC에서는 접속되지 않는다.

| 파일 | 역할 |
|---|---|
| `Dockerfile` | API 이미지 정의 |
| `.dockerignore` | CSV, artifacts, 문서, `.venv` 등을 이미지에서 제외 |
| `docker-compose.yml` | `api`(서버)와 `pipeline`(데이터 준비) 두 서비스와 볼륨 연결 |

## 사전 준비

1. Docker Desktop을 설치하고 실행한다. (`docker --version`, `docker compose version`으로 확인)
2. 프로젝트 폴더에 `Koreanmovie_review.csv`가 있어야 한다. 저장소에는 포함되지 않는다.

## 처음 실행

프로젝트 폴더(`docker-compose.yml`이 있는 곳)에서 PowerShell로 실행한다.

```powershell
# 1. 추천 데이터 준비. 원본 검사 → 집계 → TF-IDF/유사도 → 전체 검사 → artifacts/에 저장
docker compose --profile prepare run --rm pipeline

# 2. API 서버 실행 (종료는 Ctrl+C)
docker compose up --build
```

서버가 뜨면 `http://127.0.0.1:8000/docs`를 연다. `docker compose ps`의 STATUS가 `healthy`면 `/health` 검사를 통과한 것이다.

이미 `artifacts/recommendation/CURRENT.json`이 있으면(로컬에서 `run_pipeline.py`를 돌렸다면) 1번은 건너뛰고 2번만 하면 된다.

## 자주 쓰는 명령

```powershell
docker compose up -d --build     # 백그라운드로 실행
docker compose logs -f api       # 서버 로그 보기
docker compose down              # 종료
docker compose restart api       # 데이터를 다시 준비한 뒤 새 버전을 읽게 하기
```

원본 CSV를 갱신했다면 `pipeline`을 다시 실행하고, 그 뒤 `docker compose restart api`로 재시작한다.
API는 시작할 때만 데이터를 읽는다.

## 문제 해결

- **서버가 바로 종료되고 "추천 데이터가 없다"는 취지의 메시지가 나옴:** `artifacts/recommendation/CURRENT.json`이 없는 것이다. 위 1번을 먼저 실행한다.
- **`pipeline`이 CSV를 찾지 못함:** 프로젝트 폴더 바로 아래에 `Koreanmovie_review.csv`가 있는지 확인한다. 없는 파일을 마운트하면 Docker가 같은 이름의 *폴더*를 만들어 버릴 수 있으니, 그런 폴더가 생겼으면 지우고 다시 실행한다.
- **포트 8000 사용 중:** 로컬에서 띄운 uvicorn이나 이전 컨테이너가 남아 있는 것이다. 종료하거나 `docker-compose.yml`의 `127.0.0.1:8000:8000` 앞쪽 숫자를 바꾼다.
- **Linux/Mac에서 `artifacts/`에 쓰기 권한 오류:** 컨테이너가 root로 실행되어 만든 파일을 일반 사용자가 지우기 어려울 수 있다. 필요하면 `docker compose run --user "$(id -u):$(id -g)" ...`로 실행한다.

## 알려진 한계

- 컨테이너는 root로 실행된다. 배포용이라면 일반 사용자로 바꾸는 것이 좋다.
- 이미지에는 테스트용 `httpx`도 포함된다(lock 파일을 그대로 쓰기 때문). 이미지를 줄이려면 운영/개발 requirements를 나눈다.
- 컨테이너에는 백엔드와 `static/` 웹 화면(`http://127.0.0.1:8000/`)만 들어 있다. React 프론트(`frontend/`)는 포함하지 않는다.
