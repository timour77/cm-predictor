import { useState, useEffect } from 'react'
import { LeaderboardTable } from '../components/LeaderboardTable'
import { api } from '../services/api'

const WORLD_CUP_ID = 3

export function LeaderboardPage({ user }) {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    api.getLeaderboard(WORLD_CUP_ID)
      .then(setEntries)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      {loading && (
        <div className="loader">
          <div className="spinner" />
          Loading...
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}

      {!loading && !error && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <LeaderboardTable entries={entries} currentUserId={user?.id} />
        </div>
      )}
    </div>
  )
}
