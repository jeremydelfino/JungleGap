import './ChampionGrid.css'
import { useState, useMemo } from 'react'
import { getChampIcon } from '../../utils'

const TAGS = [
  { key: 'all',       label: 'Tous'      },
  { key: 'Fighter',   label: 'Combat'    },
  { key: 'Tank',      label: 'Tank'      },
  { key: 'Mage',      label: 'Mage'      },
  { key: 'Marksman',  label: 'Tireur'    },
  { key: 'Assassin',  label: 'Assassin'  },
  { key: 'Support',   label: 'Support'   },
]

export default function ChampionGrid({
  champions,
  version,
  pickedSet,         // Set des champions déjà ban/pick
  selected,          // champion preselect
  onSelect,
  onLockIn,
  disabled,          // true si tour bot
  actionLabel,       // "Ban" ou "Pick"
}) {
  const [search, setSearch] = useState('')
  const [tag,    setTag]    = useState('all')

    const filtered = useMemo(() => {
    // Normalise : minuscule + suppression espaces/apostrophes/tirets
    const norm = (s) => s.toLowerCase().replace(/[\s'-]/g, '')
    const q = norm(search.trim())
    return champions.filter(c => {
        if (q && !norm(c.name).includes(q) && !norm(c.id).includes(q)) return false
        if (tag !== 'all' && !c.tags?.includes(tag)) return false
        return true
    })
    }, [champions, search, tag])

  return (
    <div className={`cd-grid-wrap ${disabled ? 'disabled' : ''}`}>

      {/* ─── CONTROLS ─── */}
      <div className="cd-grid-controls">
        <input
          type="text"
          className="cd-grid-search"
          placeholder="🔍 Rechercher un champion…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          disabled={disabled}
        />
        <div className="cd-grid-tags">
          {TAGS.map(t => (
            <button
              key={t.key}
              className={`cd-grid-tag ${tag === t.key ? 'active' : ''}`}
              onClick={() => setTag(t.key)}
              disabled={disabled}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* ─── GRID ─── */}
      <div className="cd-grid">
        {filtered.map(c => {
          const isPicked = pickedSet.has(c.id)
          const isSel    = selected === c.id
          return (
            <button
            key={c.id}
            className={`cd-grid-cell ${isPicked ? 'picked' : ''} ${isSel ? 'selected' : ''}`}
            onClick={() => !isPicked && !disabled && onSelect(c.id)}
            disabled={isPicked || disabled}
            title={c.name}
            >
            <div className="cd-grid-cell-img">
                <img src={getChampIcon(c.id, version)} alt={c.name} referrerPolicy="no-referrer" />
            </div>
            <div className="cd-grid-cell-name">{c.name}</div>
            </button>
          )
        })}
        {filtered.length === 0 && (
          <div className="cd-grid-empty">Aucun champion trouvé</div>
        )}
      </div>

      {/* ─── LOCK IN BAR ─── */}
      <div className="cd-grid-footer">
        <div className="cd-grid-selected">
          {selected ? (
            <>
              <img src={getChampIcon(selected, version)} alt={selected} referrerPolicy="no-referrer" />
              <span>{selected}</span>
            </>
          ) : (
            <span className="cd-grid-noselect">Sélectionne un champion…</span>
          )}
        </div>
        <button
          className={`cd-grid-lockin ${actionLabel.toLowerCase()}`}
          onClick={onLockIn}
          disabled={!selected || disabled}
        >
          {actionLabel === 'Ban' ? '🚫 Bannir' : '✓ Verrouiller'}
        </button>
      </div>

    </div>
  )
}