import { useState } from 'react'

export function LoginPage({ onAuth }) {
  const [tab, setTab] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    const ok = await onAuth(tab, username, password)
    if (!ok) setError(tab === 'login' ? 'Invalid username or password' : 'Registration failed')
    setLoading(false)
  }

  return (
    <div className="login-page">
      <div>
        <div className="login-logo">⚽</div>
        <div className="login-title">CM Predictor</div>
        <div className="login-subtitle">Predict. Score. Win.</div>
      </div>

      <form className="login-form" onSubmit={handleSubmit}>
        <div className="login-tabs">
          <button
            type="button"
            className={`login-tab ${tab === 'login' ? 'active' : ''}`}
            onClick={() => setTab('login')}
          >
            Login
          </button>
          <button
            type="button"
            className={`login-tab ${tab === 'register' ? 'active' : ''}`}
            onClick={() => setTab('register')}
          >
            Register
          </button>
        </div>

        <input
          className="input"
          placeholder="Username"
          value={username}
          onChange={e => setUsername(e.target.value)}
          autoComplete="username"
          required
        />
        <input
          className="input"
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
          required
        />

        {error && <div className="error-msg">{error}</div>}

        <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
          {loading ? 'Loading...' : tab === 'login' ? 'Login' : 'Register'}
        </button>
      </form>
    </div>
  )
}
