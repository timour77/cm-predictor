export function Header({ user, onLogout }) {
  return (
    <header className="header">
      <span className="header-title">⚽ CM Predictor</span>
      {user && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="header-user">@{user.username}</span>
          <button className="btn btn-ghost btn-sm" onClick={onLogout}>
            Exit
          </button>
        </div>
      )}
    </header>
  )
}
