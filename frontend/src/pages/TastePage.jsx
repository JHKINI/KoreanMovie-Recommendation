import { useState } from 'react'
import MovieCard from '../components/MovieCard'
import { Meter } from '../components/SimilarityBars'
import { getTasteRecommendations, searchMovies } from '../services/api'
import { formatMeta } from '../utils/format'

const MIN_PICKS = 2
const MAX_PICKS = 5

// 좋아하는 영화를 2~5편 고르면 그 영화들을 모두 반영해 추천한다.
function TastePage() {
  const [query, setQuery] = useState('')
  const [found, setFound] = useState({ status: 'idle', items: [], message: '' })
  const [picked, setPicked] = useState([])
  const [result, setResult] = useState({ status: 'idle' })

  const runSearch = async () => {
    const keyword = query.trim()
    if (!keyword) {
      setFound({ status: 'error', items: [], message: '영화 제목을 입력해주세요.' })
      return
    }
    setFound({ status: 'loading', items: [], message: '' })
    try {
      const data = await searchMovies(keyword, 12)
      setFound({ status: 'ready', items: data.items, message: '' })
    } catch (err) {
      setFound({ status: 'error', items: [], message: err.message })
    }
  }

  const isPicked = (movie) => picked.some((item) => item.movie_id === movie.movie_id)

  const add = (movie) => {
    if (isPicked(movie) || picked.length >= MAX_PICKS) return
    setPicked([...picked, movie])
    setResult({ status: 'idle' })
  }

  const remove = (movieId) => {
    setPicked(picked.filter((item) => item.movie_id !== movieId))
    setResult({ status: 'idle' })
  }

  const recommend = async () => {
    setResult({ status: 'loading' })
    try {
      const data = await getTasteRecommendations(picked.map((item) => item.movie_id), 8)
      setResult({ status: 'ready', data })
    } catch (err) {
      setResult({ status: 'error', message: err.message })
    }
  }

  return (
    <div className="page">
      <h1 className="page-title">취향 추천</h1>
      <p className="section-note">좋아하는 영화를 {MIN_PICKS}~{MAX_PICKS}편 고르면, 고른 영화 모두와 비슷한 영화를 추천합니다.</p>

      <div className="search-box taste-search">
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => event.key === 'Enter' && runSearch()}
          placeholder="영화 제목으로 찾아서 추가하세요"
          aria-label="영화 제목"
        />
        <button onClick={runSearch}>검색</button>
      </div>

      {found.status === 'loading' && <p className="message">검색하고 있습니다...</p>}
      {found.status === 'error' && <p className="error">{found.message}</p>}
      {found.status === 'ready' && found.items.length === 0 && <p className="empty">"{query.trim()}"에 해당하는 영화가 없습니다.</p>}
      {found.items.length > 0 && (
        <ul className="pick-list">
          {found.items.map((movie) => (
            <li key={movie.movie_id}>
              <span>
                <strong>{movie.title}</strong>
                <small>{formatMeta(movie)}</small>
              </span>
              <button className="tab small" disabled={isPicked(movie) || picked.length >= MAX_PICKS} onClick={() => add(movie)}>
                {isPicked(movie) ? '추가됨' : '추가'}
              </button>
            </li>
          ))}
        </ul>
      )}

      <section className="picked">
        <h2>고른 영화 {picked.length}/{MAX_PICKS}</h2>
        {picked.length === 0 && <p className="section-note">아직 고른 영화가 없습니다.</p>}
        <ul className="chips">
          {picked.map((movie) => (
            <li key={movie.movie_id}>
              {movie.title}
              <button aria-label={`${movie.title} 빼기`} onClick={() => remove(movie.movie_id)}>✕</button>
            </li>
          ))}
        </ul>
        <button className="primary" disabled={picked.length < MIN_PICKS || result.status === 'loading'} onClick={recommend}>
          {picked.length < MIN_PICKS ? `${MIN_PICKS - picked.length}편 더 고르세요` : '추천 받기'}
        </button>
      </section>

      {result.status === 'loading' && <p className="message page-message">추천을 계산하고 있습니다...</p>}
      {result.status === 'error' && <p className="error">{result.message}</p>}
      {result.status === 'ready' && (
        <section className="results-section">
          <h2>이런 영화는 어때요?</h2>
          {result.data.items.length === 0 && <p className="notice">고른 영화의 장르 정보가 없어 추천 후보를 만들 수 없습니다.</p>}
          <div className="movie-list">
            {result.data.items.map((movie) => (
              <MovieCard key={movie.movie_id} movie={movie} reasons={movie.reasons}>
                <div className="meters">
                  {movie.seed_similarities.map((seed) => (
                    <Meter key={seed.movie_id} label={seed.title} value={seed.similarity} />
                  ))}
                </div>
              </MovieCard>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

export default TastePage
