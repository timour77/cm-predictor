import { useEffect, useState } from 'react'
import { api } from '../services/api'

export function CompetitionSelector({ value, onChange }) {
  const [competitions, setCompetitions] = useState([])

  useEffect(() => {
    api.getCompetitions().then(setCompetitions).catch(() => {})
  }, [])

  return (
    <div>
      <div className="section-label" style={{ marginBottom: 6 }}>Championship</div>
      <select
        className="select"
        value={value || ''}
        onChange={e => onChange(Number(e.target.value))}
      >
        <option value="">— select —</option>
        {competitions.map(c => (
          <option key={c.id} value={c.id}>
            {c.name} {c.area ? `(${c.area})` : ''}
          </option>
        ))}
      </select>
    </div>
  )
}
