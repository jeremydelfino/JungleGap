import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/client'
import useAuthStore from '../../store/auth'
import './Settings.css'

const TABS = [
  { id: 'profile',  label: 'Profil',                  icon: '👤' },
  { id: 'security', label: 'Sécurité',                icon: '🔒' },
  { id: 'socials',  label: 'Réseaux',                 icon: '🔗' },
  { id: 'promo',    label: 'Code promo',              icon: '🎁' },
  { id: 'danger',   label: 'Suppression du compte',   icon: '⚠️' },
]

/* ─── TOAST ─── */
function Toast({ msg, type, onClose }) {
  useEffect(() => { const t = setTimeout(onClose, 3500); return () => clearTimeout(t) }, [])
  return (
    <div className={`settings-toast settings-toast-${type}`}>
      <span className="settings-toast-icon">{type === 'success' ? '✓' : '✕'}</span>
      {msg}
    </div>
  )
}

/* ─── DELETE CONFIRM MODAL ─── */
function DeleteModal({ username, onConfirm, onClose, loading }) {
  const [typed, setTyped] = useState('')
  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-modal-icon">☠️</div>
        <h3 className="settings-modal-title">Supprimer le compte</h3>
        <p className="settings-modal-sub">
          Cette action est <strong>irréversible</strong>. Tous tes coins, paris et données seront effacés définitivement.
        </p>
        <div className="settings-modal-field">
          <label className="settings-label">Tape <span className="settings-modal-username">{username}</span> pour confirmer</label>
          <input
            className="settings-input"
            type="text"
            placeholder={username}
            value={typed}
            onChange={e => setTyped(e.target.value)}
            autoFocus
          />
        </div>
        <div className="settings-modal-actions">
          <button className="settings-btn-ghost" onClick={onClose}>Annuler</button>
          <button
            className="settings-btn-danger"
            onClick={() => onConfirm()}
            disabled={typed !== username || loading}
          >
            {loading ? <><span className="settings-spinner" /> Suppression…</> : 'Supprimer définitivement'}
          </button>
        </div>
      </div>
    </div>
  )
}

/* ─── REWARD CARD (affiché après redeem réussi) ─── */
function RewardCard({ rewards, coinsTotal, onClose }) {
  const hasCoins = rewards.coins > 0
  const hasCard  = !!rewards.card

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-reward-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-reward-confetti">🎉</div>
        <h3 className="settings-reward-title">Code activé !</h3>

        <div className="settings-reward-items">
          {hasCoins && (
            <div className="settings-reward-item settings-reward-coins">
              <span className="settings-reward-item-icon">🪙</span>
              <div>
                <div className="settings-reward-item-val">+{rewards.coins.toLocaleString()} coins</div>
                <div className="settings-reward-item-sub">Nouveau solde : {coinsTotal.toLocaleString()}</div>
              </div>
            </div>
          )}
          {hasCard && (
            <div className={`settings-reward-item settings-reward-card rarity-${rewards.card.rarity}`}>
              <div className="settings-reward-card-img-wrap">
                {rewards.card.image_url
                  ? <img src={rewards.card.image_url} alt={rewards.card.name} />
                  : <span>🃏</span>
                }
              </div>
              <div>
                <div className="settings-reward-item-val">{rewards.card.name}</div>
                <div className="settings-reward-item-sub">{rewards.card.rarity}</div>
              </div>
            </div>
          )}
        </div>

        <button className="settings-btn-primary settings-reward-close" onClick={onClose}>
          Super ! <span className="settings-btn-shine" />
        </button>
      </div>
    </div>
  )
}

export default function Settings() {
  const navigate          = useNavigate()
  const { user, login: loginStore, logout, token } = useAuthStore()
  const [tab, setTab]     = useState('profile')
  const [toast, setToast] = useState(null)
  const [showDelete, setShowDelete] = useState(false)
  const [reward, setReward]         = useState(null)   // { rewards, coinsTotal }

  /* ── Profile form ── */
  const [profileForm, setProfileForm]       = useState({ username: '' })
  const [profileLoading, setProfileLoading] = useState(false)

  /* ── Password form ── */
  const [pwdForm, setPwdForm]       = useState({ current: '', next: '', confirm: '' })
  const [pwdLoading, setPwdLoading] = useState(false)
  const [showPwd, setShowPwd]       = useState({ current: false, next: false, confirm: false })

  /* ── Promo form ── */
  const [promoCode, setPromoCode]       = useState('')
  const [promoLoading, setPromoLoading] = useState(false)

  /* ── Delete ── */
  const [deleteLoading, setDeleteLoading] = useState(false)

  /* ── Socials ── */
  const [socials, setSocials] = useState({
    discord:          null,  // { username, verified_at } | null
    twitch:           null,
    x_handle:         '',
    instagram_handle: '',
  })
  const [socialsLoading, setSocialsLoading] = useState({ discord: false, twitch: false, links: false })
  const [handlesForm,    setHandlesForm]    = useState({ x_handle: '', instagram_handle: '' })

  /* ── Load profile + socials ── */
  useEffect(() => {
    if (!user) { navigate('/login'); return }
    api.get('/profile/me')
      .then(r => {
        setProfileForm({ username: r.data.username || '' })
        const s = r.data.social || {}
        setSocials({
          discord:          s.discord || null,
          twitch:           s.twitch  || null,
          x_handle:         s.x_handle         || '',
          instagram_handle: s.instagram_handle || '',
        })
        setHandlesForm({
          x_handle:         s.x_handle         || '',
          instagram_handle: s.instagram_handle || '',
        })
      })
      .catch(() => {})
  }, [user])

  /* ── Retour callback OAuth ── */
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const flag = params.get('social')
    if (!flag) return

    const [platform, status] = flag.split('_')
    if (status === 'ok') {
      setToast({ msg: `Compte ${platform === 'discord' ? 'Discord' : 'Twitch'} lié avec succès !`, type: 'success' })
      setTab('socials')
      api.get('/profile/me').then(r => {
        const s = r.data.social || {}
        setSocials(prev => ({
          ...prev,
          discord: s.discord || null,
          twitch:  s.twitch  || null,
        }))
      })
    } else if (status === 'err') {
      const reason = params.get('reason') || ''
      const map = {
        already_linked: 'Ce compte est déjà lié à un autre utilisateur JungleGap',
        state_invalid:  'Lien expiré, recommence',
      }
      setToast({ msg: map[reason] || `Erreur lors de la liaison ${platform}`, type: 'error' })
      setTab('socials')
    }
    window.history.replaceState({}, '', '/settings')
  }, [])

  const notify = (msg, type = 'success') => setToast({ msg, type })

  /* ── Update profile ── */
  const handleProfileSave = async e => {
    e.preventDefault()
    if (!profileForm.username.trim()) return
    setProfileLoading(true)
    try {
      const { data } = await api.patch('/settings/profile', {
        username: profileForm.username.trim(),
      })
      loginStore({ ...user, username: data.username }, token)
      notify('Pseudo mis à jour ✓')
    } catch (err) {
      notify(err.response?.data?.detail || 'Erreur lors de la mise à jour', 'error')
    } finally { setProfileLoading(false) }
  }

  /* ── Update password ── */
  const handlePasswordSave = async e => {
    e.preventDefault()
    if (pwdForm.next !== pwdForm.confirm) { notify('Les mots de passe ne correspondent pas', 'error'); return }
    if (pwdForm.next.length < 8) { notify('Mot de passe trop court (min 8 caractères)', 'error'); return }
    setPwdLoading(true)
    try {
      await api.patch('/settings/password', {
        current_password: pwdForm.current,
        new_password:     pwdForm.next,
      })
      setPwdForm({ current: '', next: '', confirm: '' })
      notify('Mot de passe modifié ✓')
    } catch (err) {
      notify(err.response?.data?.detail || 'Mot de passe actuel incorrect', 'error')
    } finally { setPwdLoading(false) }
  }

  /* ── Redeem promo ── */
  const handleRedeem = async e => {
    e.preventDefault()
    if (!promoCode.trim()) return
    setPromoLoading(true)
    try {
      const { data } = await api.post('/promo/redeem', { code: promoCode.trim() })
      setPromoCode('')
      loginStore({ ...user, coins: data.coins_total }, token)
      setReward({ rewards: data.rewards, coinsTotal: data.coins_total })
    } catch (err) {
      notify(err.response?.data?.detail || 'Code invalide ou déjà utilisé', 'error')
    } finally { setPromoLoading(false) }
  }

  /* ── Delete account ── */
  const handleDelete = async () => {
    setDeleteLoading(true)
    try {
      await api.delete('/settings/account')
      logout()
      navigate('/')
    } catch (err) {
      notify(err.response?.data?.detail || 'Erreur lors de la suppression', 'error')
      setDeleteLoading(false)
      setShowDelete(false)
    }
  }

  /* ── Lier Discord/Twitch ── */
  const handleConnect = async (platform) => {
    setSocialsLoading(s => ({ ...s, [platform]: true }))
    try {
      const { data } = await api.get(`/social/${platform}/connect`)
      window.location.href = data.url
    } catch {
      notify(`Impossible de lier ${platform}`, 'error')
      setSocialsLoading(s => ({ ...s, [platform]: false }))
    }
  }

  /* ── Délier ── */
  const handleUnlink = async (platform) => {
    try {
      await api.delete(`/social/${platform}`)
      setSocials(s => ({
        ...s,
        ...(platform === 'discord'   && { discord: null }),
        ...(platform === 'twitch'    && { twitch:  null }),
        ...(platform === 'x'         && { x_handle: '' }),
        ...(platform === 'instagram' && { instagram_handle: '' }),
      }))
      if (platform === 'x')         setHandlesForm(f => ({ ...f, x_handle: '' }))
      if (platform === 'instagram') setHandlesForm(f => ({ ...f, instagram_handle: '' }))
      notify('Compte délié', 'success')
    } catch (err) {
      notify(err.response?.data?.detail || 'Erreur', 'error')
    }
  }

  /* ── Save handles X / Instagram ── */
  const handleSaveLinks = async () => {
    setSocialsLoading(s => ({ ...s, links: true }))
    try {
      const { data } = await api.post('/social/links', {
        x_handle:         handlesForm.x_handle.trim()         || null,
        instagram_handle: handlesForm.instagram_handle.trim() || null,
      })
      setSocials(s => ({ ...s, x_handle: data.x_handle || '', instagram_handle: data.instagram_handle || '' }))
      notify('Handles enregistrés', 'success')
    } catch (err) {
      notify(err.response?.data?.detail || 'Erreur', 'error')
    } finally {
      setSocialsLoading(s => ({ ...s, links: false }))
    }
  }

  const pwgField  = k => e => setPwdForm(f => ({ ...f, [k]: e.target.value }))
  const profField = k => e => setProfileForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <div className="settings-page">

      {/* ─── GLOW ─── */}
      <div className="settings-glow settings-glow-1" />
      <div className="settings-glow settings-glow-2" />

      {/* ─── HEADER ─── */}
      <div className="settings-header">
        <button className="settings-back" onClick={() => navigate('/profile')}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>
          Profil
        </button>
        <div className="settings-header-title">
          <h1 className="settings-title">Paramètres</h1>
          <p className="settings-sub">Gère ton compte <span className="settings-sub-accent">Jungle Gap</span></p>
        </div>
      </div>

      {/* ─── LAYOUT ─── */}
      <div className="settings-layout">

        {/* ── SIDEBAR ── */}
        <nav className="settings-sidebar">
          {TABS.map(t => (
            <button
              key={t.id}
              className={`settings-tab ${tab === t.id ? 'active' : ''} ${t.id === 'danger' ? 'danger-tab' : ''}`}
              onClick={() => setTab(t.id)}
            >
              <span className="settings-tab-icon">{t.icon}</span>
              <span className="settings-tab-label">{t.label}</span>
              {tab === t.id && <span className="settings-tab-indicator" />}
            </button>
          ))}
        </nav>

        {/* ── CONTENT ── */}
        <div className="settings-content">

          {/* ─── PROFIL ─── */}
          {tab === 'profile' && (
            <div className="settings-section" key="profile">
              <div className="settings-section-header">
                <div className="settings-section-icon-wrap"><span>👤</span></div>
                <div>
                  <div className="settings-section-title">Informations du profil</div>
                  <div className="settings-section-desc">Modifie ton pseudo affiché sur la plateforme</div>
                </div>
              </div>

              <form className="settings-form" onSubmit={handleProfileSave}>
                <div className="settings-field">
                  <label className="settings-label">
                    Pseudo
                    <span className="settings-label-hint">3–20 caractères</span>
                  </label>
                  <div className="settings-input-wrap">
                    <span className="settings-input-prefix">@</span>
                    <input
                      className="settings-input settings-input-prefixed"
                      type="text"
                      value={profileForm.username}
                      onChange={profField('username')}
                      minLength={3} maxLength={20}
                      required
                    />
                  </div>
                </div>

                <div className="settings-field settings-field-readonly">
                  <label className="settings-label">
                    Email
                    <span className="settings-label-hint settings-label-locked">🔒 non modifiable</span>
                  </label>
                  <div className="settings-input settings-input-disabled">
                    {user?.email || '—'}
                  </div>
                </div>

                <div className="settings-form-footer">
                  <div className="settings-coins-info">
                    <span className="settings-coins-dot" />
                    <span>Solde : <strong>{user?.coins?.toLocaleString() ?? '—'} coins</strong></span>
                  </div>
                  <button className="settings-btn-primary" type="submit" disabled={profileLoading}>
                    {profileLoading
                      ? <><span className="settings-spinner" /> Enregistrement…</>
                      : <><span>Enregistrer</span><span className="settings-btn-shine" /></>
                    }
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ─── SÉCURITÉ ─── */}
          {tab === 'security' && (
            <div className="settings-section" key="security">
              <div className="settings-section-header">
                <div className="settings-section-icon-wrap"><span>🔒</span></div>
                <div>
                  <div className="settings-section-title">Changer de mot de passe</div>
                  <div className="settings-section-desc">Utilise un mot de passe fort et unique</div>
                </div>
              </div>

              <form className="settings-form" onSubmit={handlePasswordSave}>
                {[
                  { key: 'current', label: 'Mot de passe actuel',  placeholder: '••••••••', autoComplete: 'current-password' },
                  { key: 'next',    label: 'Nouveau mot de passe',  placeholder: 'Min. 8 caractères', autoComplete: 'new-password' },
                  { key: 'confirm', label: 'Confirmer le nouveau',  placeholder: '••••••••', autoComplete: 'new-password' },
                ].map(({ key, label, placeholder, autoComplete }) => (
                  <div className="settings-field" key={key}>
                    <label className="settings-label">{label}</label>
                    <div className="settings-input-wrap">
                      <input
                        className={`settings-input settings-input-pwd ${key === 'confirm' && pwdForm.confirm && pwdForm.confirm !== pwdForm.next ? 'settings-input-err' : ''}`}
                        type={showPwd[key] ? 'text' : 'password'}
                        placeholder={placeholder}
                        value={pwdForm[key]}
                        onChange={pwgField(key)}
                        autoComplete={autoComplete}
                        required
                      />
                      <button type="button" className="settings-eye-btn" onClick={() => setShowPwd(s => ({ ...s, [key]: !s[key] }))}>
                        {showPwd[key] ? '🙈' : '👁️'}
                      </button>
                    </div>
                    {key === 'next' && pwdForm.next && <PasswordStrength password={pwdForm.next} />}
                    {key === 'confirm' && pwdForm.confirm && pwdForm.confirm !== pwdForm.next && (
                      <span className="settings-field-err">Les mots de passe ne correspondent pas</span>
                    )}
                  </div>
                ))}

                <div className="settings-form-footer">
                  <div className="settings-security-hint">
                    <span>🛡️</span>
                    <span>Mélange lettres, chiffres et symboles pour un mot de passe solide</span>
                  </div>
                  <button className="settings-btn-primary" type="submit" disabled={pwdLoading}>
                    {pwdLoading
                      ? <><span className="settings-spinner" /> Mise à jour…</>
                      : <><span>Mettre à jour</span><span className="settings-btn-shine" /></>
                    }
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ─── RÉSEAUX ─── */}
          {tab === 'socials' && (
            <div className="settings-section" key="socials">
              <div className="settings-section-header">
                <div className="settings-section-icon-wrap"><span>🔗</span></div>
                <div>
                  <div className="settings-section-title">Réseaux sociaux</div>
                  <div className="settings-section-desc">Lie tes comptes pour les afficher sur ton profil</div>
                </div>
              </div>

              {/* ── Discord ── */}
              <div className="settings-social-row">
                <div className="settings-social-info">
                  <div className="settings-social-icon settings-social-discord">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.37a19.79 19.79 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>
                  </div>
                  <div>
                    <div className="settings-social-name">Discord</div>
                    {socials.discord
                      ? <div className="settings-social-handle">@{socials.discord.username}</div>
                      : <div className="settings-social-handle settings-social-empty">Non lié</div>
                    }
                  </div>
                </div>
                <div className="settings-social-actions">
                  {socials.discord
                    ? <>
                        <span className="settings-social-badge">✓ Vérifié</span>
                        <button className="settings-btn-unlink" onClick={() => handleUnlink('discord')}>Délier</button>
                      </>
                    : <button className="settings-btn-link settings-btn-link-discord" onClick={() => handleConnect('discord')} disabled={socialsLoading.discord}>
                        {socialsLoading.discord ? <span className="settings-spinner" /> : 'Lier'}
                      </button>
                  }
                </div>
              </div>

              {/* ── Twitch ── */}
              <div className="settings-social-row">
                <div className="settings-social-info">
                  <div className="settings-social-icon settings-social-twitch">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M11.571 4.714h1.715v5.143H11.57zm4.715 0H18v5.143h-1.714zM6 0L1.714 4.286v15.428h5.143V24l4.286-4.286h3.428L22.286 12V0zm14.571 11.143l-3.428 3.428h-3.429l-3 3v-3H6.857V1.714h13.714Z"/></svg>
                  </div>
                  <div>
                    <div className="settings-social-name">Twitch</div>
                    {socials.twitch
                      ? <div className="settings-social-handle">@{socials.twitch.username}</div>
                      : <div className="settings-social-handle settings-social-empty">Non lié</div>
                    }
                  </div>
                </div>
                <div className="settings-social-actions">
                  {socials.twitch
                    ? <>
                        <span className="settings-social-badge">✓ Vérifié</span>
                        <button className="settings-btn-unlink" onClick={() => handleUnlink('twitch')}>Délier</button>
                      </>
                    : <button className="settings-btn-link settings-btn-link-twitch" onClick={() => handleConnect('twitch')} disabled={socialsLoading.twitch}>
                        {socialsLoading.twitch ? <span className="settings-spinner" /> : 'Lier'}
                      </button>
                  }
                </div>
              </div>

              {/* ── Séparateur ── */}
              <div className="settings-social-divider">
                <span>Liens manuels</span>
              </div>

              {/* ── X (Twitter) ── */}
              <div className="settings-field">
                <label className="settings-label">
                  X (Twitter)
                  <span className="settings-label-hint">4–15 caractères</span>
                </label>
                <div className="settings-social-input-row">
                  <div className="settings-input-wrap" style={{ flex: 1 }}>
                    <span className="settings-input-prefix">@</span>
                    <input
                      className="settings-input settings-input-prefixed"
                      type="text"
                      placeholder="pseudo_x"
                      value={handlesForm.x_handle}
                      onChange={e => setHandlesForm(f => ({ ...f, x_handle: e.target.value }))}
                      maxLength={15}
                    />
                  </div>
                  {socials.x_handle && (
                    <button className="settings-btn-unlink" onClick={() => handleUnlink('x')}>Supprimer</button>
                  )}
                </div>
              </div>

              {/* ── Instagram ── */}
              <div className="settings-field">
                <label className="settings-label">
                  Instagram
                  <span className="settings-label-hint">1–30 caractères</span>
                </label>
                <div className="settings-social-input-row">
                  <div className="settings-input-wrap" style={{ flex: 1 }}>
                    <span className="settings-input-prefix">@</span>
                    <input
                      className="settings-input settings-input-prefixed"
                      type="text"
                      placeholder="pseudo_ig"
                      value={handlesForm.instagram_handle}
                      onChange={e => setHandlesForm(f => ({ ...f, instagram_handle: e.target.value }))}
                      maxLength={30}
                    />
                  </div>
                  {socials.instagram_handle && (
                    <button className="settings-btn-unlink" onClick={() => handleUnlink('instagram')}>Supprimer</button>
                  )}
                </div>
              </div>

              <div className="settings-form-footer">
                <div className="settings-security-hint">
                  <span>💡</span>
                  <span>Ces handles ne sont pas vérifiés, ils servent juste de lien</span>
                </div>
                <button className="settings-btn-primary" onClick={handleSaveLinks} disabled={socialsLoading.links}>
                  {socialsLoading.links
                    ? <><span className="settings-spinner" /> Enregistrement…</>
                    : <><span>Enregistrer</span><span className="settings-btn-shine" /></>
                  }
                </button>
              </div>
            </div>
          )}

          {/* ─── CODE PROMO ─── */}
          {tab === 'promo' && (
            <div className="settings-section" key="promo">
              <div className="settings-section-header">
                <div className="settings-section-icon-wrap settings-section-icon-promo"><span>🎁</span></div>
                <div>
                  <div className="settings-section-title">Code promotionnel</div>
                  <div className="settings-section-desc">Entre un code pour débloquer des coins ou des cartes exclusives</div>
                </div>
              </div>

              <form className="settings-form" onSubmit={handleRedeem}>
                <div className="settings-field">
                  <label className="settings-label">Ton code</label>
                  <div className="settings-promo-row">
                    <div className="settings-input-wrap" style={{ flex: 1 }}>
                      <span className="settings-input-prefix">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>
                      </span>
                      <input
                        className="settings-input settings-input-prefixed settings-promo-input"
                        type="text"
                        placeholder="JUNGLEGAP2026"
                        value={promoCode}
                        onChange={e => setPromoCode(e.target.value.toUpperCase())}
                        maxLength={50}
                        spellCheck={false}
                        autoComplete="off"
                      />
                    </div>
                    <button className="settings-btn-promo" type="submit" disabled={promoLoading || !promoCode.trim()}>
                      {promoLoading
                        ? <><span className="settings-spinner" /> Vérification…</>
                        : <><span>Activer</span><span className="settings-btn-shine" /></>
                      }
                    </button>
                  </div>
                </div>

                <div className="settings-promo-hints">
                  <div className="settings-promo-hint">
                    <span className="settings-promo-hint-icon">🪙</span>
                    <span>Certains codes offrent des <strong>coins</strong> instantanément</span>
                  </div>
                  <div className="settings-promo-hint">
                    <span className="settings-promo-hint-icon">🃏</span>
                    <span>D'autres débloquent des <strong>cartes exclusives</strong> pour ton profil</span>
                  </div>
                  <div className="settings-promo-hint">
                    <span className="settings-promo-hint-icon">⚡</span>
                    <span>Un code ne peut être utilisé <strong>qu'une seule fois</strong> par compte</span>
                  </div>
                </div>
              </form>
            </div>
          )}

          {/* ─── DANGER ZONE ─── */}
          {tab === 'danger' && (
            <div className="settings-section" key="danger">
              <div className="settings-section-header">
                <div className="settings-section-icon-wrap settings-section-icon-danger"><span>⚠️</span></div>
                <div>
                  <div className="settings-section-title">Zone dangereuse</div>
                  <div className="settings-section-desc">Actions irréversibles sur ton compte</div>
                </div>
              </div>

              <div className="settings-danger-card">
                <div className="settings-danger-card-left">
                  <div className="settings-danger-card-title">Supprimer le compte</div>
                  <div className="settings-danger-card-desc">
                    Supprime définitivement ton compte, tous tes coins ({user?.coins?.toLocaleString() ?? 0} 🪙), tes paris et tes données. Impossible à annuler.
                  </div>
                </div>
                <button className="settings-btn-danger" onClick={() => setShowDelete(true)}>
                  Supprimer le compte
                </button>
              </div>

              <div className="settings-danger-info">
                <span className="settings-danger-info-icon">ℹ️</span>
                <span>La suppression est immédiate et définitive. Assure-toi d'avoir bien réfléchi avant de continuer.</span>
              </div>
            </div>
          )}

        </div>
      </div>

      {/* ─── TOAST ─── */}
      {toast && <Toast msg={toast.msg} type={toast.type} onClose={() => setToast(null)} />}

      {/* ─── DELETE MODAL ─── */}
      {showDelete && (
        <DeleteModal
          username={user?.username}
          onConfirm={handleDelete}
          onClose={() => setShowDelete(false)}
          loading={deleteLoading}
        />
      )}

      {/* ─── REWARD MODAL ─── */}
      {reward && (
        <RewardCard
          rewards={reward.rewards}
          coinsTotal={reward.coinsTotal}
          onClose={() => setReward(null)}
        />
      )}

    </div>
  )
}

/* ─── PASSWORD STRENGTH ─── */
function PasswordStrength({ password }) {
  const checks = [
    password.length >= 8,
    /[A-Z]/.test(password),
    /[0-9]/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ]
  const score  = checks.filter(Boolean).length
  const levels = ['', 'Faible', 'Moyen', 'Bon', 'Fort']
  const colors = ['', '#ef4444', '#f59e0b', '#65BD62', '#22c55e']

  return (
    <div className="settings-pwd-strength">
      <div className="settings-pwd-bars">
        {[1,2,3,4].map(i => (
          <div key={i} className="settings-pwd-bar" style={{ background: i <= score ? colors[score] : '#ffffff10' }} />
        ))}
      </div>
      {score > 0 && <span className="settings-pwd-label" style={{ color: colors[score] }}>{levels[score]}</span>}
    </div>
  )
}