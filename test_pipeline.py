"""작은 가상 데이터로 결측/충돌/정렬/버전/HTTP 연결을 검사합니다.

실행: python -m unittest -v test_prepare_data test_pipeline
실제 CSV는 테스트에서 수정하지 않습니다.
"""

# unittest/tempfile: 별도 테스트 패키지 없이 임시 폴더에서 자동 검사를 실행합니다.
import unittest
import tempfile
import shutil
import io
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
# TestClient/httpx: 실제 서버 포트를 열지 않고 HTTP 요청/응답을 검사합니다.
from fastapi.testclient import TestClient

from api import create_app
from build_profiles import create_profiles, make_movie_id, build_profiles
from build_features import category_similarity, numeric_similarity
from data_store import load_data, load_run, search_movies, resolve_movie_id, get_movie
from pipeline_common import file_sha256, read_json, write_json
from recommender import recommend
from review_service import get_reviews
from run_pipeline import run_pipeline


def fixture_frame():
    """결측 평점/감독/장르, 중복, 빈 리뷰가 섞인 테스트용 원본 CSV 표를 만듭니다."""
    examples = [
        ('가 영화', '연기가 좋고 재미있는 영화 첫 번째', 5.0, '드라마', '감독 가'),
        ('가 영화', '연기가 좋고 재미있는 영화 두 번째', 4.0, '드라마', '감독 가'),
        ('가 영화', '연기가 좋고 재미있는 영화 평점은 없음', None, '드라마', '감독 가'),
        ('나 영화', '연기가 좋고 재미있는 영화 다른 작품', 4.5, '드라마', '감독 가'),
        ('다 영화', '연기가 좋고 재미있는 영화 평가는 낮음', 1.0, '드라마', '감독 다'),
        ('라 영화', '연기가 좋고 재미있는 영화 장르 미상', 3.0, None, None),
        ('마 영화', '연기가 좋고 재미있는 영화 유효 평점 없음', None, '드라마', None),
        ('바 영화', '   ', 4.0, '코미디', '감독 바'),
    ]
    examples.append(examples[0])
    rows = []
    for index, example in enumerate(examples):
        title, review, rating, genre, director = example
        row = {
            'review_id': 'review_' + str(index + 1), 'review': review, 'rating': rating,
            'MOVIE_NM': title, 'DRCTR_NM': director, 'GENRE_NM': genre,
            'MOVIE_SDIV_NM': '일반영화' if genre else None,
            'GRAD_NM': '전체관람가' if genre else None, 'OPN_DE': 20250101,
            'TOT_SCRN_CO': 0, 'VIEWNG_NMPR_CO': 100,
            'bert_label': 1 if rating is not None and rating >= 3 else None,
            'pos_score': 0.8, 'neg_score': 0.2,
        }
        rows.append(row)
    return pd.DataFrame(rows)


class ProfileTests(unittest.TestCase):
    """학습 없이 집계 규칙과 영화 ID의 안정성을 확인합니다."""

    def test_missing_ratings_preserved_and_counts_separate(self):
        """평점 결측 리뷰 보존과 리뷰 수/평점 수 차이를 확인합니다."""
        source = fixture_frame()
        before = source.copy(deep=True)
        profiles, reviews, summary = create_profiles(source)
        pd.testing.assert_frame_equal(source, before)
        self.assertEqual(len(profiles), 5)
        self.assertEqual(len(reviews), 7)
        self.assertEqual(summary['excluded_titles'], ['바 영화'])
        movie = profiles.loc[profiles['title'].eq('가 영화')].iloc[0]
        self.assertEqual(movie['review_count'], 3)
        self.assertEqual(movie['rating_count'], 2)
        self.assertEqual(movie['mean_rating'], 4.5)
        self.assertIn('평점은 없음', movie['review_text'])
        unrated = profiles.loc[profiles['title'].eq('마 영화')].iloc[0]
        self.assertEqual(unrated['rating_count'], 0)
        self.assertAlmostEqual(unrated['corrected_rating'], summary['global_mean_rating'])

    def test_ids_survive_reordering_and_keep_punctuation(self):
        """행을 섞어도 ID는 같고 쉼표가 다른 제목은 합쳐지지 않는지 검사합니다."""
        data = fixture_frame()
        profiles, _, _ = create_profiles(data)
        reordered, _, _ = create_profiles(data.sample(frac=1, random_state=7))
        self.assertEqual(profiles['movie_id'].tolist(), reordered['movie_id'].tolist())
        self.assertNotEqual(make_movie_id('제목', '20250101'), make_movie_id('제목,', '20250101'))

    def test_metadata_conflict_stops_aggregation(self):
        """같은 제목의 감독/개봉일 충돌을 first로 숨기지 않고 중단하는지 확인합니다."""
        for column, value in [('DRCTR_NM', '다른 감독'), ('OPN_DE', 20260101)]:
            with self.subTest(column=column):
                data = fixture_frame()
                data.loc[1, column] = value
                with self.assertRaises(ValueError):
                    create_profiles(data)

    def test_invalid_rating_and_empty_data_stop(self):
        """잘못된 평점/빈 표가 집계되지 않게 합니다."""
        data = fixture_frame()
        data.loc[0, 'rating'] = 10
        with self.assertRaises(ValueError):
            create_profiles(data)
        with self.assertRaises(ValueError):
            create_profiles(data.iloc[:0])

    def test_rating_shrinkage_formula(self):
        """보정 평점이 실제 v, R, C, m으로 계산됐는지 독립적으로 확인합니다."""
        profiles, _, summary = create_profiles(fixture_frame(), m=20)
        movie = profiles.loc[profiles['title'].eq('가 영화')].iloc[0]
        expected = (2 * 4.5 + 20 * summary['global_mean_rating']) / 22
        self.assertAlmostEqual(movie['corrected_rating'], expected)
        with self.assertRaises(ValueError):
            create_profiles(fixture_frame(), m=0)

    def test_unknown_categories_do_not_match(self):
        """미상 범주끼리 일치 점수를 주지 않는지 검사합니다."""
        profiles = pd.DataFrame({'MOVIE_SDIV_NM': [None, None], 'GRAD_NM': [None, None]})
        self.assertEqual(category_similarity(profiles)[0, 1], 0)

    def test_review_id_zero_prefix_is_preserved(self):
        """숫자처럼 보이는 리뷰 ID의 앞자리 0이 CSV 연결에서 사라지지 않게 합니다."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = fixture_frame()
            data['review_id'] = [str(i + 1).zfill(4) for i in range(len(data))]
            source = root / 'input.csv'
            data.to_csv(source, index=False)
            build_profiles(source, root / 'output')
            reviews = pd.read_csv(root / 'output' / 'reviews.csv', dtype={'review_id': str})
            self.assertEqual(reviews['review_id'].iloc[0], '0001')

    def test_numeric_zero_and_all_missing_handling(self):
        """실제 0을 보존하고 전체 결측 수치 컬럼은 제외하는지 검사합니다."""
        profiles = pd.DataFrame({
            'TOT_SCRN_CO': [0, 10], 'VIEWNG_NMPR_CO': [None, None],
            'mean_rating': [4, 4], 'positive_ratio': [None, None],
        })
        matrix, settings = numeric_similarity(profiles, include_rating=False)
        self.assertEqual(settings['excluded_all_missing'], ['VIEWNG_NMPR_CO', 'positive_ratio'])
        self.assertEqual(settings['columns']['TOT_SCRN_CO']['min'], 0)
        self.assertAlmostEqual(matrix[0, 1], 0)


class PipelineTests(unittest.TestCase):
    """준비한 파일을 다시 로딩해서 서비스와 HTTP API가 연결되는지 검사합니다."""

    @classmethod
    def setUpClass(cls):
        """모든 테스트가 공유할 작은 데이터 버전을 임시 폴더에 한 번 준비합니다."""
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.source = cls.root / 'input.csv'
        fixture_frame().to_csv(cls.source, index=False)
        cls.artifacts = cls.root / 'artifacts'
        cls.before_hash = file_sha256(cls.source)
        with redirect_stdout(io.StringIO()):
            cls.directory = run_pipeline(cls.source, cls.artifacts)
        cls.data = load_data(cls.artifacts)
        cls.movie_id = resolve_movie_id(cls.data, title='가 영화')

    @classmethod
    def tearDownClass(cls):
        """테스트 전용 임시 폴더를 정리합니다. 실제 프로젝트 데이터는 건드리지 않습니다."""
        cls.temporary.cleanup()

    def test_source_unchanged_and_saved_evaluation(self):
        """입력 보존과 파이프라인 전체 검사 완료를 확인합니다."""
        self.assertEqual(file_sha256(self.source), self.before_hash)
        report = read_json(self.directory / 'evaluation.json')
        self.assertEqual(report['status'], 'pass')
        self.assertEqual(report['recommendation_checks'], 5)
        self.assertEqual(report['review_sort_checks'], 10)

    def test_search_is_literal_not_regex(self):
        """사용자 검색어의 정규식 문자가 검색 기능을 바꾸지 않게 합니다."""
        self.assertEqual(len(search_movies(self.data, '가 영화')), 1)
        self.assertEqual(search_movies(self.data, '['), [])
        self.assertEqual(search_movies(self.data, '없는 제목'), [])

    def test_recommendation_score_and_candidate_shortage(self):
        """점수 공식/자기 제외/후보 부족 처리를 확인합니다."""
        rows = recommend(self.data, self.movie_id, top_n=20)
        self.assertEqual(len(rows), 3)
        self.assertNotIn(self.movie_id, [row['movie_id'] for row in rows])
        self.assertEqual([row['final_score'] for row in rows], sorted([row['final_score'] for row in rows], reverse=True))
        for row in rows:
            expected_quality = (row['corrected_rating'] - 0.5) / 4.5
            self.assertAlmostEqual(row['final_score'], 0.7 * row['similarity'] + 0.3 * expected_quality)
            self.assertTrue(row['reasons'])

    def test_unknown_genre_and_missing_director(self):
        """장르 미상은 빈 추천, 감독 미상은 가산점 0인지 확인합니다."""
        unknown = resolve_movie_id(self.data, title='라 영화')
        self.assertEqual(recommend(self.data, unknown), [])
        missing_director = resolve_movie_id(self.data, title='마 영화')
        for row in recommend(self.data, missing_director):
            self.assertEqual(row['director_bonus'], 0)

    def test_actual_rating_order_and_unrated_exclusion(self):
        """실제 평점으로 높은/낮은 순서를 정하고 결측 평점은 조회에서 빼는지 확인합니다."""
        high = get_reviews(self.data, self.movie_id, order='high')
        low = get_reviews(self.data, self.movie_id, order='low')
        self.assertEqual([row['rating'] for row in high], [5, 4])
        self.assertEqual([row['rating'] for row in low], [4, 5])
        unrated = resolve_movie_id(self.data, title='마 영화')
        self.assertEqual(get_reviews(self.data, unrated), [])

    def test_error_inputs(self):
        """정수 범위/미등록 ID/리뷰 정렬 오류를 확인합니다."""
        for value in [0, 21, True, 1.1]:
            with self.assertRaises(ValueError):
                recommend(self.data, self.movie_id, value)
        with self.assertRaises(KeyError):
            recommend(self.data, '잘못된_ID')
        with self.assertRaises(ValueError):
            get_reviews(self.data, self.movie_id, order='latest')

    def test_corrupt_file_cannot_load(self):
        """다른 내용의 CSV가 섞이면 해시 검사가 로딩을 거부하는지 확인합니다."""
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / 'run'
            shutil.copytree(self.directory, copied)
            with (copied / 'movie_profiles.csv').open('a', encoding='utf-8') as output:
                output.write('corrupt')
            with self.assertRaises(ValueError):
                load_run(copied)

    def test_movie_order_mismatch_cannot_load(self):
        """파일 해시가 새로 기록돼도 영화 ID 행 순서가 틀리면 거부하는지 확인합니다."""
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / 'run'
            shutil.copytree(self.directory, copied)
            with np.load(copied / 'similarities.npz', allow_pickle=False) as stored:
                arrays = {key: stored[key].copy() for key in stored.files}
            arrays['movie_ids'] = arrays['movie_ids'][::-1]
            np.savez_compressed(copied / 'similarities.npz', **arrays)
            manifest = read_json(copied / 'manifest.json')
            manifest['files']['similarities.npz'] = file_sha256(copied / 'similarities.npz')
            write_json(copied / 'manifest.json', manifest)
            with self.assertRaises(ValueError):
                load_run(copied)

    def test_failed_update_keeps_previous_version(self):
        """새 원본 검사 실패 시 마지막 정상 데이터 포인터가 유지되는지 확인합니다."""
        before = read_json(self.artifacts / 'CURRENT.json')
        invalid = fixture_frame()
        invalid.loc[0, 'rating'] = 10
        invalid_path = self.root / 'invalid.csv'
        invalid.to_csv(invalid_path, index=False)
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                run_pipeline(invalid_path, self.artifacts)
        self.assertEqual(read_json(self.artifacts / 'CURRENT.json'), before)

    def test_shortlist_is_selected_before_rating_rerank(self):
        """유사도 20위 밖 후보는 높은 보정 평점이어도 최종 추천에 들어오지 않게 합니다."""
        # 파일 I/O와 무관한 순위 규칙만 작은 가상 데이터로 독립적으로 검사합니다.
        profiles = []
        for index in range(22):
            profiles.append({
                'movie_id': str(index), 'title': '영화 ' + str(index), 'GENRE_NM': '드라마',
                'DRCTR_NM': '', 'OPN_DE': '', 'GRAD_NM': '', 'mean_rating': 3,
                'review_count': 1, 'rating_count': 1, 'positive_ratio': 0.5,
                'corrected_rating': 5 if index == 21 else 0.5,
                'rating_quality': 1 if index == 21 else 0,
            })
        similarities = np.zeros((22, 22))
        for index in range(1, 21):
            similarities[0, index] = 0.9
        data = {'profiles': pd.DataFrame(profiles), 'id_to_index': {str(i): i for i in range(22)}, 'matrices': {'text': similarities, 'metadata': similarities}}
        rows = recommend(data, '0', top_n=20)
        self.assertEqual(len(rows), 20)
        self.assertNotIn('21', [row['movie_id'] for row in rows])

    def test_api_search_recommend_reviews_and_no_request_fit(self):
        """HTTP가 서비스 결과와 같고 요청 중 TF-IDF를 다시 fit하지 않는지 확인합니다."""
        application = create_app(self.artifacts)
        with patch('sklearn.feature_extraction.text.TfidfVectorizer.fit_transform', side_effect=AssertionError('요청 중 fit 금지')):
            with TestClient(application) as client:
                self.assertEqual(client.get('/health').status_code, 200)
                searched = client.get('/movies', params={'query': '가 영화'}).json()
                self.assertEqual(searched['items'][0]['movie_id'], self.movie_id)
                detail = client.get('/movies/' + self.movie_id).json()
                self.assertEqual(detail['review_count'], 3)
                rows = client.get('/recommend/' + self.movie_id).json()['items']
                self.assertEqual(rows, recommend(self.data, self.movie_id))
                high = client.get('/movies/' + self.movie_id + '/reviews').json()['items']
                self.assertEqual(high, get_reviews(self.data, self.movie_id))

    def test_api_404_422_and_unknown_genre(self):
        """미등록 ID는 404, 잘못된 요청 값은 422, 장르 미상은 빈 정상 결과인지 확인합니다."""
        with TestClient(create_app(self.artifacts)) as client:
            self.assertEqual(client.get('/recommend/not_registered').status_code, 404)
            self.assertEqual(client.get('/movies/not_registered/reviews').status_code, 404)
            self.assertEqual(client.get('/recommend/' + self.movie_id, params={'top_n': 0}).status_code, 422)
            self.assertEqual(client.get('/recommend/' + self.movie_id, params={'top_n': 21}).status_code, 422)
            self.assertEqual(client.get('/movies/' + self.movie_id + '/reviews', params={'order': 'latest'}).status_code, 422)
            unknown_id = resolve_movie_id(self.data, title='라 영화')
            response = client.get('/recommend/' + unknown_id)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['items'], [])

    def test_title_query_detail_recommend_and_reviews(self):
        """ID 없이 제목만 입력해 상세/추천/리뷰를 조회하고 같은 서비스 결과인지 확인합니다."""
        with TestClient(create_app(self.artifacts)) as client:
            detail = client.get('/movies/detail', params={'title': '  가 영화  '})
            self.assertEqual(detail.status_code, 200)
            self.assertEqual(detail.json()['movie_id'], self.movie_id)
            recommended = client.get('/recommend', params={'title': '가 영화', 'top_n': 3})
            self.assertEqual(recommended.status_code, 200)
            self.assertEqual(recommended.json()['items'], recommend(self.data, self.movie_id, 3))
            for order in ['high', 'low']:
                response = client.get('/movies/reviews', params={'title': '가 영화', 'order': order})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['items'], get_reviews(self.data, self.movie_id, order=order))

    def test_existing_paths_also_accept_title(self):
        """기존 movie_id 경로에도 제목을 넣을 수 있어 Swagger에서 바로 사용할 수 있게 합니다."""
        with TestClient(create_app(self.artifacts)) as client:
            self.assertEqual(client.get('/movies/가 영화').json()['movie_id'], self.movie_id)
            self.assertEqual(client.get('/recommend/가 영화').json()['items'], recommend(self.data, self.movie_id))
            self.assertEqual(client.get('/movies/가 영화/reviews').json()['items'], get_reviews(self.data, self.movie_id))

    def test_title_api_invalid_requests(self):
        """빈 제목/없는 제목/개수/날짜/정렬 오류를 확인합니다. 제목 일부를 임의로 선택하지 않습니다."""
        with TestClient(create_app(self.artifacts)) as client:
            for endpoint in ['/movies/detail', '/recommend', '/movies/reviews']:
                self.assertEqual(client.get(endpoint, params={'title': '없는 제목'}).status_code, 404)
                self.assertEqual(client.get(endpoint, params={'title': '가'}).status_code, 404)
                self.assertEqual(client.get(endpoint, params={'title': ''}).status_code, 422)
                self.assertEqual(client.get(endpoint, params={'title': '   '}).status_code, 422)
                self.assertEqual(client.get(endpoint).status_code, 422)
                self.assertEqual(client.get(endpoint, params={'title': '가 영화', 'release_date': 'bad'}).status_code, 422)
            self.assertEqual(client.get('/recommend', params={'title': '가 영화', 'top_n': 21}).status_code, 422)
            self.assertEqual(client.get('/movies/reviews', params={'title': '가 영화', 'order': 'latest'}).status_code, 422)

    def test_ambiguous_title_returns_candidates_and_can_be_filtered(self):
        """동명이작을 무작위 선택하지 않고 409/후보 반환 후 감독·개봉일로 구분합니다."""
        data = self.data.copy()
        data['profiles'] = self.data['profiles'].copy(deep=True)
        other_id = resolve_movie_id(self.data, title='나 영화')
        other_index = data['id_to_index'][other_id]
        data['profiles']['OPN_DE'] = data['profiles']['OPN_DE'].astype(str)
        data['profiles'].loc[other_index, 'title'] = '가 영화'
        data['profiles'].loc[other_index, 'OPN_DE'] = '20260101'
        data['profiles'].loc[other_index, 'DRCTR_NM'] = '다른 감독'
        with patch('api.load_data', return_value=data):
            with TestClient(create_app(self.artifacts)) as client:
                for endpoint in ['/movies/detail', '/recommend', '/movies/reviews']:
                    ambiguous = client.get(endpoint, params={'title': '가 영화'})
                    self.assertEqual(ambiguous.status_code, 409)
                    choices = ambiguous.json()['detail']['candidates']
                    self.assertEqual({row['movie_id'] for row in choices}, {self.movie_id, other_id})
                    dated = client.get(endpoint, params={'title': '가 영화', 'release_date': '20260101'})
                    self.assertEqual(dated.status_code, 200)
                    self.assertEqual(client.get(endpoint, params={'title': '가 영화', 'director': '없는 감독'}).status_code, 404)
                directed = client.get('/movies/detail', params={'title': '가 영화', 'director': '다른 감독'})
                self.assertEqual(directed.json()['movie_id'], other_id)
                self.assertEqual(client.get('/movies/가 영화').status_code, 409)

    def test_title_with_slash_and_special_characters(self):
        """제목의 슬래시/정규식 문자가 query 입력에서 정확한 글자로 처리되는지 확인합니다."""
        data = self.data.copy()
        data['profiles'] = self.data['profiles'].copy(deep=True)
        index = data['id_to_index'][self.movie_id]
        title = '가/나 [영화]?'
        data['profiles'].loc[index, 'title'] = title
        with patch('api.load_data', return_value=data):
            with TestClient(create_app(self.artifacts)) as client:
                self.assertEqual(client.get('/movies/detail', params={'title': title}).json()['movie_id'], self.movie_id)
                self.assertEqual(client.get('/recommend', params={'title': title}).status_code, 200)
                self.assertEqual(client.get('/movies/reviews', params={'title': title}).status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
