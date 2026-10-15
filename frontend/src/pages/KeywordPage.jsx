import { useEffect, useState } from 'react'
import MovieSection from '../components/MovieSection'
import { getMoviesByKeyword } from '../services/api'

// 어떤 단어가 대표 키워드로 두드러진 영화들. 영화 상세의 리뷰 탭에서 키워드를 고르면 들어올 수 있다.
function KeywordPage({ term }) {
  const [result, setResult] = useState({ term: null })

  useEffect(() => {
    let ignore = false
    getMoviesByKeyword(term)
      .then((data) => {
        if (!ignore) setResult({ term, data })
      })
      .catch((err) => {
        if (!ignore) setResult({ term, error: err.message })
      })
    return () => {
      ignore = true
    }
  }, [term])

  const loading = result.term !== term

  return (
    <div className="page">
      <a className="back-link" href="#/browse">← 전체 영화</a>
      <h1 className="page-title">"{term}" 키워드가 두드러진 영화</h1>
      <p className="section-note">리뷰에서 이 단어가 특징적으로 자주 나온 영화입니다. 리뷰 글을 단어 단위로 센 값이라 뜻이 다른 같은 단어도 함께 나올 수 있습니다.</p>

      {loading && <p className="message page-message">불러오는 중...</p>}
      {!loading && result.error && <p className="error">{result.error}</p>}
      {!loading && result.data && result.data.items.length === 0 && (
        <p className="empty">이 단어가 대표 키워드에 든 영화가 없습니다. 영화 상세에서 보이는 키워드를 눌러 들어와 보세요.</p>
      )}
      {!loading && result.data && result.data.items.length > 0 && (
        <MovieSection title={`${result.data.count}편`} movies={result.data.items} />
      )}
    </div>
  )
}

export default KeywordPage
