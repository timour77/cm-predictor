import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { TeamModal } from '../components/TeamModal'

const WORLD_CUP_ID = 2000
const ADVANCE_POSITIONS = 2
const POSSIBLE_POSITIONS = 3

function TeamCrest({ src, name, size = 20 }) {
  const [err, setErr] = useState(false)
  if (!src || err) {
    return (
      <span className="standing-crest-placeholder" style={{ width: size, height: size, fontSize: size * 0.5 }}>
        {name?.[0] ?? '?'}
      </span>
    )
  }
  return (
    <img
      src={src}
      alt={name}
      className="standing-crest"
      style={{ width: size, height: size }}
      onError={() => setErr(true)}
    />
  )
}

function GroupTable({ group, table, onTeamClick }) {
  const label = group || '?'
  return (
    <div className="group-card">
      <div className="group-title">Группа {label}</div>
      <table className="standing-table">
        <thead>
          <tr>
            <th>#</th>
            <th className="standing-team-col">Команда</th>
            <th title="Игры">И</th>
            <th title="Победы" className="standing-hide-xs">В</th>
            <th title="Ничьи" className="standing-hide-xs">Н</th>
            <th title="Поражения" className="standing-hide-xs">П</th>
            <th title="Разница мячей">±</th>
            <th title="Очки">О</th>
          </tr>
        </thead>
        <tbody>
          {table.map(row => {
            let rowClass = 'standing-row'
            if (row.position <= ADVANCE_POSITIONS) rowClass += ' standing-advance'
            else if (row.position === POSSIBLE_POSITIONS) rowClass += ' standing-possible'
            return (
              <tr key={row.team_name} className={rowClass} onClick={() => onTeamClick(row)} style={{ cursor: 'pointer' }}>
                <td className="standing-pos">{row.position}</td>
                <td className="standing-team">
                  <TeamCrest src={row.team_crest} name={row.team_name} />
                  <span className="standing-team-name">{row.team_name}</span>
                </td>
                <td>{row.played}</td>
                <td className="standing-hide-xs">{row.won}</td>
                <td className="standing-hide-xs">{row.draw}</td>
                <td className="standing-hide-xs">{row.lost}</td>
                <td className={row.goal_difference > 0 ? 'standing-gd-pos' : row.goal_difference < 0 ? 'standing-gd-neg' : ''}>
                  {row.goal_difference > 0 ? `+${row.goal_difference}` : row.goal_difference}
                </td>
                <td className="standing-pts">{row.points}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export function GroupsPage() {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedTeam, setSelectedTeam] = useState(null)

  useEffect(() => {
    setLoading(true)
    api.getStandings(WORLD_CUP_ID)
      .then(setGroups)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <div className="groups-legend">
        <span className="legend-item legend-advance">Выход в 1/8</span>
        <span className="legend-item legend-possible">Возможный выход</span>
      </div>

      {loading && (
        <div className="loader">
          <div className="spinner" />
          Загрузка групп...
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}

      {!loading && !error && groups.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <div className="empty-state-text">Таблицы групп пока недоступны</div>
        </div>
      )}

      {groups.map(g => (
        <GroupTable
          key={g.group}
          group={g.group}
          table={g.table}
          onTeamClick={setSelectedTeam}
        />
      ))}

      {selectedTeam && (
        <TeamModal
          teamId={selectedTeam.team_id}
          teamName={selectedTeam.team_name}
          teamCrest={selectedTeam.team_crest}
          competitionId={WORLD_CUP_ID}
          onClose={() => setSelectedTeam(null)}
        />
      )}
    </div>
  )
}
