import assert from 'node:assert/strict'
import test, { beforeEach } from 'node:test'

// localStorage가 없는 Node에서 테스트하려고 window.localStorage를 흉내 낸다.
let store
let failWrites
beforeEach(() => {
  store = new Map()
  failWrites = false
  globalThis.window = {
    localStorage: {
      getItem: (key) => (store.has(key) ? store.get(key) : null),
      setItem: (key, value) => {
        if (failWrites) throw new Error('quota')
        store.set(key, value)
      },
    },
  }
})

const { isFavorite, loadFavorites, loadRecent, pushRecent, toggleFavorite } = await import('./storage.js')
const movie = (id) => ({ movie_id: id, title: `영화 ${id}` })
const ids = (list) => list.map((item) => item.movie_id)

test('찜하기는 켜고 끄기를 번갈아 하고 바뀐 상태를 돌려준다', () => {
  assert.equal(isFavorite('a'), false)
  assert.equal(toggleFavorite(movie('a')), true)
  assert.equal(isFavorite('a'), true)
  assert.equal(toggleFavorite(movie('a')), false)
  assert.equal(isFavorite('a'), false)
})

test('찜한 영화는 최근에 찜한 것이 앞에 오고 50개까지만 보관한다', () => {
  for (let index = 0; index < 55; index += 1) toggleFavorite(movie(String(index)))
  const list = loadFavorites()
  assert.equal(list.length, 50)
  assert.equal(list[0].movie_id, '54')
})

test('최근 본 영화는 맨 앞에 두고 중복을 없애며 최대 개수를 지킨다', () => {
  for (const id of ['a', 'b', 'c']) pushRecent(movie(id))
  pushRecent(movie('a'))
  assert.deepEqual(ids(loadRecent()), ['a', 'c', 'b'])
  for (let index = 0; index < 20; index += 1) pushRecent(movie(`n${index}`), 8)
  assert.equal(loadRecent().length, 8)
})

test('저장된 값이 깨져 있으면 빈 목록으로 본다', () => {
  store.set('movie.favorites', '{not json')
  assert.deepEqual(loadFavorites(), [])
  store.set('movie.recent', '{"not":"a list"}')
  assert.deepEqual(loadRecent(), [])
})

test('저장소에 쓸 수 없어도 오류 없이 넘어간다', () => {
  failWrites = true
  assert.doesNotThrow(() => pushRecent(movie('a')))
  assert.doesNotThrow(() => toggleFavorite(movie('a')))
  assert.deepEqual(loadRecent(), [])
})
