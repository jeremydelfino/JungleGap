import './RankCard.css'
import { useEffect, useState } from 'react'
import { TIER_COLORS, APEX_TIERS } from '../constants'
import { getTierImage } from '../utils'

export default function RankCard({ tier, rank, lp, queueLabel = 'Solo / Duo', delay = 0 }) {
  const tierColor = TIER_COLORS[tier] || '#6b7280'
  const isApex    = tier && APEX_TIERS.has(tier)
  const tierImg   = getTierImage(tier)

  // ── LP animé ──
  const [animLp, setAnimLp] = useState(0)
  useEffect(() => {
    if (!lp) return
    const start = performance.now()
    const dur   = 800
    let raf
    const tick = (now) => {
      const t = Math.min(1, (now - start) / dur)
      const eased = 1 - Math.pow(1 - t, 3)
      setAnimLp(Math.round(lp * eased))
      if (t < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [lp])

  if (!tier) {
    return (
      <div className="rc-card rc-card-empty" style={{ animationDelay: `${delay}s` }}>
        <div className="rc-empty-bg" />
        <div className="rc-queue">{queueLabel}</div>
        <div className="rc-empty-icon">⚔</div>
        <div className="rc-empty-text">Non classé</div>
      </div>
    )
  }

  const tierName = tier.charAt(0) + tier.slice(1).toLowerCase()
  const lpToNext = isApex ? null : (100 - (lp % 100))
  const progress = isApex ? Math.min(100, (lp / 1500) * 100) : (lp % 100)

  return (
    <div
      className="rc-card"
      style={{
        animationDelay: `${delay}s`,
        '--rc-color': tierColor,
      }}
    >
      {/* Glow accent */}
      <div className="rc-glow" style={{ background: `radial-gradient(ellipse at top right, ${tierColor}25, transparent 65%)` }} />

      {/* Header */}
      <div className="rc-header">
        <div className="rc-queue">{queueLabel}</div>
        <div className="rc-tier-badge" style={{ color: tierColor, borderColor: `${tierColor}40`, background: `${tierColor}10` }}>
          Saison
        </div>
      </div>

      {/* Body */}
      <div className="rc-body">
        <div className="rc-tier-img">
          {tierImg && (
            <img src={tierImg} alt={tier} referrerPolicy="no-referrer" onError={e => { e.target.style.display = 'none' }} />
          )}
          <div className="rc-tier-img-glow" style={{ background: `radial-gradient(circle, ${tierColor}50, transparent 65%)` }} />
        </div>

        <div className="rc-text">
          <div className="rc-tier-name" style={{ color: tierColor }}>
            {tierName}
            {!isApex && rank && <span className="rc-rank"> {rank}</span>}
          </div>
          <div className="rc-lp-row">
            <span className="rc-lp-val">{animLp}</span>
            <span className="rc-lp-lbl">LP</span>
          </div>
          <div className="rc-next">
            {isApex
              ? '—  —'
              : lpToNext > 0 ? `${lpToNext} LP avant promo` : 'BO de promotion'
            }
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="rc-progress-track">
        <div
          className="rc-progress-fill"
          style={{
            width: `${progress}%`,
            background: `linear-gradient(90deg, ${tierColor}, ${tierColor}cc)`,
            boxShadow: `0 0 10px ${tierColor}80`,
          }}
        />
      </div>
    </div>
  )
}