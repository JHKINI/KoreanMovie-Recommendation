import assert from 'node:assert/strict'
import test from 'node:test'
import { browseHref, compareHref, keywordHref, movieHref, parseHash } from './route.js'

test('빈 주소와 알 수 없는 주소는 홈', () => {
  assert.equal(parseHash('').name, 'home')
  assert.equal(parseHash('#/').name, 'home')
  assert.equal(parseHash('#/없는/화면').name, 'home')
})

test('영화 상세 주소에서 ID를 꺼낸다(인코딩 포함)', () => {
  assert.equal(parseHash('#/movie/movie_007b').name, 'movie')
  assert.equal(parseHash('#/movie/movie_007b').movieId, 'movie_007b')
  assert.equal(parseHash('#/movie/%EC%8A%B9%EB%B6%80').movieId, '승부')
  assert.equal(parseHash('#/movie').name, 'home', 'ID가 없으면 홈')
})

test('비교 주소는 두 ID가 모두 있어야 한다', () => {
  const route = parseHash('#/compare/a/b')
  assert.equal(route.name, 'compare')
  assert.equal(route.a, 'a')
  assert.equal(route.b, 'b')
  assert.equal(parseHash('#/compare/a').name, 'home')
})

test('전체 영화 주소의 query를 읽는다', () => {
  const route = parseHash('#/browse?sort=reviews&dir=asc&genre=%EC%BD%94%EB%AF%B8%EB%94%94&page=2')
  assert.equal(route.name, 'browse')
  assert.equal(route.query.get('sort'), 'reviews')
  assert.equal(route.query.get('dir'), 'asc')
  assert.equal(route.query.get('genre'), '코미디')
  assert.equal(route.query.get('page'), '2')
  assert.equal(route.query.get('missing'), null)
  assert.equal(parseHash('#/browse').name, 'browse')
})

test('취향 추천 주소', () => {
  assert.equal(parseHash('#/taste').name, 'taste')
})

test('만든 주소를 다시 읽으면 원래 값이 나온다', () => {
  const tricky = 'id with/slash?and#hash 한글'
  assert.equal(parseHash(movieHref(tricky)).movieId, tricky)
  const compare = parseHash(compareHref('a/b', 'c d'))
  assert.equal(compare.a, 'a/b')
  assert.equal(compare.b, 'c d')
})

test('키워드 주소는 한글 단어를 인코딩해서 만들고 다시 읽는다', () => {
  assert.equal(keywordHref('자본주의'), '#/keyword/%EC%9E%90%EB%B3%B8%EC%A3%BC%EC%9D%98')
  const route = parseHash(keywordHref('자본주의'))
  assert.equal(route.name, 'keyword')
  assert.equal(route.term, '자본주의')
  assert.equal(parseHash('#/keyword').name, 'home', '단어가 없으면 홈')
})

test('둘러보기 주소를 만들면 파라미터가 query로 읽힌다', () => {
  const route = parseHash(browseHref({ director: '홍상수', sort: 'newest' }))
  assert.equal(route.name, 'browse')
  assert.equal(route.query.get('director'), '홍상수')
  assert.equal(route.query.get('sort'), 'newest')
})
