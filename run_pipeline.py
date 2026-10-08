"""원본 검사 → 프로필 → TF-IDF/유사도 → 기능 검사 → 정상 버전 게시를 연결합니다."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
# uuid: 같은 시각에 실행하더라도 결과 폴더가 겹치지 않게 합니다.
import uuid
# os: 모든 검사가 끝난 뒤 CURRENT.json을 한 번에 교체합니다.
import os
# 버전 기록: 다른 PC에서 어떤 라이브러리로 준비했는지 비교할 수 있습니다.
import platform
from importlib.metadata import version

from build_profiles import build_profiles
from build_features import build_features
from data_store import RUNTIME_FILES, load_run
from evaluate import evaluate_run
from pipeline_common import (
    DEFAULT_SOURCE, DEFAULT_ARTIFACTS, SCHEMA_VERSION,
    file_sha256, write_json, validate_m,
)


def run_pipeline(input_path=DEFAULT_SOURCE, artifacts_dir=DEFAULT_ARTIFACTS, m=20.0, include_rating=True):
    """새 버전을 만들고 검사가 모두 통과한 경우에만 현재 버전을 바꿉니다.

    실패한 결과는 이전 정상 버전을 덮어쓰지 않습니다. 원본/기존 Ridge CSV도 변경하지 않습니다.
    """
    validate_m(m)
    input_path, artifacts_dir = Path(input_path).resolve(), Path(artifacts_dir).resolve()
    original_hash = file_sha256(input_path)
    now = datetime.now(timezone.utc)
    run_id = now.strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:8]
    directory = artifacts_dir / 'runs' / run_id
    directory.mkdir(parents=True, exist_ok=False)
    print('[1/4] 원본 검사와 영화별 프로필 집계')
    summary = build_profiles(input_path, directory, m)
    print('[2/4] 리뷰 TF-IDF와 영화 간 유사도 계산')
    information = build_features(directory, include_rating)
    manifest = {
        'schema_version': SCHEMA_VERSION, 'data_version': run_id,
        'generated_at_utc': now.isoformat(), 'source_sha256': original_hash,
        'movie_count': summary['movie_count'], 'review_rows': summary['review_rows'],
        'global_mean_rating': summary['global_mean_rating'], 'm': float(m),
        'include_rating_in_metadata': include_rating,
        'score_settings': {'meta_weight': 0.4, 'text_weight': 0.6, 'director_bonus': 0.05, 'similarity_weight': 0.7, 'rating_weight': 0.3, 'candidate_limit': 20},
        'versions': {'python': platform.python_version()}, 'files': {},
    }
    for package in ['numpy', 'pandas', 'scipy', 'scikit-learn', 'fastapi', 'uvicorn', 'httpx']:
        manifest['versions'][package] = version(package)
    for name in RUNTIME_FILES:
        manifest['files'][name] = file_sha256(directory / name)
    write_json(directory / 'manifest.json', manifest)
    print('[3/4] 저장 파일 연결, 전체 영화 추천/리뷰 정렬 검사')
    data = load_run(directory)
    report = evaluate_run(data)
    write_json(directory / 'evaluation.json', report)
    if file_sha256(input_path) != original_hash:
        raise ValueError('준비 중 원본 CSV가 변경됐습니다. 현재 버전은 바꾸지 않습니다.')
    pointer = {'data_version': run_id, 'run_directory': 'runs/' + run_id}
    pointer_temp = artifacts_dir / ('.CURRENT_' + run_id + '.tmp')
    write_json(pointer_temp, pointer)
    # os.replace: 정상 포인터를 원자적으로 교체해 읽는 쪽이 중간 상태를 보지 않게 합니다.
    os.replace(pointer_temp, artifacts_dir / 'CURRENT.json')
    print('[4/4] 정상 버전 게시 완료')
    print('영화:', summary['movie_count'], '/ 리뷰:', summary['review_rows'], '/ TF-IDF:', information['matrix_shape'])
    print('결과 폴더:', directory)
    return directory


def main():
    """터미널에서 원본/저장 폴더/보정 강도를 받아 전체 데이터 준비를 실행합니다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--artifacts-dir', type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument('--m', type=float, default=20.0)
    parser.add_argument('--exclude-rating', action='store_true')
    args = parser.parse_args()
    try:
        run_pipeline(args.input, args.artifacts_dir, args.m, not args.exclude_rating)
    except (ValueError, OSError, AssertionError) as exc:
        parser.exit(1, f'중단: {exc}\n')


if __name__ == '__main__':
    main()
