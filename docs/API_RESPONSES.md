# API 응답 구조 안내 (프론트용)

기준일: 2026-10-09 · 기준 코드: `api.py` (버전 1.1.0) · 기준 데이터: `20261006_010220_0c0fc253` (영화 214개, 리뷰 26,768건)

아래 JSON 예시는 실제 저장 데이터를 호출해 얻은 값입니다. 서버 실행과 `/docs` 사용법은 [프로젝트_실행방법.txt](../프로젝트_실행방법.txt)를 보세요.

- 기본 주소: `http://127.0.0.1:8000`
- 모든 응답은 JSON(UTF-8)이며 모든 엔드포인트는 `GET`입니다.
- 한글 제목은 URL 인코딩해서 보냅니다. 브라우저는 `fetch`에 `encodeURIComponent(title)`를 쓰거나 `URLSearchParams`를 쓰면 됩니다.
- **CORS:** `localhost:5173`과 `127.0.0.1:5173`(Vite 개발 서버)에서 오는 GET 요청만 허용합니다. 다른 주소에서 호출하려면 `api.py`의 `allow_origins`에 추가하세요.

## 엔드포인트 한눈에 보기

| 용도 | 요청 | 응답 최상위 |
|---|---|---|
| 서버 상태 | `GET /health` | `status`, `data_version`, `movies`, `reviews` |
| 제목 검색 | `GET /movies?query=&limit=` | `count`, `items[]` (영화) |
| 영화 상세 | `GET /movies/detail?title=` | 영화 객체 |
| 추천 | `GET /recommend?title=&top_n=` | `source`, `count`, `items[]` (추천 영화), `message`, `data_version` |
| 리뷰 | `GET /movies/reviews?title=&order=&top_n=` | `movie_id`, `title`, `order`, `count`, `items[]` (리뷰) |
| 대표 키워드 | `GET /keywords?title=&top_n=` | `movie_id`, `title`, `count`, `items[]` (`term`, `score`) |
| 전체 영화 둘러보기 | `GET /movies/browse?sort=&direction=&genre=&offset=&limit=` | `total`, `offset`, `limit`, `items[]` (영화) |
| 키워드로 영화 찾기 | `GET /keywords/movies?term=&limit=` | `term`, `count`, `items[]` (영화 객체 + `keyword_score`) |
| 영화별 평점 분포 | `GET /movies/{movie_id}/ratings` | `movie_id`, `rated_reviews`, `distribution[]` (`rating`, `count`) |
| 취향 추천 | `GET /recommend/taste?movie_ids=A&movie_ids=B&top_n=` | `seeds[]`, `count`, `items[]` (추천 영화), `data_version` |
| 영화 비교 | `GET /compare?a=&b=` | `a`, `b`, `same_genre`, `similarity`, `keywords_a`, `keywords_b`, `common_keywords` |
| 전체 통계 | `GET /statistics?top_n=` | `movies`, `reviews`, `rated_reviews`, `mean_rating`, `genres[]`, `rating_distribution[]`, `top_rated[]`, `most_reviewed[]`, `data_version` |

프론트는 위 5개의 **제목 기반 경로**를 쓰는 것을 권합니다. `/movies/{movie_id}`, `/recommend/{movie_id}`, `/movies/{movie_id}/reviews`는 같은 기능의 ID 경로이며, 슬래시가 들어간 제목은 쓸 수 없습니다.

## 요청 파라미터

| 파라미터 | 사용처 | 규칙 | 기본값 |
|---|---|---|---|
| `query` | `/movies` | 200자 이하. 제목 일부(정규식 아님). 비우면 전체 | `''` |
| `limit` | `/movies` | 1~100 | 20 |
| `title` | detail/recommend/reviews | 필수, 1~200자, **정확한 제목**(앞뒤 공백·대소문자는 무시, 문장부호는 그대로) | - |
| `top_n` | recommend/reviews | 1~20 | 5 |
| `keyword` | reviews | 50자 이하. 이 글자가 들어 있는 리뷰만 조회(대소문자 무시, 정규식 아님). 비우면 필터 없음 | - |
| `sort` | browse | `rating`(보정 평점), `reviews`(리뷰 수), `newest`(개봉일), `title`(제목) | `rating` |
| `direction` | browse | `asc` 또는 `desc`. 동점은 제목 오름차순 | `desc` |
| `genre` | browse | 정확한 장르 이름(예: `드라마`). 비우면 전체 | - |
| `director` | browse | 정확한 감독 이름(공백·대소문자 무시). `genre`와 함께 쓰면 AND | - |
| `offset`, `limit` | browse | `offset` 0 이상, `limit` 1~100 | 0, 24 |
| `movie_ids` | taste | 같은 이름을 2~5번 반복(`movie_ids=a&movie_ids=b`). 영화 ID 사용. 중복은 하나로 봄 | - |
| `a`, `b` | compare | 영화 ID 또는 정확한 제목. 서로 다른 영화여야 함 | - |
| `top_n` | keywords | 1~30 | 10 |
| `top_n` | statistics | 1~20 (`top_rated`, `most_reviewed`의 길이) | 10 |
| `order` | reviews | `high`(높은 평점순) 또는 `low`(낮은 평점순) | `high` |
| `release_date` | detail/recommend/reviews | 선택. `YYYYMMDD` 8자리. 동명이작 구분용 | - |
| `director` | detail/recommend/reviews | 선택. 감독명. 동명이작 구분용 | - |

## 응답 객체

### 영화 객체

`/movies`의 `items[]`, `/movies/detail`의 최상위, `/recommend`의 `source`가 모두 같은 구조입니다.

```json
{
  "movie_id": "movie_007b520990b3d141",
  "title": "승부",
  "genre": "드라마",
  "director": "김형주",
  "release_date": "20250326",
  "age_rating": "12세이상관람가",
  "mean_rating": 3.494818652849741,
  "review_count": 207,
  "rating_count": 193,
  "positive_ratio": 0.7246376811594203,
  "corrected_rating": 3.454136542418352
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `movie_id` | string | 내부 영화 ID. 화면에 보이는 값은 아님 |
| `title` | string | 영화 제목 |
| `genre` | string \| null | 장르(드라마/코미디/멜로/로맨스). **2개 영화는 `null`** |
| `director` | string \| null | 감독. 값이 없으면 `null` |
| `release_date` | string \| null | 개봉일 `YYYYMMDD` 문자열(숫자 아님). 값이 없으면 `null` |
| `age_rating` | string \| null | 관람 등급(예: `12세이상관람가`, `전체관람가`). 값이 없으면 `null` |

`genre`, `director`, `release_date`, `age_rating`은 모두 `null`일 수 있습니다. 현재 데이터에서는 `genre`가 없는 영화 2개(예: "그 시절 우리가 좋아했던 소녀")가 네 필드 모두 `null`입니다.
| `mean_rating` | number \| null | 실제 평균 평점(0.5~5.0 척도). 평점이 전혀 없으면 `null` |
| `review_count` | integer | 보존한 리뷰 수(평점 없는 리뷰 포함) |
| `rating_count` | integer | 평점이 있는 리뷰 수 |
| `positive_ratio` | number \| null | 기존 모델이 예측한 긍정 비율(0~1). 사람의 감성 정답이 아님 |
| `corrected_rating` | number | 리뷰 수로 보정한 평점(`mean_rating`보다 평균 쪽으로 당겨짐). 항상 숫자 |

화면에 평점을 보여줄 때 `mean_rating`은 `null`일 수 있으니 처리가 필요합니다. 현재 데이터에서는 `null`인 영화가 없지만 데이터가 바뀌면 생길 수 있습니다. 소수점은 서버가 자르지 않으므로 화면에서 반올림하세요.

### 추천 항목 (`/recommend`의 `items[]`)

영화 객체의 모든 필드에 아래가 추가됩니다.

```json
{
  "movie_id": "movie_8b86efa23a9eca38",
  "title": "서울의 봄",
  "...영화 객체 필드...": "...",
  "metadata_similarity": 0.9549114944939814,
  "text_similarity": 0.7424872723577483,
  "director_bonus": 0.0,
  "similarity": 0.8274569612122415,
  "final_score": 0.799323498368165,
  "reasons": [
    "같은 장르: 드라마",
    "리뷰 표현 유사도: 0.742",
    "평점 193개를 반영한 보정 평점: 3.802"
  ]
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `metadata_similarity` | number | 등급·관객 수·스크린 수 등 메타데이터 유사도(0~1) |
| `text_similarity` | number | 리뷰 글 표현 유사도(0~1) |
| `director_bonus` | number | 같은 감독이면 `0.05`, 아니면 `0.0` |
| `similarity` | number | `0.4×메타 + 0.6×리뷰 + 감독 보너스`(0~1) |
| `final_score` | number | 최종 점수 `0.7×similarity + 0.3×평점 품질`. **`items[]`는 이 값의 내림차순으로 이미 정렬됨** |
| `reasons` | string[] | 사용자에게 보여줄 수 있는 추천 이유 문장 |

`final_score`와 `similarity`는 정답 확률이나 만족도가 아닙니다. 화면에서 "92% 일치"처럼 퍼센트로 보여주면 오해를 줄 수 있으니, 점수 대신 `reasons` 문장을 쓰는 편이 안전합니다.

### 추천 응답 최상위

```json
{
  "source": { "...영화 객체...": "..." },
  "count": 2,
  "items": [ "...추천 항목..." ],
  "message": null,
  "data_version": "20261006_010220_0c0fc253"
}
```

- `count`는 `items`의 길이입니다. 후보가 적으면 `top_n`보다 작을 수 있습니다.
- `genre`가 `null`인 영화(현재 2개)는 `items`가 빈 배열이고 `message`에 `"장르 정보가 없어 추천 후보를 만들 수 없습니다."`가 들어갑니다. **이 경우도 HTTP 200입니다.** 화면에서 `message`가 `null`이 아닌지 확인하세요.

### 리뷰 응답 (`/movies/reviews`)

```json
{
  "movie_id": "movie_8b86efa23a9eca38",
  "title": "서울의 봄",
  "order": "high",
  "count": 2,
  "items": [
    {
      "movie_id": "movie_8b86efa23a9eca38",
      "review_id": "9197",
      "source_record": 9419,
      "review": "전두광 이름이 아주 적절하네요",
      "rating": 5.0
    }
  ]
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `review_id` | string | 원본의 리뷰 번호(문자열) |
| `source_record` | integer | 원본 CSV의 데이터 레코드 순서. 평점이 같으면 이 순서로 나옴. 작성일이 아님 |
| `review` | string | 리뷰 원문. 길 수 있고 줄바꿈이 있을 수 있음 |
| `rating` | number | 작성자가 준 실제 평점(0.5~5.0) |

- `order=high`는 높은 평점순, `low`는 낮은 평점순입니다. **평점이 없는 리뷰는 이 API에 나오지 않습니다**(원본 336건).
- 작성일이 없으므로 "최신순"으로 표시하면 안 됩니다.
- ID 경로(`/movies/{movie_id}/reviews`)의 응답에는 최상위 `title`이 **없습니다.** 제목 경로(`/movies/reviews`)에만 있습니다.

### 검색 응답 (`/movies`)

```json
{ "count": 1, "items": [ "...영화 객체..." ] }
```

일치하는 영화가 없으면 오류가 아니라 `{"count": 0, "items": []}`(HTTP 200)입니다. `limit` 만큼만 반환하며 전체 개수는 알 수 없습니다.

### 대표 키워드 응답 (`/keywords`)

```json
{
  "movie_id": "movie_8b86efa23a9eca38",
  "title": "서울의 봄",
  "count": 3,
  "items": [
    { "term": "황정민", "score": 0.2461 },
    { "term": "정우성", "score": 0.2158 },
    { "term": "전두환", "score": 0.1893 }
  ]
}
```

위 `score` 값은 모양을 보여주려는 예시이고 실제 값은 호출해서 확인하세요.

- `items`는 `score` 내림차순입니다. `score`는 그 영화의 리뷰에서 얼마나 특징적인 단어인지 나타내는 상대값이라 화면에는 보여주지 않는 것을 권합니다.
- ID 경로(`/movies/{movie_id}/keywords`)도 같은 응답입니다.
- **한계:** 형태소 분석기를 쓰지 않고 한글 2글자 이상 단어를 센 것이라 조사가 붙은 형태("남산의")가 남을 수 있습니다. 원형이 어휘에 함께 있으면 합치고, 영화 제목에 들어 있는 단어는 뺍니다. 특징이 약한 영화는 `items`가 짧거나 비어 있을 수 있습니다.
- 키워드는 서버가 시작할 때 한 번 계산합니다(시작이 약 2초 늘어남).

### 키워드로 영화 찾기 (`/keywords/movies`)

```json
{
  "term": "전두환",
  "count": 2,
  "items": [{ "...영화 객체 필드...": "...", "keyword_score": 0.19 }]
}
```

- 이 단어가 그 영화의 **대표 키워드(상위 15개)** 에 든 영화를 `keyword_score` 내림차순으로 돌려줍니다(동점은 영화 ID 순). `term`은 `/keywords`로 받은 단어 그대로 정확히 일치해야 하며 부분 일치는 찾지 않습니다.
- "리뷰에 한 번이라도 나온 영화"가 아니라 "그 단어가 두드러진 영화"입니다. 그래서 결과가 적거나 비어 있을 수 있고, 비어 있어도 오류가 아니라 `items: []`(HTTP 200)입니다. `limit`은 1~50(기본 12), `term`이 비면 422입니다.
- `keyword_score`는 영화 사이의 상대 비교용이며 화면에 보여주지 않는 것을 권합니다.

### 전체 통계 응답 (`/statistics`)

```json
{
  "movies": 214,
  "reviews": 26768,
  "rated_reviews": 26432,
  "mean_rating": 3.0615541767554477,
  "genres": [{ "genre": "드라마", "count": 163 }, { "genre": "장르 미상", "count": 2 }],
  "rating_distribution": [{ "rating": 0.5, "count": 1105 }, "...1.0부터 5.0까지 0.5 간격, 항상 10개..."],
  "top_rated": ["...영화 객체..."],
  "most_reviewed": ["...영화 객체..."],
  "data_version": "20261006_010220_0c0fc253"
}
```

- `top_rated`는 리뷰 수를 반영한 **보정 평점(`corrected_rating`)** 내림차순, `most_reviewed`는 `review_count` 내림차순입니다.
- `rating_distribution`은 평점이 있는 리뷰만 센 것이라 합계가 `rated_reviews`와 같고 `reviews`와는 다를 수 있습니다.
- 장르 정보가 없는 영화는 `genres`에서 `"장르 미상"`으로 묶입니다. `mean_rating`은 영화별 평균이 아니라 모든 리뷰 평점의 평균입니다.

### 전체 영화 둘러보기 (`/movies/browse`)

```json
{ "total": 214, "offset": 0, "limit": 24, "items": ["...영화 객체..."] }
```

- `total`은 장르 필터를 적용한 **전체** 개수이고 `offset`, `limit`과 무관합니다. 마지막 쪽 번호는 `ceil(total / limit)`입니다.
- `sort=rating`은 리뷰 수를 반영한 보정 평점(`corrected_rating`) 기준입니다. `newest`는 개봉일이며 **개봉일이 없는 영화는 `direction`과 상관없이 맨 뒤**에 옵니다.
- 범위를 넘는 `offset`은 오류가 아니라 빈 `items`(HTTP 200)입니다. 잘못된 `sort`, 음수 `offset`, 범위 밖 `limit`은 422입니다.

같은 감독의 영화를 찾으려면 `director`를 쓰세요(`/movies/browse?director=홍상수&sort=newest`). 결과에 기준 영화 자신도 포함되므로 화면에서 빼야 합니다.

### 영화별 평점 분포 (`/movies/{movie_id}/ratings`)

```json
{
  "movie_id": "movie_007b520990b3d141",
  "rated_reviews": 193,
  "distribution": [{ "rating": 0.5, "count": 1 }, "...1.0부터 5.0까지 0.5 간격, 항상 10개..."]
}
```

- 평점이 있는 리뷰만 센 것이라 `rated_reviews`는 영화 객체의 `rating_count`와 같고, 분포의 합과도 같습니다. 분포로 다시 계산한 평균은 `mean_rating`과 일치합니다(자동 테스트로 확인).
- 평점이 없는 영화는 `rated_reviews`가 0이고 `count`가 모두 0인 10칸입니다. 존재하지 않는 영화는 404입니다.

### 취향 추천 (`/recommend/taste`)

```json
{
  "seeds": ["...고른 영화 객체..."],
  "count": 5,
  "items": [
    {
      "...영화 객체 필드...": "...",
      "similarity": 0.8209,
      "final_score": 0.7496,
      "seed_similarities": [
        { "movie_id": "movie_8b86efa23a9eca38", "title": "서울의 봄", "similarity": 0.8204 },
        { "movie_id": "movie_007b520990b3d141", "title": "승부", "similarity": 0.8078 }
      ],
      "reasons": ["유사한 영화: '서울의 봄' (유사도 0.820)", "유사한 영화: '승부' (유사도 0.808)", "평점 202개를 반영한 보정 평점: 3.262"]
    }
  ],
  "data_version": "20261006_010220_0c0fc253"
}
```

위 숫자는 모양을 보여 주는 예시입니다.

- 후보의 `similarity`는 **고른 영화 각각과의 유사도의 평균**이고, `seed_similarities`가 그 구성(높은 순)입니다. 이후 계산은 일반 추천과 같습니다(유사도 상위 20개 → 0.7×유사도 + 0.3×평점으로 재정렬).
- 후보는 고른 영화들이 속한 장르의 영화이며, 고른 영화는 결과에서 빠집니다. 장르가 다른 영화를 섞어 고르면 장르의 합집합이 후보입니다. 장르 정보가 없는 영화만 고르면 `items`가 빈 배열(200)입니다.
- 영화가 2편 미만이거나 5편 초과면 422, 존재하지 않는 ID가 있으면 404입니다. (같은 ID를 반복해 넣으면 하나로 세어 2편 미만이 될 수 있습니다.)
- 일반 추천 항목과 달리 `metadata_similarity`, `text_similarity`, `director_bonus`는 없습니다.

### 영화 비교 (`/compare`)

```json
{
  "a": "...영화 객체...",
  "b": "...영화 객체...",
  "same_genre": true,
  "similarity": { "metadata": 0.95, "text": 0.74, "director_bonus": 0.0, "combined": 0.83 },
  "keywords_a": ["유아인", "이병헌", "대결"],
  "keywords_b": ["황정민", "정우성", "대결"],
  "common_keywords": ["대결"]
}
```

- `similarity`는 추천에 쓰는 것과 같은 계산(`combined` = 0.4×`metadata` + 0.6×`text` + `director_bonus`)입니다. 장르가 달라도 계산하지만 그 경우 추천 후보가 아니므로 `same_genre`로 알립니다.
- `a`와 `b`가 같은 영화면 422입니다.

### 상태 확인 (`/health`)

```json
{ "status": "ok", "data_version": "20261006_010220_0c0fc253", "movies": 214, "reviews": 26768 }
```

## 오류 응답

| 코드 | 언제 | `detail` 모양 |
|---|---|---|
| 404 | 제목에 맞는 영화가 없음, 또는 조건(`release_date`/`director`)에 맞는 영화가 없음 | 문자열 |
| 409 | 같은 제목의 작품이 여러 개 | 객체 `{message, candidates[]}` |
| 422 | 파라미터 규칙 위반(범위 초과, 날짜 형식, `order` 값 등), 빈 `title` | 배열(FastAPI 기본 형식) |

`detail`의 타입이 코드마다 다릅니다(문자열/객체/배열). 화면에서 오류 문구를 보여줄 때 `typeof detail`로 분기해야 합니다.

**404**

```json
{ "detail": "조건에 맞는 영화 제목을 찾을 수 없습니다." }
```

**422** (예: `top_n=99`)

```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["query", "top_n"],
      "msg": "Input should be less than or equal to 20",
      "input": "99",
      "ctx": { "le": 20 }
    }
  ]
}
```

`loc`의 마지막 값이 잘못된 파라미터 이름입니다. `msg`는 영어이므로 사용자에게는 직접 만든 한국어 문구를 보여주세요.

**409** (코드 기준)

```json
{
  "detail": {
    "message": "같은 제목의 작품이 여러 개입니다. release_date 또는 director를 추가하세요.",
    "candidates": [ "...영화 객체(제목·감독·개봉일 포함)..." ]
  }
}
```

현재 저장 데이터에는 제목이 겹치는 영화가 없어서 **실제 데이터로는 409를 재현하지 못했습니다.** 가상 데이터로 하는 자동 테스트에서만 확인된 동작이며, 위 모양은 `api.py` 코드를 읽고 적은 것입니다. 후보를 고른 뒤 같은 요청에 `release_date`(또는 `director`)를 붙여 다시 호출하면 됩니다.

## 화면을 만들 때 참고

- 검색 → 카드 클릭 → 상세/추천/리뷰 순서로 이어지는 화면이면, 검색 결과의 `title`을 그대로 `title` 파라미터에 넣어도 됩니다. 단, 동명이작이 생기면 409가 나므로 처리할 자리를 마련해 두세요.
- 서버는 시작할 때 데이터를 한 번 읽습니다. 데이터를 다시 준비한 뒤에는 서버를 재시작해야 새 값이 보입니다. `data_version`으로 확인할 수 있습니다.
- 응답 크기가 작아(요청당 수 KB) 별도의 페이지네이션은 없습니다. `top_n`은 최대 20, `limit`은 최대 100입니다.
- 이 문서의 예시는 `fastapi.testclient`로 실제 호출한 결과입니다. 브라우저 `fetch`로 호출해 보지는 않았습니다.
