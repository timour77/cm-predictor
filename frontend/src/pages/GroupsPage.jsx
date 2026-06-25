import { useState, useEffect } from 'react'
import { api } from '../services/api'

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

function formatMatchDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

function formatMatchTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

function TeamModal({ team, onClose }) {
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getTeamMatches(team.team_id, WORLD_CUP_ID)
      .then(data => setMatches(data.sort((a, b) => new Date(a.match_date) - new Date(b.match_date))))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [team.team_id])

  function getResult(match) {
    if (match.status !== 'FINISHED' && match.status !== 'AWARDED') return null
    const isHome = match.home_team === team.team_name
    const own = isHome ? match.home_goals : match.away_goals
    const opp = isHome ? match.away_goals : match.home_goals
    if (own > opp) return 'W'
    if (own < opp) return 'L'
    return 'D'
  }

  return (
    <>
      <div className="modal-overlay" onClick={onClose} />
      <div className="modal-sheet">
        <div className="modal-handle" />
        <div className="modal-header">
          <div className="modal-team-title">
            <TeamCrest src={team.team_crest} name={team.team_name} size={36} />
            <span className="modal-team-name">{team.team_name}</span>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="loader">
              <div className="spinner" />
              Загрузка матчей...
            </div>
          )}
          {error && <div className="error-msg">{error}</div>}
          {!loading && !error && matches.length === 0 && (
            <div className="empty-state" style={{ padding: '24px' }}>
              <div className="empty-state-icon">📅</div>
              <div className="empty-state-text">Матчей не найдено</div>
            </div>
          )}
          {matches.map(m => {
            const isHome = m.home_team === team.team_name
            const opponent = isHome ? m.away_team : m.home_team
            const opponentCrest = isHome ? m.away_team_crest : m.home_team_crest
            const finished = m.status === 'FINISHED' || m.status === 'AWARDED'
            const result = getResult(m)
            const ownGoals = isHome ? m.home_goals : m.away_goals
            const oppGoals = isHome ? m.away_goals : m.home_goals

            return (
              <div key={m.external_id} className="team-match-row">
                <div className="team-match-day">тур {m.matchday}</div>
                <div className="team-match-main">
                  <div className="team-match-opponent">
                    <TeamCrest src={opponentCrest} name={opponent} size={24} />
                    <span className="team-match-opp-name">{opponent}</span>
                    <span className="team-match-venue">{isHome ? 'дома' : 'в гостях'}</span>
                  </div>
                  <div className="team-match-right">
                    {finished ? (
                      <>
                        <span className="team-match-score">
                          {isHome ? `${ownGoals}:${oppGoals}` : `${ownGoals}:${oppGoals}`}
                        </span>
                        <span className={`result-badge result-${result}`}>{result}</span>
                      </>
                    ) : (
                      <span className="team-match-date">
                        {formatMatchDate(m.match_date)}
                        <span className="team-match-time">{formatMatchTime(m.match_date)}</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </>
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
        <TeamModal team={selectedTeam} onClose={() => setSelectedTeam(null)} />
      )}
    </div>
  )
}
