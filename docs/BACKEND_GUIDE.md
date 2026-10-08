# 영화 추천 백엔드 실행·학습 안내

1차 목표는 원본 데이터에서 영화 정보와 리뷰를 연결하고 검색·추천·리뷰 조회를 안정적으로 실행하는 것이다.
프론트 화면, 크롤러, 새로운 평점 예측 모델은 이번 구현에 포함하지 않는다.
모든 코드·문서·산출물은 `D:\JungPra\pythonpra\NSMC` 아래에 저장한다.

## 1. 먼저 실행하기

현재 프로젝트에는 검증에 사용한 `.venv`가 있다. PowerShell에서 다음 명령을 실행한다.

```powershell
cd D:\JungPra\pythonpra\NSMC

# 원본 검사 → 영화별 집계 → 특징/유사도 → 전체 기능 검사
.\.venv\Scripts\python.exe run_pipeline.py

# 한 영화에 대한 추천과 실제 리뷰 조회
.\.venv\Scripts\python.exe recommender.py --title "승부" --top-n 5
.\.venv\Scripts\python.exe review_service.py --title "서울의 봄" --order high --top-n 5
.\.venv\Scripts\python.exe review_service.py --title "서울의 봄" --order low --top-n 5

# 저장된 데이터의 연결/정렬 규칙을 다시 검사
.\.venv\Scripts\python.exe evaluate.py
.\.venv\Scripts\python.exe verify_backend.py

# 작은 가상 데이터와 HTTP 요청을 포함한 자동 테스트
.\.venv\Scripts\python.exe -m unittest -v test_prepare_data test_pipeline

# API 서버 시작. 종료는 Ctrl+C
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

API 기본 주소는 `http://127.0.0.1:8000`이다. `/docs`는 FastAPI가 제공하는 요청 시험 문서다.
정확한 영화 제목만으로 상세·추천·리뷰를 조회할 수 있다. ID를 따로 복사할 필요가 없다.
Swagger의 **제목으로 조회** 항목에서 `title`에 영화 이름을 입력한다.

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/movies/detail?title=승부'
Invoke-RestMethod 'http://127.0.0.1:8000/recommend?title=승부&top_n=5'
Invoke-RestMethod 'http://127.0.0.1:8000/movies/reviews?title=서울의 봄&order=high&top_n=5'
```

새 PC에서는 Python을 설치하고 가상환경을 만든 뒤 라이브러리를 설치한다.
검증 환경은 Python 3.12이며 Python 3.12 이상을 사용하도록 작성했다. 다른 버전의 실행 검증은 별도다.

```powershell
cd D:\JungPra\pythonpra\NSMC
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.lock.txt`는 이번에 실제 테스트한 패키지 버전 전체를 기록한 파일이다.
동일 Python 환경을 재현할 때는 `-r requirements.lock.txt`로 설치할 수 있다.
다른 Python 버전에서 특정 고정 패키지를 설치하지 못하면 `requirements.txt`의 허용 범위로 설치하고 테스트한다.

## 2. 파이프라인과 파일 역할

```text
Koreanmovie_review.csv (원본: 읽기만 함)
  → prepare_data.audit_frame(): 컬럼/숫자 범위/결측/중복/제목 후보 검사
  → build_profiles.py: 영화 정보표 + 리뷰 표
  → build_features.py: TF-IDF + 범주/수치/리뷰 유사도
  → evaluate.py: 모든 영화의 추천/리뷰 동작 검사
  → CURRENT.json: 검사를 통과한 버전만 게시
  → data_store.py: 정상 버전을 한 번 읽기
  → recommender.py / review_service.py
  → api.py: 검색·추천·리뷰 요청 연결
```

| 파일 | 입력 | 출력/역할 |
|---|---|---|
| `prepare_data.py` | 원본 CSV | 검사 보고서. 원본 수정/삭제/병합을 하지 않음 |
| `build_profiles.py` | 원본 CSV | `movie_profiles.csv`, `reviews.csv`, 집계/검사 보고서 |
| `build_features.py` | 영화별 프로필 | 희소 TF-IDF, 네 종류의 유사도, 전처리 설정 |
| `run_pipeline.py` | 원본 CSV, 보정 강도 | 전체 준비/검사, 새 정상 버전 게시 |
| `data_store.py` | 현재 버전 포인터 | 프로필·리뷰·유사도 로딩 및 제목 검색 |
| `recommender.py` | 저장 데이터, 영화 ID | 추천 영화/점수/추천 이유 |
| `review_service.py` | 저장 데이터, 영화 ID | 실제 평점순 리뷰 |
| `evaluate.py` | 저장 데이터 | 전체 영화 동작 검사, 설정별 추천 사례 비교 |
| `api.py` | HTTP 요청 | JSON 응답. 시작 때만 저장 데이터 로딩 |
| `verify_backend.py` | 실제 저장 데이터 | HTTP 검색→추천→리뷰 연결과 오류 응답 검사 |
| `pipeline_common.py` | 파일 경로/설정 값 | 해시, JSON 읽기/쓰기, 공통 입력 검사 |
| `test_pipeline.py` | 작은 가상 원본 CSV | 집계·결측·충돌·버전·추천·리뷰·HTTP 검사 |

읽기 순서는 `build_profiles.py` → `build_features.py` → `recommender.py` → `review_service.py` → `api.py`를 권한다.
각 함수의 바로 아래 `"""..."""`는 함수 설명(docstring)이다.
함수별 목록은 `docs/FUNCTIONS.md`에 있고, 위 파일의 실제 코드에서도 확인할 수 있다.

## 3. 왜 이 라이브러리를 썼는가

| 라이브러리 | 사용 이유 | 이번에 사용하는 핵심 기능 |
|---|---|---|
| pandas | CSV를 표처럼 다루고 영화별 리뷰를 묶기 위해 | `read_csv`, `DataFrame`, `groupby`, 결측 검사, 중복 제거, 정렬 |
| NumPy | 영화×영화 유사도와 수치 전처리를 배열로 계산하기 위해 | `zeros`, `log1p`, `abs`, `mean`, `clip`, `.npz` 저장/읽기 |
| SciPy | TF-IDF에서 0을 전부 저장하면 낭비이므로 희소 행렬을 보존하기 위해 | `save_npz`, `load_npz` |
| scikit-learn | TF-IDF/코사인 유사도를 직접 재구현하며 생길 오류를 줄이기 위해 | `TfidfVectorizer`, `cosine_similarity` |
| FastAPI | 검색·추천·리뷰 함수를 HTTP 요청과 연결하고 값의 범위를 검사하기 위해 | `FastAPI`, `Query`, `Request`, `HTTPException` |
| Uvicorn | FastAPI 앱을 실제 HTTP 서버로 실행하기 위해 | `python -m uvicorn api:app` |
| HTTPX | 자동 테스트에서 HTTP 요청을 전달하기 위해 | FastAPI `TestClient`가 이용하는 테스트용 통신 기능 |

다음은 Python에 기본 포함된 표준 라이브러리이므로 별도 설치하지 않는다.

| 표준 라이브러리 | 이유 |
|---|---|
| `pathlib.Path` | 실행 위치가 달라도 스크립트 기준 경로를 정하고 Windows 경로를 조합 |
| `argparse` | `--input`, `--title`, `--m` 같은 터미널 옵션을 설명과 함께 받기 |
| `json` | 설정, 보고서, API/CLI 결과를 딕셔너리·리스트로 읽기/쓰기 |
| `hashlib` | 원본 보존과 파일 버전 일치를 SHA-256으로 검사 |
| `math` | NaN/무한대 검사 및 점수 비교 |
| `datetime`, `uuid` | 실행 시각과 고유 번호로 겹치지 않는 버전 폴더 만들기 |
| `os.replace` | 모든 검사가 끝난 뒤 현재 버전 포인터를 한 번에 교체 |
| `platform`, `importlib.metadata` | Python과 설치 패키지 버전 기록 |
| `contextlib.asynccontextmanager` | 서버 시작/종료 구간을 한 함수로 묶기 |
| `typing.Literal` | 리뷰 정렬 방향을 `high`, `low`로 제한 |
| `unittest`, `tempfile`, `unittest.mock` | 실제 데이터를 바꾸지 않고 임시 데이터와 가짜 호출로 자동 검사 |

## 4. 데이터 정리와 영화별 집계

원본에는 22개 컬럼이 있다. 추천에서 실제 `rating`을 사용하며 `bert_label`은 기존 모델이 예측한 감성값이다.
감성 예측의 평균을 사람의 감성 정답이나 모델 정확도로 해석하지 않는다.

1. 필수 컬럼/숫자 값/평점 범위를 검사한다. 잘못된 숫자는 임의로 고치지 않고 중단한다.
2. 제목과 리뷰의 양 끝 공백을 제거한다. 빈 제목/빈 리뷰 행은 추천용 사본에서 제외한다.
3. `영화명 + 리뷰 + 실제 평점`이 같은 행만 중복 제거한다. 서로 다른 영화의 같은 문구는 남긴다.
4. 같은 문구에 서로 다른 평점이 있으면 모두 남긴다.
5. **평점이 없는 리뷰도 텍스트에는 남긴다.** 리뷰 수 `n`과 유효 평점 수 `v`를 따로 집계한다.
6. 같은 제목 안에서 감독/장르/개봉일 등 메타데이터가 충돌하면 중단한다. 무조건 `first`로 숨기지 않는다.
7. `strip한 원문 제목 + 개봉일`로 내부 `movie_id`를 만든다. 리뷰의 `review_id`를 영화 ID로 쓰지 않는다.
8. 쉼표만 다른 제목도 자동으로 같은 작품이라 판단하지 않는다. 동일 작품 판단/별도 공식 영화 ID 연결은 추후 작업이다.

현재 원본은 영화명 216개지만 추천용 리뷰가 없는 두 영화가 제외되어 프로필은 214개다.
`reviews.csv`의 `source_record`는 물리적인 파일 줄 번호가 아니라 CSV 파서가 읽은 데이터 레코드 순서다.
줄바꿈이 포함된 리뷰도 레코드 하나로 센다.

### pandas 핵심 함수의 의미

| 사용 구문 | 의미/이번 사용 이유 |
|---|---|
| `pd.read_csv(path)` | CSV를 DataFrame으로 읽음 |
| `data.copy()` | 원본 표를 직접 바꾸지 않고 작업용 표를 만듦 |
| `.fillna('')`, `.str.strip()` | 결측 리뷰를 빈 문자열로 다루고 양 끝 공백을 제거 |
| `.loc[조건]` | 조건에 맞는 행/컬럼 선택 |
| `.drop_duplicates(subset=[...])` | 지정한 컬럼 조합이 같은 추가 행을 제거 |
| `pd.to_numeric(..., errors='coerce')` | 숫자로 변환. 원본 검사를 먼저 통과한 데이터에 적용하므로 잘못된 원본 숫자를 숨기는 용도가 아님 |
| `.groupby('MOVIE_NM')` | 같은 영화의 리뷰끼리 묶음 |
| `.get_group(title)` | 지정한 영화의 원본 메타데이터 행을 가져옴 |
| `.dropna()` / `.isna()` | 결측인 행을 제외하거나 결측 여부 확인 |
| `.mean()` / `.count()` / `len(...)` | 평균 / 유효값 개수 / 전체 행 수. 결측 평점 때문에 `count`와 `len`이 다를 수 있음 |
| `.median()` | 수치 결측을 보완할 중앙값 계산 |
| `.sort_values(..., kind='stable')` | 점수순 정렬. 동점 원본 순서 또는 별도 동점 키를 유지 |
| `.str.contains(..., regex=False)` | 검색어에 `[` 같은 문자가 있어도 정규식으로 해석하지 않음 |
| `.to_csv(..., index=False)` | DataFrame 인덱스를 불필요한 CSV 컬럼으로 쓰지 않음 |

## 5. TF-IDF와 메타데이터 유사도

### TF-IDF는 무엇을 위한 fit인가

영화별 리뷰를 합친 문자열 하나를 문서 하나로 사용한다. 각 영화의 문서를 숫자 벡터로 바꾸는 것이 목적이다.
실제 평점을 정답으로 주고 예측 오차를 줄이는 지도학습을 하지 않는다.

`fit_transform(texts)`는 두 작업을 합친 함수다.

- `fit`: 영화별 리뷰에서 어떤 글자 조합을 특징으로 쓸지, 문서에 얼마나 흔한지를 계산한다.
- `transform`: 해당 특징의 가중치로 각 문서를 숫자 벡터로 바꾼다.

이번 설정은 문자 2~3그램, `min_df=2`, `max_features=5000`, `sublinear_tf=True`, `smooth_idf=True`, `norm='l2'`다.
예를 들어 “연기가 좋다”에서 “연기”, “기 ”, “연기가” 같은 조합이 특징이 된다.
`min_df=2`는 두 영화 이상의 문서에 나온 특징을 사용한다는 뜻이다.
`sublinear_tf`는 같은 특징이 많이 반복돼도 영향이 과하게 커지지 않게 로그로 완화한다.

`cosine_similarity(tfidf)`는 두 영화 벡터의 방향이 얼마나 비슷한지 계산한다.
0에 가까우면 표현이 덜 겹치고, 1에 가까우면 숫자 표현이 비슷하다.
추천 취향의 정답 확률이나 의미 이해 정확도가 아니다.

TF-IDF는 희소 행렬 그대로 저장한다. `.toarray()`로 전체 TF-IDF를 바꾸지 않는다.
영화 214개 사이의 유사도만 214×214의 일반 NumPy 배열로 저장한다.
이전 `archive/recommendation_reference/recommendation_demo.py`의 독립 NumPy 구현과 특징 선택/동점 처리 등이 달라 결과가 완전히 같을 필요는 없다.

### 메타데이터 계산

상영구분/관람 등급이 일치하는 비율을 `cat_sim`으로 사용한다. **결측끼리 같다는 이유로 점수를 주지 않는다.**
관객 수/스크린 수에는 `log1p`를 사용한다. 수가 매우 큰 영화가 차이를 지배하는 것을 완화하고 실제 0도 보존한다.
결측은 중앙값으로 보완한다. 모든 영화에서 결측인 컬럼은 제외한다.
각 수치 컬럼은 `(값-최솟값)/(최댓값-최솟값)`으로 0~1에 맞춘다. 모두 같은 값이면 0 배열로 만든다.

```text
num_sim = 1 - 정규화된 속성 차이의 평균
meta = 0.5 × cat_sim + 0.5 × num_sim
```

NumPy의 `abs`는 차이의 절댓값, `mean`은 평균, `clip`은 범위를 제한한다.
`isfinite`는 NaN/무한대를 검사하고 `allclose`는 작은 부동소수점 오차를 허용한 비교다.
수치 결측을 중앙값으로 보완하면 서로 비슷해지는 효과는 남는다. 이를 정확한 원래 메타데이터라고 해석하지 않는다.

## 6. 추천과 평점 보정

장르가 같고 자기 영화가 아닌 후보를 만든다. `멜로/로맨스`는 하나의 장르 이름으로 취급한다.
장르 미상이면 추천 결과는 빈 목록이며 API에서 이유를 함께 반환한다.
감독 결측끼리는 같은 감독으로 보지 않는다.

```text
S = clip(0.4 × meta + 0.6 × text_sim + 같은 감독이면 0.05, 0, 1)
B = (v × R + m × C) / (v + m)
Q = (B - 0.5) / 4.5
final_score = 0.7 × S + 0.3 × Q
```

- `R`: 영화의 실제 평균 평점.
- `v`: 실제 평점이 있는 보존 리뷰 수. 고유 사용자 수가 아니다.
- `C`: 추천용 데이터의 전체 유효 평점 평균.
- `m`: 보정 강도. 초기값 20이며 최소 리뷰 수 필터가 아니다.
- 평점이 하나도 없는 영화는 `B=C`로 계산하지만 원래 평균 평점은 `None`으로 유지한다.

**유사도로 먼저 최대 20개를 고른 후**, 최종 점수로 정렬해 기본 5개를 반환한다.
처음부터 모든 후보를 최종 점수로 정렬하면 합의한 후보 선정 방식과 달라진다.
동점은 유사도·제목·ID 등 명시한 키로 처리한다. 최고 점수의 첫 행을 삭제하는 대신 자기 ID를 조건으로 제외한다.

가중치와 `m=20`은 초기 설정이다. 현재 평점이 수치 유사도에도 포함되어 최종 점수에 이중 반영된다.
`evaluate.py`는 같은 장르+보정 평점 기준 추천, 현재 추천, 수치 유사도에서 평점을 뺀 추천 사례를 나란히 기록한다.
추천 품질 우열은 이 기록만으로 결정할 수 없다.

평점을 수치 유사도에서 빼거나 m을 바꾸는 실험은 별도 저장 폴더로 실행해 기본 버전을 보존한다.

```powershell
.\.venv\Scripts\python.exe run_pipeline.py --exclude-rating --artifacts-dir artifacts\experiment_without_rating
.\.venv\Scripts\python.exe run_pipeline.py --m 50 --artifacts-dir artifacts\experiment_m50
```

## 7. 저장 데이터와 버전 연결

```text
artifacts/recommendation/
  CURRENT.json                     # 마지막 정상 버전의 위치
  runs/버전번호/
    data_audit.json                 # 원본 검사
    movie_profiles.csv             # 영화별 메타데이터·평점·리뷰 텍스트
    reviews.csv                    # 영화 ID와 연결된 개별 리뷰
    profile_manifest.json          # 집계 규칙·원본 해시·집계 파일 해시
    review_tfidf.npz               # 희소 TF-IDF
    similarities.npz              # 행 번호별 ID와 유사도
    tfidf_info.json                # 어휘·IDF·정규화 설정
    feature_manifest.json         # 특징 파일 해시
    manifest.json                 # 전체 버전·설정·패키지 버전·파일 해시
    evaluation.json               # 전체 기능 검사·설정별 사례 비교
```

프로필 행 번호와 유사도 행 번호가 같은 영화인지 `movie_ids` 배열로 검사한다.
파일 내용이 다른 버전으로 바뀌면 SHA-256 검사에서 중단한다.
이 해시는 우발적인 파일 변경/혼합 확인용이지 외부 사용자의 악의적인 파일 변경을 막는 인증 방식은 아니다.

새 실행은 항상 새 폴더를 만든다. 실패해도 `CURRENT.json`은 기존 정상 버전을 계속 가리킨다.
API는 시작할 때 해당 정상 버전을 한 번 읽는다. 파이프라인을 다시 실행한 뒤 API에 새 버전을 적용하려면 서버를 재시작한다.
요청 처리 중에는 원본 CSV를 읽거나 TF-IDF를 fit하지 않는다.

## 8. API 입출력

| 요청 | 역할 | 잘못된 입력 |
|---|---|---|
| `GET /health` | 준비된 데이터 버전/개수 확인 | 데이터가 준비되지 않으면 서버 시작 때 중단 |
| `GET /movies?query=승부&limit=20` | 제목 일부 검색 | limit은 1~100, query는 200자 이하 |
| `GET /movies/detail?title=승부` | 제목으로 영화 정보 | 제목 없음: 404, 제목 중복: 409 |
| `GET /recommend?title=승부&top_n=5` | 제목으로 추천과 추천 이유 | 제목 없음: 404, top_n 범위 오류: 422 |
| `GET /movies/reviews?title=서울의 봄&order=high&top_n=5` | 제목으로 실제 평점순 리뷰 | order는 high/low, top_n은 1~20 |
| `GET /movies/{movie_id}` | ID 또는 제목으로 영화 정보 | 미등록 입력: 404 |
| `GET /recommend/{movie_id}?top_n=5` | ID 또는 제목으로 추천 | 미등록 입력: 404, top_n 범위 오류: 422 |
| `GET /movies/{movie_id}/reviews?order=high&top_n=5` | ID 또는 제목으로 실제 평점순 리뷰 | order는 high/low, top_n은 1~20 |

제목의 양 끝 공백과 대소문자는 무시하지만 문장부호는 보존한다. 제목 일부는 `/movies?query=...`에서 검색한다.
현재 데이터의 작품이 아닌 제목은 임의로 비슷한 영화를 골라주지 않고 404를 반환한다.
같은 제목의 작품이 여러 개면 409 응답의 `detail.candidates`에 제목·감독·개봉일이 포함된 목록을 반환한다.
이때 `release_date=YYYYMMDD` 또는 `director=감독명`을 제목 조회 API에 추가하면 후보를 좁힐 수 있다.
슬래시가 포함된 제목은 경로 대신 `title` query를 사용한다. 기존 `movie_id` 경로에도 `승부` 같은 제목을 넣을 수 있다.

`find_movies_by_title()`은 작품 후보 목록을 찾고, `title_to_movie_id()`는 없음/중복을 확인한 뒤 내부 ID를 연결한다.
API 내부에서는 일관된 ID로 리뷰와 유사도 행을 연결하므로 제목 조회와 ID 조회의 추천 결과가 같다.
현재 프로필 생성은 같은 제목의 메타데이터 충돌 시 중단한다. API의 동명이작 선택 처리는 가상 프로필로 검증했으며,
동명이작을 포함하는 새 원본을 집계하려면 먼저 데이터 단계에서 작품을 구분해야 한다.

검색 결과가 없으면 200 응답의 빈 `items`가 반환된다.
후보가 적으면 실제 가능한 개수만 반환한다. 평점 없는 리뷰는 저장하지만 평점순 API에는 넣지 않는다.
평점 동점 리뷰는 `source_record`의 원본 순서다. 작성일이 없으므로 최신순이라고 표시하지 않는다.

`@application.get(...)`은 해당 경로의 요청을 아래 함수로 연결한다.
`Query(ge=1, le=20)`은 1보다 작은 값이나 20보다 큰 요청을 함수 실행 전에 거부한다.
`PathParameter`는 FastAPI의 `Path`를 다른 이름으로 가져온 것이다. URL 경로의 제목/ID 입력에 설명과 길이 조건을 붙이며, 파일 경로용 `pathlib.Path`와는 역할이 다르다.
`HTTPException(404, ...)`는 미등록 ID를 서버 오류 500으로 처리하지 않고 명시적 404 응답으로 바꾼다.
`lifespan` 함수는 서버 시작 때 데이터를 로딩하고 `yield` 이후 서버 종료 정리를 수행한다.
`async`는 FastAPI의 시작/종료 인터페이스에 맞추기 위한 부분이며 추천 점수 함수는 일반 `def`로 작성했다.

## 9. 학습과 검증의 구분

현재 콘텐츠 기반 추천에는 Ridge/LSTM 학습이 필요 없다.
`run_pipeline.py`의 TF-IDF는 리뷰 표현의 어휘/빈도 통계를 준비하는 단계이며 실제 rating으로 예측 모델을 학습하지 않는다.
이 코드에는 신경망 epoch, 역전파, 평점 예측 손실 최적화가 없다.

기존 `archive/rating_prediction/train_model.py`는 별도 기능이다. 리뷰로 실제 평점을 예측하는 TF-IDF+Ridge 모델을 학습한다.
이를 나중에 실행하려면 목적을 따로 설명하고 사용자가 실행하도록 한다.
추천 파이프라인에서 이 기존 파일을 호출하지 않는다.

자동 테스트/`evaluate.py`는 집계·영화 ID 연결·정렬·자기 제외·입력 오류·파일 버전·HTTP 응답을 확인한다.
사람의 취향, 취향별 추천 만족도, 가중치 최적값을 입증하지 않는다.
새로운 영화가 추가되면 원본을 갱신한 뒤 파이프라인을 다시 실행하고 검사를 통과한 버전을 사용한다.

## 10. 참고한 공식 문서

- [scikit-learn TF-IDF 설명](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction)
- [TfidfVectorizer 설정](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [FastAPI 테스트](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI 시작/종료 테스트](https://fastapi.tiangolo.com/advanced/testing-events/)

보정 평점 공식의 기존 설명/출처는 `docs/영화추천_통합설계_코드검증가이드_평점공식추가.pdf`에 보존되어 있다.
