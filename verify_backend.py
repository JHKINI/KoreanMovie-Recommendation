"""현재 실제 데이터에서 HTTP 검색→추천→리뷰 연결을 확인합니다.

실행: python verify_backend.py
네트워크 포트를 열지 않고 FastAPI TestClient로 실제 저장 데이터의 응답을 검사합니다.
"""

import argparse
from pathlib import Path
from fastapi.testclient import TestClient

from api import create_app
from pipeline_common import DEFAULT_ARTIFACTS, write_json


def verify_backend(artifacts_dir=DEFAULT_ARTIFACTS):
    """실제 데이터로 HTTP 응답과 잘못된 요청 처리를 검사하고 보고서를 저장합니다."""
    artifacts_dir = Path(artifacts_dir)
    checks = []
    with TestClient(create_app(artifacts_dir)) as client:
        response = client.get('/health')
        if response.status_code != 200:
            raise AssertionError('서버 상태 확인 실패')
        health = response.json()
        checks.append({'request': '/health', 'status': response.status_code})
        for title in ['승부', '서울의 봄']:
            response = client.get('/movies', params={'query': title})
            if response.status_code != 200:
                raise AssertionError('영화 검색 실패')
            choices = [row for row in response.json()['items'] if row['title'] == title]
            if not choices:
                raise AssertionError(f'검사할 영화가 없습니다: {title}')
            movie_id = choices[0]['movie_id']
            recommended = client.get('/recommend/' + movie_id, params={'top_n': 5})
            if recommended.status_code != 200:
                raise AssertionError('추천 요청 실패')
            result = recommended.json()
            if result['data_version'] != health['data_version']:
                raise AssertionError('HTTP 응답의 데이터 버전이 다릅니다.')
            if any(row['movie_id'] == movie_id for row in result['items']):
                raise AssertionError('자기 영화가 추천에 포함됐습니다.')
            checks.append({'title': title, 'request': 'search/recommend', 'status': 200, 'recommended_titles': [row['title'] for row in result['items']]})
            title_detail = client.get('/movies/detail', params={'title': title})
            title_recommendation = client.get('/recommend', params={'title': title, 'top_n': 5})
            if title_detail.status_code != 200 or title_detail.json()['movie_id'] != movie_id:
                raise AssertionError('제목만으로 영화 상세를 조회하지 못했습니다.')
            if title_recommendation.status_code != 200 or title_recommendation.json() != result:
                raise AssertionError('제목 추천과 ID 추천 결과가 다릅니다.')
            if client.get('/movies/' + title).json()['movie_id'] != movie_id:
                raise AssertionError('기존 경로에서 제목을 처리하지 못했습니다.')
            checks.append({'title': title, 'request': 'title/detail/recommend', 'status': 200})
            for order in ['high', 'low']:
                response = client.get('/movies/' + movie_id + '/reviews', params={'order': order})
                if response.status_code != 200:
                    raise AssertionError('리뷰 조회 실패')
                rows = response.json()['items']
                values = [row['rating'] for row in rows]
                if values != sorted(values, reverse=(order == 'high')):
                    raise AssertionError('HTTP 리뷰 평점 정렬 실패')
                title_reviews = client.get('/movies/reviews', params={'title': title, 'order': order})
                if title_reviews.status_code != 200 or title_reviews.json()['items'] != rows:
                    raise AssertionError('제목 리뷰 조회와 ID 리뷰 조회 결과가 다릅니다.')
                checks.append({'title': title, 'request': 'reviews/' + order, 'status': 200, 'ratings': values})
        invalid = client.get('/recommend/not_registered')
        wrong_count = client.get('/recommend/' + movie_id, params={'top_n': 0})
        wrong_order = client.get('/movies/' + movie_id + '/reviews', params={'order': 'latest'})
        if [invalid.status_code, wrong_count.status_code, wrong_order.status_code] != [404, 422, 422]:
            raise AssertionError('잘못된 HTTP 입력의 오류 코드가 다릅니다.')
        checks.append({'request': 'invalid_inputs', 'statuses': [404, 422, 422]})
    report = {'status': 'pass', 'data_version': health['data_version'], 'movie_count': health['movies'], 'review_rows': health['reviews'], 'checks': checks}
    write_json(artifacts_dir / 'api_smoke.json', report)
    return report


def main():
    """터미널에서 실제 데이터의 HTTP 연결 검사를 실행합니다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts-dir', type=Path, default=DEFAULT_ARTIFACTS)
    args = parser.parse_args()
    report = verify_backend(args.artifacts_dir)
    print('실제 데이터 API 연결 검사:', report['status'])
    print('검사 보고서:', args.artifacts_dir / 'api_smoke.json')


if __name__ == '__main__':
    main()
