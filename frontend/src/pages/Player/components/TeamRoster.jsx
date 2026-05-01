import './TeamRoster.css'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../../api/client'
import { TIER_COLORS, APEX_TIERS } from '../constants'

const ROLE_ORDER = ['TOP', 'JUNGLE', 'MID', 'MIDDLE', 'ADC', 'BOTTOM', 'SUPPORT', 'UTILITY']
const ROLE_NORM  = { MIDDLE: 'MID', BOTTOM: 'ADC', UTILITY: 'SUPPORT' }
const ROLE_LABELS = { TOP: 'Top', JUNGLE: 'Jungle', MID: 'Mid', ADC: 'Bot', SUPPORT: 'Sup' }

export default function TeamRoster({ teamCode, teamLogo, accentColor, currentPlayerPuuid, delay = 0 }) {
  const navigate = useNavigate()
  const [roster, setRoster]   = useState([])
  const [ranks,  setRanks]    = useState({})
  const [loading, setLoading] = useState(true)

  // Fetch roster
  useEffect(() => {
    if (!teamCode) return
    api.get(`/esports/teams/${teamCode}`)
      .then(r => setRoster(r.data?.roster || []))
      .catch(() => setRoster([]))
      .finally(() => setLoading(false))
  }, [teamCode])

  // Fetch ranks (batch) une fois le roster chargé
  useEffect(() => {
    const puuids = roster.filter(p => p.riot_puuid).map(p => p.riot_puuid)
    if (puuids.length === 0) return
    api.post('/players/batch-ranks', { puuids })
      .then(r => {
        const map = {}
        r.data.forEach(rk => { map[rk.puuid] = rk })
        setRanks(map)
      })
      .catch(() => {})
  }, [roster])

  if (loading || roster.length === 0) return null

  // Trier par rôle
  const sorted = [...roster]
    .filter(p => p.is_starter !== false)
    .sort((a, b) => {
      const ra = ROLE_ORDER.indexOf(a.role) === -1 ? 99 : ROLE_ORDER.indexOf(a.role)
      const rb = ROLE_ORDER.indexOf(b.role) === -1 ? 99 : ROLE_ORDER.indexOf(b.role)
      return ra - rb
    })
    .slice(0, 5)

  const handleClick = (player) => {
    const rank = ranks[player.riot_puuid]
    if (rank?.summoner_name && rank?.tag_line && rank?.region) {
      navigate(`/player/${rank.region}/${encodeURIComponent(rank.summoner_name)}/${encodeURIComponent(rank.tag_line)}`)
    }
  }

  return (
    <div className="tr-wrap" style={{ animationDelay: `${delay}s` }}>
      <div className="tr-header">
        <div className="tr-title">
          {teamLogo && <img src={teamLogo} alt={teamCode} className="tr-team-logo" referrerPolicy="no-referrer" />}
          <span className="tr-title-text">Roster {teamCode}</span>
        </div>
      </div>

      <div className="tr-grid">
        {sorted.map((p, i) => {
          const role     = ROLE_NORM[p.role] || p.role
          const roleLbl  = ROLE_LABELS[role] || role
          const rank     = ranks[p.riot_puuid]
          const tierColor = rank?.tier ? TIER_COLORS[rank.tier] : '#3a3a3a'
          const isApex   = rank?.tier && APEX_TIERS.has(rank.tier)
          const isCurrent = p.riot_puuid === currentPlayerPuuid
          const hasRank  = rank?.tier
          const clickable = !!(rank?.summoner_name && rank?.tag_line)

          return (
            <div
              key={p.id || i}
              className={`tr-card${isCurrent ? ' tr-card-current' : ''}${clickable ? ' tr-card-clickable' : ''}`}
              onClick={() => clickable && handleClick(p)}
              style={{
                animationDelay: `${delay + 0.05 + i * 0.05}s`,
                '--tr-tier-color': tierColor,
                '--tr-accent': accentColor || '#65BD62',
              }}
            >
              <div className="tr-role-badge">{roleLbl}</div>

              <div className="tr-photo-wrap">
                <div className="tr-photo-glow" />
                <div className="tr-photo">
                  {p.photo_url
                    ? <img src={p.photo_url} alt={p.summoner_name} referrerPolicy="no-referrer" onError={e => { e.target.style.display = 'none' }} />
                    : <span className="tr-photo-fallback">{p.summoner_name?.slice(0, 2).toUpperCase()}</span>
                  }
                </div>
              </div>

              <div className="tr-info">
                <div className="tr-name">{p.summoner_name}</div>
                {hasRank ? (
                  <div className="tr-rank" style={{ color: tierColor }}>
                    {rank.tier.charAt(0) + rank.tier.slice(1).toLowerCase()}
                    {!isApex && rank.rank && <span className="tr-rank-div"> {rank.rank}</span>}
                    <span className="tr-lp"> · {rank.lp ?? 0} LP</span>
                  </div>
                ) : (
                  <div className="tr-rank tr-rank-empty">— Non classé —</div>
                )}
              </div>

              {isCurrent && <div className="tr-current-tag">Profil actuel</div>}
            </div>
          )
        })}
      </div>
    </div>
  )
}