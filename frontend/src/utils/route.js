// 주소(#...)를 읽고 만드는 순수 함수. React에 의존하지 않아 단독으로 테스트할 수 있다.
// 주소 예: '#/movie/<ID>', '#/browse?sort=reviews&page=2', '#/taste', '#/compare/<A>/<B>', '#/keyword/<단어>'.
// 목록의 정렬·장르·쪽 번호처럼 공유할 만한 상태는 query에 담아 뒤로 가기로 복원된다.
export function parseHash(hash) {
  const [path, queryString = ''] = hash.replace(/^#/, '').split('?')
  const query = new URLSearchParams(queryString)
  const parts = path.split('/').filter(Boolean).map(decodeURIComponent)

  if (parts[0] === 'movie' && parts[1]) return { name: 'movie', movieId: parts[1], query }
  if (parts[0] === 'compare' && parts[1] && parts[2]) return { name: 'compare', a: parts[1], b: parts[2], query }
  if (parts[0] === 'keyword' && parts[1]) return { name: 'keyword', term: parts[1], query }
  if (parts[0] === 'browse') return { name: 'browse', query }
  if (parts[0] === 'taste') return { name: 'taste', query }
  return { name: 'home', query }
}

export const movieHref = (movieId) => `#/movie/${encodeURIComponent(movieId)}`
export const compareHref = (a, b) => `#/compare/${encodeURIComponent(a)}/${encodeURIComponent(b)}`
export const keywordHref = (term) => `#/keyword/${encodeURIComponent(term)}`
export const browseHref = (params) => `#/browse?${new URLSearchParams(params).toString()}`
