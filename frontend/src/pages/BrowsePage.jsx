import { useEffect, useState } from 'react'
import MovieCard from '../components/MovieCard'
import { useStatistics } from '../hooks/useStatistics'
import { browseMovies } from '../services/api'

const SORTS = [
  ['rating', '보정 평점'],
  ['reviews', '리뷰 수'],
  ['newest', '개봉일'],
  ['title', '제목'],
]
const PAGE_SIZE = 24

// 전체 영화 둘러보기. 정렬·장르·쪽 번호는 주소(#/browse?...)에 담아 뒤로 가기와 링크 공유가 되게 한다.
function BrowsePage({ query }) {
  const sort = SORTS.some(([value]) => value === query.get('sort')) ? query.get('sort') : 'rating'
  const direction = query.get('dir') ?? (sort === 'title' ? 'asc' : 'desc')
  const genre = query.get('genre') ?? ''
  const director = query.get('director') ?? ''
  const page = Math.max(1, parseInt(query.get('page') ?? '1', 10) || 1)

  const statistics = useStatistics()
  const genres = statistics.status === 'ready' ? statistics.data.genres.filter((row) => row.genre !== '장르 미상') : []

  // 요청 조건을 키로 삼아, 결과의 키가 현재 조건과 다르면 불러오는 중으로 본다(effect 안에서 상태를 먼저 바꾸지 않는다).
  const key = `${sort}|${direction}|${genre}|${director}|${page}`
  const [result, setResult] = useState({ key: null })

  useEffect(() => {
    let ignore = false
    browseMovies({ sort, direction, genre, director, offset: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE })
      .then((data) => {
        if (!ignore) setResult({ key, data })
      })
      .catch((err) => {
        if (!ignore) setResult({ key, error: err.message })
      })
    return () => {
      ignore = true
    }
  }, [key, sort, direction, genre, director, page])

  const update = (changes) => {
    const next = new URLSearchParams(query)
    for (const [name, value] of Object.entries(changes)) {
      if (value === '' || value === null) next.delete(name)
      else next.set(name, value)
    }
    window.location.hash = `#/browse?${next.toString()}`
  }

  const loading = result.key !== key
  const data = loading ? null : result.data
  const lastPage = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : page

  return (
    <div className="page">
      <h1 className="page-title">전체 영화</h1>

      <div className="controls">
        <label>
          정렬
          <select value={sort} onChange={(event) => update({ sort: event.target.value, dir: '', page: '' })}>
            {SORTS.map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>

        <button
          className="tab small"
          onClick={() => update({ dir: direction === 'asc' ? 'desc' : 'asc', page: '' })}
          aria-label="정렬 방향 바꾸기"
        >
          {direction === 'asc' ? '↑ 오름차순' : '↓ 내림차순'}
        </button>

        <label>
          장르
          <select value={genre} onChange={(event) => update({ genre: event.target.value, page: '' })}>
            <option value="">전체</option>
            {genres.map((row) => (
              <option key={row.genre} value={row.genre}>{row.genre} ({row.count})</option>
            ))}
          </select>
        </label>
      </div>

      {director && (
        <p className="active-filter">
          감독: {director}
          <button type="button" aria-label="감독 필터 해제" onClick={() => update({ director: '', page: '' })}>✕</button>
        </p>
      )}

      {sort === 'rating' && <p className="section-note">보정 평점은 리뷰 수가 적은 영화의 평균이 튀지 않도록 조정한 값입니다.</p>}
      {sort === 'newest' && <p className="section-note">개봉일 정보가 없는 영화는 항상 맨 뒤에 나옵니다.</p>}

      {loading && <p className="message page-message">불러오는 중...</p>}
      {!loading && result.error && <p className="error">{result.error}</p>}

      {data && (
        <>
          <p className="hint">
            {data.total === 0
              ? '조건에 맞는 영화가 없습니다.'
              : `전체 ${data.total}편 중 ${data.offset + 1}–${data.offset + data.items.length}번째`}
          </p>

          <div className="movie-list">
            {data.items.map((movie) => (
              <MovieCard key={movie.movie_id} movie={movie} />
            ))}
          </div>

          {data.total > PAGE_SIZE && (
            <nav className="pager" aria-label="쪽 이동">
              <button className="tab small" disabled={page <= 1} onClick={() => update({ page: page - 1 })}>← 이전</button>
              <span>{page} / {lastPage}</span>
              <button className="tab small" disabled={page >= lastPage} onClick={() => update({ page: page + 1 })}>다음 →</button>
            </nav>
          )}
        </>
      )}
    </div>
  )
}

export default BrowsePage
