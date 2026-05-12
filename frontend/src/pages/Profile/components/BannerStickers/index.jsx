import './BannerStickers.css'
import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import api from '../../../../api/client'

const STICKER_SIZE = 100   // doit matcher le CSS

export default function BannerStickers({ userId, isOwnProfile, bannerRef }) {
  const [stickers, setStickers]     = useState([])
  const [loading, setLoading]       = useState(true)
  const [showPicker, setShowPicker] = useState(false)
  const [inventory, setInventory]   = useState([])
  const [dragInfo, setDragInfo]     = useState(null)

  useEffect(() => { load() }, [userId])

  async function load() {
    setLoading(true)
    try {
      const path = isOwnProfile
        ? '/cards/equipped-stickers'
        : `/profile/${userId}/equipped-stickers`
      const { data } = await api.get(path)
      setStickers(Array.isArray(data) ? data : [])
    } catch {
      setStickers([])
    } finally {
      setLoading(false)
    }
  }

  async function openPicker() {
    if (!isOwnProfile) return
    setShowPicker(true)
    try {
      const { data } = await api.get('/cards/my-cards')
      const equippedIds = new Set(stickers.map(s => s.user_card_id))
      const available = data
        .filter(uc => uc.card.type === 'sticker')
        .filter(uc => !equippedIds.has(uc.id))
      setInventory(available)
    } catch {
      setInventory([])
    }
  }

  async function pickSticker(userCardId) {
    try {
      await api.post('/cards/equip-sticker', {
        user_card_id: userCardId,
        position_x:   50,
        position_y:   50,
      })
      setShowPicker(false)
      await load()
    } catch (e) {
      alert(e.response?.data?.detail || "Erreur à l'équipement")
    }
  }

  async function unequip(userCardId) {
    if (!window.confirm("Retirer ce sticker de la bannière ?")) return
    try {
      await api.delete(`/cards/equip-sticker/${userCardId}`)
      await load()
    } catch (e) {
      alert(e.response?.data?.detail || "Erreur")
    }
  }

  /* ── Drag handlers ── */
  function onPointerDown(e, sticker) {
    if (!isOwnProfile) return
    e.preventDefault()
    const rect = e.currentTarget.getBoundingClientRect()
    setDragInfo({
      id:       sticker.user_card_id,
      offsetX:  e.clientX - rect.left - rect.width / 2,
      offsetY:  e.clientY - rect.top  - rect.height / 2,
      lastX:    sticker.position_x,
      lastY:    sticker.position_y,
    })
  }

  useEffect(() => {
    if (!dragInfo) return

    function onMove(e) {
      const banner = bannerRef?.current
      if (!banner) return
      const bRect = banner.getBoundingClientRect()
      const x = ((e.clientX - bRect.left - dragInfo.offsetX) / bRect.width) * 100
      const y = ((e.clientY - bRect.top  - dragInfo.offsetY) / bRect.height) * 100
      const cx = Math.max(0, Math.min(100, x))
      const cy = Math.max(0, Math.min(100, y))

      setStickers(prev => prev.map(s =>
        s.user_card_id === dragInfo.id
          ? { ...s, position_x: cx, position_y: cy }
          : s
      ))
      dragInfo.lastX = cx
      dragInfo.lastY = cy
    }

    async function onUp() {
      try {
        await api.post('/cards/move-sticker', {
          user_card_id: dragInfo.id,
          position_x:   dragInfo.lastX,
          position_y:   dragInfo.lastY,
        })
      } catch {
        load()
      }
      setDragInfo(null)
    }

    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    return () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
  }, [dragInfo, bannerRef])

  if (loading) return null
  if (!isOwnProfile && stickers.length === 0) return null

  const canAddMore = isOwnProfile && stickers.length < 3

  return (
    <>
      {stickers.map(s => (
        <div
          key={s.user_card_id}
          className={`bs-sticker r-${s.card.rarity} ${dragInfo?.id === s.user_card_id ? 'dragging' : ''}`}
          style={{
            left: `${s.position_x}%`,
            top:  `${s.position_y}%`,
          }}
          onPointerDown={(e) => onPointerDown(e, s)}
          title={s.card.name}
        >
          <img src={s.card.image_url} alt={s.card.name} referrerPolicy="no-referrer" draggable={false} />
          {isOwnProfile && (
            <button
              className="bs-sticker-remove"
              onClick={(e) => { e.stopPropagation(); unequip(s.user_card_id) }}
              onPointerDown={(e) => e.stopPropagation()}
              title="Retirer"
            >×</button>
          )}
        </div>
      ))}

      {canAddMore && (
        <button className="bs-add-btn" onClick={openPicker}>
          <span>+</span> Sticker
        </button>
      )}

      {showPicker && createPortal(
        <div className="bs-picker-overlay" onClick={() => setShowPicker(false)}>
          <div className="bs-picker" onClick={e => e.stopPropagation()}>
            <div className="bs-picker-head">
              <div className="bs-picker-eyebrow">PERSONNALISATION</div>
              <h3 className="bs-picker-title">Choisir un sticker</h3>
              <button className="bs-picker-close" onClick={() => setShowPicker(false)}>×</button>
            </div>
            {inventory.length === 0 ? (
              <div className="bs-picker-empty">
                <div className="bs-picker-empty-icon">✨</div>
                <div className="bs-picker-empty-title">Aucun sticker disponible</div>
                <div className="bs-picker-empty-sub">Ouvre des caisses pour en obtenir.</div>
              </div>
            ) : (
              <div className="bs-picker-grid">
                {inventory.map(uc => (
                  <button
                    key={uc.id}
                    className={`bs-picker-card r-${uc.card.rarity}`}
                    onClick={() => pickSticker(uc.id)}
                  >
                    <img src={uc.card.image_url} alt={uc.card.name} referrerPolicy="no-referrer" />
                    <div className="bs-picker-card-name">{uc.card.name}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>,
        document.body
      )}
    </>
  )
}