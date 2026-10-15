import { useEffect, useState } from 'react'
import { browseHref } from '../hooks/useHashRoute'
import { browseMovies } from '../services/api'
import MovieSection from './MovieSection'

// 같은 감독의 다른 영화. 감독 정보가 없거나 다른 작품이 없으면 아무것도 보여주지 않는다.
function SameDirector({ movie }) {
  const [movies, setMovies] = useState([])

  useEffect(() => {
    if (!movie.director) return undefined
    let ignore = false
    browseMovies({ director: movie.director, sort: 'newest', limit: 13 })
      .then((data) => {
        if (!ignore) setMovies(data.items.filter((item) => item.movie_id !== movie.movie_id))
      })
      .catch(() => {})
    return () => {
      ignore = true
    }
  }, [movie.director, movie.movie_id])

  if (movies.length === 0) return null

  return (
    <MovieSection
      title={`${movie.director} 감독의 다른 영화`}
      movies={movies}
      action={
        <a className="section-link" href={browseHref({ director: movie.director, sort: 'newest' })}>
          이 감독의 영화 모두 보기 →
        </a>
      }
    />
  )
}

export default SameDirector
