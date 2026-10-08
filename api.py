"""검색·추천·리뷰 조회를 연결하는 FastAPI 백엔드입니다. 프론트는 포함하지 않습니다.

실행: python -m uvicorn api:app --host 127.0.0.1 --port 8000
먼저 python run_pipeline.py로 데이터를 준비해야 합니다.
"""

# contextlib: 서버 시작/종료 동작을 lifespan 함수로 묶기 위해 사용합니다.

from contextlib import asynccontextmanager
from pathlib import Path
# Literal: 리뷰 정렬 방향을 high/low 두 값으로 제한합니다.
from typing import Literal

# FastAPI: HTTP 요청을 파이썬 함수에 연결하고 요청 값의 범위도 검사합니다.
# FastAPI의 Path는 URL 경로 입력 설정입니다. pathlib.Path와 구분해 PathParameter로 이름을 붙입니다.
from fastapi import FastAPI, HTTPException, Path as PathParameter, Query, Request

from pipeline_common import DEFAULT_ARTIFACTS
from data_store import load_data, search_movies, get_movie, find_movies_by_title
from recommender import recommend
from review_service import get_reviews
from fastapi.middleware.cors import CORSMiddleware

def request_data(request):
    """서버 시작 때 한 번 읽은 데이터 딕셔너리를 현재 요청에 연결합니다."""
    return request.app.state.movie_data


def title_to_movie_id(data, title, release_date=None, director=None):
    """제목을 내부 영화 ID로 연결합니다. 없음=404, 동명이작=409와 후보 정보를 반환합니다."""
    try:
        candidates = find_movies_by_title(data, title, release_date, director)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not candidates:
        raise HTTPException(status_code=404, detail='조건에 맞는 영화 제목을 찾을 수 없습니다.')
    if len(candidates) > 1:
        raise HTTPException(status_code=409, detail={
            'message': '같은 제목의 작품이 여러 개입니다. release_date 또는 director를 추가하세요.',
            'candidates': candidates,
        })
    return candidates[0]['movie_id']


def movie_input_to_id(data, value):
    """기존 경로에 영화 ID 또는 정확한 제목을 넣을 수 있도록 입력값을 연결합니다."""
    if value in data['id_to_index']:
        return value
    return title_to_movie_id(data, value)


def recommendation_response(data, movie_id, top_n):
    """제목 요청/ID 요청이 동일한 추천 함수와 응답 구조를 사용하도록 묶습니다."""
    source = get_movie(data, movie_id)
    rows = recommend(data, movie_id, top_n)
    message = '장르 정보가 없어 추천 후보를 만들 수 없습니다.' if source['genre'] is None else None
    return {'source': source, 'count': len(rows), 'items': rows, 'message': message, 'data_version': data['manifest']['data_version']}


def create_app(artifacts_dir=DEFAULT_ARTIFACTS):
    """저장 폴더를 받는 API 생성 함수입니다. 테스트에서는 임시 폴더를 전달합니다."""
    artifacts_dir = Path(artifacts_dir)

    @asynccontextmanager
    async def lifespan(application):
        """서버 시작 때 정상 버전을 한 번 로딩합니다. 요청마다 학습/계산하지 않습니다."""
        application.state.movie_data = load_data(artifacts_dir)
        yield
        # 파일은 로딩 시 이미 닫혔습니다. 종료 때 메모리 참조를 정리합니다.
        application.state.movie_data = None

    application = FastAPI(title='영화 추천 백엔드', version='1.1.0', lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        )
    @application.get('/health')
    def health(request: Request):
        """현재 데이터 버전과 준비된 영화/리뷰 개수를 반환합니다."""
        data = request_data(request)
        return {'status': 'ok', 'data_version': data['manifest']['data_version'], 'movies': len(data['profiles']), 'reviews': len(data['reviews'])}

    @application.get('/movies')
    def movies(request: Request, query: str = Query(default='', max_length=200), limit: int = Query(default=20, ge=1, le=100)):
        """제목 일부로 검색합니다. 정확한 제목으로도 상세/추천/리뷰를 바로 조회할 수 있습니다."""
        rows = search_movies(request_data(request), query, limit)
        return {'count': len(rows), 'items': rows}

    # 고정 경로를 /movies/{movie_id}보다 먼저 등록해야 'detail'이 영화 ID로 해석되지 않습니다.
    @application.get('/movies/detail', tags=['제목으로 조회'], responses={404: {'description': '제목 없음'}, 409: {'description': '동명이작: 후보 선택 필요'}})
    def movie_detail_by_title(
        request: Request,
        title: str = Query(min_length=1, max_length=200, description='정확한 영화 제목. 예: 승부'),
        release_date: str | None = Query(default=None, pattern=r'^\d{8}$', description='동명이작 구분용 개봉일 YYYYMMDD'),
        director: str | None = Query(default=None, min_length=1, max_length=200, description='동명이작 구분용 감독'),
    ):
        """제목만으로 영화 상세를 조회합니다. 제목이 중복되면 개봉일/감독으로 구분하세요."""
        data = request_data(request)
        movie_id = title_to_movie_id(data, title, release_date, director)
        return get_movie(data, movie_id)

    @application.get('/recommend', tags=['제목으로 조회'], responses={404: {'description': '제목 없음'}, 409: {'description': '동명이작: 후보 선택 필요'}})
    def recommendations_by_title(
        request: Request,
        title: str = Query(min_length=1, max_length=200, description='정확한 영화 제목. 예: 승부'),
        top_n: int = Query(default=5, ge=1, le=20),
        release_date: str | None = Query(default=None, pattern=r'^\d{8}$'),
        director: str | None = Query(default=None, min_length=1, max_length=200),
    ):
        """입력한 영화 제목의 추천을 바로 반환합니다. ID 복사 단계가 필요하지 않습니다."""
        data = request_data(request)
        movie_id = title_to_movie_id(data, title, release_date, director)
        return recommendation_response(data, movie_id, top_n)

    @application.get('/movies/reviews', tags=['제목으로 조회'], responses={404: {'description': '제목 없음'}, 409: {'description': '동명이작: 후보 선택 필요'}})
    def reviews_by_title(
        request: Request,
        title: str = Query(min_length=1, max_length=200, description='정확한 영화 제목. 예: 서울의 봄'),
        order: Literal['high', 'low'] = 'high',
        top_n: int = Query(default=5, ge=1, le=20),
        release_date: str | None = Query(default=None, pattern=r'^\d{8}$'),
        director: str | None = Query(default=None, min_length=1, max_length=200),
    ):
        """영화 제목으로 실제 평점순 리뷰를 조회합니다. high/low 방향을 선택할 수 있습니다."""
        data = request_data(request)
        movie_id = title_to_movie_id(data, title, release_date, director)
        rows = get_reviews(data, movie_id, top_n, order)
        return {'movie_id': movie_id, 'title': get_movie(data, movie_id)['title'], 'order': order, 'count': len(rows), 'items': rows}

    @application.get('/movies/{movie_id}')
    def movie_detail(request: Request, movie_id: str = PathParameter(min_length=1, max_length=200, description='영화 ID 또는 정확한 제목. 예: 승부')):
        """경로에 영화 ID 또는 제목을 넣어 메타데이터, 평균/보정 평점, 리뷰 수를 조회합니다."""
        data = request_data(request)
        selected_id = movie_input_to_id(data, movie_id)
        return get_movie(data, selected_id)

    @application.get('/recommend/{movie_id}')
    def recommendations(request: Request, movie_id: str = PathParameter(min_length=1, max_length=200, description='영화 ID 또는 정확한 제목. 예: 승부'), top_n: int = Query(default=5, ge=1, le=20)):
        """경로의 영화 ID 또는 제목을 받아 같은 장르의 추천과 점수/근거를 반환합니다."""
        data = request_data(request)
        selected_id = movie_input_to_id(data, movie_id)
        return recommendation_response(data, selected_id, top_n)

    @application.get('/movies/{movie_id}/reviews')
    def reviews(request: Request, movie_id: str = PathParameter(min_length=1, max_length=200, description='영화 ID 또는 정확한 제목. 예: 서울의 봄'), order: Literal['high', 'low'] = 'high', top_n: int = Query(default=5, ge=1, le=20)):
        """경로의 영화 ID 또는 제목으로 실제 평점순 리뷰를 조회합니다."""
        data = request_data(request)
        selected_id = movie_input_to_id(data, movie_id)
        rows = get_reviews(data, selected_id, top_n, order)
        return {'movie_id': selected_id, 'order': order, 'count': len(rows), 'items': rows}

    return application


# 앱 객체만 생성합니다. CSV/유사도 로딩은 서버 시작(lifespan)에서 실행됩니다.
app = create_app()
