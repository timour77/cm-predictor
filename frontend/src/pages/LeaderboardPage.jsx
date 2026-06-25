import { useState, useEffect } from 'react'
import { LeaderboardTable } from '../components/LeaderboardTable'
import { UserDetail } from '../components/UserDetail'
import { api } from '../services/api'

const WORLD_CUP_ID = 2000

export function LeaderboardPage({ user }) {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedUser, setSelectedUser] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    api.getLeaderboard(WORLD_CUP_ID)
      .then(setEntries)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (selectedUser) {
    return (
      <UserDetail
        userId={selectedUser.user_id}
        username={selectedUser.username}
        photoUrl={selectedUser.photo_url}
        currentUserId={user?.id}
        onBack={() => setSelectedUser(null)}
      />
    )
  }

  return (
    <div className="page">
      {loading && (
        <div className="loader">
          <div className="spinner" />
          Загрузка...
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}

      {!loading && !error && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <LeaderboardTable
            entries={entries}
            currentUserId={user?.id}
            onRowClick={setSelectedUser}
          />
        </div>
      )}
    </div>
  )
}
