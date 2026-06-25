import { useState, useEffect, useCallback } from 'react'
import { MatchCard } from '../components/MatchCard'
import { api } from '../services/api'

const WORLD_CUP_ID = 2000

function todayStr() {
  return new Date().toISOString().split('T')[0]
}

export function HomePage({ user }) {
  const [date, setDate] = useState(todayStr)
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [fetchedAt, setFetchedAt] = useState(null)

  const loadMatches = useCallback((silent = false) => {
    if (!silent) setLoading(true)
    setError(null)
    api.getMatches(WORLD_CUP_ID, date)
      .then(({ matches, fetchedAt }) => { setMatches(matches); if (fetchedAt) setFetchedAt(fetchedAt) })
      .catch(e => setError(e.message))
      .finally(() => { if (!silent) setLoading(false) })
  }, [date])

  useEffect(() => { loadMatches() }, [loadMatches])

  // Auto-refresh every 60s when viewing today's matches
  useEffect(() => {
    if (date !== todayStr()) return
    const id = setInterval(() => loadMatches(true), 60_000)
    return () => clearInterval(id)
  }, [date, loadMatches])

  function shiftDate(days) {
    const d = new Date(date)
    d.setDate(d.getDate() + days)
    setDate(d.toISOString().split('T')[0])
  }

  return (
    <div className="page">
      <div className="competition-selector">
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
        {fetchedAt && (
          <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', marginTop: 6 }}>
            Данные от {fetchedAt.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </div>
        )}
      </div>

      {loading && (
        <div className="loader">
          <div className="spinner" />
          Loading matches...
        </div>
      )}

      {error && <div className="error-msg" style={{ marginBottom: 12 }}>{error}</div>}

      {!loading && !error && matches.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">📅</div>
          <div className="empty-state-text">No matches on this date</div>
        </div>
      )}

      {!loading && matches.map(match => (
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
