"""저장된 버전의 프로필·리뷰·유사도를 한 번 읽어 검색/추천에 연결합니다."""

from pathlib import Path
import math

# numpy/pandas: 준비 단계에서 저장한 숫자 배열과 CSV 표를 다시 읽습니다.
import numpy as np
import pandas as pd

from build_profiles import PROFILE_FILES
from pipeline_common import (
    DEFAULT_ARTIFACTS, SCHEMA_VERSION, read_json, check_file_hashes,
)

RUNTIME_FILES = PROFILE_FILES + [
    'profile_manifest.json', 'similarities.npz', 'review_tfidf.npz',
    'tfidf_info.json', 'feature_manifest.json',
]
PROFILE_NUMBERS = [
    'TOT_SCRN_CO', 'VIEWNG_NMPR_CO', 'review_count', 'rating_count',
    'mean_rating', 'positive_ratio', 'corrected_rating', 'rating_quality',
]


def load_run(directory):
    """하나의 버전 폴더를 읽습니다. 파일 해시/ID 순서/행렬 크기를 확인하고 반환합니다.

    모델이나 TF-IDF를 fit하지 않습니다. 반환값은 여러 함수가 공유하는 딕셔너리입니다.
    """
    directory = Path(directory)
    manifest = read_json(directory / 'manifest.json')
    if manifest.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('지원하지 않는 데이터 파일 형식입니다. 파이프라인을 다시 실행하세요.')
    if set(manifest.get('files', {})) != set(RUNTIME_FILES):
        raise ValueError('데이터 버전의 필수 파일 목록이 다릅니다.')
    check_file_hashes(directory, manifest['files'])
    profiles = pd.read_csv(directory / 'movie_profiles.csv', encoding='utf-8-sig', keep_default_na=False)
    reviews = pd.read_csv(directory / 'reviews.csv', encoding='utf-8-sig', keep_default_na=False, dtype={'review_id': str})
    for column in PROFILE_NUMBERS:
        profiles[column] = pd.to_numeric(profiles[column], errors='coerce')
    for column in ['rating', 'bert_label', 'source_record']:
        reviews[column] = pd.to_numeric(reviews[column], errors='coerce')
    if profiles.empty or not profiles['movie_id'].is_unique:
        raise ValueError('프로필이 비어 있거나 ID가 중복됐습니다.')
    if len(profiles) != manifest['movie_count'] or len(reviews) != manifest['review_rows']:
        raise ValueError('저장된 행 수와 버전 정보가 다릅니다.')
    if not set(reviews['movie_id']).issubset(set(profiles['movie_id'])):
        raise ValueError('프로필에 없는 영화의 리뷰가 있습니다.')
    if reviews['source_record'].isna().any() or not reviews['source_record'].is_unique:
        raise ValueError('리뷰 원본 레코드 번호가 비정상입니다.')
    if reviews['review'].str.strip().eq('').any():
        raise ValueError('빈 리뷰가 저장돼 있습니다.')
    for column in ['review_count', 'rating_count', 'corrected_rating', 'rating_quality']:
        values = profiles[column].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f'프로필의 {column}에 비정상 숫자가 있습니다.')
    if not profiles['rating_quality'].between(0, 1).all():
        raise ValueError('보정 평점의 정규화 값이 0~1 범위를 벗어났습니다.')
    with np.load(directory / 'similarities.npz', allow_pickle=False) as saved:
        ids = saved['movie_ids'].tolist()
        if ids != profiles['movie_id'].tolist():
            raise ValueError('프로필 행과 유사도 행의 영화 ID 순서가 다릅니다.')
        matrices = {}
        for name in ['text', 'categories', 'numbers', 'metadata']:
            matrix = saved[name].copy()
            if matrix.shape != (len(profiles), len(profiles)):
                raise ValueError(f'{name} 유사도 크기가 영화 수와 다릅니다.')
            if not np.isfinite(matrix).all() or not np.allclose(matrix, matrix.T):
                raise ValueError(f'{name} 유사도가 유한한 대칭 행렬이 아닙니다.')
            if (matrix < 0).any() or (matrix > 1).any():
                raise ValueError(f'{name} 유사도가 0~1 범위를 벗어났습니다.')
            matrices[name] = matrix
    id_to_index = {}
    for index, movie_id in enumerate(profiles['movie_id']):
        id_to_index[movie_id] = index
    return {
        'profiles': profiles, 'reviews': reviews, 'matrices': matrices,
        'manifest': manifest, 'id_to_index': id_to_index, 'directory': directory,
    }


def load_data(artifacts_dir=DEFAULT_ARTIFACTS):
    """CURRENT.json이 가리키는 마지막 정상 버전을 읽습니다."""
    artifacts_dir = Path(artifacts_dir).resolve()
    pointer_path = artifacts_dir / 'CURRENT.json'
    if not pointer_path.is_file():
        raise FileNotFoundError('추천 데이터가 없습니다. 먼저 python run_pipeline.py를 실행하세요.')
    pointer = read_json(pointer_path)
    directory = (artifacts_dir / pointer['run_directory']).resolve()
    if not directory.is_relative_to(artifacts_dir / 'runs'):
        raise ValueError('데이터 버전 경로가 runs 폴더를 벗어났습니다.')
    data = load_run(directory)
    if data['manifest']['data_version'] != pointer['data_version']:
        raise ValueError('현재 버전 정보와 실제 데이터 버전이 다릅니다.')
    return data


def get_movie_index(data, movie_id):
    """내부 영화 ID에 해당하는 행 번호를 반환합니다. 미등록 ID는 KeyError입니다."""
    if movie_id not in data['id_to_index']:
        raise KeyError('영화 ID를 찾을 수 없습니다.')
    return data['id_to_index'][movie_id]


def optional_text(value):
    """빈 문자열/결측은 None, 실제 문자열은 str로 바꿔 JSON에 넣습니다."""
    if pd.isna(value) or str(value).strip() == '':
        return None
    return str(value)


def optional_number(value):
    """결측 숫자는 None으로 바꿉니다. 유효한 숫자 0은 그대로 보존합니다."""
    if pd.isna(value):
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('유한하지 않은 숫자가 결과에 포함됐습니다.')
    return number


def movie_to_dict(row):
    """프로필의 한 행을 검색/API에서 보여줄 일반 딕셔너리로 변환합니다."""
    return {
        'movie_id': str(row['movie_id']), 'title': str(row['title']),
        'genre': optional_text(row['GENRE_NM']), 'director': optional_text(row['DRCTR_NM']),
        'release_date': optional_text(row['OPN_DE']), 'age_rating': optional_text(row['GRAD_NM']),
        'mean_rating': optional_number(row['mean_rating']),
        'review_count': int(row['review_count']), 'rating_count': int(row['rating_count']),
        'positive_ratio': optional_number(row['positive_ratio']),
        'corrected_rating': float(row['corrected_rating']),
    }


def get_movie(data, movie_id):
    """영화 ID 하나의 메타데이터를 반환합니다. 전체 리뷰 텍스트는 노출하지 않습니다."""
    index = get_movie_index(data, movie_id)
    return movie_to_dict(data['profiles'].iloc[index])


def search_movies(data, query='', limit=20):
    """제목의 일부로 검색합니다. 정규식이 아니라 입력한 글자 자체를 찾습니다."""
    if not isinstance(query, str) or len(query) > 200:
        raise ValueError('검색어는 200자 이하의 문자열이어야 합니다.')
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError('검색 개수는 1~100 사이의 정수여야 합니다.')
    query = query.strip().casefold()
    profiles = data['profiles']
    mask = profiles['title'].str.casefold().str.contains(query, regex=False, na=False)
    found = profiles.loc[mask].sort_values(['title', 'movie_id'], kind='stable').head(limit)
    results = []
    for _, row in found.iterrows():
        results.append(movie_to_dict(row))
    return results


def find_movies_by_title(data, title, release_date=None, director=None):
    """정확한 제목으로 작품 후보를 반환합니다. 동명이작은 날짜/감독으로 좁힐 수 있습니다.

    제목의 양 끝 공백과 대소문자는 무시합니다. 문장부호는 자동으로 제거하지 않습니다.
    release_date는 프로필의 YYYYMMDD 표기이며 후보가 없으면 빈 목록입니다.
    """
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValueError('제목은 비어 있지 않은 200자 이하의 문자열이어야 합니다.')
    profiles = data['profiles']
    mask = profiles['title'].str.casefold().eq(title.strip().casefold())
    if release_date is not None:
        if not isinstance(release_date, str) or not release_date.strip():
            raise ValueError('개봉일은 YYYYMMDD 형식의 문자열이어야 합니다.')
        mask = mask & profiles['OPN_DE'].astype(str).eq(release_date.strip())
    if director is not None:
        if not isinstance(director, str) or not director.strip() or len(director) > 200:
            raise ValueError('감독은 비어 있지 않은 200자 이하의 문자열이어야 합니다.')
        directors = profiles['DRCTR_NM'].fillna('').astype(str).str.casefold()
        mask = mask & directors.eq(director.strip().casefold())
    matched = profiles.loc[mask].sort_values(['title', 'movie_id'], kind='stable')
    results = []
    for _, row in matched.iterrows():
        results.append(movie_to_dict(row))
    return results


def resolve_movie_id(data, movie_id=None, title=None):
    """CLI의 ID 또는 정확한 제목을 실제 영화 ID로 변환합니다."""
    if movie_id is not None:
        get_movie_index(data, movie_id)
        return movie_id
    matched = find_movies_by_title(data, title)
    if len(matched) != 1:
        raise ValueError('정확한 제목이 없거나 여러 작품입니다. 검색한 movie_id를 사용하세요.')
    return matched[0]['movie_id']
