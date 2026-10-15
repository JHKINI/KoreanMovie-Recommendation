// 0~1 값을 막대로 보여주는 한 줄. 추천 근거(정보 유사도·리뷰 유사도)를 눈으로 비교할 수 있게 한다.
export function Meter({ label, value }) {
  return (
    <div className="meter">
      <span className="meter-label">{label}</span>
      <span className="meter-track">
        <span className="meter-fill" style={{ width: `${Math.round(Math.min(1, Math.max(0, value)) * 100)}%` }} />
      </span>
      <span className="meter-value">{value.toFixed(2)}</span>
    </div>
  )
}

// 추천 항목 하나의 근거. 정보 유사도는 장르·등급·관객 수 등 메타데이터, 리뷰 유사도는 리뷰 글 표현이다.
function SimilarityBars({ item }) {
  return (
    <div className="meters">
      <Meter label="정보 유사" value={item.metadata_similarity} />
      <Meter label="리뷰 유사" value={item.text_similarity} />
      {item.director_bonus > 0 && <span className="chip">같은 감독</span>}
    </div>
  )
}

export default SimilarityBars
