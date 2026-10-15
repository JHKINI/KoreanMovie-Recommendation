"""docs/API_RESPONSES.md에 적은 응답 구조가 실제 저장 데이터에서 유지되는지 검사합니다.

프론트가 의존하는 필드 이름·타입·정렬·오류 형식을 고정하는 테스트입니다.
준비된 추천 데이터(artifacts/recommendation/CURRENT.json)가 없으면 건너뜁니다.
"""

import pytest
from fastapi.testclient import TestClient

from api import create_app
from pipeline_common import DEFAULT_ARTIFACTS

pytestmark = pytest.mark.skipif(
    not (DEFAULT_ARTIFACTS / 'CURRENT.json').exists(),
    reason='준비된 추천 데이터가 없습니다. run_pipeline.py를 먼저 실행하세요.',
)

MOVIE_FIELDS = {
    'movie_id': str, 'title': str, 'genre': (str, type(None)), 'director': (str, type(None)),
    'release_date': (str, type(None)), 'age_rating': (str, type(None)),
    'mean_rating': (float, type(None)), 'review_count': int, 'rating_count': int,
    'positive_ratio': (float, type(None)), 'corrected_rating': float,
}
RECOMMEND_EXTRA = {
    'metadata_similarity': float, 'text_similarity': float, 'director_bonus': float,
    'similarity': float, 'final_score': float, 'reasons': list,
}
REVIEW_FIELDS = {'movie_id': str, 'review_id': str, 'source_record': int, 'review': str, 'rating': float}


@pytest.fixture(scope='module')
def client():
    # with 블록이어야 서버 시작(lifespan)에서 데이터가 로딩됩니다.
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture(scope='module')
def all_movies(client):
    body = client.get('/movies', params={'limit': 100}).json()
    return body['items']


def assert_fields(row, spec):
    assert set(spec) <= set(row), f'누락된 필드: {set(spec) - set(row)}'
    for name, expected in spec.items():
        assert isinstance(row[name], expected), f'{name}={row[name]!r}'


def test_health(client):
    body = client.get('/health').json()
    assert body['status'] == 'ok'
    assert isinstance(body['data_version'], str)
    assert body['movies'] > 0 and body['reviews'] > 0


def test_search_returns_movie_objects(client):
    response = client.get('/movies', params={'query': '승부', 'limit': 5})
    assert response.status_code == 200
    body = response.json()
    assert body['count'] == len(body['items']) >= 1
    for row in body['items']:
        assert_fields(row, MOVIE_FIELDS)
        assert '승부' in row['title']


def test_search_without_match_is_empty_200(client):
    response = client.get('/movies', params={'query': 'zzzz-없는-영화'})
    assert response.status_code == 200
    assert response.json() == {'count': 0, 'items': []}


def test_search_limit_is_respected(client):
    assert len(client.get('/movies', params={'limit': 3}).json()['items']) == 3


def test_detail_matches_search(client):
    detail = client.get('/movies/detail', params={'title': '승부'}).json()
    assert_fields(detail, MOVIE_FIELDS)
    searched = client.get('/movies', params={'query': '승부'}).json()['items']
    assert detail in searched


def test_title_is_case_and_space_insensitive(client):
    plain = client.get('/movies/detail', params={'title': '승부'}).json()
    padded = client.get('/movies/detail', params={'title': '  승부  '}).json()
    assert plain == padded


def test_recommend_structure_and_order(client):
    response = client.get('/recommend', params={'title': '승부', 'top_n': 5})
    assert response.status_code == 200
    body = response.json()
    assert_fields(body['source'], MOVIE_FIELDS)
    assert body['count'] == len(body['items']) == 5
    assert body['message'] is None
    assert isinstance(body['data_version'], str)
    scores = [row['final_score'] for row in body['items']]
    assert scores == sorted(scores, reverse=True), 'items는 final_score 내림차순이어야 합니다'
    for row in body['items']:
        assert_fields(row, {**MOVIE_FIELDS, **RECOMMEND_EXTRA})
        assert row['movie_id'] != body['source']['movie_id'], '자기 자신은 추천하지 않습니다'
        assert row['genre'] == body['source']['genre']
        assert all(isinstance(reason, str) and reason for reason in row['reasons'])


def test_recommend_by_title_equals_by_id(client):
    by_title = client.get('/recommend', params={'title': '승부'}).json()
    movie_id = by_title['source']['movie_id']
    assert client.get(f'/recommend/{movie_id}').json() == by_title


def test_recommend_for_every_movie_is_200(client, all_movies):
    """장르가 없는 영화는 빈 목록과 message를 200으로 반환합니다."""
    for movie in all_movies:
        response = client.get('/recommend', params={'title': movie['title']})
        assert response.status_code == 200, movie['title']
        body = response.json()
        if movie['genre'] is None:
            assert body['items'] == [] and body['message']
        else:
            assert body['message'] is None and body['items']


@pytest.mark.parametrize('order', ['high', 'low'])
def test_reviews_sorted_by_rating(client, order):
    response = client.get('/movies/reviews', params={'title': '서울의 봄', 'order': order, 'top_n': 20})
    assert response.status_code == 200
    body = response.json()
    assert body['order'] == order and body['title'] == '서울의 봄'
    assert body['count'] == len(body['items']) == 20
    ratings = [row['rating'] for row in body['items']]
    assert ratings == sorted(ratings, reverse=(order == 'high'))
    for row in body['items']:
        assert_fields(row, REVIEW_FIELDS)
        assert 0.5 <= row['rating'] <= 5.0


def test_reviews_by_id_path_has_no_title(client):
    movie_id = client.get('/movies/detail', params={'title': '승부'}).json()['movie_id']
    body = client.get(f'/movies/{movie_id}/reviews', params={'top_n': 1}).json()
    assert body['movie_id'] == movie_id and 'title' not in body


def test_unknown_title_is_404_with_string_detail(client):
    for path in ('/movies/detail', '/recommend', '/movies/reviews'):
        response = client.get(path, params={'title': '존재하지-않는-영화'})
        assert response.status_code == 404, path
        assert isinstance(response.json()['detail'], str)


def test_release_date_filter_can_exclude(client):
    response = client.get('/movies/detail', params={'title': '승부', 'release_date': '19000101'})
    assert response.status_code == 404


@pytest.mark.parametrize('path, params', [
    ('/recommend', {'title': '승부', 'top_n': 99}),
    ('/recommend', {'title': '승부', 'top_n': 0}),
    ('/movies/reviews', {'title': '승부', 'top_n': 21}),
    ('/movies/reviews', {'title': '승부', 'order': 'mid'}),
    ('/movies/detail', {'title': '승부', 'release_date': 'abc'}),
    ('/movies/detail', {'title': ''}),
    ('/movies', {'limit': 0}),
    ('/movies', {'limit': 101}),
])
def test_invalid_parameters_are_422_with_list_detail(client, path, params):
    response = client.get(path, params=params)
    assert response.status_code == 422
    detail = response.json()['detail']
    assert isinstance(detail, list) and detail[0]['loc'][0] == 'query'


def test_cors_allows_only_local_dev_origins(client):
    allowed = client.get('/movies', headers={'Origin': 'http://localhost:5173'})
    assert allowed.headers.get('access-control-allow-origin') == 'http://localhost:5173'
    other = client.get('/movies', headers={'Origin': 'http://example.com'})
    assert 'access-control-allow-origin' not in other.headers


def test_root_redirects_to_web_page(client):
    response = client.get('/', follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers['location'] == '/app/'
    page = client.get('/app/')
    assert page.status_code == 200 and '<title>' in page.text


def test_statistics_structure(client):
    body = client.get('/statistics', params={'top_n': 5}).json()
    assert body['movies'] > 0 and body['rated_reviews'] <= body['reviews']
    assert isinstance(body['mean_rating'], float)
    assert len(body['top_rated']) == len(body['most_reviewed']) == 5
    for row in body['top_rated'] + body['most_reviewed']:
        assert_fields(row, MOVIE_FIELDS)
    scores = [row['corrected_rating'] for row in body['top_rated']]
    assert scores == sorted(scores, reverse=True)
    assert sum(row['count'] for row in body['genres']) == body['movies']
    assert sum(row['count'] for row in body['rating_distribution']) == body['rated_reviews']
    assert client.get('/statistics', params={'top_n': 21}).status_code == 422


def test_keywords_structure_and_by_id_equals_by_title(client):
    by_title = client.get('/keywords', params={'title': '서울의 봄', 'top_n': 8})
    assert by_title.status_code == 200
    body = by_title.json()
    assert body['title'] == '서울의 봄' and body['count'] == len(body['items']) == 8
    scores = [item['score'] for item in body['items']]
    assert scores == sorted(scores, reverse=True)
    assert all(isinstance(item['term'], str) and len(item['term']) >= 2 for item in body['items'])
    assert all('봄' not in item['term'] for item in body['items']), '제목 단어는 제외'
    assert client.get(f"/movies/{body['movie_id']}/keywords", params={'top_n': 8}).json() == body


def test_keywords_errors(client):
    assert client.get('/keywords', params={'title': '존재하지-않는-영화'}).status_code == 404
    assert client.get('/keywords', params={'title': '승부', 'top_n': 31}).status_code == 422


def test_browse_pagination_total_and_sort(client):
    first = client.get('/movies/browse', params={'sort': 'reviews', 'limit': 5}).json()
    assert first['offset'] == 0 and first['limit'] == 5 and len(first['items']) == 5
    counts = [row['review_count'] for row in first['items']]
    assert counts == sorted(counts, reverse=True)
    for row in first['items']:
        assert_fields(row, MOVIE_FIELDS)
    second = client.get('/movies/browse', params={'sort': 'reviews', 'limit': 5, 'offset': 5}).json()
    assert second['total'] == first['total']
    assert not {row['movie_id'] for row in first['items']} & {row['movie_id'] for row in second['items']}
    # 마지막 쪽까지 이어 붙이면 전체 영화를 중복 없이 한 번씩 만난다.
    everything = []
    for offset in range(0, first['total'], 100):
        everything += client.get('/movies/browse', params={'limit': 100, 'offset': offset}).json()['items']
    assert len(everything) == len({row['movie_id'] for row in everything}) == first['total']


def test_browse_genre_filter_and_errors(client):
    comedy = client.get('/movies/browse', params={'genre': '코미디', 'limit': 100}).json()
    assert comedy['total'] > 0 and all(row['genre'] == '코미디' for row in comedy['items'])
    assert client.get('/movies/browse', params={'sort': 'nope'}).status_code == 422
    assert client.get('/movies/browse', params={'offset': -1}).status_code == 422


def test_taste_recommendation_over_real_data(client):
    seeds = [client.get('/movies/detail', params={'title': title}).json()['movie_id'] for title in ('승부', '서울의 봄')]
    response = client.get('/recommend/taste', params={'movie_ids': seeds, 'top_n': 5})
    assert response.status_code == 200
    body = response.json()
    assert [movie['movie_id'] for movie in body['seeds']] == seeds
    assert body['count'] == len(body['items']) == 5
    assert not set(seeds) & {row['movie_id'] for row in body['items']}, '선택한 영화는 추천에서 제외'
    scores = [row['final_score'] for row in body['items']]
    assert scores == sorted(scores, reverse=True)
    assert {seed['movie_id'] for seed in body['items'][0]['seed_similarities']} == set(seeds)


def test_taste_recommendation_errors(client):
    assert client.get('/recommend/taste', params={'movie_ids': ['x']}).status_code == 422
    assert client.get('/recommend/taste', params={'movie_ids': list('abcdef')}).status_code == 422
    assert client.get('/recommend/taste', params={'movie_ids': ['x', 'y']}).status_code == 404


def test_compare_over_real_data(client):
    ids = [client.get('/movies/detail', params={'title': title}).json()['movie_id'] for title in ('승부', '서울의 봄')]
    body = client.get('/compare', params={'a': ids[0], 'b': ids[1]}).json()
    assert body['a']['movie_id'] == ids[0] and body['b']['movie_id'] == ids[1]
    assert set(body['similarity']) == {'metadata', 'text', 'director_bonus', 'combined'}
    # 같은 쌍의 추천 계산과 일치해야 한다.
    rec = client.get('/recommend', params={'title': '승부', 'top_n': 20}).json()
    pair = next(row for row in rec['items'] if row['movie_id'] == ids[1])
    assert body['similarity']['combined'] == pair['similarity']
    assert client.get('/compare', params={'a': ids[0], 'b': ids[0]}).status_code == 422
    # 제목으로도 비교할 수 있다.
    assert client.get('/compare', params={'a': '승부', 'b': '서울의 봄'}).json() == body


def test_reviews_keyword_filter_over_real_data(client):
    body = client.get('/movies/reviews', params={'title': '승부', 'keyword': '이병헌', 'top_n': 10}).json()
    assert body['count'] > 0 and all('이병헌' in row['review'] for row in body['items'])
    movie_id = body['movie_id']
    same = client.get(f'/movies/{movie_id}/reviews', params={'keyword': '이병헌', 'top_n': 10}).json()
    assert same['items'] == body['items']


def test_movie_rating_distribution_matches_profile(client):
    movie = client.get('/movies/detail', params={'title': '승부'}).json()
    body = client.get(f"/movies/{movie['movie_id']}/ratings").json()
    assert body['movie_id'] == movie['movie_id']
    assert body['rated_reviews'] == movie['rating_count']
    assert len(body['distribution']) == 10
    assert sum(row['count'] for row in body['distribution']) == movie['rating_count']
    mean = sum(row['rating'] * row['count'] for row in body['distribution']) / body['rated_reviews']
    assert abs(mean - movie['mean_rating']) < 1e-9, '분포로 다시 계산한 평균이 프로필의 평균 평점과 같아야 한다'
    assert client.get('/movies/not-a-movie/ratings').status_code == 404


def test_browse_by_director_includes_the_movie_itself(client):
    movie = client.get('/movies/detail', params={'title': '승부'}).json()
    body = client.get('/movies/browse', params={'director': movie['director'], 'limit': 50}).json()
    assert movie['movie_id'] in [row['movie_id'] for row in body['items']]
    assert all(row['director'] == movie['director'] for row in body['items'])


def test_movies_by_keyword_over_real_data(client):
    keywords = client.get('/keywords', params={'title': '서울의 봄', 'top_n': 10}).json()
    term = keywords['items'][0]['term']
    body = client.get('/keywords/movies', params={'term': term, 'limit': 20}).json()
    assert body['term'] == term and body['count'] == len(body['items']) >= 1
    assert keywords['movie_id'] in [row['movie_id'] for row in body['items']], '그 단어를 대표 키워드로 가진 영화 자신이 결과에 있어야 한다'
    scores = [row['keyword_score'] for row in body['items']]
    assert scores == sorted(scores, reverse=True)
    for row in body['items']:
        assert_fields(row, MOVIE_FIELDS)
        listed = client.get(f"/movies/{row['movie_id']}/keywords", params={'top_n': 30}).json()['items']
        assert term in [item['term'] for item in listed], '결과의 영화는 모두 그 단어를 대표 키워드로 가져야 한다'


def test_movies_by_keyword_empty_and_invalid(client):
    empty = client.get('/keywords/movies', params={'term': '존재하지않는단어xyz'})
    assert empty.status_code == 200 and empty.json()['items'] == []
    assert client.get('/keywords/movies', params={'term': ''}).status_code == 422
    assert client.get('/keywords/movies', params={'term': '회사', 'limit': 51}).status_code == 422
