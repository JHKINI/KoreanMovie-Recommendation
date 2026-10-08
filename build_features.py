"""프로필에서 메타데이터·리뷰 TF-IDF와 영화 간 유사도를 계산해 저장합니다."""

import argparse
from pathlib import Path

# numpy: 영화끼리의 유사도를 2차원 숫자 배열로 계산하고 저장합니다.
import numpy as np
# pandas: 저장된 프로필을 읽고 숫자 컬럼의 결측값/범위를 처리합니다.
import pandas as pd
# scipy: 대부분이 0인 TF-IDF 행렬을 희소 형식 그대로 저장합니다.
from scipy.sparse import save_npz
# scikit-learn: 검증된 TF-IDF 구현과 코사인 유사도 함수를 사용합니다.
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from pipeline_common import (
    DEFAULT_ARTIFACTS, SCHEMA_VERSION, read_json, write_json,
    file_sha256, check_file_hashes,
)

FEATURE_FILES = ['similarities.npz', 'review_tfidf.npz', 'tfidf_info.json']
NUMERIC_COLUMNS = ['TOT_SCRN_CO', 'VIEWNG_NMPR_CO', 'mean_rating', 'positive_ratio']


def category_similarity(profiles):
    """상영구분/관람등급이 일치하는 비율을 계산합니다. 결측끼리는 일치가 아닙니다."""
    records = profiles.to_dict('records')
    count = len(records)
    result = np.zeros((count, count), dtype=float)
    for i in range(count):
        for j in range(count):
            matches = 0
            for column in ['MOVIE_SDIV_NM', 'GRAD_NM']:
                left, right = records[i][column], records[j][column]
                if pd.notna(left) and pd.notna(right) and str(left) != '' and left == right:
                    matches += 1
            result[i, j] = matches / 2.0
    return result


def numeric_similarity(profiles, include_rating=True):
    """수치 속성을 정규화한 뒤 1-평균 절대 차이로 유사도를 계산합니다.

    관객/스크린에는 log1p를 적용합니다. 결측은 중앙값으로 보완하고,
    전체가 결측인 컬럼은 제외합니다. 반환: (유사도 배열, 전처리 설명).
    """
    columns = NUMERIC_COLUMNS.copy()
    if not include_rating:
        columns.remove('mean_rating')
    normalized_columns = []
    settings = {}
    skipped_columns = []
    for column in columns:
        values = pd.to_numeric(profiles[column], errors='coerce').astype(float)
        if values.notna().sum() == 0:
            skipped_columns.append(column)
            continue
        use_log = column in ['TOT_SCRN_CO', 'VIEWNG_NMPR_CO']
        if use_log:
            values = np.log1p(values)
        median = float(values.median())
        values = values.fillna(median)
        minimum, maximum = float(values.min()), float(values.max())
        span = maximum - minimum
        if span == 0:
            normalized = np.zeros(len(values), dtype=float)
        else:
            normalized = ((values - minimum) / span).to_numpy()
        normalized_columns.append(normalized)
        settings[column] = {'log1p': use_log, 'median_after_log': median, 'min': minimum, 'max': maximum}

    count = len(profiles)
    result = np.zeros((count, count), dtype=float)
    if normalized_columns:
        numbers = np.column_stack(normalized_columns)
        for i in range(count):
            for j in range(count):
                difference = np.abs(numbers[i] - numbers[j]).mean()
                result[i, j] = 1.0 - float(difference)
    information = {'columns': settings, 'excluded_all_missing': skipped_columns, 'include_rating': include_rating}
    return np.clip(result, 0.0, 1.0), information


def create_features(profiles, include_rating=True):
    """프로필 행 순서를 유지하며 희소 TF-IDF, 유사도 배열, 전처리 설명을 반환합니다."""
    if profiles.empty or not profiles['movie_id'].is_unique:
        raise ValueError('프로필이 비어 있거나 movie_id가 중복됐습니다.')
    # 문자 2~3그램: 별도 한국어 형태소 분석기 없이 짧은 글자 조합을 특징으로 씁니다.
    vectorizer = TfidfVectorizer(
        analyzer='char', ngram_range=(2, 3), min_df=2, max_features=5000,
        sublinear_tf=True, smooth_idf=True, norm='l2', dtype=np.float64,
    )
    try:
        tfidf = vectorizer.fit_transform(profiles['review_text'].fillna('').tolist())
    except ValueError as exc:
        raise ValueError('TF-IDF 특징을 만들 수 없습니다. 두 영화 이상에 나타나는 2~3글자 리뷰 특징이 필요합니다.') from exc
    # 희소 TF-IDF 전체를 toarray()로 바꾸지 않습니다. 영화 수 × 영화 수 배열만 만듭니다.
    text = np.clip(cosine_similarity(tfidf), 0.0, 1.0)
    categories = category_similarity(profiles)
    numbers, number_settings = numeric_similarity(profiles, include_rating)
    metadata = 0.5 * categories + 0.5 * numbers
    matrices = {'text': text, 'categories': categories, 'numbers': numbers, 'metadata': metadata}
    for name, matrix in matrices.items():
        if not np.isfinite(matrix).all() or not np.allclose(matrix, matrix.T):
            raise ValueError(f'{name} 유사도에 비정상 값이 있습니다.')
    information = {
        'implementation': 'scikit-learn TfidfVectorizer; 이전 NumPy 참조 구현과 결과가 완전히 같을 필요는 없음',
        'analyzer': 'char', 'ngram_range': [2, 3], 'min_df': 2, 'max_features': 5000,
        'sublinear_tf': True, 'smooth_idf': True, 'norm': 'l2',
        'feature_count': int(tfidf.shape[1]), 'matrix_shape': list(tfidf.shape),
        'empty_feature_movie_ids': profiles.loc[np.asarray(tfidf.getnnz(axis=1)) == 0, 'movie_id'].tolist(),
        'vocabulary': {word: int(index) for word, index in vectorizer.vocabulary_.items()},
        'idf': vectorizer.idf_.tolist(), 'numeric_preprocessing': number_settings,
        'category_missing_rule': '미상끼리는 일치 점수를 주지 않음',
    }
    return tfidf, matrices, information


def build_features(directory=DEFAULT_ARTIFACTS / 'standalone', include_rating=True):
    """집계 파일을 검증하고 특징/유사도 파일을 같은 버전 폴더에 저장합니다."""
    directory = Path(directory)
    profile_manifest = read_json(directory / 'profile_manifest.json')
    check_file_hashes(directory, profile_manifest['files'])
    profiles = pd.read_csv(directory / 'movie_profiles.csv', encoding='utf-8-sig', keep_default_na=False)
    # 빈 메타데이터는 결측으로 표시하되 영화 제목의 'NA' 같은 실제 글자는 보존합니다.
    for column in ['MOVIE_SDIV_NM', 'GRAD_NM']:
        profiles[column] = profiles[column].replace('', pd.NA)
    tfidf, matrices, information = create_features(profiles, include_rating)
    np.savez_compressed(directory / 'similarities.npz', movie_ids=profiles['movie_id'].to_numpy(dtype=str), **matrices)
    save_npz(directory / 'review_tfidf.npz', tfidf)
    write_json(directory / 'tfidf_info.json', information)
    manifest = {'schema_version': SCHEMA_VERSION, 'profile_manifest_sha256': file_sha256(directory / 'profile_manifest.json'), 'files': {}}
    for name in FEATURE_FILES:
        manifest['files'][name] = file_sha256(directory / name)
    write_json(directory / 'feature_manifest.json', manifest)
    return information


def main():
    """터미널에서 프로필 폴더와 평점 속성 포함 여부를 받아 특징을 준비합니다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=DEFAULT_ARTIFACTS / 'standalone')
    parser.add_argument('--exclude-rating', action='store_true')
    args = parser.parse_args()
    information = build_features(args.directory, not args.exclude_rating)
    print('TF-IDF 행렬 크기:', information['matrix_shape'])
    print('유사도 저장 폴더:', args.directory)


if __name__ == '__main__':
    main()
