"""저장된 영화 정보와 유사도를 이용해 추천과 추천 근거를 반환합니다."""

import argparse
import json
from pathlib import Path

from pipeline_common import DEFAULT_ARTIFACTS, validate_top_n
from data_store import load_data, get_movie_index, movie_to_dict, optional_text, resolve_movie_id


def same_genre_indices(data, movie_id):
    """자기 영화를 제외하고 같은 장르의 프로필 행 번호를 찾습니다.

    '멜로/로맨스'를 하나의 장르 이름으로 사용합니다. 장르 미상은 빈 목록입니다.
    """
    index = get_movie_index(data, movie_id)
    profiles = data['profiles']
    genre = optional_text(profiles.iloc[index]['GENRE_NM'])
    if genre is None:
        return []
    candidates = []
    for other_index in range(len(profiles)):
        if other_index != index and profiles.iloc[other_index]['GENRE_NM'] == genre:
            candidates.append(other_index)
    return candidates


def calculate_candidate(data, source_index, candidate_index):
    """후보 하나의 유사도, 최종 점수, 추천 이유를 계산해 딕셔너리로 돌려줍니다."""
    profiles = data['profiles']
    source, candidate = profiles.iloc[source_index], profiles.iloc[candidate_index]
    meta = float(data['matrices']['metadata'][source_index, candidate_index])
    text = float(data['matrices']['text'][source_index, candidate_index])
    director = optional_text(source['DRCTR_NM'])
    other_director = optional_text(candidate['DRCTR_NM'])
    bonus = 0.05 if director is not None and director == other_director else 0.0
    similarity = min(1.0, max(0.0, 0.4 * meta + 0.6 * text + bonus))
    score = 0.7 * similarity + 0.3 * float(candidate['rating_quality'])
    result = movie_to_dict(candidate)
    result['metadata_similarity'] = meta
    result['text_similarity'] = text
    result['director_bonus'] = bonus
    result['similarity'] = similarity
    result['final_score'] = score
    result['reasons'] = [f"같은 장르: {candidate['GENRE_NM']}", f'리뷰 표현 유사도: {text:.3f}']
    if bonus:
        result['reasons'].append(f'같은 감독: {director}')
    result['reasons'].append(f"평점 {int(candidate['rating_count'])}개를 반영한 보정 평점: {float(candidate['corrected_rating']):.3f}")
    return result


def similarity_sort_key(candidate):
    """유사도 내림차순 정렬 키입니다. 동점은 제목·ID로 정해 재실행 결과를 유지합니다."""
    return (-candidate['similarity'], candidate['title'], candidate['movie_id'])


def final_sort_key(candidate):
    """최종 점수, 유사도는 내림차순이고 동점이면 제목·ID를 오름차순으로 정렬합니다."""
    return (-candidate['final_score'], -candidate['similarity'], candidate['title'], candidate['movie_id'])


def recommend(data, movie_id, top_n=5):
    """같은 장르 → 유사도 상위 20개 → 최종 점수 상위 top_n개를 반환합니다.

    data는 load_data()의 결과입니다. 후보가 부족하면 가능한 개수만 반환합니다.
    """
    validate_top_n(top_n)
    source_index = get_movie_index(data, movie_id)
    candidates = []
    for candidate_index in same_genre_indices(data, movie_id):
        candidates.append(calculate_candidate(data, source_index, candidate_index))
    candidates.sort(key=similarity_sort_key)
    shortlist = candidates[:20]
    shortlist.sort(key=final_sort_key)
    return shortlist[:top_n]


def baseline_recommend(data, movie_id, top_n=5):
    """비교 기준: 같은 장르 안에서 보정 평점이 높은 영화부터 추천합니다."""
    validate_top_n(top_n)
    candidates = []
    for index in same_genre_indices(data, movie_id):
        candidates.append(movie_to_dict(data['profiles'].iloc[index]))
    candidates.sort(key=baseline_sort_key)
    return candidates[:top_n]


def baseline_sort_key(candidate):
    """기준 추천의 보정 평점 내림차순 정렬 키입니다."""
    return (-candidate['corrected_rating'], candidate['title'], candidate['movie_id'])


def main():
    """정확한 영화 제목/ID를 터미널에서 받아 추천 결과를 JSON으로 출력합니다."""
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--title')
    selection.add_argument('--movie-id')
    parser.add_argument('--top-n', type=int, default=5)
    parser.add_argument('--artifacts-dir', type=Path, default=DEFAULT_ARTIFACTS)
    args = parser.parse_args()
    try:
        data = load_data(args.artifacts_dir)
        movie_id = resolve_movie_id(data, args.movie_id, args.title)
        result = recommend(data, movie_id, args.top_n)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f'중단: {exc}\n')
    print(json.dumps({'movie_id': movie_id, 'count': len(result), 'items': result}, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
