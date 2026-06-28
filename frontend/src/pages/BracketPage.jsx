import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { MatchCard, STAGE_LABELS, STAGE_ORDER } from '../components/MatchCard'

const WORLD_CUP_ID = 2000

const KNOCKOUT_STAGES = new Set(['LAST_32', 'LAST_16', 'QUARTER_FINALS', 'SEMI_FINALS', '3RD_PLACE', 'FINAL'])

function formatDate(utcDate) {
  if (!utcDate) return ''
  return new Date(utcDate).toLocaleDateString('ru', {
    day: 'numeric', month: 'long', timeZone: 'Europe/Madrid',
  })
}

export function BracketPage({ user }) {
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  function load() {
    setLoading(true)
    setError(null)
    api.getBracket(WORLD_CUP_ID)
      .then(data => {
        const knockout = data.filter(m => KNOCKOUT_STAGES.has(m.stage))
        setMatches(knockout)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const grouped = STAGE_ORDER.reduce((acc, stage) => {
    const stageMatches = matches
      .filter(m => m.stage === stage)
      .sort((a, b) => new Date(a.match_date) - new Date(b.match_date))
    if (stageMatches.length) acc.push({ stage, matches: stageMatches })
    return acc
  }, [])

  return (
    <div className="page">
      {loading && (
        <div className="loader">
          <div className="spinner" />
          Загрузка сетки...
        </div>
      )}

      {error && <div className="error-msg" style={{ marginBottom: 12 }}>{error}</div>}

      {!loading && !error && grouped.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">🏆</div>
          <div className="empty-state-text">Плей-офф матчи ещё не определены</div>
        </div>
      )}

      {grouped.map(({ stage, matches: stageMatches }) => (
        <div key={stage} className="bracket-round">
          <div className="bracket-round-header">
            <span className="bracket-round-title">{STAGE_LABELS[stage] || stage}</span>
            <span className="bracket-round-date">{formatDate(stageMatches[0].match_date)}</span>
          </div>
          {stageMatches.map(match => (
            <MatchCard
              key={match.external_id}
              match={match}
              currentUserId={user?.id}
              onPredictionSaved={load}
            />
          ))}
        </div>
      ))}
    </div>
  )
}
