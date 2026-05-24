export function LeaderboardTable({ entries, currentUserId }) {
  if (!entries.length) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🏆</div>
        <div className="empty-state-text">No results yet</div>
      </div>
    )
  }

  return (
    <table className="leaderboard-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Player</th>
          <th>Pts</th>
          <th>✓</th>
          <th>🎯</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((e) => {
          const rankClass = e.rank === 1 ? 'top1' : e.rank === 2 ? 'top2' : e.rank === 3 ? 'top3' : ''
          const isMe = e.user_id === currentUserId
          return (
            <tr key={e.user_id} className={isMe ? 'me' : ''}>
              <td>
                <span className={`rank-badge ${rankClass}`}>{e.rank}</span>
              </td>
              <td style={{ fontWeight: isMe ? 700 : 400 }}>
                {isMe ? '👤 ' : ''}{e.username}
              </td>
              <td style={{ fontWeight: 700, color: 'var(--yellow)' }}>{e.total_points}</td>
              <td style={{ color: 'var(--green)' }}>{e.correct_outcomes}</td>
              <td style={{ color: 'var(--blue)' }}>{e.correct_scores}</td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
