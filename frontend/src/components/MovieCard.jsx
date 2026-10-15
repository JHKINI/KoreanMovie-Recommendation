import { movieHref } from '../hooks/useHashRoute'
import { formatMeta, formatRating } from '../utils/format'
import SimilarityBars from './SimilarityBars'

// 영화 한 편을 보여주는 카드. 누르면 상세 화면으로 이동한다.
// 추천 항목이면 추천 이유(reasons)와 유사도 막대를 함께 보여주고, children은 카드 맨 아래에 붙는다.
function MovieCard({ movie, reasons, children }) {
  return (
    <a className="movie-card" href={movieHref(movie.movie_id)}>
      <h3>{movie.title}</h3>
      <p className="movie-meta">{formatMeta(movie)}</p>
      <p className="movie-stats">
        <span className="rating">⭐ {formatRating(movie.mean_rating)}</span>
        <span className="review-count">리뷰 {movie.review_count}개</span>
      </p>
      {movie.metadata_similarity !== undefined && <SimilarityBars item={movie} />}
      {reasons && reasons.length > 0 && (
        <ul className="reasons">
          {reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}
      {children}
    </a>
  )
}

export default MovieCard
