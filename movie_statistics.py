"""저장된 영화/리뷰 데이터의 전체 통계를 계산합니다. 요청 때 원본 CSV를 읽지 않습니다."""

from data_store import get_movie_index, movie_to_dict

# 원본 평점 척도는 0.5~5.0이고 0.5 간격입니다.
RATING_STEPS = [step / 2 for step in range(1, 11)]


def build_statistics(data, top_n=10):
    """입력: load_data 결과, 목록 길이. 반환: JSON으로 바꿀 수 있는 통계 딕셔너리.

    top_rated는 리뷰 수를 반영한 보정 평점 순, most_reviewed는 리뷰 수 순입니다.
    rating_distribution은 평점이 있는 리뷰만 센 것이고, 평점 없는 리뷰는 rated_reviews에서 빠집니다.
    """
    profiles = data['profiles']
    reviews = data['reviews']
    ratings = reviews['rating'].dropna()

    counts = ratings.value_counts()
    distribution = [{'rating': step, 'count': int(counts.get(step, 0))} for step in RATING_STEPS]

    genres = profiles['GENRE_NM'].fillna('').astype(str).str.strip().replace('', '장르 미상').value_counts()
    genre_rows = [{'genre': str(name), 'count': int(count)} for name, count in genres.items()]

    top_rated = profiles.sort_values(['corrected_rating', 'review_count', 'title'], ascending=[False, False, True], kind='stable').head(top_n)
    most_reviewed = profiles.sort_values(['review_count', 'corrected_rating', 'title'], ascending=[False, False, True], kind='stable').head(top_n)

    return {
        'movies': int(len(profiles)),
        'reviews': int(len(reviews)),
        'rated_reviews': int(len(ratings)),
        'mean_rating': float(ratings.mean()) if len(ratings) else None,
        'genres': genre_rows,
        'rating_distribution': distribution,
        'top_rated': [movie_to_dict(row) for _, row in top_rated.iterrows()],
        'most_reviewed': [movie_to_dict(row) for _, row in most_reviewed.iterrows()],
        'data_version': data['manifest']['data_version'],
    }


def movie_rating_distribution(data, movie_id):
    """한 영화의 평점 분포를 반환합니다. 평점이 있는 리뷰만 셉니다(없는 리뷰는 제외).

    반환: {'movie_id', 'rated_reviews', 'distribution': [{'rating', 'count'}...]} — 0.5~5.0, 항상 10개.
    미등록 영화는 KeyError입니다.
    """
    get_movie_index(data, movie_id)
    reviews = data['reviews']
    ratings = reviews.loc[reviews['movie_id'].eq(movie_id), 'rating'].dropna()
    counts = ratings.value_counts()
    return {
        'movie_id': movie_id,
        'rated_reviews': int(len(ratings)),
        'distribution': [{'rating': step, 'count': int(counts.get(step, 0))} for step in RATING_STEPS],
    }
