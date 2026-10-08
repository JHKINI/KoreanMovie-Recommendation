# 파일 정리 안내

정리일: 2026-10-06

현재 기능에 필요한 파일은 프로젝트 루트와 `artifacts/recommendation`에 유지했다.
현재 서버에 필요하지 않은 과거 실험/참고 자료는 삭제하지 않고 `archive`로 옮겼다.

```text
NSMC/
  README.md                         실행 안내
  Koreanmovie_review.csv            원본 CSV 한 개
  movie_titles.txt                  원본 영화명 216개
  requirements.txt                  필요한 패키지 범위
  requirements.lock.txt             검증한 정확한 패키지 버전
  .venv/                            현재 실행용 가상환경
  .vscode/                          사용자 편집기 설정
  [현재 백엔드 Python 코드]
  docs/                             설명·인계·설계 PDF
    BACKEND_GUIDE.md                 라이브러리 사용 이유와 실행 흐름
    FUNCTIONS.md                     함수별 설명
    CURRENT_STATUS.md               최신 구현/검증 상태
    HANDOFF_2026-10-01.md             당시 인계 원문
    FILE_ORGANIZATION.md             이 안내
    screenshots/                    제목 API 검증 화면
  artifacts/recommendation/
    CURRENT.json                    마지막 정상 버전 포인터
    api_smoke.json                  현재 API 검사 결과
    runs/[현재 버전]/                프로필·리뷰·특징·유사도·보고서
  archive/
    rating_prediction/              기존 평점 예측 코드와 CSV
    recommendation_reference/       과거 추천 참조 코드
    old_artifacts/                  이전 결과와 오래된 검사 보고서
    recovery/                       복구 기록과 이전 대화 이력
    before_organization/            구버전 인계 문서
    rebuildable/                    재생성 가능한 과거 캐시
```

## 유지해야 하는 현재 파일

| 구분 | 파일 | 이유 |
|---|---|---|
| 원본/목록 | `Koreanmovie_review.csv`, `movie_titles.txt` | 데이터 갱신/재생성과 영화명 확인 |
| 준비 | `prepare_data.py`, `build_profiles.py`, `build_features.py`, `run_pipeline.py` | 원본 검사부터 정상 데이터 게시까지 연결 |
| 조회/추천 | `data_store.py`, `recommender.py`, `review_service.py`, `api.py` | 저장 데이터 읽기와 제목 검색·추천·리뷰 API |
| 공통 기능 | `pipeline_common.py` | 경로, JSON, 해시, 입력 검사 |
| 검증 | `evaluate.py`, `verify_backend.py`, `test_prepare_data.py`, `test_pipeline.py` | 전체 기능 검사와 오류/HTTP 테스트 |
| 실행 환경 | `.venv`, `requirements.txt`, `requirements.lock.txt` | 실행과 재설치. `.venv`는 경로 이동 없이 유지 |
| 정상 산출물 | `artifacts/recommendation/CURRENT.json`과 현재 버전 폴더 | API 시작에 필요. 버전 폴더만 따로 지우면 로딩 실패 |
| 문서/설정 | `README.md`, `docs`, `.gitignore`, `.vscode` | 실행 안내, 학습 설명, 사용자 편집기 설정 |

## 현재 실행에는 필요하지 않은 자료

- `archive/rating_prediction`: 이전 평점 예측 실험을 공부/재실행할 때 필요하다. 추천 API에서는 사용하지 않는다.
- `archive/recommendation_reference`: 이전 독립 NumPy 구현과 현재 구현을 비교할 때만 필요하다.
- `archive/old_artifacts`: 이전 정상 데이터 버전과 독립 감사 보고서. 현재 포인터가 가리키지 않는다.
- `archive/recovery`, `archive/before_organization`: 복구/인계 기록. 코드 실행에는 필요하지 않지만 작업 이력을 보존한다.
- `archive/rebuildable`: 과거 `__pycache__`를 모았다. Python이 다시 만들 수 있다.
- `docs/screenshots`: 검증 증빙이며 API 실행에는 필요하지 않다.

이번 정리는 분류와 이동이며 파일을 영구 삭제하지 않았다. 이동 전후 파일 해시를 비교해 내용 보존을 확인했다.
현재 실행에 필요한 원본/정상 버전/가상환경은 유지했다.
과거 학습 코드 두 개의 원본 입력/출력 경로만 보관 폴더에 맞게 조정했고 모델을 재학습하지 않았다.
