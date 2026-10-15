import MovieCard from './MovieCard'

// 제목이 있는 영화 카드 묶음. 첫 화면의 "평점 높은 영화" 같은 목록에 쓴다.
function MovieSection({ title, description, movies, action }) {
  return (
    <section className="results-section">
      <h2>{title}</h2>
      {action}
      {description && <p className="section-note">{description}</p>}
      <div className="movie-list">
        {movies.map((movie) => (
          <MovieCard key={movie.movie_id} movie={movie} />
        ))}
      </div>
    </section>
  )
}

export default MovieSection
