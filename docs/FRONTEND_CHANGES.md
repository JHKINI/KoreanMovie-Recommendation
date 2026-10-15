# 프론트엔드 변경 요약 (팀원 코드와 합칠 때 참고)

기준일: 2026-10-11

`frontend/`는 팀원 저장소(`JHKINI/KoreanMovie-Recommendation`, 커밋 `93b4512` "docs: add frontend progress status")의
`frontend/`를 받아 이어서 개발한 것입니다. 이 문서는 **어디가 팀원 원본이고 무엇을 바꿨는지**를 적어, 합칠 때 충돌과 누락을 줄이기 위한 것입니다.
팀원의 `frontend/FRONTEND_STATUS.md`와 `frontend/README.md`는 수정하지 않았습니다.

React 19 + Vite 8, 새 라이브러리는 추가하지 않았습니다(`package-lock.json` 변경 없음). `package.json`에는 `"test": "node --test"` 스크립트 한 줄만 추가했습니다.
실행: 백엔드를 켠 뒤 `npm.cmd ci --ignore-scripts`(처음 한 번), `npm.cmd run dev -- --host 127.0.0.1`. 프로젝트 루트의 `run.bat`이 둘 다 켭니다.

## 화면(주소)

라우터 라이브러리 없이 주소의 `#`(해시)를 직접 읽습니다(`hooks/useHashRoute.js`). 정렬·장르·쪽 번호는 주소에 담겨 뒤로 가기와 링크 공유가 됩니다.

| 주소 | 화면 | 쓰는 API |
|---|---|---|
| `#/` | 홈: 검색(자동완성), 찜한 영화, 최근 본 영화, 요약 수치, 평점 높은/리뷰 많은 영화, 평점·장르 분포 | `/movies`, `/statistics` |
| `#/movie/<영화ID>` | 상세: 정보, 평점 분포, 대표 키워드, 비슷한 영화(추천 근거 막대), 리뷰(정렬·키워드 필터), 같은 감독의 다른 영화, 찜하기 | `/movies/{id}`, `/recommend/{id}`, `/movies/{id}/reviews`, `/movies/{id}/keywords`, `/movies/{id}/ratings`, `/movies/browse` |
| `#/browse?sort=&dir=&genre=&page=` | 전체 영화: 정렬, 장르 필터, 24개씩 쪽 이동 | `/movies/browse`, `/statistics`(장르 목록) |
| `#/taste` | 취향 추천: 영화 2~5편을 골라 종합 추천 | `/movies`, `/recommend/taste` |
| `#/compare/<A>/<B>` | 영화 두 편 비교 | `/compare` |
| `#/keyword/<단어>` | 그 단어가 대표 키워드로 두드러진 영화 목록. 영화 상세의 리뷰 탭에서 키워드를 고르면 링크가 나옴 | `/keywords/movies` |

상세 화면의 리뷰 탭에는 단어를 직접 입력하는 **리뷰 검색**이 있고, 둘러보기는 `director=` 주소 값으로 감독 필터를 지원합니다(상세의 "이 감독의 영화 모두 보기"에서 이동).

응답 형식은 [API_RESPONSES.md](API_RESPONSES.md)에 있습니다.

## 파일별 변경

팀원 원본 `src/` 파일은 `App.jsx`, `App.css`, `index.css`, `main.jsx`, `services/api.js`와 에셋뿐이었습니다.

| 파일 | 상태 | 내용 |
|---|---|---|
| `src/App.jsx` | **전면 교체** | 128줄 화면 전체를 45줄 껍데기로 줄임. 내비게이션과 주소별 화면 선택만 함. 팀원의 검색 화면은 `pages/HomePage.jsx`로 옮김 |
| `src/services/api.js` | **확장** | 원본의 `searchMovies`는 유지(`limit` 인자 추가). 나머지 호출 함수, 오류 문구 처리, `VITE_API_BASE_URL` 환경 변수 추가 |
| `src/App.css` | **끝에 덧붙임** | 원본 95줄은 그대로. 원본에 없던 카드·결과 목록 스타일 포함. `.app`에 밝은 색상 변수를 고정(`index.css`의 다크 모드 변수 때문에 제목이 안 보이는 문제 방지) |
| `index.html` | 수정 | `lang="ko"`, `<title>한국 영화 추천</title>` |
| `src/index.css`, `src/main.jsx`, `public/`, `assets/` | 그대로 | |
| `src/pages/` (6개) | 신규 | HomePage, MovieDetailPage, BrowsePage, TastePage, ComparePage, KeywordPage |
| `src/components/` (9개) | 신규 | MovieCard, MovieSection, BarList, KeywordChips, RatingBars, SameDirector, FavoriteButton, SimilarityBars, ErrorBoundary |
| `src/hooks/` (3개) | 신규 | useHashRoute, useMovieSearch, useStatistics |
| `src/utils/` (3개 + 테스트 3개) | 신규 | format(평점·날짜·메타 문구), storage(찜·최근 목록), route(주소 해석). 각각 `*.test.js`가 있음 |
| `package.json` | 한 줄 추가 | `"test": "node --test"` (Node 내장 테스트 러너, 라이브러리 추가 없음) |

## 설계 메모

- **null 처리:** 장르·감독·개봉일이 없는 영화(현재 2편)와 평점이 없는 영화는 빈칸 대신 "상세 정보 없음", "평점 없음"으로 보입니다(`utils/format.js`).
- **화면 오류 대응:** 화면을 그리는 중 예외가 나면 `ErrorBoundary`가 안내 문구와 복귀 링크를 보여줍니다(흰 화면 방지). 주소가 바뀌면 오류 상태가 풀립니다. 임시로 예외를 일으켜 동작을 확인했습니다.
- **자동완성:** 입력이 250ms 멈추면 6개까지 제안하고, 위/아래 화살표·Enter·Esc로 조작합니다(`role="combobox"`/`listbox`).
- **개인 목록:** 찜한 영화와 최근 본 영화는 브라우저 `localStorage`에만 저장되며 서버로 가지 않습니다. 저장소를 못 쓰는 환경에서도 오류 없이 빈 목록처럼 동작합니다.
- **상태 초기화:** 상세·비교 화면은 영화가 바뀌면 `key`로 새로 만들어, 이전 영화의 상태가 남지 않습니다. 목록 화면은 요청 조건을 키로 삼아 로딩 여부를 계산합니다(React 19 린트 규칙 `set-state-in-effect`를 지키기 위함).
- **검색 상태:** `useMovieSearch`는 `App`에서 한 번만 만들어 홈에 내려주므로, 상세에 갔다 돌아와도 검색 결과가 유지됩니다.
- **추천 점수:** 화면에 퍼센트로 보여주지 않고, 추천 이유 문장과 유사도 막대(정보 유사/리뷰 유사)로 보여줍니다. 점수는 만족도를 보장하지 않기 때문입니다.

## 합칠 때 확인할 것

1. 팀원이 `App.jsx`나 `App.css`를 그 사이에 수정했다면 충돌이 납니다. `App.jsx`는 위 구조로 옮기고, 팀원의 변경은 `pages/HomePage.jsx`에 반영하는 것을 권합니다.
2. 백엔드에 **CORS**가 필요합니다. `api.py`에 `localhost:5173`, `127.0.0.1:5173`의 GET만 허용하도록 넣어 두었습니다. 팀원의 백엔드에 이미 CORS가 있다면 한쪽으로 통일하세요.
3. 새 화면은 새 API(`/statistics`, `/keywords`, `/movies/browse`, `/recommend/taste`, `/compare`, `/movies/{id}/ratings`)를 씁니다. **백엔드도 함께 합쳐야 합니다.**
4. `npm run lint`, `npm test`(16개), `npm run build`를 통과합니다. 테스트는 순수 로직(포맷, 주소 해석, 찜·최근 목록 저장)만 검사하며, **화면(컴포넌트) 테스트는 없습니다.** 일부러 코드를 망가뜨려(찜 한도, 비교 주소 검사) 테스트가 실패하는 것도 확인했습니다.
5. GitHub Actions(`.github/workflows/test.yml`)에 프론트 검사 작업(`frontend`)을 추가했지만 GitHub에서 실행해 보지는 못했습니다. 이 저장소 구조(프론트가 `frontend/` 아래)가 팀원 저장소와 같으니 위치는 그대로 쓸 수 있습니다.

## 확인한 범위와 한계

- 브라우저 DOM 검사와 스크린샷으로 확인했습니다: 모든 화면의 동작, 오류 안내, 가로 넘침(모바일 폭 375px 기준 없음).
- 스크린샷은 일부 화면만 눈으로 봤고, 태블릿 폭과 다른 브라우저(Safari 등)는 확인하지 않았습니다.
- 접근성(키보드 이동, 스크린 리더)은 기본적인 `aria-` 속성만 넣었고 점검하지 않았습니다.
- 개발 서버(StrictMode)에서는 요청이 두 번씩 나갑니다. 빌드한 결과에서는 한 번입니다.
