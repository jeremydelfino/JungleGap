import './Games.css'
import { useNavigate } from 'react-router-dom'

const GAMES = [
  {
    id: 'coachdiff',
    path: '/games/coachdiff',
    title: 'CoachDiff',
    tagline: 'Drafte mieux que le bot',
    desc: 'Affronte un bot dans une draft style tournoi. Le meilleur draft gagne. On va pouvoir enfin voir si tes avis désastreux marcheraient vraiment.',
    icon: '🧠',
    tags: ['1v1 vs Bot', 'Draft', '5 → 10 🪙'],
    available: true,
  },
  {
    id: 'soon-1',
    path: null,
    title: 'À venir',
    tagline: 'Bientôt disponible',
    desc: 'D\'autres modes de jeu arrivent prochainement.',
    icon: '🔒',
    tags: ['Coming soon'],
    available: false,
  },
]

export default function Games() {
  const navigate = useNavigate()

  return (
    <div className="games-page">

      {/* ─── HERO ─── */}
      <section className="games-hero">
        <div className="games-hero-eyebrow">JUNGLEGAP GAMES</div>
        <h1 className="games-hero-title">Choisis ton mode de jeu</h1>
        <p className="games-hero-sub">Mini-jeux League of Legends. Mise tes coins et défie le bot ou des joueurs 😉 (soon)</p>
      </section>

      {/* ─── GRID ─── */}
      <section className="games-grid">
        {GAMES.map(g => (
          <button
            key={g.id}
            className={`game-card ${!g.available ? 'disabled' : ''}`}
            onClick={() => g.available && navigate(g.path)}
            disabled={!g.available}
          >
            <div className="game-card-icon">{g.icon}</div>
            <div className="game-card-body">
              <div className="game-card-eyebrow">{g.tagline}</div>
              <div className="game-card-title">{g.title}</div>
              <div className="game-card-desc">{g.desc}</div>
              <div className="game-card-tags">
                {g.tags.map(t => <span key={t} className="game-tag">{t}</span>)}
              </div>
            </div>
            {g.available && <div className="game-card-arrow">→</div>}
          </button>
        ))}
      </section>

    </div>
  )
}