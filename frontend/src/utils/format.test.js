import assert from 'node:assert/strict'
import test from 'node:test'
import { formatDate, formatMeta, formatRating } from './format.js'

test('평점은 자릿수에 맞춰 반올림하고, 없으면 안내 문구를 쓴다', () => {
  assert.equal(formatRating(3.494818652849741), '3.5')
  assert.equal(formatRating(3.494818652849741, 2), '3.49')
  assert.equal(formatRating(0), '0.0', '평점 0은 "없음"이 아니라 실제 값이다')
  assert.equal(formatRating(null), '평점 없음')
  assert.equal(formatRating(undefined), '평점 없음')
})

test('개봉일은 YYYYMMDD를 점으로 나누고, 형식이 다르면 null', () => {
  assert.equal(formatDate('20250326'), '2025.03.26')
  assert.equal(formatDate(null), null)
  assert.equal(formatDate(''), null)
  assert.equal(formatDate('2025'), null)
})

test('메타 문구는 있는 정보만 이어 붙이고, 모두 없으면 안내 문구', () => {
  assert.equal(formatMeta({ genre: '드라마', director: '김형주', release_date: '20250326' }), '드라마 · 김형주 · 2025.03.26')
  assert.equal(formatMeta({ genre: '드라마', director: null, release_date: null }), '드라마')
  assert.equal(formatMeta({ genre: null, director: null, release_date: null }), '상세 정보 없음')
})
