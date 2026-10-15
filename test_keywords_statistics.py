"""키워드 추출과 통계 계산을 작은 가상 데이터로 검사합니다. 저장된 추천 데이터가 없어도 실행됩니다."""

import pandas as pd

from keyword_service import build_keywords, build_stem_map, in_title
from movie_statistics import build_statistics


def make_profiles():
    # 영화마다 고유 단어 하나와, 모든 영화에 나오는 흔한 단어 '영화'를 넣는다.
    unique = ['바다', '우주', '학교', '전쟁', '요리']
    rows = []
    for index, word in enumerate(unique):
        # 원형(바다)이 단독으로도 나와야 조사가 붙은 형태(바다가/바다를/바다의)와 합쳐진다.
        text = ' '.join([f'{word} 장면', f'{word}가 인상적이다', f'{word}를 다룬 이야기', f'{word}의 분위기', '영화 좋다 영화 재밌다'] * 3)
        rows.append({'movie_id': f'm{index}', 'title': f'제목{index}', 'review_text': text})
    return pd.DataFrame(rows)


def test_particles_are_merged_into_base_word():
    texts = make_profiles()['review_text'].tolist()
    stems = build_stem_map(texts, min_df=1)
    # 어휘에 원형 '바다'가 있으면 '바다가'/'바다를'은 합쳐진다.
    assert stems.get('바다가') == '바다'
    assert stems.get('바다의') == '바다'


def test_keywords_pick_distinctive_word_and_skip_common_one():
    keywords = build_keywords(make_profiles(), top_n=3, min_df=1, max_df=0.5)
    first = [item['term'] for item in keywords['m0']]
    assert first[0] == '바다'
    assert '영화' not in first, '모든 영화에 나오는 단어는 대표 키워드가 아니다'
    assert all(0 < item['score'] <= 1 for item in keywords['m0'])


def test_title_words_are_excluded():
    assert in_title('서울의', '서울의 봄')
    assert in_title('봄은', '서울의 봄'), '제목 단어에 조사가 붙은 형태'
    assert not in_title('황정민', '서울의 봄')


def test_keywords_on_too_small_data_is_empty_not_error():
    tiny = pd.DataFrame([{'movie_id': 'a', 'title': 'x', 'review_text': ''}])
    assert build_keywords(tiny) == {}


def make_data():
    profiles = pd.DataFrame({
        'movie_id': ['a', 'b', 'c'], 'title': ['가', '나', '다'],
        'GENRE_NM': ['드라마', '드라마', None], 'DRCTR_NM': ['x', 'y', None], 'MOVIE_SDIV_NM': [None] * 3,
        'GRAD_NM': [None] * 3, 'OPN_DE': [None] * 3, 'TOT_SCRN_CO': [1] * 3, 'VIEWNG_NMPR_CO': [1] * 3,
        'review_count': [5, 9, 2], 'rating_count': [5, 8, 1], 'mean_rating': [3.0, 4.0, None],
        'positive_ratio': [None] * 3, 'corrected_rating': [3.2, 3.9, 3.0],
    })
    reviews = pd.DataFrame({'rating': [5.0, 5.0, 3.0, 0.5, None]})
    return {'profiles': profiles, 'reviews': reviews, 'manifest': {'data_version': 'test'}}


def test_statistics_counts_and_ordering():
    stats = build_statistics(make_data(), top_n=2)
    assert (stats['movies'], stats['reviews'], stats['rated_reviews']) == (3, 5, 4)
    assert abs(stats['mean_rating'] - (5 + 5 + 3 + 0.5) / 4) < 1e-9
    assert [row['title'] for row in stats['top_rated']] == ['나', '가'], '보정 평점 내림차순'
    assert [row['title'] for row in stats['most_reviewed']] == ['나', '가'], '리뷰 수 내림차순'
    assert {row['genre']: row['count'] for row in stats['genres']} == {'드라마': 2, '장르 미상': 1}


def test_rating_distribution_covers_all_steps():
    stats = build_statistics(make_data())
    distribution = stats['rating_distribution']
    assert [row['rating'] for row in distribution] == [0.5 * n for n in range(1, 11)]
    counts = {row['rating']: row['count'] for row in distribution}
    assert counts[5.0] == 2 and counts[0.5] == 1 and counts[3.0] == 1 and counts[1.0] == 0
    assert sum(counts.values()) == stats['rated_reviews']


def test_multi_character_endings_are_merged_when_base_exists():
    texts = ['노동자 노동자들의 바다 바다에서', '노동자 노동자들의 바다 바다에서', '노동자 바다']
    stems = build_stem_map(texts, min_df=1)
    assert stems['노동자들의'] == '노동자'
    assert stems['바다에서'] == '바다'


def test_ending_is_kept_when_base_word_is_absent():
    # '우주에서'만 있고 '우주'는 없으면 합치지 않는다(원형이 어휘에 있을 때만 합침).
    assert build_stem_map(['우주에서 우주에서 별빛'], min_df=1) == {}


def test_base_word_must_have_at_least_two_characters():
    # '봄은'의 원형 '봄'은 한 글자라 합치지 않는다(오탐 방지).
    assert build_stem_map(['봄 봄은 봄은'], min_df=1) == {}


def test_movies_by_keyword_sorts_by_score_and_matches_exactly():
    from keyword_service import movies_by_keyword
    keywords = {
        'a': [{'term': '노동', 'score': 0.3}, {'term': '회사', 'score': 0.1}],
        'b': [{'term': '회사', 'score': 0.5}],
        'c': [{'term': '회사', 'score': 0.5}, {'term': '노동', 'score': 0.2}],
        'd': [],
    }
    assert movies_by_keyword(keywords, '회사') == [('b', 0.5), ('c', 0.5), ('a', 0.1)], '점수 내림차순, 동점은 ID 순'
    assert movies_by_keyword(keywords, '회사', limit=2) == [('b', 0.5), ('c', 0.5)]
    assert movies_by_keyword(keywords, ' 노동 ') == [('a', 0.3), ('c', 0.2)], '앞뒤 공백은 무시'
    assert movies_by_keyword(keywords, '노') == [], '부분 일치는 찾지 않는다'
    assert movies_by_keyword({}, '회사') == []
