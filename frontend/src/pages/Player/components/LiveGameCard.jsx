import './LiveGameCard.css'
import { useNavigate } from 'react-router-dom'
import { QUEUE_NAMES } from '../constants'
import { formatDuration, getChampIcon, resolveChampName } from '../utils'

/* ─── Mini champion icon ─── */
function ChampIcon({ name, isPro, accentColor, delay = 0, size = 44 }) {
  const icon = getChampIcon(name)
  return (
    <div
      className={`lgc-champ${isPro ? ' lgc-champ-pro' : ''}`}
      style={{
        width: size, height: size,
        borderColor: isPro ? accentColor : undefined,
        boxShadow:   isPro ? `0 0 14px ${accentColor}50` : undefined,
        animationDelay: `${delay}s`,
      }}
      title={name}
    >
      {icon
        ? <img src={icon} alt={name} onError={e => { e.target.style.display = 'none' }} />
        : <span>{name?.slice(0, 2)}</span>
      }
    </div>
  )
}

export default function LiveGameCard({ live_game, player, accentColor, champMap, delay = 0 }) {
  const navigate = useNavigate()

  if (!live_game) {
    return (
      <div className="lgc-no-game" style={{ animationDelay: `${delay}s` }}>
        <div className="lgc-no-game-icon">⚔</div>
        <div>
          <div className="lgc-no-game-text">{player.summoner_name} n'est pas en game</div>
          <div className="lgc-no-game-sub">Actualisé à l'instant</div>
        </div>
      </div>
    )
  }

  const blueTeam = live_game.blue_team ?? []
  const redTeam  = live_game.red_team  ?? []
  const allTeams = [...blueTeam, ...redTeam]

  const liveParticipant = allTeams.find(
    p => (p.puuid && p.puuid === player.riot_puuid) ||
         (p.summonerName && p.summonerName === player.summoner_name)
  )

  const queueLabel = QUEUE_NAMES[live_game.gameQueueConfigId] || QUEUE_NAMES[live_game.queue_type] || 'Ranked'
  const duration   = live_game.gameLength || live_game.duration_seconds || 0

  return (
    <div className="lgc-card" style={{ animationDelay: `${delay}s` }}>
      {/* Barre accent top */}
      <div
        className="lgc-card-bar"
        style={{ background: `linear-gradient(90deg, ${accentColor}, ${accentColor}55)` }}
      />
      {/* Glow accent */}
      <div
        className="lgc-card-glow"
        style={{ background: `radial-gradient(ellipse at 50% 120%, ${accentColor}, transparent 70%)` }}
      />

      {/* Header */}
      <div className="lgc-header">
        <div className="lgc-title">
          <span className="lgc-dot" />
          {queueLabel}
          <span className="lgc-sep">·</span>
          <span className="lgc-queue">{formatDuration(duration)}</span>
        </div>
        <button className="lgc-btn" onClick={() => navigate(`/game/${live_game.id}`)}>
          Voir & Parier →
          <span className="lgc-btn-shimmer" />
        </button>
      </div>

      {/* Matchup */}
      <div className="lgc-matchup">
        {/* Blue */}
        <div className="lgc-champs-row">
          <span className="lgc-side-tag blue">Blue</span>
          <div className="lgc-champs">
            {blueTeam.slice(0, 5).map((p, i) => {
              const cName = resolveChampName(p, champMap)
              const isPro = (p.puuid && p.puuid === player.riot_puuid) ||
                            (p.summonerName && p.summonerName === player.summoner_name)
              return (
                <ChampIcon key={i} name={cName} isPro={isPro} accentColor={accentColor} delay={i * 0.04} />
              )
            })}
          </div>
        </div>

        <div className="lgc-vs-row">
          <div className="lgc-vs-line" style={{ background: '#3a6fa818' }} />
          <span className="lgc-vs-text">VS</span>
          <div className="lgc-vs-line" style={{ background: '#b03c3c18' }} />
        </div>

        {/* Red */}
        <div className="lgc-champs-row">
          <span className="lgc-side-tag red">Red</span>
          <div className="lgc-champs">
            {redTeam.slice(0, 5).map((p, i) => {
              const cName = resolveChampName(p, champMap)
              const isPro = (p.puuid && p.puuid === player.riot_puuid) ||
                            (p.summonerName && p.summonerName === player.summoner_name)
              return (
                <ChampIcon key={i} name={cName} isPro={isPro} accentColor={accentColor} delay={i * 0.04} />
              )
            })}
          </div>
        </div>
      </div>

      {/* Strip joueur suivi */}
      {liveParticipant && (() => {
        const lpChamp = resolveChampName(liveParticipant, champMap)
        return (
          <div className="lgc-pro-strip">
            {lpChamp && <span className="lgc-pro-champ">{lpChamp}</span>}
            {liveParticipant.role && lpChamp && <span className="lgc-pro-sep">·</span>}
            {liveParticipant.role && <span className="lgc-pro-kda">{liveParticipant.role}</span>}
            {liveParticipant.summonerName && (
              <span className="lgc-pro-cs">{liveParticipant.summonerName}</span>
            )}
          </div>
        )
      })()}
    </div>
  )
}