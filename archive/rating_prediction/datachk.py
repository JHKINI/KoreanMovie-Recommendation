"""기존 평점 예측 실험의 데이터 정리입니다. 추천 백엔드는 이 파일을 호출하지 않습니다."""
from pathlib import Path
import pandas as pd

# 원본은 프로젝트 루트에서 읽고, 실험 결과는 이 파일이 있는 폴더에 저장합니다.
base_dir = Path(__file__).resolve().parent
source_path = base_dir.parents[1] / 'Koreanmovie_review.csv'

df = pd.read_csv(source_path)

# 데이터 구조 확인
print(df.head())
print(df.columns.tolist())
df.info()

# 리뷰와 평점 예시
print(df[["review", "rating"]].head(10))

# 결측치 개수
print(df[["review", "rating"]].isna().sum())

# 평점별 데이터 개수
print(df["rating"].value_counts(dropna=False).sort_index())

# 평점 요약 통계
print(df["rating"].describe())

# 1. 이번 학습에 필요한 컬럼만 선택
data = df[["review", "rating"]].copy()

# 2. 리뷰 또는 평점이 없는 행 제거
before = len(data)
data = data.dropna(subset=["review", "rating"])

print("결측치로 제거된 행:", before - len(data))

# 3. 리뷰 앞뒤 공백 제거
data["review"] = data["review"].str.strip()

# 4. 공백만 있던 리뷰 제거
before = len(data)
data = data[data["review"] != ""].copy()

print("빈 리뷰로 제거된 행:", before - len(data))

# 5. 인덱스를 0부터 다시 정리
data = data.reset_index(drop=True)

print("최종 데이터 개수:", len(data))
print(data.head())

# 6. 정리된 데이터를 새 CSV로 저장
data.to_csv(base_dir / "movie_reviews_clean.csv", index=False, encoding="utf-8-sig")

# 정리된 CSV 불러오기
data = pd.read_csv(base_dir / "movie_reviews_clean.csv")

# 1. 리뷰와 평점이 모두 같은 중복 제거
before = len(data)

data = data.drop_duplicates(
    subset=["review", "rating"]
).reset_index(drop=True)

print("제거된 중복:", before - len(data))
print("남은 데이터:", len(data))

# 2. 같은 리뷰에 서로 다른 평점이 있는지 확인
rating_counts = data.groupby("review")["rating"].nunique()

conflicting_reviews = rating_counts[rating_counts > 1].index

print("\n서로 다른 평점이 있는 리뷰 예시:")
print(
    data[data["review"].isin(conflicting_reviews)]
    .sort_values(["review", "rating"])
    .head(20)
    .to_string(index=False)
)

# 3. 학습 준비용 파일로 저장
data.to_csv(
    base_dir / "movie_reviews_ready.csv",
    index=False,
    encoding="utf-8-sig"
)
