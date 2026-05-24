export function ProfilePage({ user, onLogout }) {
  return (
    <div className="page">
      <div style={{
        background: 'linear-gradient(135deg, var(--primary), var(--accent))',
        borderRadius: 'var(--radius)',
        padding: '24px 16px',
        marginBottom: '16px',
        textAlign: 'center',
        color: 'white'
      }}>
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '32px',
          margin: '0 auto 12px',
          border: '3px solid white'
        }}>👤</div>
        <div style={{ fontSize: '20px', fontWeight: '700', marginBottom: '4px' }}>{user.username}</div>
        <div style={{ fontSize: '12px', opacity: 0.9 }}>Присоединился 2 месяца назад</div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px',
        padding: '16px',
        background: 'var(--bg2)',
        borderRadius: 'var(--radius-sm)',
        marginBottom: '16px'
      }}>
        <div style={{
          textAlign: 'center',
          padding: '12px',
          background: 'var(--bg)',
          borderRadius: 'var(--radius-sm)'
        }}>
          <div style={{ fontSize: '24px', fontWeight: '700', color: 'var(--primary)' }}>2,150</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', textTransform: 'uppercase' }}>Очки</div>
        </div>
        <div style={{
          textAlign: 'center',
          padding: '12px',
          background: 'var(--bg)',
          borderRadius: 'var(--radius-sm)'
        }}>
          <div style={{ fontSize: '24px', fontWeight: '700', color: 'var(--primary)' }}>42</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', textTransform: 'uppercase' }}>Место</div>
        </div>
        <div style={{
          textAlign: 'center',
          padding: '12px',
          background: 'var(--bg)',
          borderRadius: 'var(--radius-sm)'
        }}>
          <div style={{ fontSize: '24px', fontWeight: '700', color: 'var(--primary)' }}>24</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', textTransform: 'uppercase' }}>Прогнозы</div>
        </div>
        <div style={{
          textAlign: 'center',
          padding: '12px',
          background: 'var(--bg)',
          borderRadius: 'var(--radius-sm)'
        }}>
          <div style={{ fontSize: '24px', fontWeight: '700', color: 'var(--primary)' }}>58%</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', textTransform: 'uppercase' }}>Точность</div>
        </div>
      </div>

      <button
        className="btn btn-primary btn-block"
        onClick={onLogout}
        style={{ marginTop: '16px' }}
      >
        Выйти
      </button>
    </div>
  )
}
