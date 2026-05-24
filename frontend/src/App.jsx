import { useState } from 'react'
import { useAuth } from './hooks/useAuth'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { LeaderboardPage } from './pages/LeaderboardPage'
import { ProfilePage } from './pages/ProfilePage'
import { Header } from './components/Header'

const TABS = [
  { id: 'matches', label: 'Матчи', icon: '⚽' },
  { id: 'leaderboard', label: 'Лидеры', icon: '🏆' },
  { id: 'profile', label: 'Профиль', icon: '👤' },
]

export default function App() {
  const { user, login, register, logout } = useAuth()
  const [tab, setTab] = useState('matches')

  async function handleAuth(mode, username, password) {
    if (mode === 'login') return login(username, password)
    return register(username, password)
  }

  function handleLogout() {
    logout()
    setTab('matches')
  }

  if (!user) {
    return <LoginPage onAuth={handleAuth} />
  }

  return (
    <>
      <Header user={user} onLogout={handleLogout} />

      <main style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {tab === 'matches' && <HomePage user={user} />}
        {tab === 'leaderboard' && <LeaderboardPage user={user} />}
        {tab === 'profile' && <ProfilePage user={user} onLogout={handleLogout} />}
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
