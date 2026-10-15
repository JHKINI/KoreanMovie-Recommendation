import { useEffect, useState } from 'react'
import { getKeywords } from '../services/api'

// 이 영화의 리뷰에서 특징적으로 자주 나온 단어. 누르면 그 단어가 들어간 리뷰만 보여주도록 onSelect를 부른다.
// 키워드가 없거나 불러오지 못하면 아무것도 보여주지 않는다.
function KeywordChips({ movieId, selected, onSelect }) {
  const [items, setItems] = useState([])

  useEffect(() => {
    let ignore = false
    getKeywords(movieId)
      .then((data) => {
        if (!ignore) setItems(data.items)
      })
      .catch(() => {})
    return () => {
      ignore = true
    }
  }, [movieId])

  if (items.length === 0) return null

  return (
    <div className="keywords">
      <span className="keywords-title">리뷰에서 자주 나온 표현 · 누르면 그 단어가 들어간 리뷰를 봅니다</span>
      <ul>
        {items.map((item) => (
          <li key={item.term}>
            <button
              type="button"
              className={selected === item.term ? 'keyword-chip active' : 'keyword-chip'}
              onClick={() => onSelect(selected === item.term ? '' : item.term)}
            >
              {item.term}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default KeywordChips
