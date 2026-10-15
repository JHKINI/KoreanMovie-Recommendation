import { useEffect, useState } from 'react'
import { Meter } from '../components/SimilarityBars'
import { movieHref } from '../hooks/useHashRoute'
import { compareMovies } from '../services/api'
import { formatMeta, formatRating } from '../utils/format'

function MovieColumn({ movie, keywords, common }) {
  return (
    <section className="compare-col">
      <h2><a href={movieHref(movie.movie_id)}>{movie.title}</a></h2>
      <p className="movie-meta">{formatMeta(movie)}</p>
      <dl className="stats">
        <div><dt>평균 평점</dt><dd>{formatRating(movie.mean_rating, 2)}</dd></div>
        <div><dt>보정 평점</dt><dd>{formatRating(movie.corrected_rating, 2)}</dd></div>
        <div><dt>리뷰 수</dt><dd>{movie.review_count}</dd></div>
      </dl>
      <div className="keywords">
        <span className="keywords-title">대표 키워드</span>
        {keywords.length === 0 && <p className="section-note">표시할 키워드가 없습니다.</p>}
        <ul>
          {keywords.map((term) => (
            <li key={term} className={common.includes(term) ? 'keyword-static common' : 'keyword-static'}>{term}</li>
          ))}
        </ul>
      </div>
    </section>
  )
}

// 영화 두 편을 나란히 비교한다: 평점·리뷰 수, 유사도 구성, 대표 키워드와 겹치는 키워드.
function ComparePage({ a, b }) {
  const key = `${a}|${b}`
  const [result, setResult] = useState({ key: null })

  useEffect(() => {
    let ignore = false
    compareMovies(a, b)
      .then((data) => {
        if (!ignore) setResult({ key, data })
      })
      .catch((err) => {
        if (!ignore) setResult({ key, error: err.message })
      })
    return () => {
      ignore = true
    }
  }, [key, a, b])

  if (result.key !== key) return <p className="message page-message">불러오는 중...</p>

  if (result.error) {
    return (
      <div className="page">
        <a className="back-link" href="#/">← 처음으로</a>
        <p className="error">{result.error}</p>
      </div>
    )
  }

  const { data } = result

  return (
    <div className="page">
      <a className="back-link" href={movieHref(data.a.movie_id)}>← {data.a.title} 상세 보기</a>
      <h1 className="page-title">영화 비교</h1>

      <section className="detail-hero">
        <h2>얼마나 비슷할까요?</h2>
        <div className="meters wide">
          <Meter label="정보 유사" value={data.similarity.metadata} />
          <Meter label="리뷰 유사" value={data.similarity.text} />
          <Meter label="종합" value={data.similarity.combined} />
        </div>
        <p className="section-note">
          {data.same_genre ? `같은 장르(${data.a.genre})입니다.` : '장르가 달라 추천 후보는 아니지만, 같은 방식으로 유사도를 계산했습니다.'}
          {data.similarity.director_bonus > 0 && ' 같은 감독의 작품이라 종합 점수에 0.05가 더해졌습니다.'}
        </p>
        {data.common_keywords.length > 0 && (
          <p className="common-note">
            함께 자주 나온 표현: {data.common_keywords.map((term) => (<span className="keyword-static common" key={term}>{term}</span>))}
          </p>
        )}
      </section>

      <div className="compare-grid">
        <MovieColumn movie={data.a} keywords={data.keywords_a} common={data.common_keywords} />
        <MovieColumn movie={data.b} keywords={data.keywords_b} common={data.common_keywords} />
      </div>
    </div>
  )
}

export default ComparePage
