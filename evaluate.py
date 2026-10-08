"""연결된 데이터/추천/리뷰 기능을 검사하고 추천 설정의 차이를 기록합니다.

이 검사는 추천 품질의 정답 평가가 아닙니다. 추천 품질은 별도 사람 평가가 필요합니다.
"""

import argparse
from pathlib import Path
# math: 추천 점수가 NaN/무한대인지 검사합니다.
import math
# numpy/scipy: 저장된 TF-IDF의 크기와 유사도 값을 독립적으로 확인합니다.
import numpy as np
from scipy.sparse import load_npz

from pipeline_common import DEFAULT_ARTIFACTS, read_json, write_json
from data_store import load_data, get_movie, resolve_movie_id
from recommender import recommend, baseline_recommend, same_genre_indices
from review_service import get_reviews


def check(condition, message):
    """검사 조건이 False이면 실행을 중단해 현재 버전이 게시되지 않게 합니다."""
    if not condition:
        raise AssertionError(message)


def verify_error_handling(data):
    """미등록 영화, 잘못된 개수/정렬 방향이 오류로 처리되는지 확인합니다."""
    first_id = str(data['profiles']['movie_id'].iloc[0])
    try:
        recommend(data, '없는_ID')
    except KeyError:
        pass
    else:
        raise AssertionError('미등록 영화 요청을 거부하지 않았습니다.')
    for value in [0, 21, True, 1.5]:
        for function in [recommend, get_reviews]:
            try:
                function(data, first_id, top_n=value)
            except ValueError:
                pass
            else:
                raise AssertionError('잘못된 top_n 요청을 거부하지 않았습니다.')
    try:
        get_reviews(data, first_id, order='latest')
    except ValueError:
        pass
    else:
        raise AssertionError('잘못된 리뷰 정렬 요청을 거부하지 않았습니다.')


def compare_example_settings(data):
    """기준 추천/현재 추천/평점 속성을 뺀 추천의 사례를 비교합니다. 우열을 단정하지 않습니다."""
    # 여기서는 수치 속성만 다시 계산합니다. TF-IDF를 다시 fit하지 않습니다.
    from build_features import numeric_similarity
    without_rating, _ = numeric_similarity(data['profiles'], include_rating=False)
    alternate = data.copy()
    alternate['matrices'] = data['matrices'].copy()
    alternate['matrices']['metadata'] = 0.5 * data['matrices']['categories'] + 0.5 * without_rating
    examples = []
    titles = data['profiles']['title'].tolist()
    selected = []
    for title in ['승부', '서울의 봄', '파묘']:
        if title in titles:
            selected.append(title)
    if not selected:
        selected = titles[:3]
    for title in selected:
        movie_id = resolve_movie_id(data, title=title)
        current = recommend(data, movie_id)
        baseline = baseline_recommend(data, movie_id)
        alternate_rows = recommend(alternate, movie_id)
        examples.append({
            'source_title': title,
            'current': [row['title'] for row in current],
            'genre_and_corrected_rating_baseline': [row['title'] for row in baseline],
            'without_rating_in_metadata': [row['title'] for row in alternate_rows],
            'human_review_needed': True,
        })
    return examples


def evaluate_run(data):
    """한 버전의 모든 영화에 대해 추천/리뷰/집계 연결을 검사하고 보고서를 반환합니다."""
    profiles, reviews = data['profiles'], data['reviews']
    directory = data['directory']
    tfidf = load_npz(directory / 'review_tfidf.npz')
    tfidf_info = read_json(directory / 'tfidf_info.json')
    check(tfidf.shape == (len(profiles), tfidf_info['feature_count']), 'TF-IDF와 프로필의 크기가 다릅니다.')
    check(np.isfinite(tfidf.data).all(), 'TF-IDF에 비정상 숫자가 있습니다.')
    empty_features = np.asarray(tfidf.getnnz(axis=1)) == 0
    expected_diagonal = (~empty_features).astype(float)
    check(np.allclose(np.diag(data['matrices']['text']), expected_diagonal), '리뷰 유사도 대각선 값이 잘못됐습니다.')
    movie_ids = profiles['movie_id'].tolist()
    recommendation_count = 0
    review_check_count = 0
    for movie_id in movie_ids:
        movie = get_movie(data, movie_id)
        stored_reviews = reviews.loc[reviews['movie_id'].eq(movie_id)]
        check(len(stored_reviews) == movie['review_count'], '프로필의 리뷰 행 수가 실제 리뷰와 다릅니다.')
        check(int(stored_reviews['rating'].count()) == movie['rating_count'], '유효 평점 수가 실제 리뷰와 다릅니다.')
        if movie['rating_count']:
            check(math.isclose(float(stored_reviews['rating'].mean()), movie['mean_rating']), '평균 평점이 다릅니다.')
        result = recommend(data, movie_id)
        check(len(result) == min(5, len(same_genre_indices(data, movie_id))), '추천 개수가 잘못됐습니다.')
        returned_ids = [row['movie_id'] for row in result]
        check(movie_id not in returned_ids and len(set(returned_ids)) == len(returned_ids), '자기 영화 또는 중복 추천입니다.')
        scores = [row['final_score'] for row in result]
        check(scores == sorted(scores, reverse=True), '추천 점수가 내림차순이 아닙니다.')
        for row in result:
            check(row['genre'] == movie['genre'], '다른 장르가 후보에 포함됐습니다.')
            for field in ['metadata_similarity', 'text_similarity', 'similarity', 'final_score']:
                check(math.isfinite(row[field]) and 0 <= row[field] <= 1, '추천 점수 범위가 잘못됐습니다.')
        recommendation_count += 1
        for order in ['high', 'low']:
            rows = get_reviews(data, movie_id, order=order)
            check(len(rows) == min(5, movie['rating_count']), '평점순 리뷰 개수가 잘못됐습니다.')
            ratings = [row['rating'] for row in rows]
            check(ratings == sorted(ratings, reverse=(order == 'high')), '리뷰 평점순 정렬이 잘못됐습니다.')
            for row in rows:
                check(row['movie_id'] == movie_id and row['review'].strip() != '', '다른 영화의 리뷰 또는 빈 리뷰입니다.')
            review_check_count += 1
    verify_error_handling(data)
    return {
        'status': 'pass', 'data_version': data['manifest']['data_version'],
        'movie_count': len(profiles), 'review_rows': len(reviews),
        'recommendation_checks': recommendation_count, 'review_sort_checks': review_check_count,
        'tfidf_shape': list(tfidf.shape), 'error_handling': 'pass',
        'setting_examples': compare_example_settings(data),
        'quality_note': '동작/연결 검증입니다. 추천 품질 향상과 가중치 최적화는 검증하지 않았습니다.',
    }


def main():
    """현재 게시된 데이터로 기능 검사를 다시 실행하고 보고서를 저장합니다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts-dir', type=Path, default=DEFAULT_ARTIFACTS)
    args = parser.parse_args()
    data = load_data(args.artifacts_dir)
    report = evaluate_run(data)
    write_json(data['directory'] / 'evaluation.json', report)
    print('검사 통과:', report['recommendation_checks'], '개 영화 추천,', report['review_sort_checks'], '개 리뷰 정렬')
    print('검사 보고서:', data['directory'] / 'evaluation.json')


if __name__ == '__main__':
    main()
