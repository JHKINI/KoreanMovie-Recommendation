from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error


# 1. 이 파이썬 파일과 같은 폴더의 데이터 읽기
base_dir = Path(__file__).resolve().parent

train = pd.read_csv(base_dir / "movie_reviews_train.csv")
test = pd.read_csv(base_dir / "movie_reviews_test.csv")

# 학습용과 평가용에 같은 리뷰가 없는지 확인
assert set(train["review"]).isdisjoint(set(test["review"]))


# 2. 리뷰를 숫자로 변환하기
vectorizer = TfidfVectorizer(
    analyzer="char",       # 글자 단위로 분석
    ngram_range=(1, 3),     # 글자 1~3개짜리 조각 사용
    min_df=3,              # 학습 리뷰 3개 이상에 등장하는 조각만 사용
    max_features=50000,    # 최대 50,000개 특징 사용
    sublinear_tf=True,
)

# 표현 규칙은 학습용에서만 배움
X_train = vectorizer.fit_transform(train["review"])
X_test = vectorizer.transform(test["review"])

print("학습용 shape:", X_train.shape)
print("평가용 shape:", X_test.shape)


# 3. 리뷰 특징과 실제 평점의 관계 학습하기
model = Ridge(alpha=10.0, solver="lsqr")
model.fit(X_train, train["rating"])


# 4. 평가용 리뷰의 평점 예측하기
predictions = model.predict(X_test)

# 비교 기준: 모든 리뷰에 학습용 평균 평점을 예측
baseline = [train["rating"].mean()] * len(test)

baseline_mae = mean_absolute_error(test["rating"], baseline)
model_mae = mean_absolute_error(test["rating"], predictions)

print(f"\n평균 평점만 예측한 MAE: {baseline_mae:.4f}점")
print(f"리뷰 모델의 MAE: {model_mae:.4f}점")
print(f"오차 감소량: {baseline_mae - model_mae:.4f}점")


# 5. 실제 평점과 예측값을 CSV로 저장하기
results = test.copy()
results["predicted_rating"] = predictions
results["absolute_error"] = (
    results["rating"] - results["predicted_rating"]
).abs()

output_path = base_dir / "movie_reviews_predictions.csv"
results.to_csv(output_path, index=False, encoding="utf-8-sig")

print("\n저장 완료:", output_path)