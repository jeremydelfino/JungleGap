import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000'
})

/* ─── REQUEST : injecte le token ─── */
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

/* ─── RESPONSE : gère 401 globalement ─── */
let isRedirecting = false

api.interceptors.response.use(
  response => response,
  error => {
    const status = error.response?.status
    const url    = error.config?.url || ''

    const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/verify')

    if (status === 401 && !isAuthEndpoint && !isRedirecting) {
      isRedirecting = true

      localStorage.removeItem('token')
      localStorage.removeItem('user')

      try {
        const { default: useAuthStore } = require('../store/auth')
        useAuthStore.getState().logout()
      } catch {}

      const here = window.location.pathname
      if (here !== '/login' && here !== '/register' && here !== '/') {
        window.location.href = '/login?expired=1'
      } else {
        isRedirecting = false
      }
    }
    return Promise.reject(error)
  }
)

export default api