export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const STATUS_LABELS = {
  SCHEDULED: 'Scheduled',
  TIMED: 'Scheduled',
  IN_PLAY: 'Live',
  PAUSED: 'Live',
  FINISHED: 'Finished',
  SUSPENDED: 'Suspended',
  POSTPONED: 'Postponed',
  CANCELLED: 'Cancelled',
}

export const STATUS_COLORS = {
  SCHEDULED: '#3b82f6',
  TIMED: '#3b82f6',
  IN_PLAY: '#f59e0b',
  PAUSED: '#f59e0b',
  FINISHED: '#6b7280',
  SUSPENDED: '#ef4444',
  POSTPONED: '#ef4444',
  CANCELLED: '#ef4444',
}
