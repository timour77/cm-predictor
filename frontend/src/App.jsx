import { useState } from 'react'
import { useAuth } from './hooks/useAuth'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { LeaderboardPage } from './pages/LeaderboardPage'
import { Header } from './components/Header'

const TABS = [
  { id: 'matches', label: 'Matches', icon: '⚽' },
  { id: 'leaderboard', label: 'Leaders', icon: '🏆' },
]

export default function App() {
  const { user, login, register, logout } = useAuth()
  const [tab, setTab] = useState('matches')

  async function handleAuth(mode, username, password) {
    if (mode === 'login') return login(username, password)
    return register(username, password)
  }

  if (!user) {
    return <LoginPage onAuth={handleAuth} />
  }

  return (
    <>
      <Header user={user} onLogout={logout} />

      <main style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {tab === 'matches' && <HomePage user={user} />}
        {tab === 'leaderboard' && <LeaderboardPage user={user} />}
      </main>

      <nav className="nav-tabs">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`nav-tab ${tab === t.id ? 'active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            <span className="nav-tab-icon">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </nav>
    </>
  )
}
