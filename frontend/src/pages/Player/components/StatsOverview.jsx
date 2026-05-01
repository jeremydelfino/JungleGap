import './StatsOverview.css'
import { useEffect, useState } from 'react'
import { ROLE_LABELS, ROLE_ICONS } from '../constants'
import { getChampIcon, groupByChampion } from '../utils'

export default function StatsOverview({ overall_stats, match_history, delay = 0 }) {
  if (!overall_stats || overall_stats.total === 0) {
    return (
      <div className="so-card so-empty" style={{ animationDelay: `${delay}s` }}>
        <div className="so-empty-icon">📊</div>
        <div className="so-empty-text">Aucune game récente</div>
      </div>
    )
  }

  const { winrate, wins, losses, total, avg_kda, avg_cs_min, by_role } = overall_stats
  const topChamps = groupByChampion(match_history || [], 5)

  // Tween winrate
  const [animWr, setAnimWr] = useState(0)
  useEffect(() => {
    const start = performance.now()
    const dur   = 700
    let raf
    const tick = (now) => {
      const t = Math.min(1, (now - start) / dur)
      const eased = 1 - Math.pow(1 - t, 3)
      setAnimWr(Math.round(winrate * eased))
      if (t < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [winrate])

  const wrColor = winrate >= 60 ? '#65BD62' : winrate >= 50 ? '#e2b147' : '#ef4444'
  const sortedRoles = Object.entries(by_role || {}).sort((a, b) => b[1].games - a[1].games)

  return (
    <div className="so-card" style={{ animationDelay: `${delay}s` }}>
      {/* ─── Header ─── */}
      <div className="so-header">
        <div className="so-section-label">Vue d'ensemble</div>
        <div className="so-section-sub">{total} dernières parties</div>
      </div>

      <div className="so-grid">

        {/* ─── DONUT + STATS PRIMAIRES ─── */}
        <div className="so-block so-block-wr">
          <div className="so-donut-wrap">
            <svg viewBox="0 0 120 120" className="so-donut">
              <circle cx="60" cy="60" r="50" fill="none" stroke="#ffffff0c" strokeWidth="9" />
              <circle
                cx="60" cy="60" r="50" fill="none"
                stroke={wrColor}
                strokeWidth="9"
                strokeLinecap="round"
                strokeDasharray={`${(animWr / 100) * 314} 314`}
                strokeDashoffset="0"
                transform="rotate(-90 60 60)"
                style={{ transition: 'stroke-dasharray 0.7s cubic-bezier(0.4,0,0.2,1)', filter: `drop-shadow(0 0 6px ${wrColor}80)` }}
              />
            </svg>
            <div className="so-donut-center">
              <div className="so-donut-val" style={{ color: wrColor }}>
                {animWr}<span className="so-donut-pct">%</span>
              </div>
              <div className="so-donut-lbl">Winrate</div>
            </div>
          </div>

          <div className="so-wr-meta">
            <div className="so-wr-wl">
              <span className="so-wr-w">{wins}V</span>
              <span className="so-wr-dot">·</span>
              <span className="so-wr-l">{losses}D</span>
            </div>
            <div className="so-wr-kda">
              <span className="so-wr-kda-v">{avg_kda}</span>
              <span className="so-wr-kda-l">KDA moyen</span>
            </div>
            <div className="so-wr-kda">
              <span className="so-wr-kda-v">{avg_cs_min}</span>
              <span className="so-wr-kda-l">CS / min</span>
            </div>
          </div>
        </div>

        {/* ─── PERF PAR RÔLE ─── */}
        <div className="so-block so-block-roles">
          <div className="so-block-label">Performance par rôle</div>
          <div className="so-roles-list">
            {sortedRoles.length === 0 && <div className="so-empty-mini">Pas de données</div>}
            {sortedRoles.map(([role, r]) => {
              const rwrColor = r.winrate >= 60 ? '#65BD62' : r.winrate >= 50 ? '#e2b147' : '#ef4444'
              return (
                <div key={role} className="so-role-row">
                  <div className="so-role-head">
                    <span className="so-role-icon">{ROLE_ICONS[role] || '?'}</span>
                    <span className="so-role-name">{ROLE_LABELS[role] || role}</span>
                    <span className="so-role-games">{r.games}G</span>
                  </div>
                  <div className="so-role-bar-track">
                    <div
                      className="so-role-bar-fill"
                      style={{ width: `${r.winrate}%`, background: `linear-gradient(90deg, ${rwrColor}, ${rwrColor}cc)`, boxShadow: `0 0 6px ${rwrColor}40` }}
                    />
                  </div>
                  <div className="so-role-foot">
                    <span className="so-role-wr" style={{ color: rwrColor }}>{r.winrate}%</span>
                    <span className="so-role-kda">{r.kda} KDA</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* ─── TOP CHAMPIONS ─── */}
        <div className="so-block so-block-champs">
          <div className="so-block-label">Top champions</div>
          <div className="so-champs-list">
            {topChamps.map((c, i) => {
              const icon = getChampIcon(c.name)
              const cwrColor = c.winrate >= 60 ? '#65BD62' : c.winrate >= 50 ? '#e2b147' : '#ef4444'
              return (
                <div key={i} className="so-champ-row" style={{ animationDelay: `${delay + 0.05 + i * 0.04}s` }}>
                  <div className="so-champ-icon">
                    {icon
                      ? <img src={icon} alt={c.name} onError={e => { e.target.style.display = 'none' }} />
                      : <span>{c.name?.slice(0, 2)}</span>
                    }
                  </div>
                  <div className="so-champ-info">
                    <div className="so-champ-name">{c.name}</div>
                    <div className="so-champ-meta">{c.avg_k}/{c.avg_d}/{c.avg_a} · {c.cs_min} CS</div>
                  </div>
                  <div className="so-champ-stats">
                    <div className="so-champ-wr" style={{ color: cwrColor }}>{c.winrate}%</div>
                    <div className="so-champ-games">{c.wins}V {c.losses}D</div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

      </div>
    </div>
  )
}