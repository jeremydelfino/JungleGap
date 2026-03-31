import './Player.css'
import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../../api/client'
import useAuthStore from '../../store/auth'

const TIER_COLORS = {
  CHALLENGER: '#f4c430', GRANDMASTER: '#ef4444', MASTER: '#a78bfa',
  DIAMOND: '#378add', EMERALD: '#65BD62', PLATINUM: '#00b4d8',
  GOLD: '#e2b147', SILVER: '#9ca3af', BRONZE: '#cd7f32', IRON: '#6b7280',
}

const QUEUE_NAMES = {
  420: 'Ranked Solo', 440: 'Ranked Flex', 400: 'Normal', 450: 'ARAM',
}

const CHAMP_VERSION = '14.24.1'

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const h = Math.floor(diff / 3600000)
  const m = Math.floor(diff / 60000)
  if (h > 24) return `il y a ${Math.floor(h / 24)}j`
  if (h > 0)  return `il y a ${h}h`
  return `il y a ${m}m`
}

function getChampIcon(championName) {
  if (!championName || championName === '???' || championName === '??') return null
  const ddUrl = `https://ddragon.leagueoflegends.com/cdn/${CHAMP_VERSION}/img/champion/${championName}.png`
  return `${api.defaults.baseURL}/players/proxy/icon?url=${encodeURIComponent(ddUrl)}`
}

// Résout championName depuis champMap si le champ est vide
function resolveChampName(p, champMap) {
  if (p.championName && p.championName.trim()) return p.championName.trim()
  if (p.championId && champMap[String(p.championId)]) return champMap[String(p.championId)]
  return null
}

function groupByChampion(matches) {
  const map = {}
  matches.forEach(m => {
    if (!map[m.champion]) map[m.champion] = { games: 0, wins: 0, kills: 0, deaths: 0, assists: 0 }
    map[m.champion].games++
    if (m.win) map[m.champion].wins++
    map[m.champion].kills   += m.kills
    map[m.champion].deaths  += m.deaths
    map[m.champion].assists += m.assists
  })
  return Object.entries(map)
    .map(([name, s]) => ({
      name,
      games:   s.games,
      winrate: Math.round((s.wins / s.games) * 100),
      kda:     s.deaths === 0 ? '∞' : ((s.kills + s.assists) / s.deaths).toFixed(2),
    }))
    .sort((a, b) => b.games - a.games)
    .slice(0, 5)
}

/* ── Mini champion icon réutilisable ── */
function ChampIcon({ name, isPro, accentColor, delay = 0, size = 44 }) {
  const icon = getChampIcon(name)
  return (
    <div
      className={`live-champ${isPro ? ' live-champ-pro' : ''}`}
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

export default function Player() {
  const { region, name, tag } = useParams()
  const navigate              = useNavigate()
  const { user }              = useAuthStore()

  const [data,       setData]       = useState(null)
  const [loading,    setLoading]    = useState(true)
  const [error,      setError]      = useState(null)
  const [isFav,      setIsFav]      = useState(false)
  const [favLoading, setFavLoading] = useState(false)
  const [champMap,   setChampMap]   = useState({})

  // Charge le mapping championId → championName depuis DDragon
  useEffect(() => {
    fetch(`https://ddragon.leagueoflegends.com/cdn/${CHAMP_VERSION}/data/en_US/champion.json`)
      .then(r => r.json())
      .then(d => {
        const m = {}
        Object.values(d.data).forEach(c => { m[String(parseInt(c.key))] = c.id })
        setChampMap(m)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    const fetchPlayer = async () => {
      setLoading(true); setError(null)
      try {
        const res = await api.get(`/players/${region}/${name}/${tag}`)
        setData(res.data)
        if (user && res.data?.player?.id) {
          try {
            const favRes = await api.get(`/favorites/check/${res.data.player.id}`)
            setIsFav(favRes.data.is_favorite)
          } catch {}
        }
      } catch (e) {
        setError(e.response?.data?.detail || 'Joueur introuvable')
      } finally { setLoading(false) }
    }
    fetchPlayer()
  }, [region, name, tag])

  const handleFavToggle = useCallback(async () => {
    if (!user || !data?.player?.id || favLoading) return
    setFavLoading(true)
    try {
      if (isFav) { await api.delete(`/favorites/${data.player.id}`); setIsFav(false) }
      else        { await api.post(`/favorites/${data.player.id}`);  setIsFav(true)  }
    } catch {}
    finally { setFavLoading(false) }
  }, [user, data?.player?.id, isFav, favLoading])

  if (loading) return (
    <div className="player-page">
      <div className="player-loading">
        <div className="player-spinner" />
        <div className="player-loading-text">Recherche de {decodeURIComponent(name)}#{tag}…</div>
      </div>
    </div>
  )

  if (error) return (
    <div className="player-page">
      <div className="player-error">
        <div className="player-error-icon">⚔</div>
        <div className="player-error-title">Joueur introuvable</div>
        <div className="player-error-sub">{error}</div>
        <button className="player-error-btn" onClick={() => navigate('/')}>Retour à l'accueil</button>
      </div>
    </div>
  )

  const { player, live_game, match_history, junglegap_profile, pro_player } = data
  const tierColor   = TIER_COLORS[player.tier] || '#9ca3af'
  const accentColor = pro_player?.accent_color || '#65BD62'
  const champStats  = groupByChampion(match_history || [])
  const betStats    = junglegap_profile?.bet_stats

  // blue_team / red_team viennent de la BDD (format enrichi)
  // participants vient du brut Riot (même structure mais sans stats live)
  const blueTeam = live_game?.blue_team ?? []
  const redTeam  = live_game?.red_team  ?? []

  // Cherche le participant dans blue_team + red_team (données BDD fiables)
  const allTeams = [...blueTeam, ...redTeam]
  const liveParticipant = allTeams.find(
    p => (p.puuid && p.puuid === player.riot_puuid) ||
         (p.summonerName && p.summonerName === player.summoner_name)
  )

  return (
    <div className="player-page">

      {/* ─── BANNER ─── */}
      <div className="player-banner">
        <div
          className="player-banner-bg"
          style={pro_player
            ? { background: `linear-gradient(135deg, ${accentColor}28 0%, #171717 70%)` }
            : { background: 'linear-gradient(135deg, #65BD6212 0%, #171717 70%)' }
          }
        />
        {pro_player?.team_logo_url && (
          <img className="player-banner-team-logo" src={pro_player.team_logo_url} alt={pro_player.team} referrerPolicy="no-referrer" />
        )}
        <div className="player-banner-overlay" />
      </div>

      {/* ─── HERO FLOTTANT ─── */}
      <div className="pro-float-card">
        <div
          className="pro-photo-card"
          style={!pro_player?.photo_url ? { display: 'flex', alignItems: 'center', justifyContent: 'center' } : {}}
        >
          {pro_player?.photo_url ? (
            <img src={pro_player.photo_url} alt={pro_player.name} referrerPolicy="no-referrer" />
          ) : player.profile_icon_url ? (
            <img
              src={player.profile_icon_url} alt={player.summoner_name}
              style={{ width: '90px', height: '90px', borderRadius: '14px', objectFit: 'cover' }}
              referrerPolicy="no-referrer"
              onError={e => { e.target.style.display = 'none' }}
            />
          ) : (
            <div className="pro-photo-initials">{player.summoner_name?.slice(0, 2).toUpperCase()}</div>
          )}
          <div className="pro-photo-accent" style={{ background: `linear-gradient(90deg, ${accentColor}, ${accentColor}55)` }} />
        </div>

        <div className="pro-card-info">
          <div className="pro-card-name">
            {player.summoner_name}
            <span className="pro-card-tag">#{player.tag_line}</span>
            {pro_player && (
              <span className="pro-card-badge" style={{ background: accentColor + '15', color: accentColor, border: `1px solid ${accentColor}30` }}>
                {pro_player.name} · {pro_player.team}
              </span>
            )}
            {user && (
              <button
                className={`fav-btn ${isFav ? 'fav-btn--active' : ''} ${favLoading ? 'fav-btn--loading' : ''}`}
                onClick={handleFavToggle}
                title={isFav ? 'Retirer des favoris' : 'Ajouter aux favoris'}
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill={isFav ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
                <span className="fav-btn-label">{favLoading ? '…' : isFav ? 'Favori' : 'Suivre'}</span>
              </button>
            )}
          </div>

          <div className="pro-card-badges">
            {player.tier && (
              <span className="meta-badge" style={{ color: tierColor, background: tierColor + '12', borderColor: tierColor + '28' }}>
                {player.tier} {player.rank} · {player.lp} LP
              </span>
            )}
            <span className="meta-badge muted">{player.region}</span>
            {pro_player?.role && <span className="meta-badge muted">{pro_player.role}</span>}
          </div>
        </div>
      </div>

      {/* ─── LAYOUT PRINCIPAL ─── */}
      <div className="player-layout">

        {/* ── COL GAUCHE ── */}
        <div className="left-col">

          {/* ── Live game ── */}
          {live_game ? (
            <div className="live-card">
              {/* Barre accent top */}
              <div
                className="live-card-bar"
                style={{ background: `linear-gradient(90deg, ${accentColor}, ${accentColor}55)` }}
              />
              {/* Fond accent radial */}
              <div
                className="live-card-glow"
                style={{ background: `radial-gradient(ellipse at 50% 120%, ${accentColor}, transparent 70%)` }}
              />

              {/* Header */}
              <div className="live-header">
                <div className="live-title">
                  <span className="live-dot" />
                  {QUEUE_NAMES[live_game.gameQueueConfigId] || QUEUE_NAMES[live_game.queue_type] || 'Ranked'}
                  <span className="live-sep">·</span>
                  <span className="live-queue">{formatDuration(live_game.gameLength || live_game.duration_seconds || 0)}</span>
                </div>
                <button className="live-btn" onClick={() => navigate(`/game/${live_game.id}`)}>
                  Voir & Parier →
                  <span className="live-btn-shimmer" />
                </button>
              </div>

              {/* Matchup champions */}
              <div className="live-matchup">

                {/* Blue side */}
                <div className="live-champs-row">
                  <span className="live-side-tag blue">Blue</span>
                  <div className="live-champs">
                    {blueTeam.slice(0, 5).map((p, i) => {
                      const cName = resolveChampName(p, champMap)
                      const isPro = (p.puuid && p.puuid === player.riot_puuid) ||
                                    (p.summonerName && p.summonerName === player.summoner_name)
                      return (
                        <ChampIcon
                          key={i}
                          name={cName}
                          isPro={isPro}
                          accentColor={accentColor}
                          delay={i * 0.04}
                        />
                      )
                    })}
                  </div>
                </div>

                {/* VS divider */}
                <div className="live-vs-row">
                  <div className="live-vs-line" style={{ background: '#3a6fa818' }} />
                  <span className="live-vs-text">VS</span>
                  <div className="live-vs-line" style={{ background: '#b03c3c18' }} />
                </div>

                {/* Red side */}
                <div className="live-champs-row">
                  <span className="live-side-tag red">Red</span>
                  <div className="live-champs">
                    {redTeam.slice(0, 5).map((p, i) => {
                      const cName = resolveChampName(p, champMap)
                      return (
                        <ChampIcon
                          key={i}
                          name={cName}
                          isPro={false}
                          accentColor={accentColor}
                          delay={i * 0.04}
                        />
                      )
                    })}
                  </div>
                </div>
              </div>

              {/* Strip : champion du joueur suivi */}
              {liveParticipant && (() => {
                const lpChamp = resolveChampName(liveParticipant, champMap)
                return (
                  <div className="live-pro-strip">
                    {lpChamp && <span className="live-pro-champ">{lpChamp}</span>}
                    {liveParticipant.role && lpChamp && <span className="live-pro-sep">·</span>}
                    {liveParticipant.role && <span className="live-pro-kda">{liveParticipant.role}</span>}
                    {liveParticipant.summonerName && (
                      <span className="live-pro-cs">{liveParticipant.summonerName}</span>
                    )}
                  </div>
                )
              })()}
            </div>
          ) : (
            <div className="no-game">
              <div className="no-game-icon">⚔</div>
              <div>
                <div className="no-game-text">{player.summoner_name} n'est pas en game</div>
                <div className="no-game-sub">Actualisé à l'instant</div>
              </div>
            </div>
          )}

          {/* ── Champion stats ── */}
          {champStats.length > 0 && (
            <div className="section-block">
              <div className="section-label">
                Champions joués
                <span className="section-label-sub">10 dernières parties</span>
              </div>
              <div className="champ-grid">
                {champStats.map((c, i) => (
                  <div className="champ-card" key={i}>
                    <div className="champ-img">
                      <img
                        src={`https://ddragon.leagueoflegends.com/cdn/${CHAMP_VERSION}/img/champion/${c.name}.png`}
                        alt={c.name}
                        referrerPolicy="no-referrer"
                        onError={e => { e.target.style.display = 'none' }}
                      />
                    </div>
                    <div className="champ-name">{c.name}</div>
                    <div className="champ-kda">{c.kda} KDA</div>
                    <div
                      className="champ-wr"
                      style={{ color: c.winrate >= 60 ? '#65BD62' : c.winrate >= 50 ? '#e2b147' : '#ef4444' }}
                    >
                      {c.winrate}% <span className="champ-games">{c.games}G</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Match history ── */}
          {match_history?.length > 0 && (
            <div className="section-block">
              <div className="section-label">
                Historique
                <span className="section-label-sub">10 dernières parties</span>
              </div>
              <div className="match-list">
                {match_history.map((m, i) => (
                  <div className={`match-row ${m.win ? 'win' : 'loss'}`} key={i}>
                    <div className="match-result-pill">{m.win ? 'V' : 'D'}</div>
                    <div className="match-champ">
                      <img
                        src={`https://ddragon.leagueoflegends.com/cdn/${CHAMP_VERSION}/img/champion/${m.champion}.png`}
                        alt={m.champion}
                        onError={e => { e.target.style.display = 'none' }}
                      />
                    </div>
                    <div className="match-info">
                      <div className="match-name">{m.champion}{m.role ? ` · ${m.role}` : ''}</div>
                      <div className="match-meta">{timeAgo(m.played_at)} · {formatDuration(m.duration)}</div>
                    </div>
                    <div className="match-right">
                      <div className="match-kda">
                        {m.kills}<span className="match-kda-sep">/</span>{m.deaths}<span className="match-kda-sep">/</span>{m.assists}
                      </div>
                      <div className="match-cs">{m.cs} CS</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── SIDEBAR ── */}
        <div className="sidebar">
          {junglegap_profile ? (
            <div className="sidebar-card">
              <div className="sidebar-section-label">Profil Jungle Gap</div>

              <div className="jg-profile-header">
                <div className="jg-avatar">
                  {junglegap_profile.avatar_url
                    ? <img src={junglegap_profile.avatar_url} alt="avatar" referrerPolicy="no-referrer" />
                    : <span>{junglegap_profile.username?.slice(0, 2).toUpperCase()}</span>
                  }
                </div>
                <div>
                  <div className="jg-username">{junglegap_profile.username}</div>
                  {junglegap_profile.equipped_title && (
                    <div className="jg-title">✦ {junglegap_profile.equipped_title}</div>
                  )}
                </div>
              </div>

              <div className="jg-coins">
                <span className="jg-coin-dot" />
                <span className="jg-coin-val">{junglegap_profile.coins?.toLocaleString()}</span>
                <span className="jg-coin-lbl">coins</span>
              </div>

              <div className="jg-stats-grid">
                <div className="jg-stat">
                  <div className="jg-stat-val green">
                    {betStats?.winrate != null ? `${betStats.winrate}%` : '—'}
                  </div>
                  <div className="jg-stat-lbl">Win rate</div>
                </div>
                <div className="jg-stat">
                  <div className="jg-stat-val accent">{betStats?.won ?? '—'}</div>
                  <div className="jg-stat-lbl">Paris gagnés</div>
                </div>
                <div className="jg-stat">
                  <div className="jg-stat-val gold">
                    {betStats?.streak > 0 ? `🔥 ${betStats.streak}` : betStats?.streak ?? '—'}
                  </div>
                  <div className="jg-stat-lbl">Streak</div>
                </div>
                <div className="jg-stat">
                  <div className="jg-stat-val muted">{betStats?.total ?? '—'}</div>
                  <div className="jg-stat-lbl">Total paris</div>
                </div>
              </div>

              <button className="jg-profile-btn" onClick={() => navigate(`/profile/${junglegap_profile.id}`)}>
                Voir le profil →
                <span className="jg-profile-btn-shimmer" />
              </button>
            </div>
          ) : (
            <div className="sidebar-card">
              <div className="sidebar-section-label">Profil Jungle Gap</div>
              <div className="jg-no-profile">
                <div className="jg-no-profile-icon">🎯</div>
                <div className="jg-no-profile-text">Ce joueur n'a pas encore lié de compte Jungle Gap.</div>
                <button className="jg-register-btn" onClick={() => navigate('/register')}>
                  Créer un compte →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}