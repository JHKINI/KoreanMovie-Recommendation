"""영화별 대표 키워드를 리뷰 글에서 뽑습니다.

추천용 TF-IDF(문자 2~3그램)는 "연기가" 같은 글자 조각이라 화면에 보여주기 어렵습니다.
그래서 키워드는 별도로 단어(한글 2글자 이상) 단위 TF-IDF를 사용합니다.
형태소 분석기를 쓰지 않으므로 아래 한계가 있습니다.
- 끝의 조사·어미(은는이가을를의과와도에로만, 들의, 에서, 으로, 처럼 등)가 붙은 형태가 같은 단어의 원형과
  함께 있으면 원형으로 합칩니다. 원형이 따로 없으면 조사가 붙은 채로 남습니다.
- 영화 제목에 들어 있는 단어는 뺍니다.
"""

import re
from keyword_quality_filter import filter_keyword_items

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

TOKEN_PATTERN = r'[가-힣]{2,}'
TOKEN = re.compile(TOKEN_PATTERN)
PARTICLES = '은는이가을를의과와도에로만'
# 여러 글자 어미. 긴 것부터 확인해야 '들의'가 '의'보다 먼저 걸립니다.
SUFFIXES = tuple(sorted(
    ['에서는', '으로는', '들의', '들은', '들이', '들을', '에서', '으로', '에게', '처럼', '보다', '까지', '부터', '라는', *PARTICLES],
    key=len, reverse=True))


def build_stem_map(texts, min_df=3):
    """입력: 영화별 리뷰 문서 목록. 반환: {조사가 붙은 단어: 원형}. 원형도 어휘에 있을 때만 합칩니다."""
    counter = CountVectorizer(token_pattern=TOKEN_PATTERN, min_df=min_df, lowercase=False)
    try:
        counter.fit(texts)
    except ValueError:
        return {}
    vocabulary = set(counter.vocabulary_)
    stems = {}
    for term in vocabulary:
        for suffix in SUFFIXES:
            base = term[:-len(suffix)]
            if term.endswith(suffix) and len(base) >= 2 and base in vocabulary:
                stems[term] = base
                break
    return stems


def in_title(term, title):
    """단어가 영화 제목에 포함되면 키워드로 쓰지 않습니다. 제목은 이미 아는 정보입니다."""
    compact = title.replace(' ', '')
    # '봄은'처럼 제목 단어에 조사가 붙은 형태도 같은 단어로 봅니다.
    forms = {term, term[:-1]} if term[-1] in PARTICLES else {term}
    return any(form and (form in compact or (len(compact) >= 2 and compact in form)) for form in forms)


def build_keywords(profiles, top_n=15, min_df=3, max_df=0.4):
    """입력: 영화 프로필 표(movie_id, title, review_text). 반환: {movie_id: [{'term', 'score'}...]}.

    min_df: 최소 몇 개 영화에 나온 단어만 쓸지. max_df: 이 비율보다 많은 영화에 나오는 흔한 단어는 제외.
    어휘가 비어 있는 작은 데이터에서는 빈 딕셔너리를 반환합니다.
    """
    texts = profiles['review_text'].fillna('').tolist()
    stems = build_stem_map(texts, min_df)

    def analyzer(text):
        return [stems.get(token, token) for token in TOKEN.findall(text)]

    vectorizer = TfidfVectorizer(analyzer=analyzer, min_df=min_df, max_df=max_df, sublinear_tf=True)
    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return {}
    terms = vectorizer.get_feature_names_out()

    result = {}
    for row, (movie_id, title) in enumerate(zip(profiles['movie_id'], profiles['title'])):
        start, end = matrix.indptr[row], matrix.indptr[row + 1]
        scored = sorted(zip(matrix.indices[start:end], matrix.data[start:end]), key=lambda pair: (-pair[1], terms[pair[0]]))
        items = []
        for column, score in scored:
            term = str(terms[column])
            if in_title(term, str(title)):
                continue
            items.append({'term': term, 'score': round(float(score), 4)})
            if len(items) == top_n:
                break
        result[str(movie_id)] = filter_keyword_items(items)
    return result


def movies_by_keyword(keywords, term, limit=12):
    """입력: build_keywords 결과, 찾을 단어, 최대 개수. 반환: [(movie_id, score)] — 그 단어가 대표 키워드에 든 영화를 점수 순으로.

    단어는 앞뒤 공백을 뺀 정확한 일치만 찾습니다(부분 일치 아님). 동점은 영화 ID 오름차순입니다.
    대표 키워드(영화마다 상위 15개) 안에 든 경우만 찾으므로 "리뷰에 한 번이라도 나온 영화"와는 다릅니다.
    """
    term = term.strip()
    found = []
    for movie_id, items in keywords.items():
        for item in items:
            if item['term'] == term:
                found.append((movie_id, item['score']))
                break
    found.sort(key=lambda pair: (-pair[1], pair[0]))
    return found[:limit]
