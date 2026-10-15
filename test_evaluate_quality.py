"""evaluate_quality.py가 실제 추천(recommender.recommend)과 같은 결과를 내는지, 시트 집계가 맞는지 검사합니다."""

import csv

import pytest

from evaluate_quality import (
    CONFIGS, all_lists, baseline_indices, build_context, build_report, make_sheet, recommend_indices, score_sheets,
)
from recommender import recommend
from test_browse_taste import IDS, make_data


def test_current_config_matches_recommender_for_every_movie():
    data = make_data()
    context = build_context(data)
    lists = all_lists(context, 'current')
    for index, movie_id in enumerate(IDS):
        expected = [row['movie_id'] for row in recommend(data, movie_id)]
        assert [context['ids'][i] for i in lists[index]] == expected, movie_id


def test_unknown_genre_and_single_member_genre_get_no_recommendation():
    context = build_context(make_data())
    lists = all_lists(context, 'current')
    assert lists[3] == [], '코미디는 영화가 하나뿐이라 후보가 없다'
    assert lists[4] == [], '장르 미상'


def test_baseline_orders_by_corrected_rating_and_random_is_reproducible():
    context = build_context(make_data())
    # 드라마(가, 나, 다)의 보정 평점: 가 3.1, 나 3.9, 다 3.5
    assert [context['ids'][i] for i in baseline_indices(context, 0)] == ['b', 'c']
    assert all_lists(context, 'random_same_genre', seed=1) == all_lists(context, 'random_same_genre', seed=1)


def test_text_only_config_ignores_metadata():
    context = build_context(make_data())
    config = {'meta_w': 0.0, 'text_w': 1.0, 'bonus': 0.0, 'sim_w': 1.0, 'quality_w': 0.0, 'shortlist': 20, 'meta_key': 'meta'}
    # 가의 후보 중 리뷰 유사도: 다 0.9 > 나 0.1
    assert [context['ids'][i] for i in recommend_indices(context, 0, config)] == ['c', 'b']


def test_report_has_every_config_and_current_overlaps_itself_fully():
    report = build_report(make_data())
    assert 'meta_alt' not in build_context(make_data()), '가상 데이터에는 평점 제외 행렬이 없으므로 그 설정은 빠진다'
    assert 'metadata_without_rating' not in report['configs']
    assert set(report['configs']) == set(CONFIGS) - {'metadata_without_rating'}
    assert report['configs']['current']['overlap_with_current'] == 1.0
    assert 0 <= report['configs']['random_same_genre']['coverage'] <= 1


def test_sheet_is_blind_and_score_counts_wins(tmp_path):
    data = make_data()
    sheet_path, key_path = make_sheet(data, 10, tmp_path, seed=7)
    with sheet_path.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    with key_path.open(encoding='utf-8-sig', newline='') as handle:
        key = list(csv.DictReader(handle))
    assert len(rows) == len(key) == 3, '추천 목록이 있는 영화는 가, 나, 다 세 편'
    assert all('current' not in value and 'baseline' not in value for row in rows for value in row.values()), '시트에 설정 이름이 드러나면 안 된다'
    assert {row['A의 설정'] for row in key} | {row['B의 설정'] for row in key} == {'current', 'baseline_rating'}

    # 모든 문항에 현재 설정이 놓인 쪽을 답하면 current가 전승해야 한다.
    for row, answer in zip(rows, key):
        row['더 좋은 목록 (A / B / 비슷함)'] = 'A' if answer['A의 설정'] == 'current' else 'B'
    filled = tmp_path / 'filled.csv'
    with filled.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    assert score_sheets([filled], key_path) == {'answered': 3, 'wins': {'current': 3}, 'ties': 0}


def hub_context():
    """S가 보는 후보 X(허브: 다른 영화와 모두 매우 비슷)와 Y(비허브). 보정이 없으면 X가 근소하게 앞선다."""
    import numpy as np
    text = np.array([
        [1.0, 0.60, 0.58, 0.10],   # S
        [0.60, 1.0, 0.90, 0.90],   # X
        [0.58, 0.90, 1.0, 0.10],   # Y
        [0.10, 0.90, 0.10, 1.0],   # Z
    ])
    return {
        'ids': ['s', 'x', 'y', 'z'], 'titles': ['S', 'X', 'Y', 'Z'], 'genre': ['드라마'] * 4, 'director': [None] * 4,
        'quality': np.zeros(4), 'corrected': np.zeros(4), 'reviews': np.zeros(4, dtype=int),
        'meta': np.zeros((4, 4)), 'text': text,
    }


def test_hub_correction_demotes_hub_and_is_off_by_default():
    context = hub_context()
    base = {'meta_w': 0.0, 'text_w': 1.0, 'bonus': 0.0, 'sim_w': 1.0, 'quality_w': 0.0, 'shortlist': 20, 'meta_key': 'meta', 'hub_w': 0.0}
    assert [context['ids'][i] for i in recommend_indices(context, 0, base)] == ['x', 'y', 'z']
    corrected = recommend_indices(context, 0, {**base, 'hub_w': 0.5})
    assert [context['ids'][i] for i in corrected] == ['y', 'x', 'z'], '허브인 X가 Y 뒤로 밀려야 한다'


def test_hub_corrected_is_a_registered_config_and_current_has_no_correction():
    from evaluate_quality import CURRENT
    assert CURRENT['hub_w'] == 0.0
    assert CONFIGS['hub_corrected'][1] == {'hub_w': 0.5}
