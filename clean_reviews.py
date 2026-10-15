"""원본 리뷰 CSV를 정제해 Koreanmovie_review_cleaned.csv를 만듭니다.

원본에는 따옴표/꺾쇠 안의 글자(영화 제목 등)가 지워진 리뷰가 섞여 있습니다.
- 공백만 남은 경우("천사는 바이러스 는")는 조사를 앞말에 붙여 복구합니다.
- 글자가 통째로 사라진 경우("영화 제목은 이지만", 문장이 조사로 시작)는 제외합니다.
- 빈 리뷰, 너무 짧은 리뷰, 평점 없는 리뷰도 제외합니다.
제외된 행은 Koreanmovie_review_removed.csv에 사유와 함께 저장합니다.
표준 라이브러리만 사용하므로 가상환경 없이 실행됩니다.
"""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

MIN_LENGTH = 10
PARTICLES = '은|는|을|를|과|의'
# 앞말과 떨어져 홀로 남은 조사: "화란 과 화란" -> "화란과 화란"
DETACHED = re.compile(rf'(?<=[0-9A-Za-z가-힣])\s+({PARTICLES})(?=\s|$|[,.!?])')
# 문장 맨 앞/문장부호 뒤에서 조사가 시작되면 앞의 글자가 지워진 것
ORPHAN = re.compile(rf'(?:^|[.!?]\s+)({PARTICLES}|이지만|이라는|이라고)(?=\s|$|[,.!?])')
# 앞말에 이미 붙은 '제목은 이지만'처럼 서술어 앞이 비어 있는 경우
GAP = re.compile(r'(?:은|는)\s+(?:이지만|이라는|이라고)\b')


def clean_text(text):
    """공백을 정리하고 떨어진 조사를 앞말에 붙입니다."""
    text = re.sub(r'\s+', ' ', text).strip()
    return DETACHED.sub(r'\1', text)


def removal_reason(raw_text, text, rating):
    """제외 사유를 반환합니다. 남겨도 되면 None."""
    if not text:
        return '빈 리뷰'
    if len(text) < MIN_LENGTH:
        return f'너무 짧음(<{MIN_LENGTH}자)'
    if rating == '':
        return '평점 없음'
    if ORPHAN.search(raw_text.strip()) or GAP.search(raw_text):
        return '글자 누락 의심'
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('Koreanmovie_review.csv'))
    parser.add_argument('--output', type=Path, default=Path('Koreanmovie_review_cleaned.csv'))
    parser.add_argument('--removed', type=Path, default=Path('Koreanmovie_review_removed.csv'))
    args = parser.parse_args()

    with open(args.input, encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)

    kept, removed, reasons = [], [], Counter()
    for row in rows:
        raw_text = row['review']
        text = clean_text(raw_text)
        reason = removal_reason(raw_text, text, row['rating'].strip())
        if reason:
            reasons[reason] += 1
            removed.append({**row, 'remove_reason': reason})
        else:
            kept.append({**row, 'review': text})

    with open(args.output, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(kept)
    with open(args.removed, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields + ['remove_reason'])
        writer.writeheader()
        writer.writerows(removed)

    print(f'원본 {len(rows)}건 -> 정제 {len(kept)}건 / 제외 {len(removed)}건')
    for reason, count in reasons.most_common():
        print(f'  제외 사유 - {reason}: {count}건')


if __name__ == '__main__':
    main()
