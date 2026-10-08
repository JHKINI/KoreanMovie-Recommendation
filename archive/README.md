# 보관 자료

현재 추천 백엔드 실행에는 이 폴더의 자료를 사용하지 않는다. 과거 실험과 복구 기록을 보존하기 위해 모았다.

| 폴더 | 내용 |
|---|---|
| `rating_prediction` | 기존 TF-IDF+Ridge 평점 예측 코드와 clean/ready/train/test/predictions CSV |
| `recommendation_reference` | 이전 NumPy/pandas 추천 참조 코드와 검증 코드 |
| `old_artifacts` | 이전 추천 데이터 버전과 10월 3일자 독립 검사 보고서 |
| `recovery` | 삭제된 작업 폴더 복구 기록, 첨부 대화 이력, 삭제 전 파일 목록 |
| `before_organization` | 이전 구버전 인계 문서 |
| `rebuildable` | 실행하면 다시 만들어지는 과거 Python 캐시 |

`organization_manifest_2026-10-06.json`에는 이동 전후 경로와 이동 당시 파일 SHA-256을 기록했다.
평점 실험의 `datachk.py`와 `movie_chk.py`는 이동 후에도 원본을 찾도록 경로 부분을 수정했다.
이동 당시의 해시와 이 두 파일의 현재 해시는 다를 수 있다.

현재 원본 CSV, 정상 추천 데이터, `.venv`는 이 폴더로 옮기지 않았다.
