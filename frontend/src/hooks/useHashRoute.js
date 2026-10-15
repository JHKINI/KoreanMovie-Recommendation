import { useSyncExternalStore } from 'react'
import { parseHash } from '../utils/route'

export { browseHref, compareHref, keywordHref, movieHref } from '../utils/route'

function subscribe(callback) {
  window.addEventListener('hashchange', callback)
  return () => window.removeEventListener('hashchange', callback)
}

const getHash = () => window.location.hash

// 현재 주소를 { name, ..., query }로 돌려준다. 라우터 라이브러리 없이 쓰는 간단한 해시 라우팅.
export function useHashRoute() {
  return parseHash(useSyncExternalStore(subscribe, getHash))
}
