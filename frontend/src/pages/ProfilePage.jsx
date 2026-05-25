import { useState, useEffect } from 'react'
import { api } from '../services/api'

function formatJoinDate(isoStr) {
  if (!isoStr) return '—'
  return new Date(isoStr).toLocaleDateString('ru', { year: 'numeric', month: 'long' })
}

function accuracy(correct, total) {
  if (!total) return '—'
  return Math.round((correct / total) * 100) + '%'
}

export function ProfilePage({ user, onLogout }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getMyStats()
      .then(setStats)
      .finally(() => setLoading(false))
  }, [])

  const statCells = [
    { label: 'Очки',     value: loading ? '…' : (stats?.total_points ?? 0) },
    { label: 'Место',    value: loading ? '…' : (stats?.rank ?? '—') },
    { label: 'Прогнозы', value: loading ? '…' : (stats?.total_predictions ?? 0) },
    { label: 'Точность', value: loading ? '…' : accuracy(stats?.correct_predictions, stats?.total_predictions) },
  ]

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
        <div style={{ fontSize: '12px', opacity: 0.9 }}>
          {loading ? '…' : `В игре с ${formatJoinDate(stats?.created_at)}`}
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px',
        marginBottom: '16px'
      }}>
        {statCells.map(({ label, value }) => (
          <div key={label} style={{
            textAlign: 'center',
            padding: '16px 12px',
            background: 'var(--bg2)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border)'
          }}>
            <div style={{ fontSize: '26px', fontWeight: '700', color: 'var(--primary)' }}>{value}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
          </div>
        ))}
      </div>

      <button className="btn btn-danger btn-block" onClick={onLogout}>
        Выйти
      </button>
    </div>
  )
}
