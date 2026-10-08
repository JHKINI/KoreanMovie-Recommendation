# Frontend 진행사항

## 1. 프로젝트 기본 정보

- 프로젝트: NSMC 한국 영화 추천 시스템
- Frontend: React + Vite
- Backend: FastAPI
- Frontend 위치: `NSMC/frontend/`
- Frontend 개발 서버: `http://localhost:5173`
- Backend API 서버: `http://127.0.0.1:8000`

## 2. 현재까지 완료

### React 프로젝트
- [x] `frontend/` 디렉터리 생성
- [x] Vite + React 프로젝트 생성
- [x] ESLint 설정
- [x] npm 설치 및 실행 확인

### 기본 화면
- [x] 기본 Vite 화면 제거
- [x] 한국 영화 추천 서비스 홈 화면 구성
- [x] Header / Logo
- [x] Hero 영역
- [x] 영화 검색 입력창
- [x] 검색 버튼
- [x] 검색 결과 영역
- [x] 영화 카드 기본 UI
- [x] 안내 영역

### Backend API 연결
- [x] `src/services/api.js` 생성
- [x] FastAPI `/movies` API 연결
- [x] 영화 제목 검색 구현
- [x] API 응답을 React 상태에 저장
- [x] 검색 결과 영화 카드 출력
- [x] 로딩 상태 처리
- [x] 오류 처리
- [x] 빈 검색어 처리
- [x] Enter 키 검색

### CORS
- [x] React `localhost:5173` → FastAPI `127.0.0.1:8000` 통신 문제 확인
- [x] FastAPI `CORSMiddleware` 설정
- [x] 정상적인 영화 검색 확인

### Git / GitHub
- [x] 로컬 Git 저장소 생성
- [x] 첫 커밋 생성
- [x] `main` 브랜치 설정
- [x] GitHub 저장소 연결
- [x] 현재 프로젝트 기준으로 GitHub push 완료

## 3. 현재 Frontend 구조

```text
frontend/
├── public/
├── src/
│   ├── assets/
│   ├── services/
│   │   └── api.js
│   ├── App.css
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
├── eslint.config.js
├── index.html
├── package-lock.json
├── package.json
└── vite.config.js
```

## 4. 현재 구현된 검색 기능

```text
검색어 입력
   ↓
검색 버튼 / Enter
   ↓
searchMovies()
   ↓
FastAPI /movies
   ↓
응답 수신
   ↓
영화 카드 출력
```

영화 카드에 표시되는 정보:

- 영화 제목
- 장르
- 감독
- 개봉일
- 평균 평점
- 리뷰 수

## 5. 학습한 React 개념

### useState

화면에서 변하는 값을 관리하는 React Hook.

현재 상태:

```text
query
movies
loading
error
```

### map()

검색 결과 배열의 각 영화 데이터를 하나씩 꺼내 영화 카드 JSX를 만드는 데 사용.

```text
movies 배열
   ↓ map()
영화 1 → 카드
영화 2 → 카드
영화 3 → 카드
```

### async / await

Frontend에서 Backend API 요청 결과를 기다릴 때 사용.

```text
검색
 ↓
API 요청
 ↓
응답 대기
 ↓
결과 출력
```

## 6. 다음 개발 순서

### 1순위 — 영화 상세 페이지
- [ ] 검색 결과 영화 카드 클릭
- [ ] 선택한 영화 상세 정보 조회
- [ ] FastAPI 상세 API 연결
- [ ] 상세 페이지 UI 구성

### 2순위 — 추천 결과 페이지
- [ ] 추천 API 연결
- [ ] 추천 영화 목록 표시
- [ ] 추천 점수 및 관련 정보 표시
- [ ] 추천 영화 카드 구성

### 3순위 — 리뷰 기능
- [ ] 리뷰 API 연결
- [ ] 리뷰 목록 표시
- [ ] 평점 / 리뷰 내용 표시
- [ ] 상위 리뷰 또는 정렬 기능

### 4순위 — Frontend 구조 정리

예정 구조:

```text
src/
├── components/
│   ├── SearchBar.jsx
│   ├── MovieCard.jsx
│   └── ReviewCard.jsx
├── pages/
│   ├── Home.jsx
│   ├── MovieDetail.jsx
│   └── Recommendation.jsx
├── services/
│   └── api.js
├── App.jsx
└── ...
```

기능을 먼저 구현한 뒤 컴포넌트 단위로 분리한다.

## 7. 연동 예정 Backend API

```text
GET /movies
GET /movies/detail
GET /movies/reviews
GET /recommend
GET /health
```

실제 Swagger 응답 구조를 확인한 뒤 Frontend에 연결한다.

## 8. 개발 원칙

- Backend의 현재 정상 작동 구조는 불필요하게 변경하지 않는다.
- Frontend는 `frontend/` 안에서 개발한다.
- 한 기능씩 구현하고 실행 확인 후 다음 단계로 진행한다.
- API 응답 구조를 확인한 뒤 Frontend 코드를 작성한다.
- Git commit은 기능 단위로 남긴다.

## 9. Git Commit 예시

```text
feat: connect movie search API
feat: implement movie detail page
feat: implement recommendation page
feat: add review section
fix: handle API search error
style: improve movie card layout
```

## 10. 현재 상태 요약

### 완료

- React/Vite 프로젝트
- 홈 화면
- 검색 UI
- 영화 검색 API 연결
- 검색 결과 출력
- 로딩 / 오류 처리
- CORS 해결
- GitHub 업로드

### 진행 예정

```text
검색
 ↓
영화 상세
 ↓
추천 결과
 ↓
리뷰
 ↓
UI 정리
 ↓
최종 테스트
```

**현재 Frontend는 검색 기능까지 Backend와 실제 연동된 상태이며, 다음 작업은 영화 상세 페이지 구현이다.**
