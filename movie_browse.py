"""검색어 없이 전체 영화를 정렬·필터·페이지로 둘러봅니다."""

import pandas as pd

from data_store import movie_to_dict

SORTS = ('title', 'rating', 'reviews', 'newest')
DIRECTIONS = ('asc', 'desc')


def browse_movies(data, sort='rating', direction='desc', genre=None, offset=0, limit=24, director=None):
    """입력: 정렬 기준, 방향, 장르(선택), 시작 위치, 개수. 반환: {total, offset, limit, items}.

    rating은 리뷰 수를 반영한 보정 평점(corrected_rating) 기준입니다. newest는 개봉일이며
    개봉일이 없는 영화는 방향과 관계없이 맨 뒤에 둡니다. 동점은 제목 오름차순으로 고정합니다.
    director를 주면 그 감독의 영화만 보여줍니다(정확히 일치, 대소문자 무시).
    total은 장르·감독 필터를 적용한 전체 개수이고 offset/limit과 무관합니다.
    """
    if sort not in SORTS:
        raise ValueError(f'sort는 {", ".join(SORTS)} 중 하나여야 합니다.')
    if direction not in DIRECTIONS:
        raise ValueError('direction은 asc 또는 desc여야 합니다.')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError('offset은 0 이상의 정수여야 합니다.')
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError('limit은 1~100 사이의 정수여야 합니다.')

    profiles = data['profiles']
    if genre is not None:
        genres = profiles['GENRE_NM'].fillna('').astype(str).str.strip()
        profiles = profiles.loc[genres.eq(genre.strip())]

    if director is not None:
        directors = profiles['DRCTR_NM'].fillna('').astype(str).str.strip().str.casefold()
        profiles = profiles.loc[directors.eq(director.strip().casefold())]

    ascending = direction == 'asc'
    frame = profiles.assign(_date=pd.to_numeric(profiles['OPN_DE'], errors='coerce'))
    columns, flags = {
        'title': (['title', 'movie_id'], [ascending, True]),
        'rating': (['corrected_rating', 'review_count', 'title'], [ascending, ascending, True]),
        'reviews': (['review_count', 'corrected_rating', 'title'], [ascending, ascending, True]),
        'newest': (['_date', 'title'], [ascending, True]),
    }[sort]
    frame = frame.sort_values(columns, ascending=flags, kind='stable', na_position='last')

    page = frame.iloc[offset:offset + limit]
    return {
        'total': int(len(frame)), 'offset': offset, 'limit': limit,
        'items': [movie_to_dict(row) for _, row in page.iterrows()],
    }
