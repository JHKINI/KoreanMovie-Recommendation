const API_BASE_URL = 'http://127.0.0.1:8000'

export async function searchMovies(query) {
  const response = await fetch(
    `${API_BASE_URL}/movies?query=${encodeURIComponent(query)}&limit=20`
  )

  if (!response.ok) {
    throw new Error('영화 검색에 실패했습니다.')
  }

  return response.json()
}