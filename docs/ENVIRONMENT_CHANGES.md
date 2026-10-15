# 환경 변경 기록

기준일: 2026-10-09

원래 프로젝트는 다른 PC(`D:\JungPra\pythonpra\NSMC`, 사용자 `AISW_203_104`)에서 만들었다.
이 PC(`C:\Users\PC_1M\Documents\moive`)에서 실행하기 위해 아래와 같이 고쳤다.

## 고친 내용

| 대상 | 변경 전 | 변경 후 |
|---|---|---|
| `.venv` | 다른 PC의 Python을 가리켜 이 PC에서 실행 불가 | `py -3.12 -m venv --clear .venv`로 다시 만들고 `requirements.lock.txt`로 설치 (Python 3.12.10) |
| `README.md`, `docs/BACKEND_GUIDE.md`, `프로젝트_실행방법.txt` | `D:\JungPra\pythonpra\NSMC`, `\NSMC` | `C:\Users\PC_1M\Documents\moive` |
| `archive/rating_prediction/README.md`, `archive/recommendation_reference/README.md` | `D:\JungPra\pythonpra\NSMC` | `C:\Users\PC_1M\Documents\moive` |
| `archive/recommendation_reference/verify.py` | CSV 경로 `D:/JungPra/pythonpra/NSMC/...`로 고정 | 파일 위치 기준 상대 경로 (`ROOT.parents[1] / 'Koreanmovie_review.csv'`) |

## 추가한 파일 (2026-10-09)

| 파일 | 내용 |
|---|---|
| `pytest.ini`, `requirements-dev.txt` | pytest 설정과 개발용 패키지(pytest). 기존 `unittest` 33개는 수정 없이 pytest에서도 통과 |
| `test_api_contract.py` | `docs/API_RESPONSES.md`의 응답 구조를 실제 저장 데이터로 검사하는 테스트(2026-10-11 기준 37건, 파라미터화 포함). 전체 pytest는 104건 통과. 추천 데이터가 없으면 건너뜀 |
| `static/index.html`, `api.py` 수정 | 서버만 켜면 `http://127.0.0.1:8000/`에서 열리는 단일 HTML 데모 화면. 같은 `api.py`에 `localhost:5173`(Vite)용 CORS(GET만)와 `/statistics`, `/keywords`, `/movies/{id}/keywords` 추가 |
| `keyword_service.py`, `movie_statistics.py`, `test_keywords_statistics.py` | 대표 키워드(단어 단위 TF-IDF, 서버 시작 때 1회 계산)와 전체 통계 |
| `test_pipeline.py` 수정 | "요청 중 TF-IDF fit 금지" 검사의 패치 범위를 서버 시작 이후의 요청으로 좁힘. 키워드를 시작 때 한 번 계산하기 때문이며, 요청 처리 중 fit을 막는 의도는 그대로 |
| `frontend/` | 팀원 저장소(JHKINI/KoreanMovie-Recommendation, 커밋 93b4512)의 React 프론트를 받아 이어서 개발. 상세·추천·리뷰 화면, 키워드, 첫 화면 통계 추가 |
| `.github/workflows/test.yml` | GitHub Actions. main 푸시와 PR마다 pytest 실행. CSV·artifacts가 없는 환경이라(같은 조건으로 로컬에서 흉내 냄) 67건 실행, `test_api_contract.py` 37건은 건너뜀. 프론트 검사 작업(lint, 테스트 16개, build)도 포함. **GitHub에서 실제로 돌려 보지는 못함** |
| `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `docs/DOCKER.md` | Docker 실행 (작성만 했고 빌드는 검증하지 못함) |
| `docs/API_RESPONSES.md` | 프론트용 응답 구조 안내 |

## 고치지 않은 것

- `archive/recovery/`, `archive/before_organization/`, `docs/HANDOFF_2026-10-01.md`는 과거 기록이므로 원문 그대로 둔다.
- `README.md`의 `git clone` 안내는 저장소 구조 설명이라 그대로 둔다.
- 서비스 코드(`api.py` 등)에는 고정 경로가 없어 수정하지 않았다.

## 고친 뒤 확인한 결과

- 자동 테스트 33개 통과 (`test_prepare_data`, `test_pipeline`).
- `verify_backend.py`로 실제 데이터 API 연결 검사 통과.
- 서버 실행 후 `/health`(영화 214개, 리뷰 26,768건), `/recommend?title=승부`(200), 없는 제목(404) 확인.
- 평점 예측 실험(`archive/rating_prediction`)과 `archive/recommendation_reference`의 스크립트는 다시 실행하지 않았다.

## 다른 PC에서 쓸 때

문서의 경로는 이 PC 기준이다. 다른 PC에서는 `cd` 경로를 본인의 프로젝트 폴더로 바꾸고,
`.venv`는 복사하지 말고 `py -m venv .venv` 후 `pip install -r requirements.lock.txt`로 새로 만든다.
원본 `Koreanmovie_review.csv`는 저장소에 포함되지 않으므로 따로 준비한다.

## 참고

- `verify_backend.py`를 실행하면 `artifacts/recommendation/api_smoke.json`이 생성된다. `artifacts/`는 `.gitignore` 대상이다.
- 테스트 실행 시 Starlette가 `httpx` 대신 `httpx2`를 권장한다는 deprecation 경고가 나온다. 동작에는 영향이 없다.

## 프론트 실행 (Node.js 필요)

Node.js LTS가 필요하다(`winget install OpenJS.NodeJS.LTS`). PowerShell이 `npm.ps1` 실행을 막으면 `npm` 대신 `npm.cmd`를 쓴다(보안 정책은 바꾸지 않는다).

```powershell
cd C:\Users\PC_1M\Documents\moive\frontend
npm.cmd ci --ignore-scripts      # 처음 한 번
npm.cmd run dev -- --host 127.0.0.1
```

백엔드(`8000`)를 먼저 켜 두고 `http://127.0.0.1:5173`을 연다.
