import { Avatar } from './UserDetail'

export function LeaderboardTable({ entries, currentUserId, onRowClick }) {
  if (!entries.length) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🏆</div>
        <div className="empty-state-text">Результатов пока нет</div>
      </div>
    )
  }

  return (
    <table className="leaderboard-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Игрок</th>
          <th>Очки</th>
          <th title="Угаданные исходы">✓</th>
          <th title="Угаданные счета">🎯</th>
        </tr>
      </thead>
      <tbody>
        {entries.map(e => {
          const rankClass = e.rank === 1 ? 'top1' : e.rank === 2 ? 'top2' : e.rank === 3 ? 'top3' : ''
          const isMe = e.user_id === currentUserId
          return (
            <tr
              key={e.user_id}
              className={isMe ? 'me' : ''}
              onClick={() => onRowClick?.(e)}
              style={onRowClick ? { cursor: 'pointer' } : undefined}
            >
              <td>
                <span className={`rank-badge ${rankClass}`}>{e.rank}</span>
              </td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Avatar photoUrl={e.photo_url} username={e.username} size={28} />
                  <span style={{ fontWeight: isMe ? 700 : 400 }}>
                    {e.is_bot ? '🤖 ' : ''}{e.username}
                  </span>
                  {isMe && <span className="me-tag">Я</span>}
                </div>
              </td>
              <td style={{ fontWeight: 700, color: 'var(--warning)' }}>{e.total_points}</td>
              <td style={{ color: 'var(--success)' }}>{e.correct_outcomes}</td>
              <td style={{ color: 'var(--primary)' }}>{e.correct_scores}</td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
