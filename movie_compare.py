"""영화 두 편을 나란히 비교합니다. 유사도 구성 요소와 대표 키워드의 겹침을 보여줍니다."""

from data_store import get_movie, get_movie_index, optional_text
from recommender import calculate_candidate


def compare_movies(data, movie_id_a, movie_id_b, keywords, keyword_count=15):
    """입력: 영화 ID 두 개, 서버 시작 때 계산한 키워드 딕셔너리. 반환: 비교 결과 딕셔너리.

    similarity는 추천에 쓰는 것과 같은 계산(0.4×메타 + 0.6×리뷰 + 감독 보너스)입니다.
    장르가 다른 두 영화도 계산은 하지만 추천 후보가 되려면 같은 장르여야 하므로 same_genre로 알려 줍니다.
    """
    if movie_id_a == movie_id_b:
        raise ValueError('서로 다른 영화 두 편을 선택하세요.')
    index_a, index_b = get_movie_index(data, movie_id_a), get_movie_index(data, movie_id_b)
    pair = calculate_candidate(data, index_a, index_b)
    profiles = data['profiles']
    genre_a = optional_text(profiles.iloc[index_a]['GENRE_NM'])
    genre_b = optional_text(profiles.iloc[index_b]['GENRE_NM'])

    terms_a = [item['term'] for item in keywords.get(movie_id_a, [])[:keyword_count]]
    terms_b = [item['term'] for item in keywords.get(movie_id_b, [])[:keyword_count]]
    return {
        'a': get_movie(data, movie_id_a),
        'b': get_movie(data, movie_id_b),
        'same_genre': genre_a is not None and genre_a == genre_b,
        'similarity': {
            'metadata': pair['metadata_similarity'], 'text': pair['text_similarity'],
            'director_bonus': pair['director_bonus'], 'combined': pair['similarity'],
        },
        'keywords_a': terms_a,
        'keywords_b': terms_b,
        'common_keywords': [term for term in terms_a if term in terms_b],
    }
