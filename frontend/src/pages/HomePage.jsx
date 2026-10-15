import { useState } from 'react'
import BarList from '../components/BarList'
import MovieCard from '../components/MovieCard'
import MovieSection from '../components/MovieSection'
import { movieHref } from '../hooks/useHashRoute'
import { useStatistics } from '../hooks/useStatistics'
import { formatMeta } from '../utils/format'
import { loadFavorites, loadRecent } from '../utils/storage'

// 검색 + 전체 현황 화면. 검색 상태는 App의 useMovieSearch에서 받는다.
function HomePage({ search }) {
  const { query, setQuery, movies, searchedQuery, loading, error, search: runSearch, suggestions } = search
  const statistics = useStatistics()
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1) // 화살표로 고른 자동완성 항목의 번호(-1은 없음)
  // 이 브라우저에 저장된 개인 목록. 홈에 올 때마다 새로 만들어지므로 처음 값만 읽으면 된다.
  const [recent] = useState(loadRecent)
  const [favorites] = useState(loadFavorites)

  const handleKeyDown = (event) => {
    const showing = open && suggestions.length > 0
    if (event.key === 'ArrowDown' && showing) {
      event.preventDefault()
      setActive((index) => Math.min(index + 1, suggestions.length - 1))
    } else if (event.key === 'ArrowUp' && showing) {
      event.preventDefault()
      setActive((index) => Math.max(index - 1, -1))
    } else if (event.key === 'Escape') {
      setOpen(false)
      setActive(-1)
    } else if (event.key === 'Enter') {
      setOpen(false)
      if (showing && suggestions[active]) {
        // 화살표로 고른 항목이 있으면 검색 대신 그 영화로 바로 이동한다.
        window.location.hash = movieHref(suggestions[active].movie_id)
      } else {
        runSearch()
      }
    }
  }

  return (
    <>
      <section className="hero">
        <h1>어떤 영화를 좋아하세요?</h1>

        <p>영화 제목을 검색하면 비슷한 영화를 추천해드려요.</p>

        <div className="search-box">
          <div className="search-field">
            <input
              type="text"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value)
                setOpen(true)
                setActive(-1)
              }}
              onFocus={() => setOpen(true)}
              onBlur={() => setOpen(false)}
              onKeyDown={handleKeyDown}
              placeholder="영화 제목을 입력하세요"
              aria-label="영화 제목"
              autoComplete="off"
              role="combobox"
              aria-expanded={open && suggestions.length > 0}
              aria-controls="movie-suggestions"
              aria-activedescendant={active >= 0 ? `suggestion-${active}` : undefined}
            />

            {open && suggestions.length > 0 && (
              // 목록을 눌러도 입력창이 먼저 blur되어 닫히지 않도록 mousedown 기본 동작을 막는다.
              <ul id="movie-suggestions" role="listbox" className="suggestions" onMouseDown={(event) => event.preventDefault()}>
                {suggestions.map((movie, index) => (
                  <li key={movie.movie_id} id={`suggestion-${index}`} role="option" aria-selected={index === active} className={index === active ? 'active' : undefined}>
                    <a href={movieHref(movie.movie_id)}>
                      <strong>{movie.title}</strong>
                      <small>{formatMeta(movie)}</small>
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <button
            onClick={() => {
              setOpen(false)
              runSearch()
            }}
          >
            검색
          </button>
        </div>

        {loading && <p className="message">영화를 검색하고 있습니다...</p>}

        {error && <p className="error">{error}</p>}
      </section>

      {!loading && !error && searchedQuery !== null && movies.length === 0 && (
        <p className="empty">"{searchedQuery}"에 해당하는 영화가 없습니다. 제목의 일부만 입력해 보세요.</p>
      )}

      {movies.length > 0 && (
        <section className="results-section">
          <h2>검색 결과 {movies.length}건</h2>

          <div className="movie-list">
            {movies.map((movie) => (
              <MovieCard key={movie.movie_id} movie={movie} />
            ))}
          </div>
        </section>
      )}

      {favorites.length > 0 && <MovieSection title="찜한 영화" description="이 브라우저에만 저장됩니다." movies={favorites} />}

      {recent.length > 0 && <MovieSection title="최근 본 영화" movies={recent} />}

      {statistics.status === 'loading' && <p className="message page-message">영화 목록을 불러오는 중...</p>}

      {statistics.status === 'error' && <p className="empty">{statistics.message}</p>}

      {statistics.status === 'ready' && (
        <>
          <dl className="summary">
            <div>
              <dt>영화</dt>
              <dd>{statistics.data.movies.toLocaleString()}편</dd>
            </div>
            <div>
              <dt>리뷰</dt>
              <dd>{statistics.data.reviews.toLocaleString()}건</dd>
            </div>
            <div>
              <dt>전체 평균 평점</dt>
              <dd>{statistics.data.mean_rating.toFixed(2)}</dd>
            </div>
          </dl>

          <MovieSection
            title="평점이 높은 영화"
            description="리뷰 수가 적은 영화의 평균이 튀지 않도록 보정한 평점 순서입니다."
            movies={statistics.data.top_rated}
          />

          <MovieSection title="리뷰가 많은 영화" movies={statistics.data.most_reviewed} />

          <section className="results-section">
            <h2>데이터 한눈에 보기</h2>
            <div className="bar-grid">
              <BarList
                title="리뷰 평점 분포"
                rows={statistics.data.rating_distribution.map((row) => ({ label: `${row.rating.toFixed(1)}점`, count: row.count }))}
              />
              <BarList
                title="장르별 영화 수"
                rows={statistics.data.genres.map((row) => ({ label: row.genre, count: row.count }))}
              />
            </div>
          </section>
        </>
      )}
    </>
  )
}

export default HomePage
