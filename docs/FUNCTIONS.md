# 함수별 설명

코드의 실제 함수 설명(docstring)에서 만든 목록입니다. 함수 아래의 전체 설명에는 입력/반환과 처리 이유가 더 자세히 적혀 있습니다.

실행은 main() 또는 API 요청에서 시작합니다. 계산 함수는 직접 호출해 작은 데이터로 확인할 수 있습니다.

## prepare_data.py

| 함수 | 역할 |
|---|---|
| `present(series)` | NaN, 빈 문자열, 공백만 있는 값을 검사합니다. 원본은 변경하지 않습니다. |
| `samples(mask, limit=5)` | 검사 조건에 해당하는 원본 데이터 레코드 번호를 최대 limit개 반환합니다. |
| `normalize_title(value)` | 제목 변형 후보를 찾기 위한 비교 문자열을 만듭니다. 실제 영화명은 바꾸지 않습니다. |
| `audit_frame(df)` | DataFrame을 읽어 JSON으로 저장할 수 있는 검사 결과를 반환합니다. |
| `main(argv=None)` | 터미널의 입력/출력 경로를 받아 검사 보고서를 쓰고 검사 상태의 종료 코드를 반환합니다. |

## pipeline_common.py

| 함수 | 역할 |
|---|---|
| `file_sha256(path)` | 입력: 파일 경로. 반환: 파일 내용의 SHA-256 문자열. 원본은 읽기만 합니다. |
| `write_json(path, data)` | 딕셔너리/리스트를 UTF-8 JSON으로 저장합니다. NaN은 저장을 거부합니다. |
| `read_json(path)` | UTF-8 JSON 파일을 읽어 딕셔너리/리스트로 돌려줍니다. |
| `validate_top_n(top_n)` | 요청 개수가 1~20의 정수인지 검사합니다. bool은 정수로 인정하지 않습니다. |
| `validate_m(m)` | 보정 강도 m이 0보다 큰 유한한 수인지 검사합니다. |
| `check_file_hashes(directory, expected)` | 파일별 해시 딕셔너리와 실제 파일을 비교해 손상/버전 혼합을 검사합니다. |
| `protect_input(source, output_dir, names)` | 출력 파일 목록 중 입력 원본과 같은 경로가 있으면 저장 전에 중단합니다. |

## build_profiles.py

| 함수 | 역할 |
|---|---|
| `clean_review_rows(data)` | 원본 표의 복사본에서 빈 제목/리뷰와 영화·리뷰·평점 중복을 제거합니다. |
| `get_metadata_value(movie_rows, column)` | 한 영화의 유효 메타데이터를 가져옵니다. 서로 다른 값이 둘 이상이면 중단합니다. |
| `make_movie_id(title, release_date)` | 제목+개봉일로 재실행해도 같은 내부 ID를 만듭니다. 공식 영화 ID는 아닙니다. |
| `create_profiles(data, m=20.0)` | 검사를 통과한 원본 표를 프로필, 리뷰 표, 집계 보고서로 바꿉니다. |
| `build_profiles(input_path=DEFAULT_SOURCE, output_dir=DEFAULT_ARTIFACTS / 'standalone', m=20.0)` | CSV를 읽어 프로필/리뷰/검사 보고서/해시 목록을 지정 폴더에 저장합니다. |
| `main()` | 터미널 옵션을 읽고 영화별 집계를 실행합니다. |

## build_features.py

| 함수 | 역할 |
|---|---|
| `category_similarity(profiles)` | 상영구분/관람등급이 일치하는 비율을 계산합니다. 결측끼리는 일치가 아닙니다. |
| `numeric_similarity(profiles, include_rating=True)` | 수치 속성을 정규화한 뒤 1-평균 절대 차이로 유사도를 계산합니다. |
| `create_features(profiles, include_rating=True)` | 프로필 행 순서를 유지하며 희소 TF-IDF, 유사도 배열, 전처리 설명을 반환합니다. |
| `build_features(directory=DEFAULT_ARTIFACTS / 'standalone', include_rating=True)` | 집계 파일을 검증하고 특징/유사도 파일을 같은 버전 폴더에 저장합니다. |
| `main()` | 터미널에서 프로필 폴더와 평점 속성 포함 여부를 받아 특징을 준비합니다. |

## data_store.py

| 함수 | 역할 |
|---|---|
| `load_run(directory)` | 하나의 버전 폴더를 읽습니다. 파일 해시/ID 순서/행렬 크기를 확인하고 반환합니다. |
| `load_data(artifacts_dir=DEFAULT_ARTIFACTS)` | CURRENT.json이 가리키는 마지막 정상 버전을 읽습니다. |
| `get_movie_index(data, movie_id)` | 내부 영화 ID에 해당하는 행 번호를 반환합니다. 미등록 ID는 KeyError입니다. |
| `optional_text(value)` | 빈 문자열/결측은 None, 실제 문자열은 str로 바꿔 JSON에 넣습니다. |
| `optional_number(value)` | 결측 숫자는 None으로 바꿉니다. 유효한 숫자 0은 그대로 보존합니다. |
| `movie_to_dict(row)` | 프로필의 한 행을 검색/API에서 보여줄 일반 딕셔너리로 변환합니다. |
| `get_movie(data, movie_id)` | 영화 ID 하나의 메타데이터를 반환합니다. 전체 리뷰 텍스트는 노출하지 않습니다. |
| `search_movies(data, query='', limit=20)` | 제목의 일부로 검색합니다. 정규식이 아니라 입력한 글자 자체를 찾습니다. |
| `find_movies_by_title(data, title, release_date=None, director=None)` | 정확한 제목으로 작품 후보를 반환합니다. 동명이작은 날짜/감독으로 좁힐 수 있습니다. |
| `resolve_movie_id(data, movie_id=None, title=None)` | CLI의 ID 또는 정확한 제목을 실제 영화 ID로 변환합니다. |

## recommender.py

| 함수 | 역할 |
|---|---|
| `same_genre_indices(data, movie_id)` | 자기 영화를 제외하고 같은 장르의 프로필 행 번호를 찾습니다. |
| `calculate_candidate(data, source_index, candidate_index)` | 후보 하나의 유사도, 최종 점수, 추천 이유를 계산해 딕셔너리로 돌려줍니다. |
| `similarity_sort_key(candidate)` | 유사도 내림차순 정렬 키입니다. 동점은 제목·ID로 정해 재실행 결과를 유지합니다. |
| `final_sort_key(candidate)` | 최종 점수, 유사도는 내림차순이고 동점이면 제목·ID를 오름차순으로 정렬합니다. |
| `recommend(data, movie_id, top_n=5)` | 같은 장르 → 유사도 상위 20개 → 최종 점수 상위 top_n개를 반환합니다. |
| `baseline_recommend(data, movie_id, top_n=5)` | 비교 기준: 같은 장르 안에서 보정 평점이 높은 영화부터 추천합니다. |
| `baseline_sort_key(candidate)` | 기준 추천의 보정 평점 내림차순 정렬 키입니다. |
| `main()` | 정확한 영화 제목/ID를 터미널에서 받아 추천 결과를 JSON으로 출력합니다. |

## review_service.py

| 함수 | 역할 |
|---|---|
| `get_reviews(data, movie_id, top_n=5, order='high')` | 해당 영화의 평점 있는 리뷰를 정렬해 반환합니다. |
| `main()` | 터미널에서 영화와 정렬 방향을 받아 실제 리뷰를 JSON으로 출력합니다. |

## evaluate.py

| 함수 | 역할 |
|---|---|
| `check(condition, message)` | 검사 조건이 False이면 실행을 중단해 현재 버전이 게시되지 않게 합니다. |
| `verify_error_handling(data)` | 미등록 영화, 잘못된 개수/정렬 방향이 오류로 처리되는지 확인합니다. |
| `compare_example_settings(data)` | 기준 추천/현재 추천/평점 속성을 뺀 추천의 사례를 비교합니다. 우열을 단정하지 않습니다. |
| `evaluate_run(data)` | 한 버전의 모든 영화에 대해 추천/리뷰/집계 연결을 검사하고 보고서를 반환합니다. |
| `main()` | 현재 게시된 데이터로 기능 검사를 다시 실행하고 보고서를 저장합니다. |

## run_pipeline.py

| 함수 | 역할 |
|---|---|
| `run_pipeline(input_path=DEFAULT_SOURCE, artifacts_dir=DEFAULT_ARTIFACTS, m=20.0, include_rating=True)` | 새 버전을 만들고 검사가 모두 통과한 경우에만 현재 버전을 바꿉니다. |
| `main()` | 터미널에서 원본/저장 폴더/보정 강도를 받아 전체 데이터 준비를 실행합니다. |

## api.py

| 함수 | 역할 |
|---|---|
| `request_data(request)` | 서버 시작 때 한 번 읽은 데이터 딕셔너리를 현재 요청에 연결합니다. |
| `title_to_movie_id(data, title, release_date=None, director=None)` | 제목을 내부 영화 ID로 연결합니다. 없음=404, 동명이작=409와 후보 정보를 반환합니다. |
| `movie_input_to_id(data, value)` | 기존 경로에 영화 ID 또는 정확한 제목을 넣을 수 있도록 입력값을 연결합니다. |
| `recommendation_response(data, movie_id, top_n)` | 제목 요청/ID 요청이 동일한 추천 함수와 응답 구조를 사용하도록 묶습니다. |
| `create_app(artifacts_dir=DEFAULT_ARTIFACTS)` | 저장 폴더를 받는 API 생성 함수입니다. 테스트에서는 임시 폴더를 전달합니다. |
| `lifespan(application)` | 서버 시작 때 정상 버전을 한 번 로딩합니다. 요청마다 학습/계산하지 않습니다. |
| `health(request: Request)` | 현재 데이터 버전과 준비된 영화/리뷰 개수를 반환합니다. |
| `movies(request: Request, query: str=Query(default='', max_length=200), limit: int=Query(default=20, ge=1, le=100))` | 제목 일부로 검색합니다. 정확한 제목으로도 상세/추천/리뷰를 바로 조회할 수 있습니다. |
| `movie_detail_by_title(request: Request, title: str=Query(min_length=1, max_length=200, description='정확한 영화 제목. 예: 승부'), release_date: str | None=Query(default=None, pattern='^\\d{8}$', description='동명이작 구분용 개봉일 YYYYMMDD'), director: str | None=Query(default=None, min_length=1, max_length=200, description='동명이작 구분용 감독'))` | 제목만으로 영화 상세를 조회합니다. 제목이 중복되면 개봉일/감독으로 구분하세요. |
| `recommendations_by_title(request: Request, title: str=Query(min_length=1, max_length=200, description='정확한 영화 제목. 예: 승부'), top_n: int=Query(default=5, ge=1, le=20), release_date: str | None=Query(default=None, pattern='^\\d{8}$'), director: str | None=Query(default=None, min_length=1, max_length=200))` | 입력한 영화 제목의 추천을 바로 반환합니다. ID 복사 단계가 필요하지 않습니다. |
| `reviews_by_title(request: Request, title: str=Query(min_length=1, max_length=200, description='정확한 영화 제목. 예: 서울의 봄'), order: Literal['high', 'low']='high', top_n: int=Query(default=5, ge=1, le=20), release_date: str | None=Query(default=None, pattern='^\\d{8}$'), director: str | None=Query(default=None, min_length=1, max_length=200))` | 영화 제목으로 실제 평점순 리뷰를 조회합니다. high/low 방향을 선택할 수 있습니다. |
| `movie_detail(request: Request, movie_id: str=PathParameter(min_length=1, max_length=200, description='영화 ID 또는 정확한 제목. 예: 승부'))` | 경로에 영화 ID 또는 제목을 넣어 메타데이터, 평균/보정 평점, 리뷰 수를 조회합니다. |
| `recommendations(request: Request, movie_id: str=PathParameter(min_length=1, max_length=200, description='영화 ID 또는 정확한 제목. 예: 승부'), top_n: int=Query(default=5, ge=1, le=20))` | 경로의 영화 ID 또는 제목을 받아 같은 장르의 추천과 점수/근거를 반환합니다. |
| `reviews(request: Request, movie_id: str=PathParameter(min_length=1, max_length=200, description='영화 ID 또는 정확한 제목. 예: 서울의 봄'), order: Literal['high', 'low']='high', top_n: int=Query(default=5, ge=1, le=20))` | 경로의 영화 ID 또는 제목으로 실제 평점순 리뷰를 조회합니다. |

## verify_backend.py

| 함수 | 역할 |
|---|---|
| `verify_backend(artifacts_dir=DEFAULT_ARTIFACTS)` | 실제 데이터로 HTTP 응답과 잘못된 요청 처리를 검사하고 보고서를 저장합니다. |
| `main()` | 터미널에서 실제 데이터의 HTTP 연결 검사를 실행합니다. |
