import { useState, useEffect } from 'react'
import { CompetitionSelector } from '../components/CompetitionSelector'
import { LeaderboardTable } from '../components/LeaderboardTable'
import { api } from '../services/api'

export function LeaderboardPage({ user }) {
  const [competitionId, setCompetitionId] = useState(
    () => Number(localStorage.getItem('competitionId')) || null
  )
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!competitionId) return
    setLoading(true)
    setError(null)
    api.getLeaderboard(competitionId)
      .then(setEntries)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [competitionId])

  function handleCompetitionChange(id) {
    setCompetitionId(id)
    localStorage.setItem('competitionId', id)
  }

  return (
    <div className="page">
      <div style={{ marginBottom: 16 }}>
        <CompetitionSelector value={competitionId} onChange={handleCompetitionChange} />
      </div>

      {!competitionId && (
        <div className="empty-state">
          <div className="empty-state-icon">🏆</div>
          <div className="empty-state-text">Select a championship to see the leaderboard</div>
        </div>
      )}

      {loading && (
        <div className="loader">
          <div className="spinner" />
          Loading...
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}

      {!loading && !error && competitionId && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <LeaderboardTable entries={entries} currentUserId={user?.id} />
        </div>
      )}
    </div>
  )
}
