import './JungleGapSidebar.css'
import { useNavigate } from 'react-router-dom'

export default function JungleGapSidebar({ junglegap_profile, delay = 0 }) {
  const navigate = useNavigate()

  if (!junglegap_profile) {
    return (
      <div className="jgs-card jgs-card-empty" style={{ animationDelay: `${delay}s` }}>
        <div className="jgs-empty-glow" />
        <div className="jgs-empty-icon">🎯</div>
        <div className="jgs-empty-content">
          <div className="jgs-empty-title">Ce joueur n'a pas de compte JungleGap</div>
          <div className="jgs-empty-text">Si ce compte est le votre, créez un compte JungleGap et liez-le à votre profil</div>
        </div>
        <button className="jgs-register-btn" onClick={() => navigate('/register')}>
          Créer un compte
          <span className="jgs-btn-arrow">→</span>
        </button>
      </div>
    )
  }

  const { username, avatar_url, coins, equipped_title, bet_stats, id } = junglegap_profile

  return (
    <div className="jgs-card" style={{ animationDelay: `${delay}s` }}>
      {/* Glow accent */}
      <div className="jgs-bg-glow" />

      {/* Badge en haut à gauche */}
      <div className="jgs-tag">
        <span className="jgs-tag-dot" />
        Compte JungleGap
      </div>

      <div className="jgs-content">
        {/* Avatar */}
        <div className="jgs-avatar">
          {avatar_url
            ? <img src={avatar_url} alt={username} referrerPolicy="no-referrer" onError={e => { e.target.style.display = 'none' }} />
            : <span>{username?.slice(0, 2).toUpperCase()}</span>
          }
          <div className="jgs-avatar-ring" />
        </div>

        {/* User info */}
        <div className="jgs-user-info">
          <div className="jgs-username">{username}</div>
          {equipped_title && <div className="jgs-title">✦ {equipped_title}</div>}
          <div className="jgs-coins">
            <span className="jgs-coin-dot" />
            <span className="jgs-coin-val">{coins?.toLocaleString() ?? 0}</span>
            <span className="jgs-coin-lbl">coins</span>
          </div>
        </div>

        {/* Stats inline */}
        <div className="jgs-stats">
          <div className="jgs-stat">
            <div className="jgs-stat-val green">{bet_stats?.winrate != null ? `${bet_stats.winrate}%` : '—'}</div>
            <div className="jgs-stat-lbl">Win rate</div>
          </div>
          <div className="jgs-stat-sep" />
          <div className="jgs-stat">
            <div className="jgs-stat-val accent">{bet_stats?.won ?? '—'}</div>
            <div className="jgs-stat-lbl">Gagnés</div>
          </div>
          <div className="jgs-stat-sep" />
          <div className="jgs-stat">
            <div className="jgs-stat-val gold">
              {bet_stats?.streak > 0 ? `🔥${bet_stats.streak}` : (bet_stats?.streak ?? '—')}
            </div>
            <div className="jgs-stat-lbl">Streak</div>
          </div>
          <div className="jgs-stat-sep" />
          <div className="jgs-stat">
            <div className="jgs-stat-val muted">{bet_stats?.total ?? '—'}</div>
            <div className="jgs-stat-lbl">Total</div>
          </div>
        </div>

        {/* CTA */}
        <button className="jgs-profile-btn" onClick={() => navigate(`/profile/${id}`)}>
          Voir le profil
          <span className="jgs-btn-arrow">→</span>
          <span className="jgs-profile-btn-shimmer" />
        </button>
      </div>
    </div>
  )
}