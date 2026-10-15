// 백엔드 값을 화면에 보여줄 문자열로 바꾼다. 값이 없으면(null) 빈칸 대신 안내 문구를 쓴다.

export function formatRating(value, digits = 1) {
  return value === null || value === undefined ? '평점 없음' : value.toFixed(digits)
}

// '20250326' -> '2025.03.26'
export function formatDate(value) {
  if (!value || value.length !== 8) return null
  return `${value.slice(0, 4)}.${value.slice(4, 6)}.${value.slice(6, 8)}`
}

// '드라마 · 김형주 · 2025.03.26' 처럼 있는 정보만 이어 붙인다.
export function formatMeta(movie) {
  const parts = [movie.genre, movie.director, formatDate(movie.release_date)].filter(Boolean)
  return parts.length ? parts.join(' · ') : '상세 정보 없음'
}
