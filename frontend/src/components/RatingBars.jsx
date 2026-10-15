import { useEffect, useState } from 'react'
import { getRatingDistribution } from '../services/api'

// 이 영화의 리뷰 평점 분포를 작은 세로 막대로 보여준다(0.5~5.0, 10칸).
// 평점이 있는 리뷰가 없거나 불러오지 못하면 아무것도 보여주지 않는다.
function RatingBars({ movieId }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    let ignore = false
    getRatingDistribution(movieId)
      .then((result) => {
        if (!ignore) setData(result)
      })
      .catch(() => {})
    return () => {
      ignore = true
    }
  }, [movieId])

  if (!data || data.rated_reviews === 0) return null

  const max = Math.max(1, ...data.distribution.map((row) => row.count))

  return (
    <figure className="histogram">
      <figcaption>리뷰 평점 분포 (평점이 있는 리뷰 {data.rated_reviews}개)</figcaption>
      <div className="histogram-bars">
        {data.distribution.map((row) => (
          <div className="histogram-col" key={row.rating} title={`${row.rating.toFixed(1)}점: ${row.count}개`}>
            <span className="histogram-count">{row.count}</span>
            <span className="histogram-bar" style={{ height: `${(row.count / max) * 100}%` }} />
            <span className="histogram-label">{row.rating.toFixed(1)}</span>
          </div>
        ))}
      </div>
    </figure>
  )
}

export default RatingBars
