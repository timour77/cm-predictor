import { useState } from 'react'
import { api } from '../services/api'
import { STATUS_LABELS, STATUS_COLORS } from '../utils/constants'

const TZ_SLOTS = [
  { label: 'BCN', tz: 'Europe/Madrid' },
  { label: 'ZRH', tz: 'Europe/Zurich' },
  { label: 'UFA', tz: 'Asia/Yekaterinburg' },
]

function formatTz(utcDate, tz) {
  if (!utcDate) return ''
  return new Date(utcDate).toLocaleTimeString('ru', {
    hour: '2-digit', minute: '2-digit', timeZone: tz,
  })
}

function TeamCrest({ src, name }) {
  if (src) {
    return <img className="team-crest" src={src} alt={name} onError={e => { e.target.style.display = 'none' }} />
  }
  return <div className="team-crest-placeholder">⚽</div>
}

const isScheduled = (status) => ['SCHEDULED', 'TIMED'].includes(status)
const isFinished = (status) => status === 'FINISHED'
const isLive = (status) => ['IN_PLAY', 'PAUSED'].includes(status)

function parseScore(scoreStr) {
  if (!scoreStr) return [0, 0]
  const parts = scoreStr.split('-')
  if (parts.length === 2) {
    const h = parseInt(parts[0], 10)
    const a = parseInt(parts[1], 10)
    if (!isNaN(h) && !isNaN(a)) return [h, a]
  }
  return [0, 0]
}

function calcOutcome(home, away) {
  if (home > away) return '1'
  if (away > home) return '2'
  return 'X'
}

function outcomeText(outcome, homeTeam, awayTeam) {
  if (outcome === '1') return `Победа ${homeTeam}`
  if (outcome === '2') return `Победа ${awayTeam}`
  return 'Ничья'
}

function formatRelativeTime(isoStr) {
  if (!isoStr) return ''
  const diff = Date.now() - new Date(isoStr).getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return 'только что'
  if (min < 60) return `${min} мин назад`
  const h = Math.floor(min / 60)
  if (h < 24) return `${h} ч назад`
  const d = Math.floor(h / 24)
  if (d < 7) return `${d} дн назад`
  return new Date(isoStr).toLocaleDateString('ru', { day: 'numeric', month: 'short' })
}

function ScoreStepper({ value, onChange }) {
  return (
    <div className="score-stepper">
      <button
        className="stepper-btn"
        onClick={() => onChange(value + 1)}
        type="button"
      >+</button>
      <div className="stepper-value">{value}</div>
      <button
        className="stepper-btn"
        onClick={() => onChange(Math.max(0, value - 1))}
        type="button"
        disabled={value === 0}
      >−</button>
    </div>
  )
}

export function MatchCard({ match, currentUserId, onPredictionSaved }) {
  const pred = match.user_prediction
  const [homeGoals, setHomeGoals] = useState(parseScore(pred?.predicted_score)[0])
  const [awayGoals, setAwayGoals] = useState(parseScore(pred?.predicted_score)[1])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(!!pred)
  const [showPredictions, setShowPredictions] = useState(false)
  const [allPredictions, setAllPredictions] = useState(null)
  const [predLoading, setPredLoading] = useState(false)

  const outcome = calcOutcome(homeGoals, awayGoals)
  const predictedScore = `${homeGoals}-${awayGoals}`

  const statusLabel = STATUS_LABELS[match.status] || match.status
  const statusClass = isFinished(match.status) ? 'finished' : isLive(match.status) ? 'live' : ''

  function handleChange(setter) {
    return (val) => { setter(val); setSaved(false) }
  }

  async function handleSave() {
    setSaving(true)
    setError(null)
    try {
      const result = await api.savePrediction(match.external_id, match.competition_id, outcome, predictedScore)
      setSaved(true)
      onPredictionSaved && onPredictionSaved(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  async function togglePredictions() {
    if (allPredictions !== null) {
      setShowPredictions(v => !v)
      return
    }
    setPredLoading(true)
    try {
      const data = await api.getMatchPredictions(match.external_id)
      setAllPredictions(data)
      setShowPredictions(true)
    } catch {
      // silently ignore
    } finally {
      setPredLoading(false)
    }
  }

  const homeScore = match.home_goals !== null && match.home_goals !== undefined ? match.home_goals : '-'
  const awayScore = match.away_goals !== null && match.away_goals !== undefined ? match.away_goals : '-'

  const outcomeLabel = { '1': 'Победа хозяев', 'X': 'Ничья', '2': 'Победа гостей' }

  return (
    <div className="match-card">
      <div className="match-header">
        <div className="match-times">
          {TZ_SLOTS.map(({ label, tz }) => (
            <span key={tz} className="match-time-slot">
              <span className="match-time-label">{label}</span>
              {formatTz(match.match_date, tz)}
            </span>
          ))}
        </div>
        {match.matchday && <span>MD {match.matchday}</span>}
        <span
          className={`match-status ${statusClass}`}
          style={{ color: STATUS_COLORS[match.status] }}
        >
          {statusLabel}
        </span>
      </div>
      {match.venue && (
        <div className="match-venue">{match.venue}</div>
      )}

      <div className="match-teams">
        <div className="team">
          <TeamCrest src={match.home_team_crest} name={match.home_team} />
          <span className="team-name">{match.home_team}</span>
        </div>

        <div className="match-score">
          {isFinished(match.status) || isLive(match.status)
            ? <>{homeScore}<span className="match-score-separator"> : </span>{awayScore}</>
            : <span style={{ fontSize: 20, color: 'var(--text-muted)' }}>vs</span>
          }
        </div>

        <div className="team">
          <TeamCrest src={match.away_team_crest} name={match.away_team} />
          <span className="team-name">{match.away_team}</span>
        </div>
      </div>

      {/* Prediction form for scheduled matches */}
      {isScheduled(match.status) && (
        saved ? (
          <div className="prediction-saved-view">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="chip" style={{ fontSize: 16, fontWeight: 700 }}>{predictedScore}</span>
              <span className={`outcome-chip outcome-${outcome}`}>
                {outcomeText(outcome, match.home_team, match.away_team)}
              </span>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={() => setSaved(false)}>
              ✏ Изменить
            </button>
          </div>
        ) : (
          <div className="prediction-form">
            <div className="stepper-row">
              <ScoreStepper value={homeGoals} onChange={handleChange(setHomeGoals)} />
              <div className="stepper-colon">:</div>
              <ScoreStepper value={awayGoals} onChange={handleChange(setAwayGoals)} />
            </div>

            <div className="stepper-footer">
              <span className={`outcome-chip outcome-${outcome}`}>
                {outcomeText(outcome, match.home_team, match.away_team)}
              </span>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? '...' : 'Сохранить'}
              </button>
            </div>

            {error && <div className="error-msg">{error}</div>}
          </div>
        )
      )}

      {/* Show saved prediction result for finished matches */}
      {isFinished(match.status) && pred && (
        <div className="prediction-result">
          <div>
            Прогноз:
            <span className={`prediction-badge outcome-${pred.outcome}`} style={{ marginLeft: 8 }}>
              {pred.outcome}
            </span>
            {pred.predicted_score && (
              <span className="chip" style={{ marginLeft: 6 }}>{pred.predicted_score}</span>
            )}
          </div>
          <span className="points-badge">+{pred.points} pts</span>
        </div>
      )}

      {/* Predictions toggle */}
      <button className="predictions-toggle" onClick={togglePredictions}>
        <span>Прогнозы участников</span>
        <span>{predLoading ? '...' : showPredictions ? '▲' : '▼'}</span>
      </button>

      {showPredictions && allPredictions && (
        <div className="predictions-list">
          {allPredictions.length === 0 ? (
            <div className="predictions-empty">Нет прогнозов</div>
          ) : allPredictions.map(p => (
            <div
              key={p.user_id}
              className={`prediction-row${p.user_id === currentUserId ? ' me' : ''}`}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <span className="prediction-row-name">{p.is_bot ? '🤖 ' : ''}{p.username}</span>
                  {isFinished(match.status) && (
                    <span className="points-badge">+{p.points}</span>
                  )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  {p.predicted_score && (
                    <span className="chip">{p.predicted_score}</span>
                  )}
                  {p.outcome && (
                    <span className={`prediction-badge outcome-${p.outcome}`} style={{ fontSize: 11 }}>
                      {outcomeText(p.outcome, match.home_team, match.away_team)}
                    </span>
                  )}
                </div>
                {p.updated_at && (
                  <div style={{ marginTop: 4, fontSize: 11, color: 'var(--text-muted)', display: 'flex', gap: 6 }}>
                    <span>{formatRelativeTime(p.updated_at)}</span>
                    {p.edit_count > 0 && <span>· ред. {p.edit_count}×</span>}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
