import './Navbar.css'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../../../store/auth'

export default function Navbar() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  return (
    <nav className="navbar">
      <div className="navbar-logo" onClick={() => navigate('/')}>JINXIT</div>

      <div className="navbar-right">
        {user ? (
          <>
            <span className="navbar-bets-link" onClick={() => navigate('/bets')}>
              Mes paris
            </span>
            <div className="navbar-coins" onClick={() => navigate('/profile')}>
              <div className="coin-dot" />
              {user.coins?.toLocaleString()} coins
            </div>
            <div className="navbar-avatar" onClick={() => navigate('/profile')}>
              {user.username?.slice(0, 2).toUpperCase()}
            </div>
            <button className="btn-nav-ghost" onClick={() => { logout(); navigate('/') }}>
              Déconnexion
            </button>
          </>
        ) : (
          <>
            <button className="btn-nav-ghost" onClick={() => navigate('/login')}>
              Connexion
            </button>
            <button className="btn-nav-primary" onClick={() => navigate('/register')}>
              S'inscrire
            </button>
          </>
        )}
      </div>
    </nav>
  )
}