"""원본 CSV를 검사하고 영화별 프로필과 리뷰 표를 만듭니다.

실행: python build_profiles.py
권장: python run_pipeline.py (모든 준비 단계를 연결해서 실행)
"""

# argparse: 터미널에서 --input, --output-dir 같은 선택 값을 받습니다.
import argparse
import hashlib
import json
from pathlib import Path

# pandas: CSV를 표로 읽고 결측 검사, 중복 제거, 영화별 집계를 수행합니다.
import pandas as pd

from prepare_data import audit_frame, META
from pipeline_common import (
    DEFAULT_SOURCE, DEFAULT_ARTIFACTS, SCHEMA_VERSION,
    file_sha256, write_json, validate_m, protect_input,
)

PROFILE_FILES = ['movie_profiles.csv', 'reviews.csv', 'data_audit.json']


def clean_review_rows(data):
    """원본 표의 복사본에서 빈 제목/리뷰와 영화·리뷰·평점 중복을 제거합니다.

    평점이 없는 리뷰는 텍스트 정보이므로 보존합니다. 원본 DataFrame은 바꾸지 않습니다.
    source_record는 CSV 헤더를 제외한 원본 데이터 레코드 번호입니다.
    """
    clean = data.copy()
    clean['source_record'] = range(1, len(clean) + 1)
    for column in ['MOVIE_NM', 'review']:
        clean[column] = clean[column].fillna('').astype(str).str.strip()
    clean = clean.loc[clean['MOVIE_NM'].ne('') & clean['review'].ne('')].copy()
    for column in ['rating', 'bert_label', 'pos_score', 'neg_score', 'TOT_SCRN_CO', 'VIEWNG_NMPR_CO']:
        clean[column] = pd.to_numeric(clean[column], errors='coerce')
    clean = clean.drop_duplicates(subset=['MOVIE_NM', 'review', 'rating'])
    return clean.reset_index(drop=True)


def get_metadata_value(movie_rows, column):
    """한 영화의 유효 메타데이터를 가져옵니다. 서로 다른 값이 둘 이상이면 중단합니다.

    first()로 충돌을 숨기지 않기 위해 먼저 유효값의 종류를 확인합니다.
    """
    values = movie_rows[column].dropna()
    if column in ['TOT_SCRN_CO', 'VIEWNG_NMPR_CO']:
        values = pd.to_numeric(values, errors='coerce').dropna()
        unique_values = values.drop_duplicates().tolist()
        if len(unique_values) > 1:
            raise ValueError(f'같은 영화의 {column} 값이 서로 다릅니다.')
        return float(unique_values[0]) if unique_values else None

    values = values.astype(str).str.strip()
    values = values.loc[values.ne('')]
    if column == 'OPN_DE':
        # 20250101과 20250101.0은 같은 개봉일 표기로 처리합니다.
        dates = []
        for value in values:
            number = float(value)
            if not number.is_integer():
                raise ValueError('개봉일은 YYYYMMDD 형식이어야 합니다.')
            date_text = str(int(number))
            pd.to_datetime(date_text, format='%Y%m%d', errors='raise')
            dates.append(date_text)
        unique_values = sorted(set(dates))
    else:
        unique_values = values.drop_duplicates().tolist()
    if len(unique_values) > 1:
        title = str(movie_rows['MOVIE_NM'].iloc[0])
        raise ValueError(f'영화 {title!r}의 {column} 값이 충돌합니다. 먼저 작품을 구분하세요.')
    return unique_values[0] if unique_values else None


def make_movie_id(title, release_date):
    """제목+개봉일로 재실행해도 같은 내부 ID를 만듭니다. 공식 영화 ID는 아닙니다.

    쉼표/문장부호가 다른 제목은 자동으로 합치지 않습니다.
    """
    key = json.dumps([title, release_date], ensure_ascii=False)
    return 'movie_' + hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]


def create_profiles(data, m=20.0):
    """검사를 통과한 원본 표를 프로필, 리뷰 표, 집계 보고서로 바꿉니다.

    n=보존 리뷰 행 수, v=유효 평점 수, R=평균 평점, B=보정 평점입니다.
    반환값은 (프로필 DataFrame, 리뷰 DataFrame, 보고서 딕셔너리)입니다.
    """
    validate_m(m)
    audit = audit_frame(data)
    if audit['errors']:
        raise ValueError('원본 검사 실패: ' + json.dumps(audit['errors'], ensure_ascii=False))
    clean = clean_review_rows(data)
    if clean.empty or clean['rating'].count() == 0:
        raise ValueError('유효한 리뷰와 평점이 있어야 영화 프로필을 만들 수 있습니다.')
    global_mean = float(clean['rating'].mean())

    metadata_source = data.copy()
    metadata_source['MOVIE_NM'] = metadata_source['MOVIE_NM'].fillna('').astype(str).str.strip()
    groups = clean.groupby('MOVIE_NM', sort=True)
    metadata_groups = metadata_source.groupby('MOVIE_NM', sort=True)
    profiles = []
    title_to_id = {}
    for title, movie_rows in groups:
        # 리뷰가 없는 행에 기록된 메타데이터도 검사 대상으로 사용합니다.
        original_movie_rows = metadata_groups.get_group(title)
        profile = {'title': title}
        for column in META:
            profile[column] = get_metadata_value(original_movie_rows, column)
        movie_id = make_movie_id(title, profile['OPN_DE'])
        title_to_id[title] = movie_id
        profile['movie_id'] = movie_id
        profile['review_count'] = int(len(movie_rows))
        profile['rating_count'] = int(movie_rows['rating'].count())
        count = profile['rating_count']
        mean = float(movie_rows['rating'].mean()) if count else None
        profile['mean_rating'] = mean
        labels = movie_rows['bert_label'].dropna()
        profile['positive_ratio'] = float(labels.mean()) if len(labels) else None
        # 결측 평균에 0을 넣지 않고 전체 평균을 사용합니다.
        usable_mean = mean if mean is not None else global_mean
        corrected = (count * usable_mean + m * global_mean) / (count + m)
        profile['corrected_rating'] = float(corrected)
        profile['rating_quality'] = float((corrected - 0.5) / 4.5)
        # 같은 문구는 텍스트에 한 번만 넣어 반복 가중치를 줄입니다.
        profile['review_text'] = ' '.join(movie_rows['review'].drop_duplicates().tolist())
        profiles.append(profile)

    profiles = pd.DataFrame(profiles)
    profiles = profiles.sort_values(['title', 'movie_id'], kind='stable').reset_index(drop=True)
    if not profiles['movie_id'].is_unique:
        raise ValueError('내부 영화 ID가 중복됐습니다.')
    clean['movie_id'] = clean['MOVIE_NM'].map(title_to_id)
    reviews = clean[['movie_id', 'review_id', 'source_record', 'MOVIE_NM', 'review', 'rating', 'bert_label']].copy()
    reviews = reviews.rename(columns={'MOVIE_NM': 'title'})
    excluded_titles = sorted(set(metadata_source['MOVIE_NM']) - set(title_to_id) - {''})
    summary = {
        'input_rows': len(data), 'review_rows': len(reviews), 'movie_count': len(profiles),
        'removed_rows': len(data) - len(reviews), 'excluded_titles': excluded_titles,
        'reviews_without_rating': int(reviews['rating'].isna().sum()),
        'unknown_genre_titles': profiles.loc[profiles['GENRE_NM'].isna(), 'title'].tolist(),
        'global_mean_rating': global_mean, 'm': float(m),
        'identity_rule': 'strip한 원문 제목 + 개봉일. 제목 문장부호는 보존.',
        'duplicate_rule': 'MOVIE_NM + strip한 review + 실제 rating',
        'audit': audit,
    }
    return profiles, reviews, summary


def build_profiles(input_path=DEFAULT_SOURCE, output_dir=DEFAULT_ARTIFACTS / 'standalone', m=20.0):
    """CSV를 읽어 프로필/리뷰/검사 보고서/해시 목록을 지정 폴더에 저장합니다."""
    input_path, output_dir = Path(input_path), Path(output_dir)
    protect_input(input_path, output_dir, PROFILE_FILES + ['profile_manifest.json'])
    fingerprint = file_sha256(input_path)
    # 식별자는 계산용 숫자가 아니므로 앞의 0을 잃지 않게 문자열로 읽습니다.
    data = pd.read_csv(input_path, encoding='utf-8-sig', low_memory=False, dtype={'review_id': 'string'})
    profiles, reviews, summary = create_profiles(data, m)
    if file_sha256(input_path) != fingerprint:
        raise ValueError('집계 중 원본 CSV가 변경됐습니다. 다시 실행하세요.')
    output_dir.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(output_dir / 'movie_profiles.csv', index=False, encoding='utf-8-sig')
    reviews.to_csv(output_dir / 'reviews.csv', index=False, encoding='utf-8-sig')
    audit = summary.pop('audit')
    write_json(output_dir / 'data_audit.json', audit)
    summary['schema_version'] = SCHEMA_VERSION
    summary['source_sha256'] = fingerprint
    summary['files'] = {}
    for name in PROFILE_FILES:
        summary['files'][name] = file_sha256(output_dir / name)
    write_json(output_dir / 'profile_manifest.json', summary)
    return summary


def main():
    """터미널 옵션을 읽고 영화별 집계를 실행합니다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_ARTIFACTS / 'standalone')
    parser.add_argument('--m', type=float, default=20.0)
    args = parser.parse_args()
    summary = build_profiles(args.input, args.output_dir, args.m)
    print('보존 리뷰:', summary['review_rows'], '/ 영화:', summary['movie_count'])
    print('평점 없는 리뷰 보존:', summary['reviews_without_rating'])
    print('저장 폴더:', args.output_dir)


if __name__ == '__main__':
    main()
