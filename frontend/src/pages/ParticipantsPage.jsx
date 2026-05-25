import { useState, useEffect } from 'react'
import { api } from '../services/api'

function StatBox({ label, value }) {
  return (
    <div className="stat-box">
      <div className="stat-box-value">{value ?? '—'}</div>
      <div className="stat-box-label">{label}</div>
    </div>
  )
}

function outcomeColor(outcome) {
  if (outcome === '1') return 'var(--success)'
  if (outcome === '2') return 'var(--danger)'
  return 'var(--warning)'
}

function PredictionHistoryItem({ p }) {
  const hasMatch = p.home_team && p.away_team
  const isFinished = p.match_status === 'FINISHED'
  const actualScore = isFinished && p.home_goals !== null && p.away_goals !== null
    ? `${p.home_goals}–${p.away_goals}`
    : null

  function actualOutcome() {
    if (!isFinished || p.home_goals === null) return null
    if (p.home_goals > p.away_goals) return '1'
    if (p.away_goals > p.home_goals) return '2'
    return 'X'
  }
  const actual = actualOutcome()

  return (
    <div className="pred-history-item">
      <div className="pred-history-match">
        {hasMatch
          ? <span>{p.home_team} — {p.away_team}</span>
          : <span style={{ color: 'var(--text-muted)' }}>Матч #{p.match_id}</span>
        }
        {p.competition_name && (
          <span className="pred-history-comp">{p.competition_name}</span>
        )}
      </div>

      <div className="pred-history-row">
        <div className="pred-history-left">
          {p.predicted_score && (
            <span className="chip">{p.predicted_score}</span>
          )}
          {p.outcome && (
            <span
              className="prediction-badge"
              style={{
                background: `${outcomeColor(p.outcome)}22`,
                color: outcomeColor(p.outcome),
              }}
            >
              {p.outcome}
            </span>
          )}
        </div>

        <div className="pred-history-right">
          {actualScore && (
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {actualScore}
              {actual && (
                <span
                  style={{
                    marginLeft: 4,
                    fontWeight: 600,
                    color: outcomeColor(actual),
                  }}
                >
                  {actual}
                </span>
              )}
            </span>
          )}
          {isFinished && (
            <span className={`points-badge ${p.points > 0 ? '' : 'zero'}`}>
              {p.points > 0 ? `+${p.points}` : '0'}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

function UserDetail({ userId, username, currentUserId, onBack }) {
  const [stats, setStats] = useState(null)
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.getUserStats(userId),
      api.getUserPredictions(userId),
    ])
      .then(([s, p]) => { setStats(s); setPredictions(p) })
      .finally(() => setLoading(false))
  }, [userId])

  const isMe = userId === currentUserId

  return (
    <div className="page">
      <div className="user-detail-header">
        <button className="btn btn-ghost btn-sm" onClick={onBack}>← Назад</button>
        <div className="user-detail-name">
          {username}
          {isMe && <span className="me-tag">Я</span>}
        </div>
      </div>

      {loading ? (
        <div className="loader"><div className="spinner" />Загрузка...</div>
      ) : (
        <>
          <div className="stats-grid">
            <StatBox label="Очки" value={stats?.total_points} />
            <StatBox label="Прогнозов" value={stats?.total_predictions} />
            <StatBox label="Угаданных" value={stats?.correct_predictions} />
            <StatBox label="Место" value={stats?.rank ? `#${stats.rank}` : '—'} />
          </div>

          <div className="section-label" style={{ margin: '20px 0 10px' }}>
            История ставок
          </div>

          {predictions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📋</div>
              <div className="empty-state-text">Нет ставок</div>
            </div>
          ) : (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              {predictions.map(p => (
                <PredictionHistoryItem key={p.id} p={p} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export function ParticipantsPage({ user }) {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedUser, setSelectedUser] = useState(null)

  useEffect(() => {
    api.getUsers()
      .then(setUsers)
      .finally(() => setLoading(false))
  }, [])

  if (selectedUser) {
    return (
      <UserDetail
        userId={selectedUser.id}
        username={selectedUser.username}
        currentUserId={user?.id}
        onBack={() => setSelectedUser(null)}
      />
    )
  }

  return (
    <div className="page">
      <div className="section-label" style={{ marginBottom: 12 }}>
        Участники
      </div>

      {loading ? (
        <div className="loader"><div className="spinner" />Загрузка...</div>
      ) : users.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">👥</div>
          <div className="empty-state-text">Нет участников</div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {users.map((u, i) => (
            <button
              key={u.id}
              className={`participant-row${u.id === user?.id ? ' me' : ''}`}
              onClick={() => setSelectedUser(u)}
            >
              <span className="participant-rank">{i + 1}</span>
              <span className="participant-name">
                {u.username}
                {u.id === user?.id && <span className="me-tag">Я</span>}
              </span>
              <div className="participant-stats">
                <span className="points-badge">{u.total_points} pts</span>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {u.total_predictions} ставок
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
