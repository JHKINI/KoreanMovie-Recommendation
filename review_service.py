"""영화를 선택해 실제 리뷰를 높은/낮은 실제 평점순으로 조회합니다."""

import argparse
import json
from pathlib import Path

from pipeline_common import DEFAULT_ARTIFACTS, validate_top_n
from data_store import load_data, get_movie_index, optional_text, resolve_movie_id


def get_reviews(data, movie_id, top_n=5, order='high'):
    """해당 영화의 평점 있는 리뷰를 정렬해 반환합니다.

    결측 평점 리뷰는 저장돼 있지만 평점순 조회에서 제외합니다.
    동점은 원본 레코드 순서입니다. 작성일이 없으므로 최신순이라고 부르지 않습니다.
    """
    validate_top_n(top_n)
    if order not in ['high', 'low']:
        raise ValueError('order는 high 또는 low여야 합니다.')
    get_movie_index(data, movie_id)
    rows = data['reviews'].loc[data['reviews']['movie_id'].eq(movie_id)].copy()
    rows = rows.dropna(subset=['rating'])
    rows = rows.sort_values(['rating', 'source_record'], ascending=[order == 'low', True], kind='stable').head(top_n)
    result = []
    for _, row in rows.iterrows():
        result.append({
            'movie_id': str(row['movie_id']), 'review_id': optional_text(row['review_id']),
            'source_record': int(row['source_record']), 'review': str(row['review']),
            'rating': float(row['rating']),
        })
    return result


def main():
    """터미널에서 영화와 정렬 방향을 받아 실제 리뷰를 JSON으로 출력합니다."""
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--title')
    selection.add_argument('--movie-id')
    parser.add_argument('--top-n', type=int, default=5)
    parser.add_argument('--order', choices=['high', 'low'], default='high')
    parser.add_argument('--artifacts-dir', type=Path, default=DEFAULT_ARTIFACTS)
    args = parser.parse_args()
    try:
        data = load_data(args.artifacts_dir)
        movie_id = resolve_movie_id(data, args.movie_id, args.title)
        rows = get_reviews(data, movie_id, args.top_n, args.order)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f'중단: {exc}\n')
    print(json.dumps({'movie_id': movie_id, 'order': args.order, 'count': len(rows), 'items': rows}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
