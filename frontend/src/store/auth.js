import { create } from 'zustand'

/* ─── Helper : décode le JWT et vérifie l'expiration ─── */
function isTokenValid(token) {
  if (!token) return false
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    if (!payload.exp) return true
    return payload.exp * 1000 > Date.now()
  } catch {
    return false
  }
}

/* ─── Hydrate depuis localStorage en validant le token ─── */
function hydrate() {
  const token = localStorage.getItem('token')
  const user  = JSON.parse(localStorage.getItem('user') || 'null')

  if (!token || !isTokenValid(token)) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    return { user: null, token: null }
  }
  return { user, token }
}

const useAuthStore = create((set) => ({
  ...hydrate(),

  login: (user, token) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    set({ user, token })
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ user: null, token: null })
  },

  updateCoins: (coins) => set(state => {
    if (!state.user) return state
    const updatedUser = { ...state.user, coins }
    localStorage.setItem('user', JSON.stringify(updatedUser))
    return { user: updatedUser }
  }),

  updateUser: (fields) => set(state => {
    if (!state.user) return state
    const updatedUser = { ...state.user, ...fields }
    localStorage.setItem('user', JSON.stringify(updatedUser))
    return { user: updatedUser }
  }),
}))

export default useAuthStore