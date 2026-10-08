"""파일 경로, JSON 저장, 파일 검사처럼 여러 단계가 함께 사용하는 함수입니다."""

# pathlib: 문자열을 직접 붙이지 않고 Windows 파일 경로를 안전하게 다룹니다.
from pathlib import Path
# json: 설정과 검사 결과를 사람이 읽을 수 있는 파일로 저장합니다.
import json
# hashlib: 파일 내용의 지문(SHA-256)을 만들어 다른 버전이 섞였는지 확인합니다.
import hashlib
# math: NaN과 무한대처럼 JSON이나 추천 점수에 넣으면 안 되는 수를 확인합니다.
import math

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = PROJECT_DIR / 'Koreanmovie_review.csv'
DEFAULT_ARTIFACTS = PROJECT_DIR / 'artifacts' / 'recommendation'
SCHEMA_VERSION = 1


def file_sha256(path):
    """입력: 파일 경로. 반환: 파일 내용의 SHA-256 문자열. 원본은 읽기만 합니다."""
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        while True:
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, data):
    """딕셔너리/리스트를 UTF-8 JSON으로 저장합니다. NaN은 저장을 거부합니다."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)
    path.write_text(text, encoding='utf-8')


def read_json(path):
    """UTF-8 JSON 파일을 읽어 딕셔너리/리스트로 돌려줍니다."""
    return json.loads(Path(path).read_text(encoding='utf-8'))


def validate_top_n(top_n):
    """요청 개수가 1~20의 정수인지 검사합니다. bool은 정수로 인정하지 않습니다."""
    if isinstance(top_n, bool) or not isinstance(top_n, int) or not 1 <= top_n <= 20:
        raise ValueError('top_n은 1~20 사이의 정수여야 합니다.')


def validate_m(m):
    """보정 강도 m이 0보다 큰 유한한 수인지 검사합니다."""
    if isinstance(m, bool) or not isinstance(m, (int, float)) or not math.isfinite(m) or m <= 0:
        raise ValueError('m은 0보다 큰 유한한 수여야 합니다.')


def check_file_hashes(directory, expected):
    """파일별 해시 딕셔너리와 실제 파일을 비교해 손상/버전 혼합을 검사합니다."""
    directory = Path(directory)
    for name, fingerprint in expected.items():
        # 여기서는 프로그램이 정한 파일 이름만 사용합니다.
        path = directory / name
        if not path.is_file() or file_sha256(path) != fingerprint:
            raise ValueError(f'파일이 없거나 내용이 다른 버전입니다: {name}')


def protect_input(source, output_dir, names):
    """출력 파일 목록 중 입력 원본과 같은 경로가 있으면 저장 전에 중단합니다."""
    source = Path(source).resolve()
    for name in names:
        if source == (Path(output_dir) / name).resolve():
            raise ValueError('출력 파일이 입력 원본과 같은 경로입니다.')
