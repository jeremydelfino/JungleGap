import './MatchRow.css'
import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  formatDuration, timeAgo,
  getChampIcon, getSpellIcon, getItemIcon, getRuneIcon,
} from '../utils'
import { QUEUE_NAMES, ROLE_LABELS } from '../constants'

const ROLE_ORDER = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']

function ItemSlot({ id, size = 'sm' }) {
  const icon = getItemIcon(id)
  return (
    <div className={`mr-item mr-item-${size}${!id ? ' mr-item-empty' : ''}`}>
      {icon && <img src={icon} alt="" referrerPolicy="no-referrer" onError={e => { e.target.style.display = 'none' }} />}
    </div>
  )
}

function ParticipantRow({ p, isSelf, onClickPlayer }) {
  const champIcon = getChampIcon(p.champion)
  const kdaRatio  = p.deaths === 0 ? '∞' : ((p.kills + p.assists) / p.deaths).toFixed(1)
  return (
    <div className={`mr-part${isSelf ? ' mr-part-self' : ''}`}>
      <div className="mr-part-champ">
        {champIcon
          ? <img src={champIcon} alt={p.champion} onError={e => { e.target.style.display = 'none' }} />
          : <span>{p.champion?.slice(0, 2)}</span>
        }
      </div>
      <div className="mr-part-info">
        <div
          className="mr-part-name"
          onClick={() => onClickPlayer(p)}
          title={`${p.summoner_name}#${p.tag_line}`}
        >
          {p.summoner_name || '—'}
        </div>
        <div className="mr-part-kda">
          {p.kills}/{p.deaths}/{p.assists}
          <span className="mr-part-kda-r"> · {kdaRatio}</span>
        </div>
      </div>
      <div className="mr-part-items">
        {p.items.slice(0, 6).map((id, i) => <ItemSlot key={i} id={id} size="xs" />)}
      </div>
    </div>
  )
}

export default function MatchRow({ match, playerPuuid, delay = 0 }) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const drawerRef = useRef(null)
  const [drawerHeight, setDrawerHeight] = useState(0)

  useEffect(() => {
    if (!drawerRef.current) return
    setDrawerHeight(open ? drawerRef.current.scrollHeight : 0)
  }, [open])

  const {
    champion, role, win, kills, deaths, assists, cs, duration,
    played_at, items, spell1_id, spell2_id, primary_rune, secondary_tree,
    queue_id, kp, level, vision_score, participants,
  } = match

  const champIcon = getChampIcon(champion)
  const spell1    = getSpellIcon(spell1_id)
  const spell2    = getSpellIcon(spell2_id)
  const rune1     = getRuneIcon(primary_rune, 'keystone')
  const rune2     = getRuneIcon(secondary_tree, 'tree')
  const kdaRatio  = deaths === 0 ? '∞' : ((kills + assists) / deaths).toFixed(2)
  const kdaColor  = deaths === 0 ? '#a78bfa' : (kills + assists) / deaths >= 4 ? '#65BD62' : (kills + assists) / deaths >= 2.5 ? '#e2b147' : '#9ca3af'
  const csMin     = (cs / (duration / 60)).toFixed(1)
  const queueName = QUEUE_NAMES[queue_id] || 'Match'
  const roleLbl   = ROLE_LABELS[role] || role

  const blueParts = participants.filter(p => p.team_id === 100).sort((a, b) => ROLE_ORDER.indexOf(a.role) - ROLE_ORDER.indexOf(b.role))
  const redParts  = participants.filter(p => p.team_id === 200).sort((a, b) => ROLE_ORDER.indexOf(a.role) - ROLE_ORDER.indexOf(b.role))

  const handlePlayerClick = (p) => {
    if (!p.summoner_name || !p.tag_line) return
    if (p.puuid === playerPuuid) return
    navigate(`/player/EUW/${encodeURIComponent(p.summoner_name)}/${encodeURIComponent(p.tag_line)}`)
  }

  return (
    <div
      className={`mr-row ${win ? 'mr-win' : 'mr-loss'}${open ? ' mr-open' : ''}`}
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="mr-head" onClick={() => setOpen(!open)}>

        {/* Result */}
        <div className="mr-result">
          <div className={`mr-outcome ${win ? 'mr-w' : 'mr-l'}`}>{win ? 'Victoire' : 'Défaite'}</div>
          <div className="mr-queue">{queueName}</div>
          <div className="mr-when">{timeAgo(played_at)}</div>
          <div className="mr-duration">{formatDuration(duration)}</div>
        </div>

        {/* Champ + spells + runes */}
        <div className="mr-build">
          <div className="mr-champ-icon">
            {champIcon
              ? <img src={champIcon} alt={champion} onError={e => { e.target.style.display = 'none' }} />
              : <span>{champion?.slice(0, 2)}</span>
            }
            <div className="mr-champ-level">{level}</div>
          </div>
          <div className="mr-spells">
            <div className="mr-spell">{spell1 && <img src={spell1} alt="" onError={e => { e.target.style.display = 'none' }} />}</div>
            <div className="mr-spell">{spell2 && <img src={spell2} alt="" onError={e => { e.target.style.display = 'none' }} />}</div>
          </div>
          <div className="mr-runes">
            <div className="mr-rune mr-rune-keystone">{rune1 && <img src={rune1} alt="" onError={e => { e.target.style.display = 'none' }} />}</div>
            <div className="mr-rune mr-rune-tree">{rune2 && <img src={rune2} alt="" onError={e => { e.target.style.display = 'none' }} />}</div>
          </div>
        </div>

        {/* KDA */}
        <div className="mr-kda-block">
          <div className="mr-kda-main">
            <span className="mr-k">{kills}</span>
            <span className="mr-kda-sep">/</span>
            <span className="mr-d">{deaths}</span>
            <span className="mr-kda-sep">/</span>
            <span className="mr-a">{assists}</span>
          </div>
          <div className="mr-kda-ratio" style={{ color: kdaColor }}>{kdaRatio} KDA</div>
          <div className="mr-kp">{kp}% P/Kill {roleLbl && `· ${roleLbl}`}</div>
        </div>

        {/* CS / Vision */}
        <div className="mr-stats-block">
          <div className="mr-stat-line">
            <span className="mr-stat-v">{cs}</span>
            <span className="mr-stat-l">CS</span>
            <span className="mr-stat-sub">({csMin}/min)</span>
          </div>
          <div className="mr-stat-line">
            <span className="mr-stat-v">{vision_score}</span>
            <span className="mr-stat-l">vision</span>
          </div>
        </div>

        {/* Items */}
        <div className="mr-items-grid">
          {[0, 1, 2, 3, 4, 5].map(i => <ItemSlot key={i} id={items[i]} size="md" />)}
          <ItemSlot id={items[6]} size="md" />
        </div>

        {/* Toggle */}
        <button className={`mr-toggle${open ? ' mr-toggle-open' : ''}`} aria-label="Détails">
          <span className="mr-toggle-arrow">▾</span>
        </button>
      </div>

      {/* Drawer */}
      <div className="mr-drawer" style={{ maxHeight: drawerHeight }}>
        <div ref={drawerRef} className="mr-drawer-inner">
          <div className="mr-teams">
            <div className="mr-team mr-team-blue">
              <div className="mr-team-label">Équipe Bleue {blueParts.some(p => p.win) && <span className="mr-team-tag mr-team-tag-w">Victoire</span>}{blueParts.some(p => !p.win) && !blueParts.some(p => p.win) && <span className="mr-team-tag mr-team-tag-l">Défaite</span>}</div>
              {blueParts.map((p, i) => (
                <ParticipantRow key={i} p={p} isSelf={p.puuid === playerPuuid} onClickPlayer={handlePlayerClick} />
              ))}
            </div>
            <div className="mr-team mr-team-red">
              <div className="mr-team-label">Équipe Rouge {redParts.some(p => p.win) && <span className="mr-team-tag mr-team-tag-w">Victoire</span>}{redParts.some(p => !p.win) && !redParts.some(p => p.win) && <span className="mr-team-tag mr-team-tag-l">Défaite</span>}</div>
              {redParts.map((p, i) => (
                <ParticipantRow key={i} p={p} isSelf={p.puuid === playerPuuid} onClickPlayer={handlePlayerClick} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}