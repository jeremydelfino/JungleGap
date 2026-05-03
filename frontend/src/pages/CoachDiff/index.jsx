import './CoachDiff.css'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/auth'
import { startGame, getHistory } from '../../api/coachdiff'

const ENTRY_COST = 5
const WIN_PAYOUT = 10

const RULES = [
  { icon: '⚔️', title: 'Format tournoi', desc: '6 bans, 6 picks, puis 4 bans, 4 picks. Comme la LCK / LEC.' },
  { icon: '🤖', title: '1v1 contre un bot', desc: 'Le bot drafte aléatoirement pondéré par la tier list pro.' },
  { icon: '🎯', title: 'Assigne les rôles', desc: 'À la fin, place tes champions sur top / jungle / mid / adc / supp.' },
  { icon: '💯', title: 'Score sur 100', desc: 'WR SoloQ, matchups, synergies, présence Pro. Le meilleur draft gagne.' },
]

export default function CoachDiff() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [resumeGame, setResumeGame] = useState(null)
  const [error, setError] = useState(null)

  /* ─── Détection partie en cours ─── */
  useEffect(() => {
    if (!user) { setLoading(false); return }
    getHistory()
      .then(games => {
        const inProgress = games?.find(g => g.status === 'in_progress')
        if (inProgress) setResumeGame(inProgress)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [user])

  /* ─── Lancer ─── */
  const handleStart = async () => {
    if (starting) return
    setStarting(true); setError(null)
    try {
      const game = await startGame()
      navigate(`/games/coachdiff/${game.id}`)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Impossible de lancer la partie')
      setStarting(false)
    }
  }

  const handleResume = () => navigate(`/games/coachdiff/${resumeGame.id}`)

  /* ─── Pas connecté ─── */
  if (!user) {
    return (
      <div className="cd-page">
        <div className="cd-locked">
          <div className="cd-locked-icon">🔒</div>
          <div className="cd-locked-title">Connecte-toi pour jouer</div>
          <button className="cd-btn-primary" onClick={() => navigate('/login')}>Se connecter</button>
        </div>
      </div>
    )
  }

  const canPay = (user.coins ?? 0) >= ENTRY_COST

  return (
    <div className="cd-page">

      {/* ─── HERO ─── */}
      <section className="cd-hero">
        <div className="cd-hero-eyebrow">JEU · COACHDIFF</div>
        <h1 className="cd-hero-title">Drafte mieux que le bot</h1>
        <p className="cd-hero-sub">Format tournoi LCK. Score sur 100. Le meilleur draft gagne.</p>
      </section>

      {/* ─── REPRENDRE ─── */}
      {!loading && resumeGame && (
        <section className="cd-resume">
          <div className="cd-resume-icon">⏸️</div>
          <div className="cd-resume-body">
            <div className="cd-resume-title">Tu as une partie en cours</div>
            <div className="cd-resume-desc">Reprends là où tu t'étais arrêté.</div>
          </div>
          <button className="cd-btn-primary" onClick={handleResume}>Reprendre →</button>
        </section>
      )}

      {/* ─── RULES ─── */}
      <section className="cd-section">
        <div className="cd-section-title">Comment ça marche</div>
        <div className="cd-rules">
          {RULES.map(r => (
            <div className="cd-rule" key={r.title}>
              <div className="cd-rule-icon">{r.icon}</div>
              <div className="cd-rule-title">{r.title}</div>
              <div className="cd-rule-desc">{r.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── BET / START ─── */}
      <section className="cd-bet-card">
        <div className="cd-bet-row">
          <div className="cd-bet-col">
            <div className="cd-bet-label">Mise</div>
            <div className="cd-bet-value cost">−{ENTRY_COST} 🪙</div>
          </div>
          <div className="cd-bet-arrow">→</div>
          <div className="cd-bet-col">
            <div className="cd-bet-label">Si victoire</div>
            <div className="cd-bet-value win">+{WIN_PAYOUT} 🪙</div>
          </div>
          <div className="cd-bet-col">
            <div className="cd-bet-label">Si égalité</div>
            <div className="cd-bet-value draw">remboursé</div>
          </div>
          <div className="cd-bet-col">
            <div className="cd-bet-label">Si défaite</div>
            <div className="cd-bet-value lose">0</div>
          </div>
        </div>

        <div className="cd-balance">
          Solde actuel : <span className="cd-balance-val">{user.coins?.toLocaleString() ?? '—'} 🪙</span>
        </div>

        {error && <div className="cd-error">{error}</div>}

        <button
          className={`cd-btn-launch ${!canPay ? 'disabled' : ''}`}
          onClick={handleStart}
          disabled={!canPay || starting || !!resumeGame}
        >
          {starting ? 'Lancement…'
            : resumeGame ? 'Termine d\'abord ta partie en cours'
            : !canPay ? `Il te manque ${ENTRY_COST - (user.coins ?? 0)} coins`
            : `Lancer une partie · −${ENTRY_COST} 🪙`}
        </button>
      </section>

    </div>
  )
}