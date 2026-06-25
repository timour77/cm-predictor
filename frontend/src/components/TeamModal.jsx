import { useState, useEffect } from 'react'
import { api } from '../services/api'

function SmallCrest({ src, name, size = 20 }) {
  const [err, setErr] = useState(false)
  if (!src || err) {
    return (
      <span
        className="standing-crest-placeholder"
        style={{ width: size, height: size, fontSize: size * 0.5, flexShrink: 0 }}
      >
        {name?.[0] ?? '?'}
      </span>
    )
  }
  return (
    <img
      src={src}
      alt={name}
      className="standing-crest"
      style={{ width: size, height: size, flexShrink: 0 }}
      onError={() => setErr(true)}
    />
  )
}

function formatMatchDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

function formatMatchTime(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

export function TeamModal({ teamId, teamName, teamCrest, competitionId, onClose }) {
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!teamId) {
      setError('ID команды недоступен')
      setLoading(false)
      return
    }
    api.getTeamMatches(teamId, competitionId)
      .then(data => setMatches(data.sort((a, b) => new Date(a.match_date) - new Date(b.match_date))))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [teamId, competitionId])

  function getResult(match) {
    if (match.status !== 'FINISHED' && match.status !== 'AWARDED') return null
    const isHome = match.home_team_id === teamId || match.home_team === teamName
    const own = isHome ? match.home_goals : match.away_goals
    const opp = isHome ? match.away_goals : match.home_goals
    if (own > opp) return 'W'
    if (own < opp) return 'L'
    return 'D'
  }

  return (
    <>
      <div className="modal-overlay" onClick={onClose} />
      <div className="modal-sheet">
        <div className="modal-handle" />
        <div className="modal-header">
          <div className="modal-team-title">
            <SmallCrest src={teamCrest} name={teamName} size={36} />
            <span className="modal-team-name">{teamName}</span>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="loader">
              <div className="spinner" />
              Загрузка матчей...
            </div>
          )}
          {error && <div className="error-msg" style={{ margin: 16 }}>{error}</div>}
          {!loading && !error && matches.length === 0 && (
            <div className="empty-state" style={{ padding: '24px' }}>
              <div className="empty-state-icon">📅</div>
              <div className="empty-state-text">Матчей не найдено</div>
            </div>
          )}
          {matches.map(m => {
            const isHome = m.home_team_id === teamId || m.home_team === teamName
            const opponent = isHome ? m.away_team : m.home_team
            const opponentCrest = isHome ? m.away_team_crest : m.home_team_crest
            const ownGoals = isHome ? m.home_goals : m.away_goals
            const oppGoals = isHome ? m.away_goals : m.home_goals
            const finished = m.status === 'FINISHED' || m.status === 'AWARDED'
            const result = getResult(m)

            return (
              <div key={m.external_id} className="team-match-row">
                <div className="team-match-day">тур {m.matchday}</div>
                <div className="team-match-main">
                  <div className="team-match-opponent">
                    <SmallCrest src={opponentCrest} name={opponent} size={24} />
                    <span className="team-match-opp-name">{opponent}</span>
                    <span className="team-match-venue">{isHome ? 'дома' : 'в гостях'}</span>
                  </div>
                  <div className="team-match-right">
                    {finished ? (
                      <>
                        <span className="team-match-score">{ownGoals}:{oppGoals}</span>
                        <span className={`result-badge result-${result}`}>{result}</span>
                      </>
                    ) : (
                      <span className="team-match-date">
                        {formatMatchDate(m.match_date)}
                        <span className="team-match-time">{formatMatchTime(m.match_date)}</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </>
  )
}
