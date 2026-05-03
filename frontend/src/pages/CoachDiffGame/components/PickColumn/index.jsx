import './PickColumn.css'
import { getChampSplash } from '../../utils'
import { SIDE_LABELS } from '../../constants'

export default function PickColumn({ side, picks, version, isCurrentSlot }) {
  const slots = Array.from({ length: 5 }, (_, i) => picks[i] || null)
  const sideLower = side.toLowerCase()

  return (
    <div className={`cd-picks cd-picks-${sideLower}`}>
      <div className={`cd-picks-header ${sideLower}`}>
        {side === 'BLUE' && <span className={`cd-picks-bar ${sideLower}-bar`} />}
        <span className="cd-picks-label">{SIDE_LABELS[side]}</span>
        {side === 'RED' && <span className={`cd-picks-bar ${sideLower}-bar`} />}
      </div>

      <div className="cd-picks-list">
        {slots.map((champ, i) => {
          const isActive = isCurrentSlot && i === picks.length
          const splash = champ ? getChampSplash(champ) : null
          return (
            <div key={i} className={`cd-pick-slot ${sideLower} ${champ ? 'filled' : 'empty'} ${isActive ? 'active' : ''}`}>
              {champ ? (
                <>
                  {splash && <img src={splash} alt={champ} className="cd-pick-splash" referrerPolicy="no-referrer" onError={e => { e.target.style.display = 'none' }} />}
                  <div className={`cd-pick-fade ${sideLower === 'blue' ? 'fade-right' : 'fade-left'}`} />
                  <div className={`cd-pick-name ${sideLower}`}>{champ}</div>
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