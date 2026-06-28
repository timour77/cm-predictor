const BASE = import.meta.env.VITE_API_URL || '/api'

function getHeaders() {
  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: getHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  // Auth
  login: (username, password) => request('POST', '/auth/login', { username, password }),
  register: (username, password) => request('POST', '/auth/register', { username, password }),
  telegramAuth: (initData) => request('POST', '/auth/telegram', { initData }),
  getMyStats: () => request('GET', '/auth/me/stats'),

  // Matches
  getMatches: async (competitionId, date, status) => {
    const params = new URLSearchParams({ competition_id: competitionId })
    if (date) params.set('date', date)
    if (status) params.set('status', status)
    const res = await fetch(`${BASE}/matches?${params}`, { method: 'GET', headers: getHeaders() })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || 'Request failed')
    }
    const data = await res.json()
    const fetchedAt = res.headers.get('X-Cache-Fetched-At')
    return { matches: data, fetchedAt: fetchedAt ? new Date(parseInt(fetchedAt) * 1000) : null }
  },
  // Predictions
  savePrediction: (matchId, competitionId, outcome, predictedScore) =>
    request('POST', '/predictions', { match_id: matchId, competition_id: competitionId, outcome, predicted_score: predictedScore }),
  updatePrediction: (id, matchId, competitionId, outcome, predictedScore) =>
    request('PUT', `/predictions/${id}`, { match_id: matchId, competition_id: competitionId, outcome, predicted_score: predictedScore }),
  deletePrediction: (id) => request('DELETE', `/predictions/${id}`),
  getMyPredictions: (competitionId) => {
    const params = competitionId ? `?competition_id=${competitionId}` : ''
    return request('GET', `/predictions${params}`)
  },

  getMatchPredictions: (matchId) => request('GET', `/predictions/match/${matchId}`),

  // Users
  getUsers: () => request('GET', '/users'),
  getUserStats: (userId) => request('GET', `/users/${userId}/stats`),
  getUserPredictions: (userId) => request('GET', `/users/${userId}/predictions`),

  // Bracket (all matches, no date filter)
  getBracket: (competitionId) => {
    const params = new URLSearchParams({ competition_id: competitionId })
    return fetch(`${BASE}/matches?${params}`, { method: 'GET', headers: getHeaders() })
      .then(async res => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: res.statusText }))
          throw new Error(err.detail || 'Request failed')
        }
        return res.json()
      })
  },

  // Standings
  getStandings: (competitionId) => request('GET', `/competitions/${competitionId}/standings`),

  // Teams
  getTeamMatches: (teamId, competitionId, teamName) => {
    const params = new URLSearchParams({ competition_id: competitionId })
    if (teamName) params.set('team_name', teamName)
    return request('GET', `/teams/${teamId || 0}/matches?${params}`)
  },

  // Leaderboard
  getLeaderboard: (competitionId) => {
    const params = competitionId ? `?competition_id=${competitionId}` : ''
    return request('GET', `/leaderboard${params}`)
  },
  getMyPosition: (competitionId) => {
    const params = competitionId ? `?competition_id=${competitionId}` : ''
    return request('GET', `/leaderboard/me${params}`)
  },
}
