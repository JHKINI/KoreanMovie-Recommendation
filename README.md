# 🎬 Korean Movie Recommendation

> **NSMC 한국 영화 리뷰 데이터를 기반으로 영화 유사도 분석 및 추천 시스템을 구현한 프로젝트**

한국 영화 리뷰 및 영화 메타데이터를 활용하여 사용자가 선택한 영화와 유사한 영화를 추천하는 **콘텐츠 기반 영화 추천 시스템**입니다.

영화의 장르·메타데이터와 리뷰 텍스트의 TF-IDF 기반 유사도를 결합하고, 영화의 평점 수를 고려한 보정 평점을 함께 반영하여 추천 결과를 생성합니다.

현재 **FastAPI 기반 추천 백엔드**까지 구현되어 있으며, Swagger UI를 통해 API를 직접 테스트할 수 있습니다.

---

## 📌 Project Overview

### 목적

영화의 단순 평점 순위가 아닌,

- 영화 장르
- 영화 메타데이터
- 사용자 리뷰 텍스트
- 평점 및 리뷰 수

를 함께 활용하여 **입력한 영화와 유사하면서 품질이 높은 영화를 추천**하는 것을 목표로 합니다.

### 주요 기능

- 영화 제목 검색
- 영화 상세 정보 조회
- 영화 리뷰 조회
- 영화 유사도 기반 추천
- 추천 결과에 대한 추천 근거 제공
- 영화 제목 기반 REST API 제공
- Swagger UI를 통한 API 테스트

---

## 🏗️ System Architecture

```text
                ┌─────────────────────┐
                │  Korean Movie Data  │
                │   Review / Metadata │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │    Data Pipeline    │
                │                     │
                │ Data Cleaning       │
                │ Feature Engineering │
                │ TF-IDF              │
                │ Similarity          │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Recommendation      │
                │ Engine              │
                │                     │
                │ Genre Filtering     │
                │ Metadata Similarity │
                │ Text Similarity     │
                │ Rating Quality      │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │      FastAPI        │
                │       Backend       │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │    Swagger UI       │
                │  /docs              │
                └─────────────────────┘
```

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| Language | Python |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn |
| Feature Extraction | TF-IDF |
| API | FastAPI |
| Server | Uvicorn |
| Testing | unittest |
| Data Storage | CSV / NumPy |
| Documentation | Swagger UI |

---

## 🔍 Recommendation Algorithm

추천 과정은 다음과 같이 구성되어 있습니다.

### 1. 장르 기반 후보군 생성

사용자가 선택한 영화와 동일한 장르의 영화를 우선 후보로 선정합니다.

```text
입력 영화
   ↓
영화 장르 확인
   ↓
동일 장르 영화 추출
```

### 2. 메타데이터 유사도 계산

영화의 메타데이터를 기반으로 영화 간 유사도를 계산합니다.

### 3. 리뷰 텍스트 유사도 계산

영화 리뷰 텍스트를 TF-IDF 방식으로 벡터화하고 영화 간 리뷰 표현의 유사도를 계산합니다.

```text
영화 리뷰
   ↓
TF-IDF Vectorization
   ↓
Review Similarity
```

### 4. 감독 보정

동일한 감독이 제작한 영화의 경우 추가적인 보너스 점수를 적용합니다.

```text
같은 감독
→ Director Bonus +0.05
```

### 5. 최종 추천 점수 계산

최종 유사도는 메타데이터와 리뷰 텍스트 유사도를 결합하여 계산합니다.

```text
Similarity
= 0.4 × Metadata Similarity
+ 0.6 × Text Similarity
+ Director Bonus
```

이후 영화의 보정 평점을 함께 반영하여 최종 추천 점수를 계산합니다.

```text
Final Score
= 0.7 × Similarity
+ 0.3 × Rating Quality
```

---

## ⭐ Recommendation Process

```text
입력 영화
   │
   ▼
동일 장르 영화 후보 생성
   │
   ▼
유사도 계산
 ┌─┴──────────────────┐
 │                    │
 ▼                    ▼
메타데이터 유사도     리뷰 TF-IDF 유사도
 │                    │
 └─────────┬──────────┘
           ▼
       감독 보정
           │
           ▼
      유사도 계산
           │
           ▼
      상위 후보 20개
           │
           ▼
      보정 평점 반영
           │
           ▼
      최종 점수 계산
           │
           ▼
       Top-N 추천
```

---

## 🚀 FastAPI

FastAPI를 활용하여 영화 검색, 상세 조회, 추천, 리뷰 조회 기능을 REST API로 제공합니다.

### API 실행

```bash
python run_pipeline.py

python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

서버 실행 후 Swagger UI에서 API를 확인할 수 있습니다.

```text
http://127.0.0.1:8000/docs
```

---

## 📡 주요 API

### 영화 검색

```http
GET /movies
```

영화 제목 일부를 입력하여 영화를 검색합니다.

```text
/movies?query=서울
```

### 영화 상세 조회

```http
GET /movies/detail
```

```text
/movies/detail?title=서울의 봄
```

영화의 메타데이터, 평균 평점, 리뷰 수 등의 정보를 조회합니다.

### 영화 추천

```http
GET /recommend
```

```text
/recommend?title=승부&top_n=5
```

입력한 영화와 유사한 영화를 추천합니다.

### 리뷰 조회

```http
GET /movies/reviews
```

```text
/movies/reviews?title=서울의 봄&order=high&top_n=5
```

영화의 리뷰를 평점순으로 조회할 수 있습니다.

### Health Check

```http
GET /health
```

현재 API 서버의 상태와 데이터 버전을 확인합니다.

---

## 📂 Project Structure

```text
KoreanMovie-Recommendation/
│
├── api.py                    # FastAPI 서버
├── recommender.py            # 영화 추천 로직
├── review_service.py         # 영화 리뷰 조회
├── data_store.py             # 데이터 로딩 및 조회
├── pipeline_common.py        # 파이프라인 공통 기능
│
├── prepare_data.py           # 데이터 전처리
├── build_profiles.py         # 영화 프로파일 생성
├── build_features.py         # 특징 및 유사도 생성
├── evaluate.py               # 추천 결과 평가
├── run_pipeline.py           # 전체 데이터 파이프라인 실행
│
├── test_pipeline.py          # 파이프라인 테스트
├── test_prepare_data.py      # 데이터 준비 테스트
├── verify_backend.py         # 백엔드 검증
│
├── artifacts/
│   └── recommendation/       # 추천 시스템 실행 결과
│
├── docs/
│   ├── BACKEND_GUIDE.md
│   ├── FUNCTIONS.md
│   ├── CURRENT_STATUS.md
│   └── FILE_ORGANIZATION.md
│
├── archive/
│   └── rating_prediction/    # 기존 평점 예측 실험
│
├── requirements.txt
└── README.md
```

---

## 📊 Data

본 프로젝트는 한국 영화 리뷰 및 영화 정보를 활용합니다.
출처: https://www.kaggle.com/datasets/suminwang/korean-movie-review-data-30kbert

> **주의:** 프로젝트 폴더명은 `NSMC`이지만, 현재 사용 데이터는 일반적으로 알려진 NSMC 감성분류 데이터셋과 동일한 형태의 이진 감성 데이터가 아닙니다.

데이터 원본은 저장소에 포함하지 않으며 별도로 준비해야 합니다.

```text
Koreanmovie_review.csv
```

데이터 재배포 및 이용 조건은 원본 데이터 제공처의 정책을 확인해야 합니다.

---

## ⚙️ Installation

### 1. Repository Clone

```bash
git clone <YOUR_REPOSITORY_URL>
cd KoreanMovie-Recommendation
```

### 2. Virtual Environment

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run

### 데이터 파이프라인

```bash
python run_pipeline.py
```

### 추천 테스트

```bash
python recommender.py --title "승부"
```

### 리뷰 조회

```bash
python review_service.py --title "서울의 봄" --order high
```

### 테스트

```bash
python -m unittest -v test_prepare_data test_pipeline
```

### API 서버

```bash
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

---

## 🧪 기존 평점 예측 실험

프로젝트 초기에는 영화 리뷰를 이용한 **평점 예측 실험**도 진행했습니다.

해당 실험은 현재 추천 시스템과 분리하여 `archive/rating_prediction`에 보관했습니다.

### 사용 모델

```text
TF-IDF
   ↓
Ridge Regression
   ↓
Review Rating Prediction
```

실험 결과:

| Model | MAE |
|---|---:|
| Mean Rating Baseline | 0.8913 |
| TF-IDF + Ridge | 0.7464 |

> MAE는 평균 절대 오차이며 정확도를 의미하지 않습니다.

해당 결과는 교육 및 실험 목적의 결과이며, 현재 추천 API 실행에는 사용되지 않습니다.

---

## 🔎 Evaluation

추천 시스템에서는 동일 장르 내 후보를 대상으로 리뷰 텍스트 및 메타데이터 기반 유사도를 계산합니다.

추천 결과는 다음 요소를 함께 고려합니다.

- 장르 일치
- 메타데이터 유사도
- 리뷰 텍스트 유사도
- 감독 일치 여부
- 영화 평점 품질

또한 동일 조건에서 실행했을 때 결과가 일정하게 유지될 수 있도록 정렬 기준을 명시적으로 구성했습니다.

---

## 💡 Key Points

### 1. 단순 평점순 추천에서 확장

단순히 평점이 높은 영화를 보여주는 방식이 아니라 **입력 영화와 유사한 영화**를 우선적으로 탐색합니다.

### 2. 리뷰 텍스트 활용

사용자 리뷰를 TF-IDF로 벡터화하여 영화 간 리뷰 표현의 유사도를 추천에 활용했습니다.

### 3. 추천 근거 제공

추천 결과에 단순 점수만 제공하는 것이 아니라,

```text
같은 장르
리뷰 표현 유사도
같은 감독
보정 평점
```

등의 추천 근거를 함께 반환하도록 구현했습니다.

### 4. API 서비스화

추천 알고리즘을 Python 코드 실행에만 머무르지 않고 **FastAPI REST API**로 연결하여 외부 클라이언트에서 사용할 수 있는 형태로 구성했습니다.

---

## 📈 Future Work

- [ ] 영화 포스터 및 상세 정보 제공
- [ ] 웹 프론트엔드 구현
- [ ] 사용자 기반 개인화 추천
- [ ] 협업 필터링 적용
- [ ] 추천 모델 성능 비교
- [ ] 추천 결과 평가 지표 고도화
- [ ] Docker 기반 배포
- [ ] 클라우드 서버 배포

---

## 🤝 Team

**3인 협업 프로젝트**

- 구가은
- 양진희
- 정의형

### Collaboration

3인이 협업하여 한국 영화 리뷰 및 영화 데이터를 활용한 **영화 추천 시스템**을 개발했습니다.

- 데이터 전처리 및 모델 개발
- 추천 알고리즘 구현
- 영화 유사도 분석
- TF-IDF 기반 리뷰 분석
- FastAPI 기반 REST API 개발
- 테스트 및 결과 검증

---

## 📚 Reference

- 한국 영화 리뷰 데이터
- Scikit-learn
- FastAPI
- Pandas
- NumPy

---

> **Project Status:** Recommendation Backend 구현 완료 / Frontend 미구현
