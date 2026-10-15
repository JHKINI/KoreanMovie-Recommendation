# 팀원 저장소와 합치는 방법

기준일: 2026-10-11

이 폴더(압축해서 전달하는 폴더)를 팀원의 GitHub 저장소(`JHKINI/KoreanMovie-Recommendation`)에 합치는 **한 가지 예시**입니다.
꼭 이 방식이어야 하는 것은 아니고, 팀에서 정한 방식이 있으면 그것을 따르세요. 명령은 Windows PowerShell 기준입니다.

## 1. 지금 상태

- 이 폴더는 팀원 저장소의 커밋 **`93b4512`**(2026-10-08, "docs: add frontend progress status") 시점을 기준으로 이어서 만든 것입니다. git 저장소가 아니라서 커밋 기록이 없습니다.
- 비교는 팀원 저장소를 그 시점으로 받아 파일 단위로 했습니다(줄바꿈 차이는 무시). **그 이후 팀원이 올린 커밋이 있으면 아래 목록에 없는 변경이 있을 수 있으니, 합치기 전에 `git log`로 확인하세요.**
- 팀원 저장소에서 이 폴더가 **바꾸지 않은** 백엔드 원본: `data_store.py`, `evaluate.py`, `build_*.py`, `pipeline_common.py`, `prepare_data.py`, `run_pipeline.py`, `verify_backend.py`, `test_prepare_data.py`, `requirements*.txt` 등.

## 2. 달라진 파일

### 수정한 원본 파일 (17개) — 충돌이 날 수 있는 곳

| 영역 | 파일 | 무엇을 바꿨나 |
|---|---|---|
| 백엔드 | `api.py` | 엔드포인트 추가(통계·키워드·둘러보기·비교·취향 추천·평점 분포), CORS, `static/` 서빙, 시작 때 키워드 계산 |
| 백엔드 | `recommender.py` | `recommend_for_taste()` 함수 추가(기존 함수는 그대로) |
| 백엔드 | `review_service.py` | `get_reviews()`에 `keyword` 인자 추가(기본값 `None`이라 기존 호출은 그대로) |
| 테스트 | `test_pipeline.py` | "요청 중 TF-IDF fit 금지" 검사의 범위를 서버 시작 이후 요청으로 좁힘. 키워드를 시작 때 한 번 계산하기 때문 |
| 프론트 | `frontend/src/App.jsx` | **전면 교체**(화면 전체를 `pages/`로 옮기고 껍데기만 남김) |
| 프론트 | `frontend/src/services/api.js` | 호출 함수 추가, 오류 문구 처리, `VITE_API_BASE_URL` |
| 프론트 | `frontend/src/App.css` | 원본 95줄 뒤에 스타일 덧붙임 |
| 프론트 | `frontend/index.html`, `frontend/package.json` | `lang`·`title` 두 줄 / `"test"` 스크립트 한 줄 |
| 설정 | `.gitignore` | `docs/human_eval/human_eval_sheet.csv`만 CSV 무시에서 예외 |
| 문서 | `README.md`, `docs/BACKEND_GUIDE.md`, `docs/CURRENT_STATUS.md`, `프로젝트_실행방법.txt` | 새 기능·실행 방법 반영, 낡은 문장 정리 |
| 문서 | `archive/*/README.md`, `archive/recommendation_reference/verify.py` | 경로 수정(`D:\...` → 상대 경로 또는 이 PC 경로) |

### 새로 추가한 파일

- **백엔드:** `evaluate_quality.py`, `keyword_service.py`, `movie_browse.py`, `movie_compare.py`, `movie_statistics.py`
- **테스트:** `test_api_contract.py`, `test_browse_taste.py`, `test_evaluate_quality.py`, `test_keywords_statistics.py`, `pytest.ini`, `requirements-dev.txt`
- **실행·배포:** `run.bat`, `stop.bat`, `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `.github/workflows/test.yml`, `static/index.html`
- **프론트:** `frontend/src/` 아래 `pages/`(6), `components/`(9), `hooks/`(3), `utils/`(6, 테스트 3개 포함)
- **문서:** `docs/` 아래 `API_RESPONSES.md`, `DOCKER.md`, `ENVIRONMENT_CHANGES.md`, `FRONTEND_CHANGES.md`, `MERGE_GUIDE.md`, `PORTFOLIO_SUMMARY.md`, `RECOMMENDATION_EVALUATION.md`, `human_eval/human_eval_sheet.csv`

### 팀원 저장소에만 있는 파일

- `docs/README.md`: 루트 `README.md`의 낡은 복사본(웹 업로드로 생긴 것으로 보임)이고 내부 링크가 깨져 있습니다. 합친 뒤 삭제하거나 새 README에 맞춰 갱신하세요.

## 3. 압축 파일을 받은 사람이 복사하면 안 되는 것

압축 파일에는 아래도 함께 들어 있습니다. **저장소에 올리거나 다른 PC에서 쓰지 마세요.**

| 대상 | 크기 | 이유 |
|---|---|---|
| `.venv/` | 약 360MB | 만든 PC의 Python 경로가 박혀 있어 다른 PC에서 실행되지 않습니다. `py -3.12 -m venv .venv`로 새로 만드세요. |
| `frontend/node_modules/` | 약 89MB | `npm ci --ignore-scripts`로 다시 설치하면 됩니다. |
| `artifacts/` | 약 20MB | 추천 데이터는 `run_pipeline.py`로 다시 만들 수 있습니다. **`artifacts/human_eval/human_eval_key.csv`는 사람 평가의 정답 키이므로 평가자에게 보이면 안 됩니다.** |
| `Koreanmovie_review.csv` | 약 13MB | 원본 데이터입니다. 재배포 조건이 확인되지 않았으니 저장소에 올리지 말고 각자 Kaggle에서 받으세요. |
| `archive/` 안의 CSV·옛 산출물 | 약 40MB | `.gitignore`가 이미 제외하는 파일들입니다. |

`.gitignore`가 `.venv`, `artifacts/`, `*.csv`, `node_modules`(프론트 `.gitignore`)를 제외하므로, 아래처럼 git으로 올리면 이 파일들은 자동으로 빠집니다. 폴더를 통째로 복사해 올리는 경우에만 주의하면 됩니다.

## 4. 합치는 방법 (권장)

**원칙:** 팀원의 기존 코드를 덮어쓰지 말고, **브랜치에서 합친 뒤 PR로 검토**합니다. 한 사람이 합치는 것이 가장 단순합니다.

### 4-1. 준비

```powershell
git clone https://github.com/JHKINI/KoreanMovie-Recommendation.git
cd KoreanMovie-Recommendation
git log --oneline -5          # 93b4512 이후에 새 커밋이 있는지 확인
git checkout -b feature/web-ui-and-evaluation
```

압축 파일은 **저장소 밖의 다른 폴더**에 풀어 두세요(예: `C:\work\moive_zip`).

### 4-2. 파일 복사 (제외 대상을 빼고)

`robocopy`로 위 3번의 제외 대상을 빼고 복사합니다. 이 명령은 같은 이름의 파일을 **덮어쓰므로**, 4-1에서 만든 브랜치에서만 실행하세요(되돌리기 쉽습니다).

```powershell
robocopy C:\work\moive_zip . /E /XD .venv node_modules artifacts __pycache__ .vscode .git /XF Koreanmovie_review.csv
```

> `robocopy`는 성공해도 종료 코드가 0~7(정상 범위)로 나옵니다. 오류 메시지가 없으면 정상입니다.
> 사람 평가 시트(`docs/human_eval/human_eval_sheet.csv`)는 복사되고, 정답 키는 `artifacts/`에 있어서 위 명령에서 제외되므로 따라오지 않습니다.

### 4-3. 변경 내용 확인

```powershell
git status                    # 수정된 파일과 새 파일 목록. 위 2번 목록과 비교
git diff --stat               # 수정된 파일별 변경량
git diff api.py               # 충돌 가능 파일은 내용을 직접 확인
```

- 목록에 **없는** 파일이 `modified`로 나오면, 팀원이 그 사이에 고친 것을 덮어쓴 것일 수 있습니다. `git checkout -- <파일>`로 되돌린 뒤 직접 합치세요.
- 줄바꿈 때문에 파일 전체가 바뀐 것으로 보이면 `git config core.autocrlf true`를 설정한 뒤 다시 확인하세요(이 폴더의 파일은 줄바꿈이 섞여 있습니다).

### 4-4. 커밋은 나눠서 (PR 하나에 다 넣지 않기)

리뷰하기 쉽도록 성격별로 나눕니다. 순서는 아래가 안전합니다.

| 순서 | 내용 | 파일 |
|---|---|---|
| 1 | 백엔드 기능과 테스트 | `api.py`, `recommender.py`, `review_service.py`, `keyword_service.py`, `movie_*.py`, `test_*.py`, `pytest.ini`, `requirements-dev.txt` |
| 2 | 프론트 | `frontend/` 전체(`node_modules` 제외) |
| 3 | 추천 평가 | `evaluate_quality.py`, `docs/RECOMMENDATION_EVALUATION.md`, `docs/human_eval/`, `.gitignore` |
| 4 | 실행·배포 도구 | `run.bat`, `stop.bat`, `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.github/` |
| 5 | 문서 | `README.md`, `docs/*.md`, `프로젝트_실행방법.txt` 등 |

```powershell
git add api.py recommender.py review_service.py keyword_service.py movie_*.py test_*.py pytest.ini requirements-dev.txt
git commit -m "feat: add statistics, keywords, browse, compare, taste recommendation APIs"
# 이어서 2~5번도 같은 방식으로 add → commit
git push -u origin feature/web-ui-and-evaluation
```

그다음 GitHub에서 Pull Request를 만들고, 팀원이 확인한 뒤 `main`에 합칩니다.

### 4-5. 합친 뒤 확인

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest        # 저장 데이터가 없으면 계약 테스트는 건너뛰고 나머지는 통과해야 함
cd frontend; npm.cmd ci --ignore-scripts; npm.cmd run lint; npm.cmd test; npm.cmd run build
```

그리고 원본 CSV를 두고 `run_pipeline.py`를 실행한 뒤 `run.bat`으로 화면이 뜨는지, `pytest` 전체가 통과하는지 확인하세요.

## 5. 충돌이 날 만한 곳과 해결 방법

| 파일 | 상황 | 권장 |
|---|---|---|
| `frontend/src/App.jsx` | 팀원이 그 사이 화면을 고쳤다면 충돌 | 팀원의 변경을 `pages/HomePage.jsx`에 옮기고, `App.jsx`는 이 폴더의 구조(껍데기)를 쓰는 것을 권장 |
| `frontend/src/App.css`, `services/api.js` | 같은 파일에 서로 다른 추가 | 둘 다 남기고, 중복된 클래스·함수만 정리 |
| `api.py` | 팀원이 엔드포인트를 추가했다면 | 둘 다 남기세요. 고정 경로(`/movies/browse` 등)는 `/movies/{movie_id}`보다 **먼저** 등록돼야 합니다(순서가 바뀌면 `browse`가 영화 ID로 해석됨) |
| CORS | 팀원 저장소 백엔드에 이미 CORS가 있다면 | 한쪽으로 통일 |
| `README.md` | 양쪽이 수정 | 이 폴더 것을 기준으로 하되 팀원의 새 내용을 옮기기 |

## 6. 다른 방법

- **폴더 비교 도구:** VS Code에서 두 폴더를 열고 "선택 항목을 비교"하거나, WinMerge 같은 도구로 폴더 전체를 비교해 파일별로 반영할 수 있습니다. git 사용이 부담스러울 때 쓸 수 있습니다.
- **PR을 나눠서 순차 합치기:** 4-4의 순서대로 5개의 브랜치/PR을 만들어 하나씩 합치면 리뷰 부담이 줄고 문제가 생긴 부분을 찾기 쉽습니다.
- **합치지 않고 이 폴더를 기준으로 삼기:** 팀원이 프론트를 더 고치지 않기로 했다면, 이 폴더를 새 저장소의 시작점으로 쓰는 것도 가능합니다. 이 경우에도 3번의 제외 대상은 올리지 마세요.

## 7. 합치기 전에 팀원에게 확인할 것

1. 93b4512 이후 올린 변경이 있는지, 프론트를 지금도 고치고 있는지
2. 프론트를 React 단독(개발 서버)으로 둘지, 빌드해서 FastAPI가 같이 서빙하게 할지(지금은 개발 서버 방식)
3. 사람 평가 시트(`docs/human_eval/`)를 누가 어떻게 채울지
4. `docs/README.md`(낡은 복사본)를 지울지

---

**이 문서가 확인한 범위:** 팀원 저장소(`93b4512`)와 이 폴더의 파일 비교(수정 17개, 추가 약 50개)까지입니다. 위 명령들(`robocopy`, `git` 흐름)은 일반적인 방법을 적은 것이고, 이 폴더에서 실제로 실행해 보지는 않았습니다. 이 폴더는 git 저장소가 아니라서 합치기 자체를 시험하지 못했습니다.
