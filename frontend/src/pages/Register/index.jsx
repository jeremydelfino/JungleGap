import { useState, useRef, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import './Register.css'
import api from '../../api/client'
import useAuthStore from '../../store/auth'

const REGIONS = [
  { id: 'EUW',  flag: '🇪🇺' },
  { id: 'EUNE', flag: '🌍'  },
  { id: 'NA',   flag: '🇺🇸' },
  { id: 'KR',   flag: '🇰🇷' },
  { id: 'BR',   flag: '🇧🇷' },
  { id: 'JP',   flag: '🇯🇵' },
  { id: 'TR',   flag: '🇹🇷' },
  { id: 'OCE',  flag: '🇦🇺' },
]

const STEPS = ['Compte', 'Riot ID', 'Vérifier', 'Email']

function Stepper({ current }) {
  return (
    <div className="reg-stepper">
      {STEPS.map((label, i) => (
        <div className="reg-si" key={i}>
          <div className={`reg-dot ${i < current ? 'done' : ''} ${i === current ? 'active' : ''}`}>
            {i < current ? '✓' : i + 1}
          </div>
          <span className={`reg-label ${i === current ? 'active' : ''}`}>{label}</span>
          {i < STEPS.length - 1 && <div className={`reg-line ${i < current ? 'done' : ''}`} />}
        </div>
      ))}
    </div>
  )
}

function getStrength(p) {
  if (!p) return null
  if (p.length < 6) return { label: 'Faible', c: 'w', pct: 30 }
  if (p.length < 10 || !/[A-Z]/.test(p) || !/[0-9]/.test(p)) return { label: 'Moyen', c: 'm', pct: 62 }
  return { label: 'Fort', c: 's', pct: 100 }
}

// ─── Step 4 : saisie du code email ──────────────────────────
function EmailCodeStep({ email, onSuccess }) {
  const [digits, setDigits]     = useState(['', '', '', '', '', ''])
  const [error, setError]       = useState('')
  const [verifying, setVerify]  = useState(false)
  const [resending, setResend]  = useState(false)
  const [resent, setResent]     = useState(false)
  const [countdown, setCountdown] = useState(0)
  const refs = useRef([])

  // Countdown renvoi
  useEffect(() => {
    if (countdown <= 0) return
    const t = setTimeout(() => setCountdown(c => c - 1), 1000)
    return () => clearTimeout(t)
  }, [countdown])

  const handleDigit = (i, val) => {
    if (!/^\d?$/.test(val)) return
    const next = [...digits]
    next[i] = val
    setDigits(next)
    setError('')
    if (val && i < 5) refs.current[i + 1]?.focus()
  }

  const handleKeyDown = (i, e) => {
    if (e.key === 'Backspace' && !digits[i] && i > 0) {
      refs.current[i - 1]?.focus()
    }
  }

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (pasted.length === 6) {
      setDigits(pasted.split(''))
      refs.current[5]?.focus()
    }
  }

  const verify = async () => {
    const code = digits.join('')
    if (code.length < 6) return setError('Entre les 6 chiffres du code')
    setVerify(true); setError('')
    try {
      const { data } = await api.post('/auth/register/verify-email', { email, code })
      onSuccess(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Code incorrect')
      setDigits(['', '', '', '', '', ''])
      refs.current[0]?.focus()
    } finally { setVerify(false) }
  }

  const resend = async () => {
    if (countdown > 0) return
    setResend(true); setError('')
    try {
      await api.post('/auth/register/resend-code', { email })
      setResent(true)
      setCountdown(60)
      setTimeout(() => setResent(false), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors du renvoi')
    } finally { setResend(false) }
  }

  return (
    <>
      <h1 className="auth-title">Vérifie ton email</h1>
      <p className="auth-sub">
        On a envoyé un code à <strong style={{ color: '#e8eaf0' }}>{email}</strong>
      </p>

      {/* Input 6 chiffres */}
      <div className="email-code-wrap" onPaste={handlePaste}>
        {digits.map((d, i) => (
          <input
            key={i}
            ref={el => refs.current[i] = el}
            className={`email-code-input ${error ? 'err' : ''}`}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={d}
            onChange={e => handleDigit(i, e.target.value)}
            onKeyDown={e => handleKeyDown(i, e)}
            autoFocus={i === 0}
          />
        ))}
      </div>

      {error && <p className="auth-error" style={{ marginTop: 12 }}>{error}</p>}
      {resent && <p style={{ color: '#65BD62', fontSize: 13, textAlign: 'center', marginTop: 8, fontFamily: 'Inter, sans-serif' }}>✓ Code renvoyé !</p>}

      <button
        className="auth-btn btn-green"
        onClick={verify}
        disabled={verifying || digits.join('').length < 6}
        style={{ marginTop: 20 }}
      >
        {verifying
          ? <><span className="auth-spinner" /><span>Vérification…</span></>
          : <><span>Confirmer</span><span className="btn-shimmer" /></>
        }
      </button>

      <p className="auth-footer" style={{ marginTop: 16 }}>
        Tu n'as pas reçu le code ?{' '}
        <button
          onClick={resend}
          disabled={resending || countdown > 0}
          style={{ background: 'none', border: 'none', padding: 0, cursor: countdown > 0 ? 'default' : 'pointer', fontFamily: 'inherit' }}
          className="auth-link"
        >
          {countdown > 0 ? `Renvoyer (${countdown}s)` : 'Renvoyer'}
        </button>
      </p>
    </>
  )
}

// ─── Composant principal ─────────────────────────────────────
export default function Register() {
  const navigate = useNavigate()
  const { login } = useAuthStore()

  const [step, setStep]       = useState(0)
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  const [acc, setAcc] = useState({ username: '', email: '', password: '', confirm: '' })
  const setA = k => e => { setAcc(a => ({ ...a, [k]: e.target.value })); setError('') }
  const str = getStrength(acc.password)

  const [region, setRegion] = useState('')
  const [riotId, setRiotId] = useState('')
  const [riotData, setRiotData] = useState(null)
  const [verifying, setVerifying] = useState(false)

  // Email enregistré après register/complete ou register
  const [pendingEmail, setPendingEmail] = useState('')

  const go0 = e => {
    e.preventDefault(); setError('')
    if (acc.password !== acc.confirm) return setError('Les mots de passe ne correspondent pas')
    if (acc.password.length < 8) return setError('Minimum 8 caractères')
    setStep(1)
  }

  const skipRiot = async () => {
    setError(''); setLoading(true)
    try {
      const { data } = await api.post('/auth/register', {
        username: acc.username,
        email:    acc.email,
        password: acc.password,
      })
      console.log('skipRiot response:', data)  // ← ajoute ça
      setPendingEmail(data.email)
      setStep(3)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la création du compte')
    } finally { setLoading(false) }
  }

  const go1 = async e => {
    e.preventDefault(); setError('')
    if (!region) return setError('Sélectionne ta région')
    const parts = riotId.trim().split('#')
    if (parts.length !== 2 || !parts[0] || !parts[1]) return setError('Format : GameName#TAG')
    setLoading(true)
    try {
      const { data } = await api.post('/auth/register/init-riot', {
        email: acc.email, game_name: parts[0].trim(),
        tag_line: parts[1].trim(), region,
      })
      setRiotData(data); setStep(2)
    } catch (err) {
      setError(err.response?.data?.detail || 'Riot ID introuvable')
    } finally { setLoading(false) }
  }

  const verify = async () => {
    setError(''); setVerifying(true)
    try {
      const { data } = await api.post('/auth/register/complete', {
        username: acc.username, email: acc.email, password: acc.password,
        game_name: riotData.game_name, tag_line: riotData.tag_line,
        region, expected_icon_id: riotData.icon_id,
      })
      setPendingEmail(data.email)
      setStep(3)
    } catch (err) {
      setError(err.response?.data?.detail || 'Mauvaise icône, réessaie')
    } finally { setVerifying(false) }
  }

  const handleEmailVerified = (data) => {
    login({ username: data.username, coins: data.coins }, data.token)
    navigate('/')
  }

  return (
    <div className="auth-page">
      {/* ─── GLOWS ─── */}
      <div className="auth-glow auth-glow-1" />
      <div className="auth-glow auth-glow-2" />
      <div className="auth-glow auth-glow-3" />

      {/* ─── IMAGES FLOTTANTES ─── */}
      <img src="/logo.png"       className="auth-float auth-float-1" alt="" />
      <img src="/teemo1_png.png" className="auth-float auth-float-2" alt="" />
      <img src="/teemo2.png"     className="auth-float auth-float-3" alt="" />
      <img src="/jungle1.webp"   className="auth-float auth-float-4" alt="" />

      {/* ─── CARD ─── */}
      <div className="auth-card" style={{ maxWidth: step === 2 ? 420 : 400 }}>
        <div className="auth-logo" onClick={() => navigate('/')}>junglegap</div>
        <Stepper current={step} />

        {/* ── STEP 0 : Compte ── */}
        {step === 0 && <>
          <h1 className="auth-title">Créer un compte</h1>
          <p className="auth-sub">4 étapes, c'est rapide.</p>

          <div className="auth-bonus">
            <div className="bonus-dot" />
            <span>500 coins offerts à l'inscription</span>
          </div>

          <form onSubmit={go0}>
            <div className="auth-fields">
              <div className="auth-field">
                <label className="auth-label">Pseudo</label>
                <input className="auth-input" type="text" placeholder="TonPseudo"
                  value={acc.username} onChange={setA('username')}
                  required minLength={3} maxLength={20} autoComplete="username" />
              </div>
              <div className="auth-field">
                <label className="auth-label">Email</label>
                <input className="auth-input" type="email" placeholder="you@example.com"
                  value={acc.email} onChange={setA('email')} required autoComplete="email" />
              </div>
              <div className="auth-field">
                <label className="auth-label">Mot de passe</label>
                <input className="auth-input" type="password" placeholder="••••••••"
                  value={acc.password} onChange={setA('password')} required autoComplete="new-password" />
                {str && (
                  <div className="strength-row">
                    <div className="strength-track">
                      <div className={`strength-fill sf-${str.c}`} style={{ width: `${str.pct}%` }} />
                    </div>
                    <span className={`strength-label sl-${str.c}`}>{str.label}</span>
                  </div>
                )}
              </div>
              <div className="auth-field">
                <label className="auth-label">Confirmation</label>
                <input
                  className={`auth-input ${acc.confirm && acc.confirm !== acc.password ? 'err' : ''}`}
                  type="password" placeholder="••••••••"
                  value={acc.confirm} onChange={setA('confirm')} required autoComplete="new-password" />
              </div>
            </div>

            {error && <p className="auth-error" style={{ marginTop: 12 }}>{error}</p>}

            <button className="auth-btn btn-green" type="submit" style={{ marginTop: 20 }}>
              Continuer <span className="btn-shimmer" />
            </button>
          </form>

          <p className="auth-footer">
            Déjà un compte ? <Link to="/login" className="auth-link">Se connecter</Link>
          </p>
        </>}

        {/* ── STEP 1 : Riot ID ── */}
        {step === 1 && <>
          <h1 className="auth-title">Riot ID</h1>
          <p className="auth-sub">Liaison obligatoire pour parier sur les parties live.</p>

          <form onSubmit={go1}>
            <div className="auth-fields">
              <div className="auth-field">
                <label className="auth-label">Région</label>
                <div className="reg-regions">
                  {REGIONS.map(r => (
                    <button key={r.id} type="button"
                      className={`reg-region ${region === r.id ? 'r-on' : ''}`}
                      onClick={() => { setRegion(r.id); setError('') }}>
                      <span className="reg-flag">{r.flag}</span>
                      <span className="reg-id">{r.id}</span>
                    </button>
                  ))}
                </div>
              </div>
              <div className="auth-field">
                <label className="auth-label">Riot ID</label>
                <input className="auth-input" type="text" placeholder="GameName#TAG"
                  value={riotId} onChange={e => { setRiotId(e.target.value); setError('') }} required />
              </div>
            </div>

            {error && <p className="auth-error" style={{ marginTop: 12 }}>{error}</p>}

            <div className="reg-nav" style={{ marginTop: 20 }}>
              <button type="button" className="btn-ghost" onClick={() => { setStep(0); setError('') }}>
                Retour
              </button>
              <button className="auth-btn btn-green" type="submit" disabled={loading}>
                {loading
                  ? <><span className="auth-spinner" /><span>Vérification…</span></>
                  : <><span>Continuer</span><span className="btn-shimmer" /></>
                }
              </button>
            </div>
          </form>

          <p className="auth-footer" style={{ marginTop: 16 }}>
            Pas accès à LoL pour l'instant ?{' '}
            <button
              onClick={skipRiot}
              disabled={loading}
              style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontFamily: 'inherit' }}
              className="auth-link"
            >
              Passer cette étape
            </button>
          </p>
        </>}

        {/* ── STEP 2 : Vérification icône Riot ── */}
        {step === 2 && riotData && <>
          <h1 className="auth-title">Vérification</h1>
          <p className="auth-sub">Équipe cette icône dans LoL puis reviens ici.</p>

          <div className="verify-block">
            <div className="verify-summoner">
              <div className="verify-icon-wrap">
                <img src={riotData.icon_url} alt={`icône ${riotData.icon_id}`} />
              </div>
              <div className="verify-info">
                <div className="verify-name">{riotData.game_name}</div>
                <div className="verify-tag">#{riotData.tag_line}</div>
              </div>
            </div>

            <div className="verify-divider" />

            <div className="verify-target">
              <span className="verify-target-label">Équipe cette icône dans LoL</span>
              <img
                className="verify-target-icon"
                src={riotData.icon_url}
                alt={`icône ${riotData.icon_id}`}
              />
              <p className="verify-target-hint">
                Profil → Icône → sélectionne l'icône <strong>#{riotData.icon_id}</strong><br />
                Sauvegarde puis clique sur Vérifier
              </p>
            </div>
          </div>

          {error && <p className="auth-error" style={{ marginTop: 12 }}>{error}</p>}

          <div className="reg-nav" style={{ marginTop: 16 }}>
            <button type="button" className="btn-ghost" onClick={() => { setStep(1); setError('') }}>
              Retour
            </button>
            <button className="auth-btn btn-green" onClick={verify} disabled={verifying} style={{ flex: 2 }}>
              {verifying
                ? <><span className="auth-spinner" /><span>Vérification…</span></>
                : <><span>Vérifier et créer mon compte</span><span className="btn-shimmer" /></>
              }
            </button>
          </div>
        </>}

        {/* ── STEP 3 : Email ── */}
        {step === 3 && (
          <EmailCodeStep
            email={pendingEmail || acc.email}
            onSuccess={handleEmailVerified}
          />
        )}
      </div>
    </div>
  )
}