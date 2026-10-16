"""검수 결과(manual_label=0)를 기준으로 대표 키워드를 제외하는 필터.

사용:
    from keyword_quality_filter import filter_keyword_items

    items = filter_keyword_items(items)

키워드 항목은 문자열 또는 {'term': ...} / {'keyword': ...} 형태를 지원합니다.
원본 리스트는 수정하지 않습니다.
"""

EXCLUDED_KEYWORDS = {
    '남았습니다',
    '있네요',
    '영화네요',
    '되는데요',
    '말입니다',
    '수고하셨습니다',
    '봤습니다',
    '것입니다',
    '없죠',
    '관람했어요',
    '없어요',
    '보고왔어요',
    '생겼어요',
    '영화였어요',
    '같은데요',
    '다녀왔다',
    '영화였네요',
    '있었습니다',
    '것이죠',
    '되겠죠',
    '그랬어요',
}


def filter_keyword_items(items):
    """검수에서 제외 판정된 21개 키워드를 목록에서 제거합니다."""
    filtered = []
    for item in items:
        if isinstance(item, str):
            term = item
        elif isinstance(item, dict):
            term = item.get('term', item.get('keyword', ''))
        else:
            filtered.append(item)
            continue

        if term not in EXCLUDED_KEYWORDS:
            filtered.append(item)

    return filtered
