// frontend/src/pages/Profile/index.jsx
import './Profile.css'
import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useAuthStore from '../../store/auth'
import api from '../../api/client'
import TcgCard from '../../components/ui/TcgCard'
import { TIER_COLORS, APEX_TIERS } from '../Player/constants'
import { getTierImage } from '../Player/utils'

const REGIONS = ['EUW','EUNE','NA','KR','BR','JP','TR','OCE']

const BET_TYPE_LABELS  = { who_wins: 'Victoire', first_blood: 'First Blood' }
const BET_VALUE_LABELS = { blue: 'Équipe Bleue', red: 'Équipe Rouge' }

/* ─── Helpers ─── */
function computeStats(bets) {
  const won    = bets.filter(b => b.status === 'won')
  const lost   = bets.filter(b => b.status === 'lost')
  const gained = won.reduce((s, b)  => s + (b.payout  || 0), 0)
  const spent  = lost.reduce((s, b) => s + (b.amount  || 0), 0)
  const resolved = won.length + lost.length
  const winrate  = resolved > 0 ? Math.round((won.length / resolved) * 100) : null
  let streak = 0
  for (const b of bets) {
    if (b.status === 'won') streak++
    else if (b.status === 'lost') break
  }
  return { gained, spent, winrate, streak, total: bets.length, profit: gained - spent }
}

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const d = Math.floor(diff / 86400000)
  const h = Math.floor(diff / 3600000)
  const m = Math.floor(diff / 60000)
  if (d > 0) return `il y a ${d}j`
  if (h > 0) return `il y a ${h}h`
  if (m > 0) return `il y a ${m}m`
  return 'à l\'instant'
}

function formatRank(ra) {
  if (!ra?.tier) return 'Non classé'
  const tierCap = ra.tier.charAt(0) + ra.tier.slice(1).toLowerCase()
  const isApex  = APEX_TIERS.has(ra.tier)
  if (isApex) return `${tierCap} · ${ra.lp ?? 0} LP`
  return `${tierCap} ${ra.rank ?? ''} · ${ra.lp ?? 0} LP`
}

/* ─── Mini-stepper ajout compte Riot ─── */
function AddRiotStepper({ onDone, onCancel }) {
  const [step,      setStep]      = useState(0)
  const [region,    setRegion]    = useState('EUW')
  const [riotId,    setRiotId]    = useState('')
  const [pending,   setPending]   = useState(null)
  const [loading,   setLoading]   = useState(false)
  const [verifying, setVerifying] = useState(false)
  const [error,     setError]     = useState('')

  const handleInit = async () => {
    setError(''); setLoading(true)
    const parts = riotId.trim().split('#')
    if (parts.length !== 2 || !parts[0] || !parts[1]) {
      setError('Format attendu : GameName#TAG')
      setLoading(false)
      return
    }
    try {
      const { data } = await api.post('/profile/riot-accounts/init', {
        game_name: parts[0].trim(),
        tag_line:  parts[1].trim(),
        region,
      })
      setPending(data)
      setStep(1)
    } catch (err) {
      setError(err.response?.data?.detail || 'Riot ID introuvable')
    } finally { setLoading(false) }
  }

  const handleVerify = async () => {
    setError(''); setVerifying(true)
    try {
      const { data } = await api.post('/profile/riot-accounts/verify', {
        riot_account_id: pending.riot_account_id,
      })
      onDone(data.riot_account)
    } catch (err) {
      setError(err.response?.data?.detail || 'Mauvaise icône, réessaie')
    } finally { setVerifying(false) }
  }

  return (
    <div className="add-riot-stepper">
      {step === 0 && (
        <>
          <div className="add-riot-regions">
            {REGIONS.map(r => (
              <button
                key={r}
                className={`add-riot-region-btn ${region === r ? 'active' : ''}`}
                onClick={() => { setRegion(r); setError('') }}
              >{r}</button>
            ))}
          </div>
          <div className="add-riot-input-row">
            <input
              className="add-riot-input"
              type="text"
              placeholder="GameName#TAG"
              value={riotId}
              onChange={e => { setRiotId(e.target.value); setError('') }}
            />
            <button
              className="profile-btn-primary"
              onClick={handleInit}
              disabled={loading || !riotId.trim()}
            >
              {loading ? <span className="profile-spinner-sm" /> : 'Suivant →'}
            </button>
          </div>
          {error && <div className="add-riot-error">{error}</div>}
          <button className="add-riot-cancel" onClick={onCancel}>Annuler</button>
        </>
      )}

      {step === 1 && pending && (
        <>
          <div className="add-riot-verify-row">
            <img className="add-riot-verify-icon" src={pending.icon_url} alt={`icône ${pending.icon_id}`} />
            <div className="add-riot-verify-info">
              <div className="add-riot-verify-name">
                {pending.game_name}<span className="profile-riot-tag">#{pending.tag_line}</span>
              </div>
              <div className="add-riot-verify-instruction">
                Équipe l'icône <strong>#{pending.icon_id}</strong> dans LoL puis clique Vérifier
              </div>
            </div>
          </div>
          {error && <div className="add-riot-error">{error}</div>}
          <div className="add-riot-verify-actions">
            <button className="add-riot-cancel" onClick={() => { setStep(0); setError('') }}>Retour</button>
            <button className="profile-btn-primary" onClick={handleVerify} disabled={verifying}>
              {verifying ? <span className="profile-spinner-sm" /> : '✓ Vérifier'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}

/* ─── Composant principal ─────────────────────────────────── */
export default function Profile() {
  const navigate              = useNavigate()
  const { userId }            = useParams()
  const { user, token, login } = useAuthStore()
  const fileRef               = useRef(null)

  const isOwnProfile = !userId || (user && String(user.id) === String(userId))

  const [profile,        setProfile]        = useState(null)
  const [loading,        setLoading]        = useState(true)
  const [showTeamPicker, setShowTeamPicker] = useState(false)
  const [bets,           setBets]           = useState([])
  const [betsLoading,    setBetsLoading]    = useState(false)
  const [userCards,      setUserCards]      = useState([])
  const [showAddRiot,    setShowAddRiot]    = useState(false)
  const [rightTab,       setRightTab]       = useState('bets')   // 'bets' | 'cards'
  const [esportsTeams,   setEsportsTeams]   = useState([])

  const loadProfile = () => {
    const endpoint = isOwnProfile ? '/profile/me' : `/profile/user/${userId}`
    api.get(endpoint)
      .then(r => setProfile(r.data))
      .catch(() => setProfile(null))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!token) { navigate('/login'); return }
    loadProfile()
    if (isOwnProfile) {
      setBetsLoading(true)
      api.get('/bets/my-bets')
        .then(r => setBets(r.data))
        .catch(() => setBets([]))
        .finally(() => setBetsLoading(false))
      api.get('/cards/my-cards')
        .then(r => setUserCards(r.data))
        .catch(() => setUserCards([]))
    }
  }, [userId])

  useEffect(() => {
    api.get('/esports/teams')
      .then(r => setEsportsTeams(r.data))
      .catch(() => {})
  }, [])

  const handlePickTeam = async (team) => {
    try {
      await api.post('/profile/set-team', { name: team.name, logo: team.logo, color: team.color })
      setProfile(p => ({ ...p, favorite_team: { name: team.name, logo: team.logo, color: team.color } }))
    } catch (err) { console.error(err) }
    setShowTeamPicker(false)
  }

  const handleRemoveTeam = async () => {
    try {
      await api.post('/profile/set-team', { name: '', logo: '', color: '' })
      setProfile(p => ({ ...p, favorite_team: null }))
    } catch (err) { console.error(err) }
  }

  const handleAvatarUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const fd  = new FormData()
    fd.append('file', file)
    const tkn = localStorage.getItem('token')
    try {
      const res    = await api.post(`/upload/avatar?authorization=Bearer ${tkn}`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      const newUrl = res.data.avatar_url || res.data.url
      setProfile(p => ({ ...p, avatar_url: newUrl }))
      login({ ...user, avatar_url: newUrl }, token)
    } catch (err) { console.error(err) }
  }

  const handleDeleteRiot = async (accountId) => {
    try {
      await api.delete(`/profile/riot-accounts/${accountId}`)
      setProfile(p => ({ ...p, riot_accounts: p.riot_accounts.filter(ra => ra.id !== accountId) }))
    } catch (err) { console.error(err) }
  }

  const handleSetPrimary = async (accountId) => {
    try {
      await api.post(`/profile/riot-accounts/${accountId}/set-primary`)
      setProfile(p => ({
        ...p,
        riot_accounts: p.riot_accounts.map(ra => ({ ...ra, is_primary: ra.id === accountId })),
      }))
    } catch (err) { console.error(err) }
  }

  const handleRiotAdded = (newAccount) => {
    setShowAddRiot(false)
    setProfile(p => ({ ...p, riot_accounts: [...(p.riot_accounts || []), newAccount], riot_linked: true }))
  }

  const goToPlayerPage = (ra) => {
    if (!ra) return
    navigate(`/player/${ra.region}/${encodeURIComponent(ra.summoner_name)}/${encodeURIComponent(ra.tag_line)}`)
  }

  if (loading) return (
    <div className="profile-page">
      <div className="profile-loading">
        <div className="profile-spinner" />
        <div className="profile-loading-text">Chargement du profil…</div>
      </div>
    </div>
  )

  if (!profile) return (
    <div className="profile-page">
      <div className="profile-loading">
        <div className="profile-loading-text">Profil introuvable.</div>
      </div>
    </div>
  )

  const displayName  = profile?.username || '—'
  const riotAccounts = profile?.riot_accounts || []
  const primaryAcc   = riotAccounts.find(ra => ra.is_primary) || riotAccounts[0] || null
  const otherAccs    = riotAccounts.filter(ra => ra.id !== primaryAcc?.id)
  const favTeam      = profile?.favorite_team
  const accentColor  = favTeam?.color || '#65BD62'
  const lolIconUrl   = primaryAcc?.profile_icon_url || null
  const avatarSrc    = profile?.avatar_url || lolIconUrl
  const tierColor    = primaryAcc?.tier ? TIER_COLORS[primaryAcc.tier] : '#6b7280'
  const tierImg      = primaryAcc?.tier ? getTierImage(primaryAcc.tier) : null
  const stats = isOwnProfile
    ? computeStats(bets)
    : {
        gained:  profile?.bet_stats?.total_won     ?? 0,
        spent:   profile?.bet_stats?.total_wagered ?? 0,
        winrate: profile?.bet_stats?.winrate       ?? null,
        streak:  profile?.bet_stats?.streak        ?? 0,
        total:   profile?.bet_stats?.total         ?? 0,
        profit:  (profile?.bet_stats?.total_won ?? 0) - (profile?.bet_stats?.total_wagered ?? 0),
      }
  const canAddMore = isOwnProfile && riotAccounts.length < 3

  return (
    <div className="profile-page">

      {/* ─── BANNER IMMERSIF ─── */}
      <div className="profile-banner" style={{ '--accent': accentColor }}>
        <div className="profile-banner-bg" style={{ background: `linear-gradient(135deg, ${accentColor}28 0%, ${accentColor}08 35%, #171717 75%)` }} />
        {favTeam?.logo && (
          <img className="profile-banner-team-logo" src={favTeam.logo} alt={favTeam.name} referrerPolicy="no-referrer" />
        )}
        <div className="profile-banner-glow" style={{ background: `radial-gradient(circle at 20% 50%, ${accentColor}25, transparent 60%)` }} />
        <div className="profile-banner-overlay" />
      </div>

      {/* ─── HERO ─── */}
      <div className="profile-hero">
        <div className="profile-avatar-wrap">
          <div className="profile-avatar" style={{ borderColor: accentColor + '50' }}>
            {avatarSrc
              ? <img src={avatarSrc} alt={displayName} referrerPolicy="no-referrer" onError={e => { e.target.style.display = 'none' }} />
              : <div className="profile-avatar-fallback">{displayName.slice(0, 2).toUpperCase()}</div>
            }
          </div>
          {isOwnProfile && (
            <>
              <button className="profile-avatar-edit" onClick={() => fileRef.current?.click()} title="Changer l'avatar">📷</button>
              <input ref={fileRef} type="file" accept="image/*" hidden onChange={handleAvatarUpload} />
            </>
          )}
        </div>

        <div className="profile-hero-info">
          <div className="profile-hero-tag">PROFIL JOUEUR</div>
          <h1 className="profile-hero-name">{displayName}</h1>
          <div className="profile-hero-meta">
            {favTeam ? (
              <button
                className="profile-hero-team"
                style={{ '--tc': accentColor }}
                onClick={() => isOwnProfile && setShowTeamPicker(true)}
              >
                {favTeam.logo && <img src={favTeam.logo} alt="" referrerPolicy="no-referrer" />}
                <span>Fan de <strong>{favTeam.name}</strong></span>
              </button>
            ) : isOwnProfile ? (
              <button className="profile-hero-team profile-hero-team-empty" onClick={() => setShowTeamPicker(true)}>
                ⚑ Choisir une équipe favorite
              </button>
            ) : null}
            {primaryAcc?.region && (
              <div className="profile-hero-region">
                <span className="profile-hero-region-dot" />
                {primaryAcc.region}
              </div>
            )}
          </div>

          {isOwnProfile && favTeam && (
            <button className="profile-hero-team-remove" onClick={handleRemoveTeam}>
              ✕ Retirer l'équipe
            </button>
          )}
        </div>

        {/* Stat strip */}
        <div className="profile-stat-strip">
          <div className="pss-item">
            <div className="pss-val" style={{ color: stats.profit >= 0 ? '#65BD62' : '#ef4444' }}>
              {stats.profit >= 0 ? '+' : ''}{stats.profit.toLocaleString()}
            </div>
            <div className="pss-lbl">Profit net</div>
          </div>
          <div className="pss-divider" />
          <div className="pss-item">
            <div className="pss-val pss-val-accent">{stats.winrate !== null ? `${stats.winrate}%` : '—'}</div>
            <div className="pss-lbl">Winrate</div>
          </div>
          <div className="pss-divider" />
          <div className="pss-item">
            <div className="pss-val pss-val-gold">{stats.streak > 0 ? `🔥 ${stats.streak}` : '0'}</div>
            <div className="pss-lbl">Streak</div>
          </div>
          <div className="pss-divider" />
          <div className="pss-item">
            <div className="pss-val">{stats.total}</div>
            <div className="pss-lbl">Paris</div>
          </div>
        </div>
      </div>

      {/* ─── COMPTE RIOT PRINCIPAL (full-width showcase) ─── */}
      {primaryAcc && (
        <div className="profile-main-riot" style={{ '--tier-color': tierColor }}>
          <div className="pmr-glow" style={{ background: `radial-gradient(circle at 80% 50%, ${tierColor}22, transparent 60%)` }} />

          <div className="pmr-left">
            <div className="pmr-icon-wrap">
              <div className="pmr-icon-glow" style={{ background: `radial-gradient(circle, ${tierColor}40, transparent 65%)` }} />
              {primaryAcc.profile_icon_url
                ? <img src={primaryAcc.profile_icon_url} alt="" className="pmr-icon" referrerPolicy="no-referrer" />
                : <div className="pmr-icon pmr-icon-placeholder">?</div>
              }
            </div>
            <div className="pmr-info">
              <div className="pmr-badge">COMPTE PRINCIPAL</div>
              <div className="pmr-name">
                {primaryAcc.summoner_name}
                <span className="pmr-tag">#{primaryAcc.tag_line}</span>
              </div>
              <div className="pmr-region">{primaryAcc.region}</div>
            </div>
          </div>

          <div className="pmr-rank">
            {tierImg && (
              <div className="pmr-rank-img">
                <img src={tierImg} alt={primaryAcc.tier} referrerPolicy="no-referrer" />
              </div>
            )}
            <div className="pmr-rank-info">
              <div className="pmr-rank-tier" style={{ color: tierColor }}>
                {formatRank(primaryAcc)}
              </div>
              <div className="pmr-rank-queue">Solo / Duo</div>
            </div>
          </div>

          <div className="pmr-actions">
            <button className="pmr-btn pmr-btn-primary" onClick={() => goToPlayerPage(primaryAcc)}>
              Voir la page joueur →
            </button>
          </div>
        </div>
      )}

      {/* ─── COMPTES SECONDAIRES (compacts) ─── */}
      {(otherAccs.length > 0 || (canAddMore && isOwnProfile)) && (
        <div className="profile-secondary-riots">
          <div className="psr-header">
            <span className="psr-label">Autres comptes liés</span>
            <span className="psr-count">{riotAccounts.length}/3</span>
          </div>

          <div className="psr-list">
            {otherAccs.map(ra => {
              const tc = ra.tier ? TIER_COLORS[ra.tier] : '#6b7280'
              const ti = ra.tier ? getTierImage(ra.tier) : null
              return (
                <div key={ra.id} className="psr-item">
                  <div className="psr-item-left">
                    {ra.profile_icon_url
                      ? <img src={ra.profile_icon_url} alt="" className="psr-icon" referrerPolicy="no-referrer" />
                      : <div className="psr-icon psr-icon-placeholder">?</div>
                    }
                    <div className="psr-item-info">
                      <div className="psr-item-name">
                        {ra.summoner_name}<span className="psr-item-tag">#{ra.tag_line}</span>
                      </div>
                      <div className="psr-item-meta">
                        {ti && <img src={ti} alt="" className="psr-tier-mini" referrerPolicy="no-referrer" />}
                        <span style={{ color: tc }}>{formatRank(ra)}</span>
                        <span className="psr-item-region">· {ra.region}</span>
                      </div>
                    </div>
                  </div>
                  <div className="psr-item-actions">
                    <button className="psr-action" title="Voir page joueur" onClick={() => goToPlayerPage(ra)}>→</button>
                    {isOwnProfile && (
                      <>
                        <button className="psr-action" title="Définir comme principal" onClick={() => handleSetPrimary(ra.id)}>★</button>
                        <button className="psr-action danger" title="Supprimer" onClick={() => handleDeleteRiot(ra.id)}>✕</button>
                      </>
                    )}
                  </div>
                </div>
              )
            })}

            {isOwnProfile && showAddRiot && (
              <AddRiotStepper onDone={handleRiotAdded} onCancel={() => setShowAddRiot(false)} />
            )}

            {canAddMore && !showAddRiot && (
              <button className="psr-add-btn" onClick={() => setShowAddRiot(true)}>
                + Ajouter un compte Riot
              </button>
            )}
          </div>
        </div>
      )}

      {/* Cas spécial : aucun compte du tout */}
      {riotAccounts.length === 0 && isOwnProfile && (
        <div className="profile-no-riot">
          <div className="profile-no-riot-icon">🎮</div>
          <div className="profile-no-riot-title">Aucun compte Riot lié</div>
          <div className="profile-no-riot-sub">Lie un compte pour afficher ton rank et accéder à ta page joueur</div>
          {showAddRiot
            ? <AddRiotStepper onDone={handleRiotAdded} onCancel={() => setShowAddRiot(false)} />
            : <button className="profile-btn-primary" onClick={() => setShowAddRiot(true)}>+ Lier un compte Riot</button>
          }
        </div>
      )}

      {/* ─── GRID 2 COLONNES ─── */}
      <div className="profile-grid">

        {/* ── COL GAUCHE — Stats détaillées ── */}
        <div className="profile-col-left">

          <div className="profile-card">
            <div className="profile-card-label">Statistiques détaillées</div>
            <div className="profile-stats-grid">
              <div className="profile-stat">
                <div className="profile-stat-val green">+{stats.gained.toLocaleString()}</div>
                <div className="profile-stat-lbl">Coins gagnés</div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat-val red">-{stats.spent.toLocaleString()}</div>
                <div className="profile-stat-lbl">Coins perdus</div>
              </div>
              <div className="profile-stat">
                <div className="profile-stat-val accent">{stats.winrate !== null ? `${stats.winrate}%` : '—'}</div>
                <div className="profile-stat-lbl">Win rate</div>
                {stats.winrate !== null && (
                  <div className="profile-stat-bar">
                    <div className="profile-stat-bar-fill" style={{ width: `${stats.winrate}%`, background: stats.winrate >= 50 ? '#65BD62' : '#ef4444' }} />
                  </div>
                )}
              </div>
              <div className="profile-stat">
                <div className="profile-stat-val gold">{stats.streak > 0 ? `🔥 ${stats.streak}` : '0'}</div>
                <div className="profile-stat-lbl">Streak actuel</div>
              </div>
            </div>
          </div>

          {/* Solde rapide */}
          {isOwnProfile && (
            <div className="profile-card profile-card-balance">
              <div className="profile-card-label">Solde actuel</div>
              <div className="profile-balance-val">
                <span className="profile-balance-icon">🪙</span>
                <span>{user?.coins?.toLocaleString() ?? '—'}</span>
              </div>
              <div className="profile-balance-sub">coins disponibles</div>
              <button className="profile-btn-secondary" onClick={() => navigate('/settings')} style={{ marginTop: 12, width: '100%' }}>
                ⚙️ Paramètres du compte
              </button>
            </div>
          )}

        </div>

        {/* ── COL DROITE — Tabs Paris/Cartes ── */}
        <div className="profile-col-right">
          <div className="profile-card profile-card-tabs">
            <div className="profile-tabs">
              <button
                className={`profile-tab ${rightTab === 'bets' ? 'active' : ''}`}
                onClick={() => setRightTab('bets')}
              >
                🎯 Paris
                {bets.length > 0 && <span className="profile-tab-count">{bets.length}</span>}
              </button>
              <button
                className={`profile-tab ${rightTab === 'cards' ? 'active' : ''}`}
                onClick={() => setRightTab('cards')}
              >
                🃏 Collection
                {userCards.length > 0 && <span className="profile-tab-count">{userCards.length}</span>}
              </button>
            </div>

            {/* Tab Paris */}
            {rightTab === 'bets' && (
              <div className="profile-bets-scroll">
                {betsLoading && <div className="profile-bets-empty">Chargement…</div>}
                {!betsLoading && !isOwnProfile && <div className="profile-bets-empty">Historique privé.</div>}
                {!betsLoading && isOwnProfile && bets.length === 0 && <div className="profile-bets-empty">Aucun pari pour le moment.</div>}
                {!betsLoading && isOwnProfile && bets.map(bet => {
                  const isWon     = bet.status === 'won'
                  const isLost    = bet.status === 'lost'
                  const isPending = bet.status === 'pending'
                  const champion  = bet.game?.bet_player?.champion_name
                  const champIcon = bet.game?.bet_player?.champion_icon
                  const proName   = bet.game?.pro?.name
                  const teamName  = bet.game?.pro?.team
                  const betLabel  = BET_TYPE_LABELS[bet.bet_type]  || bet.bet_type
                  const sideLabel = BET_VALUE_LABELS[bet.bet_value] || bet.bet_value
                  return (
                    <div key={bet.id} className={`profile-bet-row ${bet.status}`}>
                      <div className="profile-bet-champ">
                        {champIcon
                          ? <img src={champIcon} alt={champion} onError={e => { e.target.style.display = 'none' }} />
                          : <span className="profile-bet-champ-fallback">🎯</span>
                        }
                      </div>
                      <div className="profile-bet-info">
                        <div className="profile-bet-main">
                          <span className="profile-bet-type">{betLabel}</span>
                          <span className="profile-bet-sep">·</span>
                          <span className="profile-bet-side">{sideLabel}</span>
                          {champion && <span className="profile-bet-champ-name">{champion}</span>}
                        </div>
                        <div className="profile-bet-sub">
                          {proName  && <span>{proName}</span>}
                          {teamName && <span className="profile-bet-team">{teamName}</span>}
                          <span className="profile-bet-time">{timeAgo(bet.created_at)}</span>
                        </div>
                      </div>
                      <div className="profile-bet-result">
                        <div className={`profile-bet-amount ${isWon ? 'green' : isLost ? 'red' : 'muted'}`}>
                          {isWon     && `+${(bet.payout || 0).toLocaleString()}`}
                          {isLost    && `-${bet.amount.toLocaleString()}`}
                          {isPending && `${bet.amount.toLocaleString()}`}
                        </div>
                        <div className={`profile-bet-status-badge ${bet.status}`}>
                          {isWon  && '✓ Gagné'}
                          {isLost && '✗ Perdu'}
                          {isPending && '⏳ En cours'}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Tab Cartes */}
            {rightTab === 'cards' && (
              <div className="profile-tcg-scroll">
                {!isOwnProfile && <div className="profile-bets-empty">Collection privée.</div>}
                {isOwnProfile && userCards.length === 0 && (
                  <div className="profile-bets-empty">
                    <div style={{ fontSize: 32, marginBottom: 8 }}>🃏</div>
                    Aucune carte dans la collection.
                  </div>
                )}
                {isOwnProfile && userCards.length > 0 && (
                  <div className="profile-tcg-grid">
                    {userCards.map(uc => (
                      <TcgCard key={uc.id} card={uc.card} size="sm" />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

      </div>

      {/* ─── TEAM PICKER MODAL ─── */}
      {showTeamPicker && (
        <div className="profile-picker-overlay" onClick={() => setShowTeamPicker(false)}>
          <div className="profile-picker-modal" onClick={e => e.stopPropagation()}>
            <div className="profile-picker-header">
              <div className="profile-picker-title">Choisis ton équipe favorite</div>
              <button className="profile-picker-close" onClick={() => setShowTeamPicker(false)}>✕</button>
            </div>
            <div className="profile-picker-section">
              <div className="profile-picker-teams">
                {esportsTeams.map(team => {
                  const selected = favTeam?.name === team.name
                  return (
                    <div
                      key={team.name}
                      className={`profile-picker-team ${selected ? 'selected' : ''}`}
                      style={{ '--tc': team.color || '#65BD62' }}
                      onClick={() => handlePickTeam(team)}
                    >
                      {team.logo && <img className="profile-picker-logo" src={team.logo} alt={team.name} referrerPolicy="no-referrer" />}
                      <div className="profile-picker-team-name">{team.name}</div>
                      {selected && <div className="profile-picker-check">✓</div>}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}