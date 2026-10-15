"""추천 설정을 바꿔 가며 214편 전체의 추천 목록을 비교하는 보고서를 만듭니다.

이 보고서는 추천이 어떤 성질을 가지는지(안정성, 인기 쏠림, 다양성, 커버리지)를 수치로 보여줄 뿐
사용자 만족도를 측정하지 않습니다. 만족도는 --sheet로 만든 블라인드 시트를 사람이 채워서 확인합니다.
TF-IDF를 다시 계산하지 않고 저장된 유사도 행렬만 사용하므로 몇 초 안에 끝납니다.

  python evaluate_quality.py                       보고서(JSON)와 표 출력
  python evaluate_quality.py --sheet 20            사람 평가용 블라인드 시트 20개 생성
  python evaluate_quality.py --score 채운시트.csv   채운 시트의 선호 집계
"""

import argparse
import csv
import random
from collections import Counter
from pathlib import Path

import numpy as np

from data_store import load_data, optional_text
from pipeline_common import DEFAULT_ARTIFACTS, PROJECT_DIR, write_json

TOP_N = 5
DEFAULT_KEY_DIR = PROJECT_DIR / 'artifacts' / 'human_eval'
CURRENT = {'meta_w': 0.4, 'text_w': 0.6, 'bonus': 0.05, 'sim_w': 0.7, 'quality_w': 0.3, 'shortlist': 20, 'meta_key': 'meta', 'hub_w': 0.0}

# 이름 -> (설명, 현재 설정에서 바꿀 값). baseline_rating/random_same_genre는 별도 방식입니다.
CONFIGS = {
    'current': ('현재 설정 (정보 0.4 + 리뷰 0.6, 유사도 0.7 + 평점 0.3)', {}),
    'text_only': ('리뷰 유사도만 사용', {'meta_w': 0.0, 'text_w': 1.0}),
    'meta_only': ('정보(메타데이터) 유사도만 사용', {'meta_w': 1.0, 'text_w': 0.0}),
    'no_quality': ('평점 반영 없이 유사도만으로 정렬', {'sim_w': 1.0, 'quality_w': 0.0}),
    'quality_heavy': ('평점 비중을 0.6으로 올림 (유사도 0.4)', {'sim_w': 0.4, 'quality_w': 0.6}),
    'no_director_bonus': ('같은 감독 보너스 제거', {'bonus': 0.0}),
    'metadata_without_rating': ('메타 유사도에서 평점 속성을 뺌 (평점 이중 반영 제거)', {'meta_key': 'meta_alt'}),
    'hub_corrected': ('쏠림 보정 실험: 다른 영화들과 평균적으로 유난히 비슷한 영화의 유사도를 낮춤 (강도 0.5)', {'hub_w': 0.5}),
    'baseline_rating': ('기준선: 같은 장르에서 보정 평점이 높은 순', None),
    'random_same_genre': ('대조군: 같은 장르에서 무작위 (시드 고정)', None),
}


def build_context(data):
    """저장 데이터에서 계산에 필요한 배열만 꺼냅니다. 행렬은 복사하지 않고 읽기만 합니다."""
    profiles = data['profiles']
    context = {
        'ids': profiles['movie_id'].astype(str).tolist(),
        'titles': profiles['title'].astype(str).tolist(),
        'genre': [optional_text(value) for value in profiles['GENRE_NM']],
        'director': [optional_text(value) for value in profiles['DRCTR_NM']],
        'quality': profiles['rating_quality'].astype(float).to_numpy(),
        'corrected': profiles['corrected_rating'].astype(float).to_numpy(),
        'reviews': profiles['review_count'].astype(int).to_numpy(),
        'meta': np.asarray(data['matrices']['metadata']),
        'text': np.asarray(data['matrices']['text']),
    }
    # 평점 속성을 뺀 메타 유사도(evaluate.py와 같은 방식). 필요한 행렬이 없으면 이 설정만 건너뜁니다.
    try:
        from build_features import numeric_similarity
        without_rating, _ = numeric_similarity(profiles, include_rating=False)
        context['meta_alt'] = 0.5 * np.asarray(data['matrices']['categories']) + 0.5 * without_rating
    except (ImportError, KeyError, ValueError):
        pass
    return context


def hubness(context, config, neighbors=10):
    """영화마다 '같은 장르의 다른 영화들과 얼마나 비슷한 편인지'(가장 비슷한 neighbors개의 평균 유사도)를 계산합니다.

    이 값이 유난히 큰 영화가 여러 추천 목록에 반복해서 나오는 '허브'입니다. 결과는 context에 캐시합니다.
    """
    key = ('hub', config['meta_key'], config['meta_w'], config['text_w'], neighbors)
    if key in context:
        return context[key]
    combined = config['meta_w'] * context[config['meta_key']] + config['text_w'] * context['text']
    result = np.zeros(len(context['ids']))
    members_by_genre = {}
    for index, genre in enumerate(context['genre']):
        if genre is not None:
            members_by_genre.setdefault(genre, []).append(index)
    for members in members_by_genre.values():
        if len(members) < 2:
            continue
        block = combined[np.ix_(members, members)].copy()
        np.fill_diagonal(block, -np.inf)
        top = np.sort(block, axis=1)[:, -min(neighbors, len(members) - 1):]
        result[members] = top.mean(axis=1)
    context[key] = result
    return result


def recommend_indices(context, source, config, top_n=TOP_N):
    """recommender.recommend()와 같은 절차를 행렬 연산으로 계산합니다: 같은 장르 → 유사도 상위 N → 최종 점수."""
    genre = context['genre'][source]
    if genre is None:
        return []
    candidates = [index for index, value in enumerate(context['genre']) if value == genre and index != source]
    if not candidates:
        return []
    cols = np.array(candidates)
    similarity = config['meta_w'] * context[config['meta_key']][source, cols] + config['text_w'] * context['text'][source, cols]
    director = context['director'][source]
    if director is not None and config['bonus']:
        similarity = similarity + np.array([config['bonus'] if context['director'][i] == director else 0.0 for i in candidates])
    similarity = np.clip(similarity, 0.0, 1.0)
    if config.get('hub_w'):
        # 평균 허브 정도와의 차이만큼 빼서, 유난히 많은 영화와 비슷한 영화의 유사도를 낮춘다(전체 눈금은 유지).
        hub = hubness(context, config)
        similarity = np.clip(similarity - config['hub_w'] * (hub[cols] - hub.mean()), 0.0, 1.0)
    order = sorted(range(len(candidates)), key=lambda k: (-similarity[k], context['titles'][candidates[k]], context['ids'][candidates[k]]))
    shortlist = order[:config['shortlist']]
    final = {k: config['sim_w'] * similarity[k] + config['quality_w'] * context['quality'][candidates[k]] for k in shortlist}
    shortlist.sort(key=lambda k: (-final[k], -similarity[k], context['titles'][candidates[k]], context['ids'][candidates[k]]))
    return [candidates[k] for k in shortlist[:top_n]]


def baseline_indices(context, source, top_n=TOP_N):
    """같은 장르에서 보정 평점이 높은 순서(동점은 제목·ID)."""
    genre = context['genre'][source]
    if genre is None:
        return []
    candidates = [i for i, value in enumerate(context['genre']) if value == genre and i != source]
    candidates.sort(key=lambda i: (-context['corrected'][i], context['titles'][i], context['ids'][i]))
    return candidates[:top_n]


def random_indices(context, source, rng, top_n=TOP_N):
    """같은 장르에서 무작위로 뽑는 대조군. 어떤 추천이든 이 값보다 나아야 의미가 있습니다."""
    genre = context['genre'][source]
    if genre is None:
        return []
    candidates = [i for i, value in enumerate(context['genre']) if value == genre and i != source]
    return rng.sample(candidates, min(top_n, len(candidates)))


def all_lists(context, name, seed=42):
    """한 설정으로 모든 영화의 추천 목록(행 번호)을 만듭니다."""
    count = len(context['ids'])
    if name == 'baseline_rating':
        return [baseline_indices(context, source) for source in range(count)]
    if name == 'random_same_genre':
        rng = random.Random(seed)
        return [random_indices(context, source, rng) for source in range(count)]
    changes = CONFIGS[name][1]
    config = {**CURRENT, **changes}
    if config['meta_key'] not in context:
        return None
    return [recommend_indices(context, source, config) for source in range(count)]


def summarize(context, lists, reference):
    """한 설정의 목록 전체를 요약합니다. reference는 현재 설정의 목록이며 겹침 계산에 씁니다."""
    sources = [s for s in range(len(lists)) if reference[s] and lists[s]]
    frequency = Counter()
    overlap, rating_gap, popularity, relevance, diversity, same_director = [], [], [], [], [], []
    for source in sources:
        recs = lists[source]
        frequency.update(recs)
        union = set(recs) | set(reference[source])
        overlap.append(len(set(recs) & set(reference[source])) / len(union))
        rating_gap.append(float(np.mean([context['corrected'][i] - context['corrected'][source] for i in recs])))
        popularity.append(float(np.mean([context['reviews'][i] for i in recs])))
        relevance.append(float(np.mean([context['text'][source, i] for i in recs])))
        if len(recs) >= 2:
            pairs = [1 - context['text'][a, b] for position, a in enumerate(recs) for b in recs[position + 1:]]
            diversity.append(float(np.mean(pairs)))
        director = context['director'][source]
        if director is not None:
            same_director.append(sum(context['director'][i] == director for i in recs) / len(recs))
    eligible = sum(value is not None for value in context['genre'])
    hubs = [{'title': context['titles'][i], 'times': times} for i, times in frequency.most_common(3)]
    return {
        'sources': len(sources),
        'overlap_with_current': round(float(np.mean(overlap)), 3),
        'rating_gap_vs_source': round(float(np.mean(rating_gap)), 3),
        'mean_review_count': round(float(np.mean(popularity)), 1),
        'text_similarity_to_source': round(float(np.mean(relevance)), 3),
        'diversity': round(float(np.mean(diversity)), 3) if diversity else None,
        'same_director_share': round(float(np.mean(same_director)), 3) if same_director else None,
        'coverage': round(len(frequency) / eligible, 3),
        'most_recommended': hubs,
        'max_times_recommended': hubs[0]['times'] if hubs else 0,
    }


def build_report(data):
    """모든 설정의 요약과 카탈로그 기준값을 담은 보고서 딕셔너리를 만듭니다."""
    context = build_context(data)
    reference = all_lists(context, 'current')
    report = {
        'data_version': data['manifest']['data_version'],
        'top_n': TOP_N,
        'catalog_mean_review_count': round(float(np.mean(context['reviews'])), 1),
        'configs': {},
        'note': '추천의 성질을 설명하는 수치입니다. 사용자 만족도나 정확도가 아닙니다.',
    }
    for name, (description, _) in CONFIGS.items():
        lists = all_lists(context, name)
        if lists is None:
            continue
        report['configs'][name] = {'description': description, **summarize(context, lists, reference)}
    return report


# ---------- 사람 평가 시트 ----------

def make_sheet(data, size, directory, key_directory=None, seed=42, systems=('current', 'baseline_rating')):
    """기준 영화 size개에 대해 두 설정의 추천 목록을 A/B로 섞어 CSV로 저장합니다(평가자는 어느 설정인지 모름).

    시트(directory)는 평가자에게 공유하고, 정답 키(key_directory, 기본은 같은 폴더)는 공유하지 않습니다.
    """
    context = build_context(data)
    lists = {name: all_lists(context, name) for name in systems}
    eligible = [s for s in range(len(context['ids'])) if all(lists[name][s] for name in systems)]
    rng = random.Random(seed)
    chosen = rng.sample(eligible, min(size, len(eligible)))
    directory = Path(directory)
    key_directory = Path(key_directory) if key_directory else directory
    directory.mkdir(parents=True, exist_ok=True)
    key_directory.mkdir(parents=True, exist_ok=True)
    sheet_rows, key_rows = [], []
    for number, source in enumerate(chosen, 1):
        order = list(systems)
        rng.shuffle(order)
        titles = {label: ' / '.join(context['titles'][i] for i in lists[name][source]) for label, name in zip('AB', order)}
        sheet_rows.append([number, context['titles'][source], titles['A'], titles['B'], '', ''])
        key_rows.append([number, order[0], order[1]])
    header = ['번호', '기준 영화', '목록 A', '목록 B', '더 좋은 목록 (A / B / 비슷함)', '메모']
    with (directory / 'human_eval_sheet.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(sheet_rows)
    with (key_directory / 'human_eval_key.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['번호', 'A의 설정', 'B의 설정'])
        writer.writerows(key_rows)
    return directory / 'human_eval_sheet.csv', key_directory / 'human_eval_key.csv'


def score_sheets(sheet_paths, key_path):
    """채운 시트들(평가자별 CSV)과 키로 설정별 승수를 집계합니다. 여러 평가자의 응답을 모두 합칩니다."""
    with Path(key_path).open(encoding='utf-8-sig', newline='') as handle:
        key = {int(row['번호']): (row['A의 설정'], row['B의 설정']) for row in csv.DictReader(handle)}
    wins, ties, answered = Counter(), 0, 0
    for path in sheet_paths:
        with Path(path).open(encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                answer = row['더 좋은 목록 (A / B / 비슷함)'].strip().upper()
                number = int(row['번호'])
                if answer in ('A', 'B'):
                    wins[key[number][0 if answer == 'A' else 1]] += 1
                    answered += 1
                elif answer in ('비슷함', 'S', '='):
                    ties += 1
                    answered += 1
    return {'answered': answered, 'wins': dict(wins), 'ties': ties}


def print_table(report):
    """보고서를 표로 출력합니다."""
    print(f"데이터 버전 {report['data_version']} · 목록 길이 {report['top_n']} · 카탈로그 평균 리뷰 수 {report['catalog_mean_review_count']}")
    columns = ['overlap_with_current', 'rating_gap_vs_source', 'mean_review_count', 'text_similarity_to_source', 'diversity', 'same_director_share', 'coverage', 'max_times_recommended']
    print('설정'.ljust(26) + ''.join(name[:12].rjust(14) for name in columns))
    for name, row in report['configs'].items():
        print(name.ljust(26) + ''.join(str(row[column]).rjust(14) for column in columns))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--artifacts-dir', type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument('--out', type=Path, help='보고서 JSON 저장 경로. 기본: 데이터 버전 폴더의 quality_report.json')
    parser.add_argument('--sheet', type=int, metavar='N', help='사람 평가용 블라인드 시트를 N개 만듭니다.')
    parser.add_argument('--systems', nargs=2, default=['current', 'baseline_rating'], choices=list(CONFIGS), metavar='NAME', help='시트에서 비교할 두 설정(기본: current baseline_rating)')
    parser.add_argument('--sheet-dir', type=Path, default=PROJECT_DIR / 'docs' / 'human_eval')
    parser.add_argument('--score', nargs='+', type=Path, metavar='CSV', help='채운 시트(들)를 집계합니다. --key 필요')
    parser.add_argument('--key-dir', type=Path, default=DEFAULT_KEY_DIR, help='정답 키를 저장할 폴더(공유 금지). 기본: artifacts/human_eval')
    parser.add_argument('--key', type=Path, default=DEFAULT_KEY_DIR / 'human_eval_key.csv', help='--score에 쓸 정답 키')
    args = parser.parse_args()

    if args.score:
        print(score_sheets(args.score, args.key))
        return
    data = load_data(args.artifacts_dir)
    if args.sheet:
        sheet, key = make_sheet(data, args.sheet, args.sheet_dir, args.key_dir, systems=tuple(args.systems))
        print('시트(평가자에게 공유):', sheet)
        print('정답 키(공유 금지):', key)
        return
    report = build_report(data)
    out = args.out or data['directory'] / 'quality_report.json'
    write_json(out, report)
    print_table(report)
    print('저장:', out)


if __name__ == '__main__':
    main()
