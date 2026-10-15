import { useEffect, useState } from 'react'
import { getStatistics } from '../services/api'

// 첫 화면에 쓸 전체 통계를 한 번 불러온다. 실패해도 검색은 쓸 수 있으므로 오류는 상태로만 둔다.
export function useStatistics() {
  const [state, setState] = useState({ status: 'loading', data: null })

  useEffect(() => {
    let ignore = false
    getStatistics(6)
      .then((data) => {
        if (!ignore) setState({ status: 'ready', data })
      })
      .catch((err) => {
        if (!ignore) setState({ status: 'error', data: null, message: err.message })
      })
    return () => {
      ignore = true
    }
  }, [])

  return state
}
