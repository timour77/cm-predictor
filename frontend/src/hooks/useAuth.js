import { useState, useCallback } from 'react'
import { api } from '../services/api'

export function useAuth() {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user')
    return stored ? JSON.parse(stored) : null
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const login = useCallback(async (username, password) => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.login(username, password)
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', JSON.stringify({ id: data.user_id, username: data.username }))
      setUser({ id: data.user_id, username: data.username })
      return true
    } catch (e) {
      setError(e.message)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const register = useCallback(async (username, password) => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.register(username, password)
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', JSON.stringify({ id: data.user_id, username: data.username }))
      setUser({ id: data.user_id, username: data.username })
      return true
    } catch (e) {
      setError(e.message)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const telegramLogin = useCallback(async (initData) => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.telegramAuth(initData)
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', JSON.stringify({ id: data.user_id, username: data.username }))
      setUser({ id: data.user_id, username: data.username })
      return true
    } catch (e) {
      setError(e.message)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }, [])

  return { user, loading, error, login, register, telegramLogin, logout }
}
