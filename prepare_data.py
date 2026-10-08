"""영화 추천 원본 CSV 검사. 데이터 정리/삭제/병합은 수행하지 않습니다.

실행: python prepare_data.py --input Koreanmovie_review.csv
종료 코드: 0=검사 통과(경고 가능), 1=데이터 검사 실패, 2=입출력/구조 오류.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED = [
    'review_id', 'review', 'rating', 'MOVIE_NM', 'DRCTR_NM',
    'GENRE_NM', 'MOVIE_SDIV_NM', 'GRAD_NM', 'OPN_DE',
    'TOT_SCRN_CO', 'VIEWNG_NMPR_CO', 'bert_label',
    'pos_score', 'neg_score',
]
META = ['DRCTR_NM', 'GENRE_NM', 'MOVIE_SDIV_NM', 'GRAD_NM',
        'OPN_DE', 'TOT_SCRN_CO', 'VIEWNG_NMPR_CO']


def present(series):
    """NaN, 빈 문자열, 공백만 있는 값을 검사합니다. 원본은 변경하지 않습니다."""
    return series.notna() & series.astype('string').str.strip().ne('').fillna(False)


def samples(mask, limit=5):
    """검사 조건에 해당하는 원본 데이터 레코드 번호를 최대 limit개 반환합니다."""
    # CSV header is line 1, but quoted reviews can span multiple physical lines.
    # Report parsed data record numbers (1-based), not physical line numbers.
    return [int(i) + 1 for i in mask.index[mask][:limit]]


def normalize_title(value):
    """제목 변형 후보를 찾기 위한 비교 문자열을 만듭니다. 실제 영화명은 바꾸지 않습니다."""
    text = unicodedata.normalize('NFKC', str(value)).casefold()
    return ''.join(ch for ch in text if ch.isalnum())


def audit_frame(df):
    """DataFrame을 읽어 JSON으로 저장할 수 있는 검사 결과를 반환합니다."""
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError('필수 컬럼 누락: ' + ', '.join(missing))
    if df.empty:
        raise ValueError('데이터가 비어 있습니다.')

    warnings, errors = [], []
    report = {
        'rows': len(df), 'columns_count': len(df.columns),
        'columns': df.columns.tolist(),
        'missing': {c: int(df[c].isna().sum()) for c in df},
        'blank_strings': {
            c: int((df[c].notna() & ~present(df[c])).sum()) for c in df
        },
        'record_number_note': '예시 번호는 헤더를 제외한 1부터 시작하는 데이터 레코드 번호입니다.',
    }
    absent_counts = {c: int((~present(df[c])).sum()) for c in REQUIRED}
    if any(absent_counts.values()):
        warnings.append({'code': 'MISSING_VALUES', 'counts': absent_counts})

    numeric = {}
    for col in ['rating', 'bert_label', 'pos_score', 'neg_score',
                'TOT_SCRN_CO', 'VIEWNG_NMPR_CO']:
        valid_input = present(df[col])
        values = pd.to_numeric(df[col].where(valid_input), errors='coerce')
        bad_parse = valid_input & values.isna()
        bad_finite = values.notna() & ~np.isfinite(values)
        if bad_parse.any() or bad_finite.any():
            errors.append({'code': 'INVALID_NUMERIC', 'column': col,
                           'count': int((bad_parse | bad_finite).sum()),
                           'sample_records': samples(bad_parse | bad_finite)})
        numeric[col] = values.where(np.isfinite(values))
        values = numeric[col]
        if col == 'rating':
            invalid = values.notna() & (~values.between(0.5, 5) |
                        ~np.isclose(values * 2, np.round(values * 2), atol=1e-8, rtol=0))
        elif col == 'bert_label':
            invalid = values.notna() & ~values.isin([0, 1])
        elif col in ('pos_score', 'neg_score'):
            invalid = values.notna() & ~values.between(0, 1)
        else:
            invalid = values.notna() & (values < 0)
        if invalid.any():
            errors.append({'code': 'OUT_OF_DOMAIN', 'column': col,
                           'count': int(invalid.sum()), 'sample_records': samples(invalid)})

    rating = numeric['rating'].dropna()
    report['rating'] = {
        'valid_numeric_count': len(rating),
        'min': float(rating.min()) if len(rating) else None,
        'max': float(rating.max()) if len(rating) else None,
        'values': sorted(float(v) for v in rating.unique()),
    }
    titles = df['MOVIE_NM'].astype('string').str.strip().where(present(df['MOVIE_NM']))
    # A reporting-only view; original labels are preserved in df.
    genres = df['GENRE_NM'].astype('string').str.strip().where(present(df['GENRE_NM']), '(미상)')
    report['movies'] = {
        'raw_unique_names': int(df.MOVIE_NM.nunique()),
        'stripped_unique_names': int(titles.nunique()),
        'genre_movie_counts': {
            str(k): int(v) for k, v in pd.DataFrame({'title': titles, 'genre': genres})
            .groupby('genre')['title'].nunique().items()
        },
    }
    groups = {}
    for title in df.MOVIE_NM.dropna().unique():
        key = normalize_title(title)
        if key:
            groups.setdefault(key, set()).add(str(title))
    variants = [sorted(names) for names in groups.values() if len(names) > 1]
    report['possible_title_variants'] = sorted(variants)
    if variants:
        warnings.append({'code': 'TITLE_VARIANTS', 'group_count': len(variants),
                         'note': '후보 표시만 수행. 동일 작품 여부 확인 전 병합 금지.'})

    duplicate_all = int(df.duplicated().sum())
    duplicate_reviews = int(df.duplicated(['MOVIE_NM', 'review', 'rating']).sum())
    report['duplicates'] = {'all_columns_extra_rows': duplicate_all,
                            'movie_review_rating_extra_rows': duplicate_reviews}
    if duplicate_all or duplicate_reviews:
        warnings.append({'code': 'DUPLICATE_ROWS', **report['duplicates']})
    ids = df.loc[present(df.review_id), 'review_id']
    report['review_id'] = {'missing_or_blank': int((~present(df.review_id)).sum()),
                          'unique_nonmissing': int(ids.nunique()),
                          'duplicate_nonmissing_extra_rows': int(ids.duplicated().sum()),
                          'note': '리뷰 식별자이며 영화 식별자가 아닙니다.'}
    if ids.duplicated().any():
        warnings.append({'code': 'DUPLICATE_REVIEW_ID', 'count': int(ids.duplicated().sum())})

    conflicts = {}
    for col in META:
        view = pd.DataFrame({'title': titles, 'value': df[col].where(present(df[col]))})
        counts = view.groupby('title')['value'].nunique()
        bad = counts[counts > 1]
        conflicts[col] = {'movie_count': len(bad), 'sample_titles': bad.index[:10].tolist()}
    report['metadata_conflicts'] = conflicts
    if any(v['movie_count'] for v in conflicts.values()):
        warnings.append({'code': 'METADATA_CONFLICT', 'note': 'first 집계 전에 검토가 필요합니다.'})

    label, pos, neg = (numeric[c] for c in ['bert_label', 'pos_score', 'neg_score'])
    comparable = label.isin([0, 1]) & pos.between(0, 1) & neg.between(0, 1)
    mismatched = comparable & label.ne((pos > neg).astype(int))
    report['sentiment'] = {
        'label_values': sorted(float(v) for v in label.dropna().unique()),
        'comparable_rows': int(comparable.sum()),
        'pos_gt_neg_label_mismatches': int(mismatched.sum()),
        'equal_scores_rows': int((comparable & pos.eq(neg)).sum()),
        'note': '일치 여부는 일관성 검사이며 예측의 정확도 검증이 아닙니다. 동점도 별도 검토합니다.',
    }
    if mismatched.any():
        warnings.append({'code': 'SENTIMENT_MISMATCH', 'count': int(mismatched.sum())})
    report['status'] = 'fail' if errors else ('pass_with_warnings' if warnings else 'pass')
    report['errors'], report['warnings'] = errors, warnings
    return report


def main(argv=None):
    """터미널의 입력/출력 경로를 받아 검사 보고서를 쓰고 검사 상태의 종료 코드를 반환합니다."""
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=base / 'Koreanmovie_review.csv')
    parser.add_argument('--output', type=Path, default=base / 'artifacts' / 'data_audit.json')
    args = parser.parse_args(argv)
    src, dst = args.input.resolve(), args.output.resolve()
    try:
        if src == dst:
            raise ValueError('검사 보고서 경로는 원본 CSV와 달라야 합니다.')
        fingerprint = hashlib.sha256(src.read_bytes()).hexdigest()
        df = pd.read_csv(src, encoding='utf-8-sig', low_memory=False)
        report = audit_frame(df)
        if hashlib.sha256(src.read_bytes()).hexdigest() != fingerprint:
            raise ValueError('검사 중 입력 파일이 변경되었습니다. 다시 실행하세요.')
        report['source'] = {'path': str(src), 'sha256': fingerprint}
        report['generated_at_utc'] = datetime.now(timezone.utc).isoformat()
        report['environment'] = {'python': sys.version.split()[0],
                                 'pandas': pd.__version__, 'numpy': np.__version__}
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        print(f'[중단] {exc}', file=sys.stderr)
        return 2
    print(f"[검사] {report['status']}")
    print(f"행/열: {report['rows']:,} / {report['columns_count']}")
    print(f"영화명 수: {report['movies']['raw_unique_names']}")
    print(f"리뷰 결측: {report['missing']['review']} / 평점 결측: {report['missing']['rating']}")
    print(f"평점 범위: {report['rating']['min']} ~ {report['rating']['max']}")
    print('장르별 영화 수:', report['movies']['genre_movie_counts'])
    print('제목 변형 후보:', report['possible_title_variants'])
    print(f"경고 종류: {len(report['warnings'])} / 오류 종류: {len(report['errors'])}")
    for item in report['errors']:
        print('[오류]', item)
    print('보고서:', dst)
    print('원본 데이터는 삭제·수정·병합하지 않았습니다.')
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())

