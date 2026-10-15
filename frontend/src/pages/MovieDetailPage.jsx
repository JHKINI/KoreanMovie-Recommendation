import { useEffect, useState } from 'react'
import FavoriteButton from '../components/FavoriteButton'
import KeywordChips from '../components/KeywordChips'
import MovieCard from '../components/MovieCard'
import RatingBars from '../components/RatingBars'
import SameDirector from '../components/SameDirector'
import { compareHref, keywordHref } from '../hooks/useHashRoute'
import { getMovie, getRecommendations, getReviews } from '../services/api'
import { formatMeta, formatRating } from '../utils/format'
import { pushRecent } from '../utils/storage'

const ORDER_LABELS = { high: '높은 평점순', low: '낮은 평점순' }

// 영화 상세 화면: 정보 요약 + 대표 키워드 + [비슷한 영화] / [리뷰] 탭.
// 영화가 바뀌면 App에서 key로 새로 만들기 때문에 상태를 되돌리는 코드가 필요 없다.
function MovieDetailPage({ movieId }) {
  const [state, setState] = useState({ status: 'loading' })
  const [tab, setTab] = useState('reco')
  const [reviews, setReviews] = useState({ order: 'high', keyword: '', status: 'idle', items: [], message: '' })
  const [draft, setDraft] = useState('')

  useEffect(() => {
    let ignore = false
    Promise.all([getMovie(movieId), getRecommendations(movieId, 6)])
      .then(([movie, reco]) => {
        if (ignore) return
        pushRecent(movie)
        setState({ status: 'ready', movie, reco })
      })
      .catch((err) => {
        if (!ignore) setState({ status: 'error', message: err.message })
      })
    return () => {
      ignore = true
    }
  }, [movieId])

  const loadReviews = async (order, keyword) => {
    setReviews({ order, keyword, status: 'loading', items: [], message: '' })
    try {
      const data = await getReviews(movieId, order, 10, keyword)
      setReviews({ order, keyword, status: 'ready', items: data.items, message: '' })
    } catch (err) {
      setReviews({ order, keyword, status: 'error', items: [], message: err.message })
    }
  }

  const openReviews = () => {
    setTab('reviews')
    if (reviews.status === 'idle') loadReviews(reviews.order, reviews.keyword)
  }

  // 키워드를 누르면 리뷰 탭으로 넘어가 그 단어가 들어간 리뷰만 보여준다. 같은 키워드를 다시 누르면 해제한다.
  const selectKeyword = (keyword) => {
    setTab('reviews')
    setDraft(keyword)
    loadReviews(reviews.order, keyword)
  }

  // 직접 입력한 글자가 들어간 리뷰만 찾는다. 비우고 검색하면 필터를 푼다.
  const searchReviews = (event) => {
    event.preventDefault()
    loadReviews(reviews.order, draft.trim())
  }

  if (state.status === 'loading') return <p className="message page-message">불러오는 중...</p>

  if (state.status === 'error') {
    return (
      <div className="page">
        <a className="back-link" href="#/">← 처음으로</a>
        <p className="error">{state.message}</p>
      </div>
    )
  }

  const { movie, reco } = state

  return (
    <div className="page">
      <a className="back-link" href="#/">← 처음으로</a>

      <section className="detail-hero">
        <div className="title-row">
          <h1>{movie.title}</h1>
          <FavoriteButton movie={movie} />
        </div>
        <p className="movie-meta">
          {formatMeta(movie)}
          {movie.age_rating && ` · ${movie.age_rating}`}
        </p>

        <div className="hero-body">
        <dl className="stats">
          <div>
            <dt>평균 평점 (5점 만점)</dt>
            <dd>{formatRating(movie.mean_rating, 2)}</dd>
          </div>
          <div>
            <dt>보정 평점</dt>
            <dd>{formatRating(movie.corrected_rating, 2)}</dd>
          </div>
          <div>
            <dt>리뷰 수</dt>
            <dd>{movie.review_count}</dd>
          </div>
          <div>
            <dt>평점이 있는 리뷰</dt>
            <dd>{movie.rating_count}</dd>
          </div>
        </dl>

        <RatingBars movieId={movieId} />
        </div>

        <KeywordChips movieId={movieId} selected={reviews.keyword} onSelect={selectKeyword} />
      </section>


      <div className="tabs" role="tablist">
        <button
          role="tab"
          aria-selected={tab === 'reco'}
          className={tab === 'reco' ? 'tab active' : 'tab'}
          onClick={() => setTab('reco')}
        >
          비슷한 영화
        </button>
        <button
          role="tab"
          aria-selected={tab === 'reviews'}
          className={tab === 'reviews' ? 'tab active' : 'tab'}
          onClick={openReviews}
        >
          리뷰
        </button>
      </div>

      {tab === 'reco' && (
        <section>
          {reco.message && <p className="notice">{reco.message}</p>}
          {reco.items.length > 0 && (
            <p className="section-note">막대는 추천 근거입니다. 정보 유사는 장르·등급·관객 수 같은 영화 정보, 리뷰 유사는 리뷰 글 표현이 얼마나 비슷한지입니다.</p>
          )}
          <div className="movie-list">
            {reco.items.map((item) => (
              <div className="movie-item" key={item.movie_id}>
                <MovieCard movie={item} reasons={item.reasons} />
                <a className="compare-link" href={compareHref(movie.movie_id, item.movie_id)}>
                  이 영화와 비교하기
                </a>
              </div>
            ))}
          </div>
        </section>
      )}

      {tab === 'reviews' && (
        <section>
          <form className="review-search" onSubmit={searchReviews}>
            <input
              type="search"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="리뷰에서 찾을 단어 (예: 연기)"
              aria-label="리뷰 검색"
              maxLength={50}
            />
            <button type="submit" className="tab small">리뷰 검색</button>
          </form>

          <div className="order-toggle">
            {Object.entries(ORDER_LABELS).map(([order, label]) => (
              <button
                key={order}
                className={reviews.order === order ? 'tab small active' : 'tab small'}
                onClick={() => loadReviews(order, reviews.keyword)}
              >
                {label}
              </button>
            ))}
            {reviews.keyword && (
              <button
                className="tab small filter"
                onClick={() => {
                  setDraft('')
                  loadReviews(reviews.order, '')
                }}
              >
                "{reviews.keyword}" 포함 리뷰만 · 해제 ✕
              </button>
            )}
          </div>

          {reviews.keyword && (
            <a className="section-link" href={keywordHref(reviews.keyword)}>
              "{reviews.keyword}" 키워드가 두드러진 다른 영화 보기 →
            </a>
          )}

          {reviews.status === 'loading' && <p className="message">리뷰를 불러오는 중...</p>}
          {reviews.status === 'error' && <p className="error">{reviews.message}</p>}
          {reviews.status === 'ready' && reviews.items.length === 0 && (
            <p className="notice">
              {reviews.keyword ? `평점이 있는 리뷰 중 "${reviews.keyword}"이(가) 들어간 글이 없습니다.` : '평점이 있는 리뷰가 없습니다.'}
            </p>
          )}
          {reviews.status === 'ready' &&
            reviews.items.map((review) => (
              <article className="review" key={review.review_id}>
                <span className="rating">⭐ {review.rating.toFixed(1)}</span>
                <p>{review.review}</p>
              </article>
            ))}
        </section>
      )}

      <SameDirector movie={movie} />
    </div>
  )
}

export default MovieDetailPage
