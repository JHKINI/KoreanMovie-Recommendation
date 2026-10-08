# 한국어 영화 추천과 리뷰 평점 예측

현재 우선 목표는 장르·메타데이터·리뷰 유사도·보정 평점 기반 추천 백엔드입니다.
프론트는 구현하지 않았으며 기존 평점 예측 실험은 아래에 보존합니다.

## 추천 백엔드 실행

자세한 라이브러리 선택 이유, 함수 설명, 데이터 흐름과 입출력은 [백엔드 안내](docs/BACKEND_GUIDE.md)를 읽으세요.
함수별 설명은 [함수 목록](docs/FUNCTIONS.md)에 있습니다.
최신 구현/검증 상태는 [현재 상태](docs/CURRENT_STATUS.md)에 기록했습니다. [10월 1일자 인계 원문](docs/HANDOFF_2026-10-01.md)은 문서 폴더에 보관했습니다.

```powershell
cd D:\JungPra\pythonpra\NSMC
.\.venv\Scripts\python.exe run_pipeline.py
.\.venv\Scripts\python.exe recommender.py --title "승부"
.\.venv\Scripts\python.exe review_service.py --title "서울의 봄" --order high
.\.venv\Scripts\python.exe -m unittest -v test_prepare_data test_pipeline
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

서버 시작 후 `http://127.0.0.1:8000/docs`에서 요청을 시험할 수 있습니다.
`제목으로 조회` 항목에서 `title`에 `승부` 같은 영화 이름을 넣으면 상세·추천·리뷰를 바로 조회할 수 있습니다.
추천 데이터는 `artifacts/recommendation`에 버전별로 저장하며 마지막 정상 버전만 서비스에서 읽습니다.
이 준비 과정은 리뷰 통계(TF-IDF)를 계산하며 Ridge/LSTM 학습을 실행하지 않습니다.

## 기존 평점 예측 실험

코드와 기존 CSV 결과는 `archive/rating_prediction`으로 모았습니다. 이 실험은 현재 추천 서버 실행에 필요하지 않습니다.
정리된 폴더별 역할과 유지할 파일은 [파일 정리 안내](docs/FILE_ORGANIZATION.md)를 참고하세요.

리뷰 글로 작성자가 준 실제 평점(0.5~5.0)을 예측하는 교육용 프로젝트입니다.
TF-IDF + Ridge부터 이해하고 이후 LSTM과 비교하는 것이 목표입니다.

## 데이터 준비
출처: https://www.kaggle.com/datasets/suminwang/korean-movie-review-data-30kbert
폴더명은 NSMC지만 표준 NSMC 이진 감성 데이터가 아닙니다.
원본을 다운로드하거나 기존 PC에서 복사해 이 폴더에 `Koreanmovie_review.csv`로 둡니다.
CSV는 저장소에 포함하지 않습니다. 데이터 재배포 조건은 별도로 확인해야 합니다.
`bert_label`, `neg_score`, `pos_score`는 기존 모델 예측이므로 정답으로 사용하지 않습니다.

## 새 PC에서 실행 (Windows PowerShell)
```powershell
git clone https://github.com/JungUH-0/JungPra.git
cd JungPra/pythonpra/NSMC
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe archive\rating_prediction\datachk.py
.\.venv\Scripts\python.exe archive\rating_prediction\split_data.py
.\.venv\Scripts\python.exe archive\rating_prediction\train_model.py
```
`datachk.py`는 프로젝트 루트의 원본을 읽고 정리 CSV를 `archive/rating_prediction`에 저장합니다.
기존 실행은 Python 3.14에서 이루어졌습니다. 패키지 버전은 아직 고정하지 않았으므로 환경에 따라 결과가 달라질 수 있습니다.

## 실행 흐름
1. `datachk.py`: 리뷰/평점 결측, 빈 리뷰와 완전 중복을 제거하고 clean/ready CSV를 저장합니다.
2. `split_data.py`: 같은 리뷰 문구가 양쪽에 들어가지 않도록 분리해 train/test CSV를 저장합니다.
3. `train_model.py`: 학습용에만 TF-IDF를 fit하고 Ridge를 학습해 predictions CSV를 저장합니다.
재실행하면 해당 출력 CSV를 덮어씁니다. 입력 원본은 수정하지 않습니다.

## 확인된 결과
- ready 26,321행, train 21,052행, test 5,269행, 양쪽 리뷰 교집합 0.
- 학습 행렬 (21052, 50000), 평가 행렬 (5269, 50000).
- 사용자 실행 결과: 평균 평점 기준 MAE 0.8913점, Ridge MAE 0.7464점.
- MAE는 평균 절대 오차이며 정확도 퍼센트가 아닙니다.
- 모델 설정: 문자 1~3그램, min_df=3, max_features=50000, sublinear_tf=True, Ridge alpha=10, solver=lsqr.
- predictions CSV: review, rating, predicted_rating, absolute_error.

## 평가의 한계
영화 단위 분리가 아니므로 새로운 영화에 대한 일반화 평가로 해석하지 않습니다.
플랫폼별 평점 척도 통일 여부는 미검증입니다.
튜닝은 기존 학습용 내부에서 리뷰 문구 기준으로 나눈 검증용 데이터로 진행합니다.
평가용은 설정을 선택하는 데 반복 사용하지 않습니다.

최신 진행 상황은 `docs/CURRENT_STATUS.md`, 과거 인계 기록은 `docs/HANDOFF_2026-10-01.md`를 참고하세요.
