import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { STAGE_LABELS, STAGE_ORDER } from '../components/MatchCard'

const WORLD_CUP_ID = 2000

const MATCH_H = 64
const MATCH_W = 134
const COL_GAP = 36
const SLOT_H = 88    // match height + gap between matches in first round
const HEADER_H = 28  // space for stage label above matches

function centerY(roundIdx, matchIdx) {
  return HEADER_H + (matchIdx + 0.5) * Math.pow(2, roundIdx) * SLOT_H
}

function colX(roundIdx) {
  return roundIdx * (MATCH_W + COL_GAP)
}

function Slot({ match, x, y }) {
  const done = match?.status === 'FINISHED'
  const hw = done && match.home_goals > match.away_goals
  const aw = done && match.away_goals > match.home_goals
  const live = match?.status === 'IN_PLAY' || match?.status === 'PAUSED' || match?.status === 'LIVE'

  const date = match?.match_date
    ? new Date(match.match_date).toLocaleDateString('ru', { day: 'numeric', month: 'short', timeZone: 'Europe/Madrid' })
    : null

  const teamRow = (crest, name, goals, bold, muted) => (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 5, padding: '0 8px',
      height: MATCH_H / 2,
      opacity: muted ? 0.38 : 1,
      transition: 'opacity 0.15s',
    }}>
      {crest
        ? <img src={crest} style={{ width: 16, height: 16, objectFit: 'contain', flexShrink: 0 }} alt=""
            onError={e => { e.target.style.display = 'none' }} />
        : <div style={{ width: 16, flexShrink: 0 }} />
      }
      <span style={{
        flex: 1, fontSize: 11, fontWeight: bold ? 700 : 400,
        color: bold ? 'var(--text)' : 'var(--text-muted)',
        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
      }}>
        {!name || name === 'TBD' ? '?' : name}
      </span>
      {(done || live) && goals !== null && goals !== undefined && (
        <span style={{ fontSize: 12, fontWeight: bold ? 700 : 400, color: bold ? 'var(--text)' : 'var(--text-muted)', minWidth: 14, textAlign: 'right', flexShrink: 0 }}>
          {goals}
        </span>
      )}
    </div>
  )

  return (
    <div style={{
      position: 'absolute',
      left: x,
      top: y - MATCH_H / 2,
      width: MATCH_W,
      height: MATCH_H,
      background: 'rgba(22, 32, 54, 0.85)',
      backdropFilter: 'blur(14px)',
      WebkitBackdropFilter: 'blur(14px)',
      border: `1px solid ${live ? 'rgba(251,191,36,0.4)' : 'rgba(255,255,255,0.1)'}`,
      borderRadius: 10,
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
    }}>
      {match ? (
        <>
          {teamRow(match.home_team_crest, match.home_team, match.home_goals, hw, aw)}
          <div style={{ height: 1, background: 'rgba(255,255,255,0.08)', flexShrink: 0 }} />
          {teamRow(match.away_team_crest, match.away_team, match.away_goals, aw, hw)}
          {!done && !live && date && (
            <div style={{
              position: 'absolute', bottom: 3, right: 7,
              fontSize: 9, color: 'rgba(148,163,184,0.6)', lineHeight: 1, pointerEvents: 'none',
            }}>
              {date}
            </div>
          )}
          {live && (
            <div style={{
              position: 'absolute', bottom: 3, right: 7,
              fontSize: 9, color: 'var(--warning)', lineHeight: 1, fontWeight: 700,
            }}>
              LIVE
            </div>
          )}
        </>
      ) : (
        <div style={{ textAlign: 'center', fontSize: 11, color: 'rgba(148,163,184,0.4)' }}>TBD</div>
      )}
    </div>
  )
}

export function BracketPage() {
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getBracket(WORLD_CUP_ID)
      .then(data => setMatches(data.filter(m => m.stage && m.stage !== 'GROUP_STAGE')))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const playoffStages = STAGE_ORDER.filter(s => s !== '3RD_PLACE')

  // Collect each stage sorted by external_id (the API's stable identifier)
  const byStage = {}
  playoffStages.forEach(stage => {
    const sm = matches.filter(m => m.stage === stage).sort((a, b) => a.external_id - b.external_id)
    if (sm.length) byStage[stage] = sm
  })
  const activeStages = playoffStages.filter(s => byStage[s])

  // For the 2026 WC, LAST_16 slot IDs are lower than LAST_32 IDs (pre-assigned
  // before the 48-team format added the LAST_32 round), and the bracket topology
  // is non-consecutive: LAST_32[8,9] (Brazil/IvoryCoast) feeds LAST_16[2],
  // not LAST_16[4] as floor(mi/2) would imply with an unmodified sort.
  //
  // Fix: for each round, reorder its matches so that consecutive pairs align
  // with the correct slot in the NEXT round. We infer the pairing by looking
  // at which current-round teams already appear in the next round.
  // Consecutive pairs in the external_id sort always feed the same next-round slot.
  const rounds = []
  activeStages.forEach((stage, si) => {
    let sm = byStage[stage]
    const nextSm = byStage[activeStages[si + 1]]

    if (nextSm) {
      const numPairs = Math.floor(sm.length / 2)

      // Map every team name → pair index (floor(i/2)) in the current stage
      const teamToPair = {}
      sm.forEach((m, i) => {
        const p = Math.floor(i / 2)
        if (m.home_team && m.home_team !== 'TBD') teamToPair[m.home_team] = p
        if (m.away_team && m.away_team !== 'TBD') teamToPair[m.away_team] = p
      })

      // For each next-round slot, find which current-round pair feeds it
      const assignedPairs = new Set()
      const pairForSlot = nextSm.map(m => {
        for (const team of [m.home_team, m.away_team]) {
          if (team && team !== 'TBD' && teamToPair[team] !== undefined) {
            const p = teamToPair[team]
            if (!assignedPairs.has(p)) { assignedPairs.add(p); return p }
          }
        }
        return null
      })

      // Fill slots with no known team using remaining pairs (original id order)
      const remaining = []
      for (let i = 0; i < numPairs; i++) if (!assignedPairs.has(i)) remaining.push(i)
      let ri = 0
      const finalPairs = pairForSlot.map(p => p !== null ? p : remaining[ri++])

      // Rebuild the stage in the corrected order
      const reordered = []
      finalPairs.forEach(p => {
        if (sm[p * 2]) reordered.push(sm[p * 2])
        if (sm[p * 2 + 1]) reordered.push(sm[p * 2 + 1])
      })
      sm = reordered
    }

    rounds.push({ stage, matches: sm })
  })
  const thirdPlace = matches.find(m => m.stage === '3RD_PLACE')

  const firstCount = rounds[0]?.matches.length ?? 0
  const NAV_PAD = 96
  const totalH = HEADER_H + firstCount * SLOT_H + (thirdPlace ? MATCH_H + 48 : 0) + NAV_PAD
  const totalW = rounds.length ? colX(rounds.length - 1) + MATCH_W : 0

  // Build SVG connector lines between rounds
  const lines = []
  rounds.forEach((round, ri) => {
    if (ri >= rounds.length - 1) return
    round.matches.forEach((_, mi) => {
      const x1 = colX(ri) + MATCH_W
      const y1 = centerY(ri, mi)
      const midX = colX(ri) + MATCH_W + COL_GAP / 2
      const nextMI = Math.floor(mi / 2)
      const y2 = centerY(ri + 1, nextMI)

      // Horizontal from right edge of match to midpoint
      lines.push(<line key={`h-${ri}-${mi}`} x1={x1} y1={y1} x2={midX} y2={y1} />)

      // Vertical at midpoint + horizontal to next round (drawn once per pair from the top match)
      if (mi % 2 === 0) {
        const yPartner = mi + 1 < round.matches.length ? centerY(ri, mi + 1) : y1
        lines.push(<line key={`v-${ri}-${mi}`} x1={midX} y1={y1} x2={midX} y2={yPartner} />)
        lines.push(<line key={`h2-${ri}-${nextMI}`} x1={midX} y1={y2} x2={colX(ri + 1)} y2={y2} />)
      }
    })
  })

  if (loading) return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 12 }}>
      <div className="spinner" />
      <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>Загрузка сетки...</span>
    </div>
  )

  if (error) return (
    <div style={{ padding: 16 }}><div className="error-msg">{error}</div></div>
  )

  if (!rounds.length) return (
    <div className="empty-state">
      <div className="empty-state-icon">🏆</div>
      <div className="empty-state-text">Плей-офф ещё не определён</div>
    </div>
  )

  const thirdPlaceY = HEADER_H + firstCount * SLOT_H + 32

  return (
    <div style={{ flex: 1, overflow: 'auto', WebkitOverflowScrolling: 'touch', padding: 16 }}>
      <div style={{ position: 'relative', width: totalW, height: totalH }}>

        {/* Stage column labels */}
        {rounds.map((r, ri) => (
          <div key={r.stage} style={{
            position: 'absolute', left: colX(ri), top: 0, width: MATCH_W,
            textAlign: 'center', fontSize: 10, fontWeight: 700,
            color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.06em',
            lineHeight: `${HEADER_H}px`,
          }}>
            {STAGE_LABELS[r.stage]}
          </div>
        ))}

        {/* SVG connector lines */}
        <svg
          style={{ position: 'absolute', top: 0, left: 0, width: totalW, height: totalH, overflow: 'visible', pointerEvents: 'none' }}
        >
          <g style={{ stroke: 'rgba(255,255,255,0.15)', strokeWidth: 1.5, fill: 'none', strokeLinecap: 'round' }}>
            {lines}
          </g>
        </svg>

        {/* Match slots */}
        {rounds.map((r, ri) =>
          r.matches.map((match, mi) => (
            <Slot key={match.external_id} match={match} x={colX(ri)} y={centerY(ri, mi)} />
          ))
        )}

        {/* Third place match — shown below main bracket */}
        {thirdPlace && (
          <>
            <div style={{
              position: 'absolute', left: 0, top: thirdPlaceY - MATCH_H / 2 - 20,
              fontSize: 10, fontWeight: 700, color: 'var(--text-muted)',
              textTransform: 'uppercase', letterSpacing: '0.06em',
            }}>
              {STAGE_LABELS['3RD_PLACE']}
            </div>
            <Slot match={thirdPlace} x={0} y={thirdPlaceY} />
          </>
        )}
      </div>
    </div>
  )
}
