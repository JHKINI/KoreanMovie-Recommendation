// 브라우저(localStorage)에만 저장하는 개인 목록: 찜한 영화, 최근 본 영화. 서버로 보내지 않는다.
// 저장소를 쓸 수 없는 환경(사생활 보호 모드 등)에서는 조용히 빈 목록처럼 동작한다.
const FAVORITES = 'movie.favorites'
const RECENT = 'movie.recent'

function load(key) {
  try {
    const value = JSON.parse(window.localStorage.getItem(key))
    return Array.isArray(value) ? value : []
  } catch {
    return []
  }
}

function save(key, list) {
  try {
    window.localStorage.setItem(key, JSON.stringify(list))
  } catch {
    // 저장하지 못해도 화면은 계속 동작한다.
  }
}

export const loadFavorites = () => load(FAVORITES)
export const loadRecent = () => load(RECENT)
export const isFavorite = (movieId) => load(FAVORITES).some((movie) => movie.movie_id === movieId)

// 찜 상태를 뒤집고 바뀐 상태(true=찜함)를 돌려준다.
export function toggleFavorite(movie) {
  const list = load(FAVORITES)
  const exists = list.some((item) => item.movie_id === movie.movie_id)
  save(FAVORITES, exists ? list.filter((item) => item.movie_id !== movie.movie_id) : [movie, ...list].slice(0, 50))
  return !exists
}

// 최근 본 영화를 맨 앞에 두고, 같은 영화는 하나만 남기며, 최대 max개만 보관한다.
export function pushRecent(movie, max = 8) {
  const rest = load(RECENT).filter((item) => item.movie_id !== movie.movie_id)
  save(RECENT, [movie, ...rest].slice(0, max))
}
