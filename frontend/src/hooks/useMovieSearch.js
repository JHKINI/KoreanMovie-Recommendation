import { useEffect, useState } from 'react'
import { searchMovies } from '../services/api'

// 검색 상태. App에서 한 번만 만들어 홈 화면에 내려주므로, 상세 화면에 갔다 돌아와도 결과가 유지된다.
export function useMovieSearch() {
  const [query, setQuery] = useState('')
  const [movies, setMovies] = useState([])
  const [searchedQuery, setSearchedQuery] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [suggested, setSuggested] = useState({ keyword: '', items: [] })

  // 자동완성: 입력이 250ms 멈추면 제목 일부로 6개까지 찾는다. 이전 요청의 늦은 응답은 버린다.
  useEffect(() => {
    const keyword = query.trim()
    if (!keyword) return undefined
    let ignore = false
    const timer = setTimeout(() => {
      searchMovies(keyword, 6)
        .then((data) => {
          if (!ignore) setSuggested({ keyword, items: data.items })
        })
        .catch(() => {})
    }, 250)
    return () => {
      ignore = true
      clearTimeout(timer)
    }
  }, [query])

  // 현재 입력과 같은 검색어의 결과일 때만 보여준다(입력을 지우면 곧바로 사라진다).
  const suggestions = query.trim() && suggested.keyword === query.trim() ? suggested.items : []

  const search = async () => {
    const keyword = query.trim()
    if (!keyword) {
      setError('영화 제목을 입력해주세요.')
      return
    }

    try {
      setLoading(true)
      setError('')
      const data = await searchMovies(keyword)
      setMovies(data.items ?? [])
      setSearchedQuery(keyword)
    } catch (err) {
      setError(err.message)
      setMovies([])
      setSearchedQuery(null)
    } finally {
      setLoading(false)
    }
  }

  return { query, setQuery, movies, searchedQuery, loading, error, search, suggestions }
}
