import './RoleAssignPanel.css'
import { useState, useMemo } from 'react'
import { getChampIcon } from '../../utils'
import { LANES, LANE_LABELS, LANE_ICONS } from '../../constants'

export default function RoleAssignPanel({ picks, version, onSubmit, busy }) {
  // assignment: { TOP: champ | null, JUNGLE: champ | null, ... }
  const [assignment, setAssignment] = useState(() =>
    LANES.reduce((acc, l) => ({ ...acc, [l]: null }), {})
  )

  const assignedChamps = useMemo(
    () => new Set(Object.values(assignment).filter(Boolean)),
    [assignment]
  )
  const unassignedChamps = picks.filter(c => !assignedChamps.has(c))
  const isComplete = Object.values(assignment).every(Boolean)

  const handlePick = (lane, champion) => {
    setAssignment(prev => {
      const next = { ...prev }
      // Si ce champion est déjà assigné ailleurs, le retirer
      for (const l of LANES) if (next[l] === champion) next[l] = null
      // Toggle: si même champ déjà sur cette lane → désassigner
      next[lane] = next[lane] === champion ? null : champion
      return next
    })
  }

  const handleClear = (lane) => {
    setAssignment(prev => ({ ...prev, [lane]: null }))
  }

  const handleSubmit = () => {
    if (!isComplete || busy) return
    onSubmit(assignment)
  }

  return (
    <div className="cd-rap">

      {/* ─── HEADER ─── */}
      <div className="cd-rap-header">
        <div className="cd-rap-eyebrow">Phase finale</div>
        <h2 className="cd-rap-title">Assigne tes 5 champions</h2>
        <p className="cd-rap-sub">Place chaque champion sur sa lane. Le bot fera de même automatiquement.</p>
      </div>

      {/* ─── LANES ─── */}
      <div className="cd-rap-lanes">
        {LANES.map(lane => {
          const champ = assignment[lane]
          return (
            <div key={lane} className={`cd-rap-lane ${champ ? 'filled' : 'empty'}`}>
              <div className="cd-rap-lane-head">
                <span className="cd-rap-lane-icon">{LANE_ICONS[lane]}</span>
                <span className="cd-rap-lane-label">{LANE_LABELS[lane]}</span>
                {champ && (
                  <button className="cd-rap-clear" onClick={() => handleClear(lane)} title="Retirer">×</button>
                )}
              </div>
              <div className="cd-rap-lane-slot">
                {champ ? (
                  <>
                    <img src={getChampIcon(champ, version)} alt={champ} referrerPolicy="no-referrer" />
                    <span>{champ}</span>
                  </>
                ) : (
                  <span className="cd-rap-lane-empty">Choisir un champion</span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* ─── POOL ─── */}
      <div className="cd-rap-pool">
        <div className="cd-rap-pool-label">
          {unassignedChamps.length > 0
            ? `Champions à placer (${unassignedChamps.length})`
            : 'Tous les champions sont assignés ✓'}
        </div>
        <div className="cd-rap-pool-list">
          {picks.map(champ => {
            const isAssigned = assignedChamps.has(champ)
            return (
              <div key={champ} className={`cd-rap-pool-item ${isAssigned ? 'assigned' : ''}`}>
                <img src={getChampIcon(champ, version)} alt={champ} referrerPolicy="no-referrer" />
                <span>{champ}</span>
                <div className="cd-rap-pool-buttons">
                  {LANES.map(lane => {
                    const onThisLane = assignment[lane] === champ
                    return (
                      <button
                        key={lane}
                        className={`cd-rap-pool-btn ${onThisLane ? 'active' : ''}`}
                        onClick={() => handlePick(lane, champ)}
                        title={LANE_LABELS[lane]}
                      >
                        {LANE_ICONS[lane]}
                      </button>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ─── SUBMIT ─── */}
      <button
        className={`cd-rap-submit ${isComplete ? 'ready' : ''}`}
        onClick={handleSubmit}
        disabled={!isComplete || busy}
      >
        {busy ? 'Calcul du score…' : isComplete ? 'Voir le score 🏆' : `Place encore ${5 - assignedChamps.size} champion(s)`}
      </button>

    </div>
  )
}