# 기존 리뷰 평점 예측 실험

현재 추천 API와 별개로 리뷰 텍스트에서 실제 평점을 예측하는 TF-IDF+Ridge 실험이다.
기존 코드와 CSV 결과를 삭제하지 않고 이 폴더로 옮겼다.

| 파일 | 역할 |
|---|---|
| `datachk.py` | 프로젝트 루트의 원본에서 review/rating 정리 |
| `split_data.py` | 같은 리뷰 문구가 양쪽에 들어가지 않도록 학습/평가 분리 |
| `train_model.py` | TF-IDF+Ridge 학습과 평점 예측 평가 |
| `movie_chk.py` | 프로젝트 루트의 원본 영화명 분포 확인 |
| `movie_reviews_clean.csv` | 결측/빈 리뷰 제거 결과 |
| `movie_reviews_ready.csv` | 리뷰+평점 중복 제거 결과 |
| `movie_reviews_train.csv`, `movie_reviews_test.csv` | 기존 학습/평가 데이터 |
| `movie_reviews_predictions.csv` | 기존 예측과 절대 오차 결과 |

원본은 프로젝트 루트의 `Koreanmovie_review.csv` 한 개를 공유한다.
`datachk.py`/`movie_chk.py`의 입력 경로만 보관 위치에 맞게 수정했다. `split_data.py`/`train_model.py`는 같은 폴더의 CSV를 읽는다.

사용자가 이 학습 실험을 다시 실행할 때의 명령이다. 이번 파일 정리 작업에서는 모델 학습을 실행하지 않았다.

```powershell
cd D:\JungPra\pythonpra\NSMC
.\.venv\Scripts\python.exe archive\rating_prediction\datachk.py
.\.venv\Scripts\python.exe archive\rating_prediction\split_data.py
.\.venv\Scripts\python.exe archive\rating_prediction\train_model.py
```

재실행하면 이 폴더의 해당 CSV 결과를 덮어쓴다. 기존 결과는 당시 패키지 환경의 결과이므로 새로운 실행과 점수가 다를 수 있다.
