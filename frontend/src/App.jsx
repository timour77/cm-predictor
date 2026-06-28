import { useState, useEffect } from 'react'
import { useAuth } from './hooks/useAuth'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { LeaderboardPage } from './pages/LeaderboardPage'
import { ProfilePage } from './pages/ProfilePage'
import { GroupsPage } from './pages/GroupsPage'
import { BracketPage } from './pages/BracketPage'

const TABS = [
  { id: 'matches', label: 'Матчи', icon: '⚽' },
  { id: 'groups', label: 'Группы', icon: '📊' },
  { id: 'bracket', label: 'Сетка', icon: '🏆' },
  { id: 'leaderboard', label: 'Лидеры', icon: '🥇' },
  { id: 'profile', label: 'Профиль', icon: '👤' },
]

export default function App() {
  const { user, login, register, telegramLogin, logout } = useAuth()
  const [tab, setTab] = useState('matches')
  const [tgLoading, setTgLoading] = useState(() => !!window.Telegram?.WebApp?.initData)

  useEffect(() => {
    const tg = window.Telegram?.WebApp
    if (!tg?.initData) return
    tg.ready()
    tg.expand()
    telegramLogin(tg.initData).finally(() => setTgLoading(false))
  }, [])

  async function handleAuth(mode, username, password) {
    if (mode === 'login') return login(username, password)
    return register(username, password)
  }

  function handleLogout() {
    logout()
    setTab('matches')
  }

  if (tgLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: 12 }}>
        <div style={{ fontSize: 32 }}>⚽</div>
        <div style={{ color: 'var(--text-secondary)' }}>Загрузка...</div>
      </div>
    )
  }

  if (!user) {
    return <LoginPage onAuth={handleAuth} />
  }

  return (
    <>
      <main style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {tab === 'matches' && <HomePage user={user} />}
        {tab === 'groups' && <GroupsPage />}
        {tab === 'bracket' && <BracketPage user={user} />}
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
