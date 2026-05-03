import './PickColumn.css'
import { getChampIcon } from '../../utils'
import { SIDE_LABELS } from '../../constants'

export default function PickColumn({ side, picks, version, isCurrentSlot }) {
  const slots = Array.from({ length: 5 }, (_, i) => picks[i] || null)

  return (
    <div className={`cd-picks cd-picks-${side.toLowerCase()}`}>
      <div className="cd-picks-header">
        <div className="cd-picks-label">{SIDE_LABELS[side]}</div>
      </div>
      <div className="cd-picks-list">
        {slots.map((champ, i) => {
          const isActive = isCurrentSlot && i === picks.length
          return (
            <div key={i} className={`cd-pick-slot ${champ ? 'filled' : 'empty'} ${isActive ? 'active' : ''}`}>
              {champ ? (
                <>
                  <img src={getChampIcon(champ, version)} alt={champ} referrerPolicy="no-referrer" />
                  <div className="cd-pick-name">{champ}</div>
                </>
              ) : (
                <div className="cd-pick-empty">{i + 1}</div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}