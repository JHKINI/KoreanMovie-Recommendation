// 가로 막대 목록. rows: [{ label, count }]. 가장 큰 값을 100%로 맞춘다.
function BarList({ title, rows }) {
  const max = Math.max(1, ...rows.map((row) => row.count))

  return (
    <div className="bar-card">
      <h3>{title}</h3>
      <ul className="bar-list">
        {rows.map((row) => (
          <li key={row.label}>
            <span className="bar-label">{row.label}</span>
            <span className="bar-track">
              <span className="bar-fill" style={{ width: `${(row.count / max) * 100}%` }} />
            </span>
            <span className="bar-count">{row.count.toLocaleString()}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default BarList
