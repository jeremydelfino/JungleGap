import './DraftHeader.css'
import { PHASE_LABELS, SIDE_LABELS } from '../../constants'

export default function DraftHeader({ phase, step, currentTurn, userSide, timer, isUserTurn }) {
  const phaseLabel = PHASE_LABELS[phase] || phase
  const turnSide   = currentTurn?.side
  const turnAction = currentTurn?.action === 'ban' ? 'BAN' : 'PICK'

  return (
    <div className="cdh">

      {/* ─── LEFT: Phase + step ─── */}
      <div className="cdh-left">
        <div className="cdh-phase">{phaseLabel}</div>
        <div className="cdh-step">Étape {Math.min(step + 1, 20)} / 20</div>
      </div>

      {/* ─── CENTER: Turn indicator ─── */}
      <div className={`cdh-center ${isUserTurn ? 'user' : 'bot'}`}>
        <div className="cdh-actor">
          {isUserTurn ? '✦ TON TOUR' : '⏳ Le bot réfléchit…'}
        </div>
        <div className="cdh-action">
          <span className={`cdh-side-badge cdh-side-${(turnSide || '').toLowerCase()}`}>
            {SIDE_LABELS[turnSide] || '—'}
          </span>
          <span className={`cdh-action-badge cdh-action-${(currentTurn?.action || 'ban').toLowerCase()}`}>
            {turnAction}
          </span>
        </div>
      </div>

      {/* ─── RIGHT: Timer + user side ─── */}
      <div className="cdh-right">
        {timer !== null && (
          <div className={`cdh-timer ${timer <= 5 ? 'urgent' : ''}`}>
            <div className="cdh-timer-num">{timer}</div>
            <div className="cdh-timer-label">sec</div>
          </div>
        )}
        <div className="cdh-userside">
          <div className="cdh-userside-label">Tu joues</div>
          <div className={`cdh-userside-val cdh-side-${userSide.toLowerCase()}`}>
            {SIDE_LABELS[userSide]}
          </div>
        </div>
      </div>

    </div>
  )
}