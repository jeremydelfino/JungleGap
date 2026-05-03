import './CoachDiffGame.css'
import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/auth'
import { getGame, userAction, botTurn, assignRoles } from '../../api/coachdiff'
import { fetchDDragonData, getAllPicked } from './utils'
import { BOT_DELAY_MIN_MS, BOT_DELAY_MAX_MS, TURN_DURATION_S } from './constants'

import DraftHeader   from './components/DraftHeader'
import BanRow        from './components/BanRow'
import PickColumn    from './components/PickColumn'
import ChampionGrid  from './components/ChampionGrid'
import RoleAssignPanel from './components/RoleAssignPanel'
import ScoreReveal     from './components/ScoreReveal'

export default function CoachDiffGame() {
  const { gameId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()

  const [game,        setGame]        = useState(null)
  const [ddragon,     setDdragon]     = useState(null)
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState(null)
  const [busy,        setBusy]        = useState(false)
  const [selected,    setSelected]    = useState(null)
  const [timer,       setTimer]       = useState(null)
  const botTimerRef   = useRef(null)
  const tickRef       = useRef(null)

  /* ─── Load DDragon ─── */
  useEffect(() => {
    fetchDDragonData()
      .then(setDdragon)
      .catch(e => console.error('DDragon fetch failed', e))
  }, [])

  /* ─── Load game ─── */
  const loadGame = useCallback(async () => {
    try {
      const g = await getGame(gameId)
      setGame(g)
      setLoading(false)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Partie introuvable')
      setLoading(false)
    }
  }, [gameId])

  useEffect(() => { loadGame() }, [loadGame])

  /* ─── Reset selected à chaque changement de tour ─── */
  useEffect(() => {
    setSelected(null)
  }, [game?.draft_state?.step])

  /* ─── Auto bot turn ─── */
  useEffect(() => {
    if (!game || game.status !== 'in_progress') return
    const turn = game.current_turn
    if (!turn || turn.actor !== 'BOT') return

    const delay = BOT_DELAY_MIN_MS + Math.random() * (BOT_DELAY_MAX_MS - BOT_DELAY_MIN_MS)
    botTimerRef.current = setTimeout(async () => {
      try {
        setBusy(true)
        const updated = await botTurn(game.id)
        setGame(updated)
      } catch (e) {
        console.error('Bot turn failed', e)
      } finally {
        setBusy(false)
      }
    }, delay)

    return () => clearTimeout(botTimerRef.current)
  }, [game])

  /* ─── User action ─── */
  const handleUserAction = useCallback(async (champion) => {
    if (busy || !game) return
    try {
      setBusy(true)
      const updated = await userAction(game.id, champion)
      setGame(updated)
    } catch (e) {
      console.error('User action failed', e)
      alert(e?.response?.data?.detail || 'Action impossible')
    } finally {
      setBusy(false)
    }
  }, [busy, game])

  /* ─── Assign roles ─── */
  const handleAssignRoles = useCallback(async (roleMap) => {
    if (busy || !game) return
    try {
      setBusy(true)
      const updated = await assignRoles(game.id, roleMap)
      setGame(updated)
    } catch (e) {
      console.error('Role assignment failed', e)
      alert(e?.response?.data?.detail || 'Assignation impossible')
    } finally {
      setBusy(false)
    }
  }, [busy, game])

  /* ─── Timer + auto-pick on timeout ─── */
  const isUserTurn = game?.status === 'in_progress' && game?.current_turn?.actor === 'USER'

  useEffect(() => {
    clearInterval(tickRef.current)

    if (!isUserTurn || !ddragon) {
      setTimer(null)
      return
    }

    setTimer(TURN_DURATION_S)
    tickRef.current = setInterval(() => {
      setTimer(prev => {
        if (prev === null) return null
        if (prev <= 1) {
          clearInterval(tickRef.current)
          // Auto-pick d'un champion random valide
          const picked = getAllPicked(game.draft_state)
          const candidates = ddragon.champions.filter(c => !picked.has(c.id))
          if (candidates.length > 0) {
            const random = candidates[Math.floor(Math.random() * candidates.length)]
            handleUserAction(random.id)
          }
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(tickRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isUserTurn, game?.draft_state?.step, ddragon])

  /* ─── Auth + load guards ─── */
  if (!user) return <div className="cdg-loading">Connecte-toi pour jouer</div>
  if (loading || !ddragon) return <div className="cdg-loading">Chargement…</div>
  if (error) return (
    <div className="cdg-error">
      <div>{error}</div>
      <button onClick={() => navigate('/games/coachdiff')}>Retour</button>
    </div>
  )
  if (!game) return null

  /* ─── Routing par phase ─── */
/* ─── Routing par phase ─── */
  const phase = game.draft_state?.phase
  const state = game.draft_state

  if (game.status === 'finished') {
    return <ScoreReveal game={game} version={ddragon.version} />
  }

  if (phase === 'ROLE_ASSIGN') {
    const userSideKey = state.user_side.toLowerCase()
    const userPicks   = state[userSideKey]?.picks || []
    return (
      <RoleAssignPanel
        picks={userPicks}
        version={ddragon.version}
        onSubmit={handleAssignRoles}
        busy={busy}
      />
    )
  }

  /* ─── Draft UI ─── */
  const turn = game.current_turn
  const pickedSet = getAllPicked(state)
  const actionLabel = turn?.action === 'ban' ? 'Ban' : 'Pick'

  return (
    <div className="cdg-page">

      {/* ─── HEADER ─── */}
      <DraftHeader
        phase={phase}
        step={state.step}
        currentTurn={turn}
        userSide={state.user_side}
        timer={isUserTurn ? timer : null}
        isUserTurn={isUserTurn}
      />

      {/* ─── BAN ROWS ─── */}
      <div className="cdg-bans">
        <BanRow
          side="BLUE"
          bans={state.blue.bans}
          version={ddragon.version}
          isCurrentSlot={turn?.action === 'ban' && turn?.side === 'BLUE'}
        />
        <BanRow
          side="RED"
          bans={state.red.bans}
          version={ddragon.version}
          isCurrentSlot={turn?.action === 'ban' && turn?.side === 'RED'}
        />
      </div>

      {/* ─── MAIN BOARD ─── */}
      <div className="cdg-board">

        <PickColumn
          side="BLUE"
          picks={state.blue.picks}
          version={ddragon.version}
          isCurrentSlot={turn?.action === 'pick' && turn?.side === 'BLUE'}
        />

        <ChampionGrid
          champions={ddragon.champions}
          version={ddragon.version}
          pickedSet={pickedSet}
          selected={selected}
          onSelect={setSelected}
          onLockIn={() => selected && handleUserAction(selected)}
          disabled={!isUserTurn || busy}
          actionLabel={actionLabel}
        />

        <PickColumn
          side="RED"
          picks={state.red.picks}
          version={ddragon.version}
          isCurrentSlot={turn?.action === 'pick' && turn?.side === 'RED'}
        />

      </div>
    </div>
  )
}