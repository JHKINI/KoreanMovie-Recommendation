import { useState } from 'react'
import './App.css'
import { searchMovies } from './services/api'

function App() {
  const [query, setQuery] = useState('')
  const [movies, setMovies] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('영화 제목을 입력해주세요.')
      return
    }

    try {
      setLoading(true)
      setError('')

      const data = await searchMovies(query)

      setMovies(data.items || [])
    } catch (err) {
      setError('영화 검색 중 오류가 발생했습니다.')
      setMovies([])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo">🎬 Korean Movie</div>
      </header>

      <main className="main">
        <section className="hero">
          <h1>어떤 영화를 좋아하세요?</h1>

          <p>
            영화 제목을 검색하면 비슷한 영화를 추천해드려요.
          </p>

          <div className="search-box">
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="영화 제목을 입력하세요"
            />

            <button onClick={handleSearch}>
              검색
            </button>
          </div>

          {loading && (
            <p className="message">
              영화를 검색하고 있습니다...
            </p>
          )}

          {error && (
            <p className="error">
              {error}
            </p>
          )}
        </section>

        {movies.length > 0 && (
          <section className="results-section">
            <h2>검색 결과</h2>

            <div className="movie-list">
              {movies.map((movie) => (
                <div
                  className="movie-card"
                  key={movie.movie_id}
                >
                  <h3>{movie.title}</h3>

                  <p>
                    <strong>장르</strong> {movie.genre}
                  </p>

                  <p>
                    <strong>감독</strong> {movie.director}
                  </p>

                  <p>
                    <strong>개봉일</strong> {movie.release_date}
                  </p>

                  <div className="rating">
                    ⭐ {movie.mean_rating}
                  </div>

                  <p className="review-count">
                    리뷰 {movie.review_count}개
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="info-section">
          <h2>영화 추천 시스템</h2>

          <p>
            영화 리뷰와 영화 정보를 분석하여
            취향에 맞는 영화를 추천합니다.
          </p>
        </section>
      </main>
    </div>
  )
}

export default App