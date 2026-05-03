import './BanRow.css'
import { getChampIcon } from '../../utils'

export default function BanRow({ side, bans, version, isCurrentSlot }) {
  const slots = Array.from({ length: 5 }, (_, i) => bans[i] || null)

  return (
    <div className={`cd-banrow cd-banrow-${side.toLowerCase()}`}>
      <div className="cd-banrow-label">BANS</div>
      <div className="cd-banrow-slots">
        {slots.map((champ, i) => {
          const isActive = isCurrentSlot && i === bans.length
          return (
            <div key={i} className={`cd-ban-slot ${champ ? 'filled' : 'empty'} ${isActive ? 'active' : ''}`}>
              {champ ? (
                <>
                  <img src={getChampIcon(champ, version)} alt={champ} referrerPolicy="no-referrer" />
                  <div className="cd-ban-cross" />
                </>
              ) : (
                <div className="cd-ban-empty">×</div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}