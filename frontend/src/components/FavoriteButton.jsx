import { useState } from 'react'
import { isFavorite, toggleFavorite } from '../utils/storage'

// 찜하기. 이 브라우저에만 저장된다. 영화가 바뀌면 상세 화면이 새로 만들어지므로 초기값만 읽으면 된다.
function FavoriteButton({ movie }) {
  const [favorite, setFavorite] = useState(() => isFavorite(movie.movie_id))

  return (
    <button
      type="button"
      className={favorite ? 'fav-button active' : 'fav-button'}
      aria-pressed={favorite}
      onClick={() => setFavorite(toggleFavorite(movie))}
    >
      {favorite ? '★ 찜함' : '☆ 찜하기'}
    </button>
  )
}

export default FavoriteButton
