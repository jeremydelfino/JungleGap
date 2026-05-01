import './PlayerHero.css'
import { useNavigate } from 'react-router-dom'
import { getRankLabel } from '../utils'
import { TIER_COLORS, REGION_LABELS } from '../constants'

export default function PlayerHero({
  player, pro_player,
  onRefresh, refreshing,
  isFav, onFavToggle, favLoading, canFav,
}) {
  const navigate    = useNavigate()
  const tierColor   = TIER_COLORS[player.tier] || '#9ca3af'
  const accentColor = pro_player?.accent_color || '#65BD62'

  return (
    <div className="ph-wrap">
      {/* ─── BANNER (grand fond avec logo team) ─── */}
      <div className="ph-banner">
        <div
          className="ph-banner-bg"
          style={pro_player
            ? { background: `linear-gradient(135deg, ${accentColor}30 0%, #171717 80%)` }
            : { background: `linear-gradient(135deg, ${tierColor}28 0%, ${tierColor}10 30%, #171717 80%)` }
          }
        />
        {pro_player?.team_logo_url && (
          <img
            className="ph-banner-team-logo"
            src={pro_player.team_logo_url}
            alt={pro_player.team}
            referrerPolicy="no-referrer"
          />
        )}

        {/* ─── HERO (intégré dans la bannière) ─── */}
        <div className="ph-hero">
          <div className="ph-hero-left">
            {/* Photo */}
            <div className="ph-photo">
              {pro_player?.photo_url ? (
                <img src={pro_player.photo_url} alt={pro_player.name} referrerPolicy="no-referrer" />
              ) : player.profile_icon_url ? (
                <img src={player.profile_icon_url} alt="icon" referrerPolicy="no-referrer" />
              ) : (
                <div className="ph-photo-initials">{player.summoner_name.slice(0, 2).toUpperCase()}</div>
              )}
              <div className="ph-photo-accent" style={{ background: pro_player ? accentColor : tierColor }} />
            </div>

            {/* Info */}
            <div className="ph-info">
              <div className="ph-name-row">
                <h1 className="ph-name">
                  {pro_player ? pro_player.name : player.summoner_name}
                  <span className="ph-tag">#{player.tag_line}</span>
                </h1>

                {pro_player && (
                  <span
                    className="ph-badge"
                    style={{
                      background: `${accentColor}20`,
                      color: accentColor,
                      borderColor: `${accentColor}55`,
                      boxShadow: `0 0 16px ${accentColor}30`,
                    }}
                  >
                    ⚡ PRO {pro_player.team && `· ${pro_player.team}`}
                  </span>
                )}
              </div>

              <div className="ph-meta">
                <span className="ph-meta-pill">{REGION_LABELS[player.region] || player.region}</span>
                {player.tier && (
                  <span className="ph-meta-pill ph-rank-pill" style={{ color: tierColor, borderColor: `${tierColor}55`, background: `${tierColor}10` }}>
                    {getRankLabel(player.tier, player.rank, player.lp)}
                  </span>
                )}
              </div>

              <div className="ph-actions">
                <button
                  className={`ph-btn ph-btn-refresh${refreshing ? ' refreshing' : ''}`}
                  onClick={onRefresh}
                  disabled={refreshing}
                >
                  <span className="ph-btn-icon">↻</span>
                  {refreshing ? 'Actualisation…' : 'Actualiser'}
                </button>

                {canFav && (
                  <button
                    className={`ph-btn ph-btn-fav${isFav ? ' is-active' : ''}`}
                    onClick={onFavToggle}
                    disabled={favLoading}
                    title={isFav ? 'Retirer des favoris' : 'Ajouter aux favoris'}
                  >
                    <span className="ph-btn-icon">{isFav ? '❤' : '♡'}</span>
                    {isFav ? 'Favori' : 'Suivre'}
                  </button>
                )}

                <button className="ph-btn ph-btn-back" onClick={() => navigate('/')}>
                  ← Retour
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="ph-banner-overlay" />
      </div>
    </div>
  )
}