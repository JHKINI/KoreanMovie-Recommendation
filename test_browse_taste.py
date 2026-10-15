"""둘러보기·취향 추천·영화 비교·리뷰 키워드 필터를 값을 직접 정한 가상 데이터로 검사합니다.

저장된 추천 데이터가 없어도 실행됩니다(CI에서도 실행).
"""

import numpy as np
import pandas as pd
import pytest

from movie_browse import browse_movies
from movie_compare import compare_movies
from recommender import calculate_candidate, recommend_for_taste
from review_service import get_reviews

IDS = ['a', 'b', 'c', 'd', 'e']


def make_data():
    profiles = pd.DataFrame({
        'movie_id': IDS,
        'title': ['가', '나', '다', '라', '마'],
        'GENRE_NM': ['드라마', '드라마', '드라마', '코미디', None],
        'DRCTR_NM': ['감독1', '감독2', '감독1', '감독3', None],
        'OPN_DE': ['20240101', '20230101', None, '20250101', '20220101'],
        'GRAD_NM': ['12'] * 5,
        'review_count': [10, 50, 30, 20, 5],
        'rating_count': [10, 50, 30, 20, 5],
        'mean_rating': [3.0, 4.0, 3.5, 2.0, 1.0],
        'positive_ratio': [0.5] * 5,
        'corrected_rating': [3.1, 3.9, 3.5, 2.1, 1.5],
        'rating_quality': [0.5, 0.7, 0.6, 0.2, 0.1],
    })
    metadata = np.full((5, 5), 0.5)
    text = np.full((5, 5), 0.4)
    # 가-다 사이를 가깝게, 나-다는 더 가깝게 둔다.
    text[0, 2] = text[2, 0] = 0.9
    text[1, 2] = text[2, 1] = 0.8
    text[0, 1] = text[1, 0] = 0.1
    reviews = pd.DataFrame({
        'movie_id': ['a'] * 4,
        'review_id': ['1', '2', '3', '4'],
        'source_record': [1, 2, 3, 4],
        'review': ['연기가 좋다', '연기 최고', '지루하다', '연출이 아쉽다'],
        'rating': [5.0, 4.0, 1.0, np.nan],
    })
    return {
        'profiles': profiles, 'reviews': reviews,
        'matrices': {'metadata': metadata, 'text': text},
        'id_to_index': {movie_id: index for index, movie_id in enumerate(IDS)},
        'manifest': {'data_version': 'test'},
    }


# ---------- 둘러보기 ----------

def titles(result):
    return [movie['title'] for movie in result['items']]


def test_browse_sorts_and_breaks_ties_by_title():
    data = make_data()
    assert titles(browse_movies(data, 'title', 'asc')) == ['가', '나', '다', '라', '마']
    assert titles(browse_movies(data, 'title', 'desc')) == ['마', '라', '다', '나', '가']
    assert titles(browse_movies(data, 'rating', 'desc')) == ['나', '다', '가', '라', '마']
    assert titles(browse_movies(data, 'reviews', 'desc')) == ['나', '다', '라', '가', '마']
    assert titles(browse_movies(data, 'reviews', 'asc')) == ['마', '가', '라', '다', '나']


def test_browse_newest_puts_missing_date_last_in_both_directions():
    data = make_data()
    assert titles(browse_movies(data, 'newest', 'desc')) == ['라', '가', '나', '마', '다']
    assert titles(browse_movies(data, 'newest', 'asc')) == ['마', '나', '가', '라', '다']


def test_browse_genre_filter_and_pagination():
    data = make_data()
    dramas = browse_movies(data, 'title', 'asc', genre='드라마')
    assert dramas['total'] == 3 and titles(dramas) == ['가', '나', '다']
    page = browse_movies(data, 'title', 'asc', offset=1, limit=2)
    assert titles(page) == ['나', '다'] and page['total'] == 5 and page['offset'] == 1
    assert browse_movies(data, offset=99)['items'] == []
    assert browse_movies(data, genre='없는장르')['total'] == 0


@pytest.mark.parametrize('kwargs', [{'sort': 'x'}, {'direction': 'up'}, {'offset': -1}, {'limit': 0}, {'limit': 101}])
def test_browse_rejects_bad_arguments(kwargs):
    with pytest.raises(ValueError):
        browse_movies(make_data(), **kwargs)


# ---------- 취향 추천 ----------

def test_taste_uses_mean_similarity_and_excludes_seeds():
    data = make_data()
    rows = recommend_for_taste(data, ['a', 'b'], top_n=5)
    # 장르가 드라마인 후보는 다(c)뿐이고, 선택한 영화(a, b)와 코미디/장르 미상은 빠진다.
    assert [row['movie_id'] for row in rows] == ['c']
    row = rows[0]
    expected = (calculate_candidate(data, 0, 2)['similarity'] + calculate_candidate(data, 1, 2)['similarity']) / 2
    assert row['similarity'] == pytest.approx(expected)
    assert row['final_score'] == pytest.approx(0.7 * expected + 0.3 * 0.6)
    # 선택 영화별 유사도는 높은 순이다: 가(0.9)가 나(0.8)보다 앞.
    assert [seed['movie_id'] for seed in row['seed_similarities']] == ['a', 'b']
    assert row['reasons'][0].startswith("유사한 영화: '가'")


def test_taste_unions_genres_of_seeds():
    rows = recommend_for_taste(make_data(), ['a', 'd'], top_n=5)
    assert {row['movie_id'] for row in rows} == {'b', 'c'}, '드라마 후보만(코미디 후보는 선택한 d 하나뿐이라 없음)'
    rows = recommend_for_taste(make_data(), ['a', 'e'], top_n=5)
    assert {row['movie_id'] for row in rows} == {'b', 'c'}, '장르 미상 영화는 후보 장르에 기여하지 않는다'


def test_taste_validates_count_duplicates_and_unknown_ids():
    data = make_data()
    with pytest.raises(ValueError):
        recommend_for_taste(data, ['a'])
    with pytest.raises(ValueError):
        recommend_for_taste(data, ['a', 'a'])
    with pytest.raises(ValueError):
        recommend_for_taste(data, ['a', 'b', 'c', 'd', 'e', 'a', 'x'])
    with pytest.raises(KeyError):
        recommend_for_taste(data, ['a', 'zzz'])


# ---------- 영화 비교 ----------

def test_compare_components_and_common_keywords():
    data = make_data()
    keywords = {'a': [{'term': '연기'}, {'term': '연출'}], 'c': [{'term': '연출'}, {'term': '배우'}]}
    result = compare_movies(data, 'a', 'c', keywords)
    pair = calculate_candidate(data, 0, 2)
    assert result['similarity'] == {
        'metadata': pair['metadata_similarity'], 'text': pair['text_similarity'],
        'director_bonus': 0.05, 'combined': pair['similarity'],
    }, '감독1이 같아 보너스 0.05'
    assert result['same_genre'] is True
    assert result['common_keywords'] == ['연출']
    assert compare_movies(data, 'a', 'd', {})['same_genre'] is False
    assert compare_movies(data, 'a', 'e', {})['same_genre'] is False, '장르 미상은 같은 장르가 아니다'


def test_compare_rejects_same_movie():
    with pytest.raises(ValueError):
        compare_movies(make_data(), 'a', 'a', {})


# ---------- 리뷰 키워드 필터 ----------

def test_reviews_keyword_filter():
    data = make_data()
    assert [row['review_id'] for row in get_reviews(data, 'a', 10)] == ['1', '2', '3'], '평점 없는 리뷰는 제외'
    assert [row['review_id'] for row in get_reviews(data, 'a', 10, keyword='연기')] == ['1', '2']
    assert [row['review_id'] for row in get_reviews(data, 'a', 10, 'low', '연기')] == ['2', '1']
    assert get_reviews(data, 'a', 10, keyword='없는단어') == []
    assert len(get_reviews(data, 'a', 10, keyword='  ')) == 3, '공백 키워드는 필터 없음'
    assert [row['review_id'] for row in get_reviews(data, 'a', 10, keyword='연기가')] == ['1']


# ---------- 영화별 평점 분포, 감독 필터 ----------

def test_browse_director_filter():
    data = make_data()
    result = browse_movies(data, 'title', 'asc', director='감독1')
    assert result['total'] == 2 and titles(result) == ['가', '다']
    assert browse_movies(data, director='  감독1 ')['total'] == 2, '앞뒤 공백 무시'
    assert browse_movies(data, genre='드라마', director='감독3')['total'] == 0, '장르와 감독은 AND'
    assert browse_movies(data, director='없는감독')['total'] == 0


def test_movie_rating_distribution_counts_only_rated_reviews():
    from movie_statistics import movie_rating_distribution
    result = movie_rating_distribution(make_data(), 'a')
    assert result['rated_reviews'] == 3, '평점 없는 리뷰(NaN)는 제외'
    counts = {row['rating']: row['count'] for row in result['distribution']}
    assert [row['rating'] for row in result['distribution']] == [0.5 * n for n in range(1, 11)]
    assert counts[5.0] == 1 and counts[4.0] == 1 and counts[1.0] == 1 and sum(counts.values()) == 3
    assert movie_rating_distribution(make_data(), 'b')['rated_reviews'] == 0, '리뷰가 없는 영화도 10칸 0'
    with pytest.raises(KeyError):
        movie_rating_distribution(make_data(), 'zzz')
