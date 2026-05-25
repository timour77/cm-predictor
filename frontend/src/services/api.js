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
  getMyStats: () => request('GET', '/auth/me/stats'),

  // Competitions
  getCompetitions: () => request('GET', '/competitions/'),

  // Matches
  getMatches: (competitionId, date, status) => {
    const params = new URLSearchParams({ competition_id: competitionId })
    if (date) params.set('date', date)
    if (status) params.set('status', status)
    return request('GET', `/matches/?${params}`)
  },

  // Predictions
  savePrediction: (matchId, competitionId, outcome, predictedScore) =>
    request('POST', '/predictions/', { match_id: matchId, competition_id: competitionId, outcome, predicted_score: predictedScore }),
  updatePrediction: (id, matchId, competitionId, outcome, predictedScore) =>
    request('PUT', `/predictions/${id}`, { match_id: matchId, competition_id: competitionId, outcome, predicted_score: predictedScore }),
  deletePrediction: (id) => request('DELETE', `/predictions/${id}`),
  getMyPredictions: (competitionId) => {
    const params = competitionId ? `?competition_id=${competitionId}` : ''
    return request('GET', `/predictions/${params}`)
  },

  // Leaderboard
  getLeaderboard: (competitionId) => {
    const params = competitionId ? `?competition_id=${competitionId}` : ''
    return request('GET', `/leaderboard/${params}`)
  },
  getMyPosition: (competitionId) => {
    const params = competitionId ? `?competition_id=${competitionId}` : ''
    return request('GET', `/leaderboard/me${params}`)
  },
}
