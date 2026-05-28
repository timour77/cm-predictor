import { useState, useEffect, useCallback } from 'react'
import { CompetitionSelector } from '../components/CompetitionSelector'
import { MatchCard } from '../components/MatchCard'
import { api } from '../services/api'

function todayStr() {
  return new Date().toISOString().split('T')[0]
}

export function HomePage({ user }) {
  const [competitionId, setCompetitionId] = useState(
    () => Number(localStorage.getItem('competitionId')) || null
  )
  const [date, setDate] = useState(todayStr)
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [todayMode, setTodayMode] = useState(false)

  const loadMatches = useCallback(() => {
    if (todayMode) {
      setLoading(true)
      setError(null)
      api.getTodayMatches()
        .then(setMatches)
        .catch(e => setError(e.message))
        .finally(() => setLoading(false))
      return
    }
    if (!competitionId) return
    setLoading(true)
    setError(null)
    api.getMatches(competitionId, date)
      .then(setMatches)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [competitionId, date, todayMode])

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

  function toggleTodayMode() {
    setTodayMode(v => !v)
    setMatches([])
    setError(null)
  }

  // Group matches by competition when in today mode
  const grouped = todayMode
    ? matches.reduce((acc, m) => {
        const key = m.competition_name || 'Другое'
        if (!acc[key]) acc[key] = []
        acc[key].push(m)
        return acc
      }, {})
    : null

  return (
    <div className="page">
      <div className="competition-selector">
        <button
          className={`btn btn-today ${todayMode ? 'active' : ''}`}
          onClick={toggleTodayMode}
        >
          Матчи сегодня
        </button>

        {!todayMode && (
          <>
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
          </>
        )}
      </div>

      {!todayMode && !competitionId && (
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

      {!loading && !error && (competitionId || todayMode) && matches.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">📅</div>
          <div className="empty-state-text">No matches on this date</div>
        </div>
      )}

      {!loading && todayMode && grouped && Object.entries(grouped).map(([compName, compMatches]) => (
        <div key={compName}>
          <div className="today-competition-header">{compName}</div>
          {compMatches.map(match => (
            <MatchCard
              key={match.external_id}
              match={match}
              currentUserId={user?.id}
              onPredictionSaved={loadMatches}
            />
          ))}
        </div>
      ))}

      {!loading && !todayMode && matches.map(match => (
        <MatchCard
          key={match.external_id}
          match={match}
          currentUserId={user?.id}
          onPredictionSaved={loadMatches}
        />
      ))}
    </div>
  )
}
