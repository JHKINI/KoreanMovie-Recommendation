from pathlib import Path
import pandas as pd

base_dir = Path(__file__).resolve().parent
# 보관 폴더로 옮겨도 프로젝트 루트의 원본 한 개를 공유합니다.
project_dir = base_dir.parents[1]
df = pd.read_csv(project_dir / "Koreanmovie_review.csv")

# 앞뒤 공백을 제거하고 빈 영화명은 결측치로 처리
movie_names = df["MOVIE_NM"].str.strip().replace("", pd.NA)

print("전체 데이터 행 수:", len(df))
print("영화명 기준 영화 수:", movie_names.nunique())
print("영화명 없는 행 수:", movie_names.isna().sum())

# 영화별 데이터 행 수
print("\n영화별 행 수 상위 20개:")
print(movie_names.value_counts().head(20))
