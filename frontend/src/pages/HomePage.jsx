import { useState, useEffect, useCallback } from 'react'
import { CompetitionSelector } from '../components/CompetitionSelector'
import { MatchCard } from '../components/MatchCard'
import { api } from '../services/api'

function todayStr() {
  return new Date().toISOString().split('T')[0]
}

export function HomePage() {
  const [competitionId, setCompetitionId] = useState(
    () => Number(localStorage.getItem('competitionId')) || null
  )
  const [date, setDate] = useState(todayStr)
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadMatches = useCallback(() => {
    if (!competitionId) return
    setLoading(true)
    setError(null)
    api.getMatches(competitionId, date)
      .then(setMatches)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [competitionId, date])

  useEffect(() => { loadMatches() }, [loadMatches])

  function handleCompetitionChange(id) {
    setCompetitionId(id)
    localStorage.setItem('competitionId', id)
  }

  function shiftDate(days) {
    const d = new Date(date)
    d.setDate(d.getDate() + days)
    setDate(d.toISOString().split('T')[0])
  }

  return (
    <div className="page">
      <div className="competition-selector">
        <CompetitionSelector value={competitionId} onChange={handleCompetitionChange} />

        <div>
          <div className="section-label" style={{ marginBottom: 6 }}>Date</div>
          <div className="date-row">
            <button className="btn btn-ghost btn-sm" onClick={() => shiftDate(-1)}>◀</button>
            <input
              className="input"
              type="date"
              value={date}
              onChange={e => setDate(e.target.value)}
            />
            <button className="btn btn-ghost btn-sm" onClick={() => shiftDate(1)}>▶</button>
            <button className="btn btn-ghost btn-sm" onClick={() => setDate(todayStr())}>Today</button>
          </div>
        </div>
      </div>

      {!competitionId && (
        <div className="empty-state">
          <div className="empty-state-icon">⚽</div>
          <div className="empty-state-text">Select a championship to view matches</div>
        </div>
      )}

      {loading && (
        <div className="loader">
          <div className="spinner" />
          Loading matches...
        </div>
      )}

      {error && <div className="error-msg" style={{ marginBottom: 12 }}>{error}</div>}

      {!loading && !error && competitionId && matches.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">📅</div>
          <div className="empty-state-text">No matches on this date</div>
        </div>
      )}

      {!loading && matches.map(match => (
        <MatchCard
          key={match.external_id}
          match={match}
          onPredictionSaved={loadMatches}
        />
      ))}
    </div>
  )
}
