import './ScoreReveal.css'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getChampIcon } from '../../utils'
import { LANES, LANE_ICONS, LANE_LABELS, SIDE_LABELS } from '../../constants'

const VERDICT = {
  USER: { eyebrow: 'VICTOIRE', title: 'Tu as gagné',     emoji: '🏆', color: '#65BD62' },
  BOT:  { eyebrow: 'DÉFAITE',  title: 'Le bot l\'emporte', emoji: '💀', color: '#ef4444' },
  DRAW: { eyebrow: 'ÉGALITÉ',  title: 'Match nul',         emoji: '🤝', color: '#c89b3c' },
}

const PAYOUT_LABEL = {
  USER: '+10 🪙',
  BOT:  '0 🪙',
  DRAW: '+5 🪙 (remboursé)',
}

export default function ScoreReveal({ game, version }) {
  const navigate = useNavigate()
  const [revealed, setRevealed] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setRevealed(true), 200)
    return () => clearTimeout(t)
  }, [])

  const verdict = VERDICT[game.winner] || VERDICT.DRAW
  const userBd  = game.user_breakdown
  const botBd   = game.bot_breakdown
  const userSide = game.user_side
  const botSide  = game.bot_side
  const userLanes = (game.draft_state?.[userSide.toLowerCase()]?.lanes) || {}
  const botLanes  = (game.draft_state?.[botSide.toLowerCase()]?.lanes)  || {}

  return (
    <div className="cd-sr">

      {/* ─── VERDICT ─── */}
      <div className={`cd-sr-verdict ${revealed ? 'shown' : ''}`} style={{ '--vc': verdict.color }}>
        <div className="cd-sr-emoji">{verdict.emoji}</div>
        <div className="cd-sr-eyebrow">{verdict.eyebrow}</div>
        <h1 className="cd-sr-title">{verdict.title}</h1>
        <div className="cd-sr-payout">{PAYOUT_LABEL[game.winner]}</div>
      </div>

      {/* ─── SCORES ─── */}
      <div className="cd-sr-scores">

        <ScoreCard
          label="TON SCORE"
          side={userSide}
          score={game.user_score}
          breakdown={userBd}
          lanes={userLanes}
          version={version}
          isWinner={game.winner === 'USER'}
        />

        <div className="cd-sr-vs">VS</div>

        <ScoreCard
          label="BOT"
          side={botSide}
          score={game.bot_score}
          breakdown={botBd}
          lanes={botLanes}
          version={version}
          isWinner={game.winner === 'BOT'}
        />

      </div>

      {/* ─── BREAKDOWN ─── */}
      {userBd && (
        <div className="cd-sr-detail">
          <div className="cd-sr-detail-title">Détail des composantes</div>
          <BreakdownTable userBd={userBd} botBd={botBd} />
        </div>
      )}

      {/* ─── ACTIONS ─── */}
      <div className="cd-sr-actions">
        <button className="cd-sr-btn primary" onClick={() => navigate('/games/coachdiff')}>
          Rejouer
        </button>
        <button className="cd-sr-btn secondary" onClick={() => navigate('/games')}>
          Retour aux jeux
        </button>
      </div>

    </div>
  )
}

/* ─── ScoreCard ─── */
function ScoreCard({ label, side, score, breakdown, lanes, version, isWinner }) {
  return (
    <div className={`cd-sr-card cd-sr-card-${side.toLowerCase()} ${isWinner ? 'winner' : ''}`}>
      <div className="cd-sr-card-label">{label}</div>
      <div className="cd-sr-card-side">{SIDE_LABELS[side]}</div>
      <div className="cd-sr-card-score">{Math.round(score ?? 0)}<span>/100</span></div>

      <div className="cd-sr-card-roster">
        {LANES.map(lane => {
          const champ = lanes[lane]
          return (
            <div key={lane} className="cd-sr-roster-row">
              <span className="cd-sr-roster-icon">{LANE_ICONS[lane]}</span>
              {champ ? (
                <>
                  <img src={getChampIcon(champ, version)} alt={champ} referrerPolicy="no-referrer" />
                  <span className="cd-sr-roster-name">{champ}</span>
                </>
              ) : (
                <span className="cd-sr-roster-empty">—</span>
              )}
            </div>
          )
        })}
      </div>

      {breakdown && (
        <div className="cd-sr-card-mini">
          <div><span>Tier</span><b>{breakdown.breakdown?.tier?.toFixed(1)}</b></div>
          <div><span>Matchup</span><b>{breakdown.breakdown?.matchup?.toFixed(1)}</b></div>
          <div><span>Synergy</span><b>{breakdown.breakdown?.synergy?.toFixed(1)}</b></div>
        </div>
      )}
    </div>
  )
}

/* ─── BreakdownTable ─── */
function BreakdownTable({ userBd, botBd }) {
  const rows = [
    { label: 'Tier (WR + Pro)',     key: 'tier',     max: 50 },
    { label: 'Matchup vs adverse',  key: 'matchup',  max: 30 },
    { label: 'Synergie d\'équipe',  key: 'synergy',  max: 20 },
  ]
  const userBonus   = userBd?.team_bonus || 0
  const botBonus    = botBd?.team_bonus || 0
  const userPenalty = userBd?.penalty || 0
  const botPenalty  = botBd?.penalty || 0

  return (
    <div className="cd-sr-table">
      <div className="cd-sr-table-head">
        <div className="cd-sr-table-cell label">Composante</div>
        <div className="cd-sr-table-cell">Toi</div>
        <div className="cd-sr-table-cell">Bot</div>
        <div className="cd-sr-table-cell">Max</div>
      </div>
      {rows.map(r => (
        <div key={r.key} className="cd-sr-table-row">
          <div className="cd-sr-table-cell label">{r.label}</div>
          <div className="cd-sr-table-cell user">{userBd?.breakdown?.[r.key]?.toFixed(1) ?? '—'}</div>
          <div className="cd-sr-table-cell bot">{botBd?.breakdown?.[r.key]?.toFixed(1) ?? '—'}</div>
          <div className="cd-sr-table-cell max">{r.max}</div>
        </div>
      ))}
      {(userBonus > 0 || botBonus > 0) && (
        <div className="cd-sr-table-row">
          <div className="cd-sr-table-cell label">Bonus team Pro</div>
          <div className="cd-sr-table-cell user bonus">{userBonus > 0 ? `+${userBonus}` : '—'}</div>
          <div className="cd-sr-table-cell bot bonus">{botBonus > 0 ? `+${botBonus}` : '—'}</div>
          <div className="cd-sr-table-cell max">+5</div>
        </div>
      )}
      {(userPenalty > 0 || botPenalty > 0) && (
        <div className="cd-sr-table-row">
          <div className="cd-sr-table-cell label">Pénalité off-lane</div>
          <div className="cd-sr-table-cell user penalty">{userPenalty > 0 ? `−${userPenalty}` : '—'}</div>
          <div className="cd-sr-table-cell bot penalty">{botPenalty > 0 ? `−${botPenalty}` : '—'}</div>
          <div className="cd-sr-table-cell max">—</div>
        </div>
      )}
    </div>
  )
}