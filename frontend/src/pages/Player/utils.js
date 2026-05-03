import api from '../../api/client'
import { CHAMP_VERSION, APEX_TIERS } from './constants'

/* ───────────── HELPERS PARTAGÉS ───────────── */

/* ─── Format ─── */
export function formatDuration(seconds) {
  const m = Math.floor((seconds || 0) / 60)
  const s = (seconds || 0) % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

/* ─── Runes (DataDragon officiel) ─── */
// Map keystone ID → path DataDragon
const RUNE_KEYSTONE_PATHS = {
  // ─── Precision (8000) ───
  8005: 'perk-images/Styles/Precision/PressTheAttack/PressTheAttack.png',
  8008: 'perk-images/Styles/Precision/LethalTempo/LethalTempoTemp.png',
  8021: 'perk-images/Styles/Precision/FleetFootwork/FleetFootwork.png',
  8010: 'perk-images/Styles/Precision/Conqueror/Conqueror.png',

  // ─── Domination (8100) ───
  8112: 'perk-images/Styles/Domination/Electrocute/Electrocute.png',
  8124: 'perk-images/Styles/Domination/Predator/Predator.png',
  8128: 'perk-images/Styles/Domination/DarkHarvest/DarkHarvest.png',
  9923: 'perk-images/Styles/Domination/HailOfBlades/HailOfBlades.png',

  // ─── Sorcery (8200) ───
  8214: 'perk-images/Styles/Sorcery/SummonAery/SummonAery.png',
  8229: 'perk-images/Styles/Sorcery/ArcaneComet/ArcaneComet.png',
  8230: 'perk-images/Styles/Sorcery/PhaseRush/PhaseRush.png',

  // ─── Resolve (8400) ───
  8437: 'perk-images/Styles/Resolve/GraspOfTheUndying/GraspOfTheUndying.png',
  8439: 'perk-images/Styles/Resolve/VeteranAftershock/VeteranAftershock.png',
  8465: 'perk-images/Styles/Resolve/Guardian/Guardian.png',

  // ─── Inspiration (8300) ───
  8351: 'perk-images/Styles/Inspiration/GlacialAugment/GlacialAugment.png',
  8360: 'perk-images/Styles/Inspiration/UnsealedSpellbook/UnsealedSpellbook.png',
  8369: 'perk-images/Styles/Inspiration/FirstStrike/FirstStrike.png',
}

/* ─── Runes mineures (slot 1, 2, 3) — utiles si tu veux les afficher dans le drawer ─── */
const RUNE_MINOR_PATHS = {
  // Precision - Slot 1
  9101: 'perk-images/Styles/Precision/Overheal.png',
  9111: 'perk-images/Styles/Precision/Triumph.png',
  8009: 'perk-images/Styles/Precision/PresenceOfMind/PresenceOfMind.png',
  // Precision - Slot 2
  9104: 'perk-images/Styles/Precision/LegendAlacrity/LegendAlacrity.png',
  9105: 'perk-images/Styles/Precision/LegendTenacity/LegendTenacity.png',
  9103: 'perk-images/Styles/Precision/LegendBloodline/LegendBloodline.png',
  // Precision - Slot 3
  8014: 'perk-images/Styles/Precision/CoupDeGrace/CoupDeGrace.png',
  8017: 'perk-images/Styles/Precision/CutDown/CutDown.png',
  8299: 'perk-images/Styles/Sorcery/LastStand/LastStand.png',

  // Domination - Slot 1
  8126: 'perk-images/Styles/Domination/CheapShot/CheapShot.png',
  8139: 'perk-images/Styles/Domination/TasteOfBlood/GreenTerror_TasteOfBlood.png',
  8143: 'perk-images/Styles/Domination/SuddenImpact/SuddenImpact.png',
  // Domination - Slot 2
  8136: 'perk-images/Styles/Domination/ZombieWard/ZombieWard.png',
  8120: 'perk-images/Styles/Domination/GhostPoro/GhostPoro.png',
  8138: 'perk-images/Styles/Domination/EyeballCollection/EyeballCollection.png',
  // Domination - Slot 3
  8135: 'perk-images/Styles/Domination/TreasureHunter/TreasureHunter.png',
  8134: 'perk-images/Styles/Domination/IngeniousHunter/IngeniousHunter.png',
  8105: 'perk-images/Styles/Domination/RelentlessHunter/RelentlessHunter.png',
  8106: 'perk-images/Styles/Domination/UltimateHunter/UltimateHunter.png',

  // Sorcery - Slot 1
  8224: 'perk-images/Styles/Sorcery/NullifyingOrb/Pokeshield.png',
  8226: 'perk-images/Styles/Sorcery/ManaflowBand/ManaflowBand.png',
  8275: 'perk-images/Styles/Sorcery/NimbusCloak/6361.png',
  // Sorcery - Slot 2
  8210: 'perk-images/Styles/Sorcery/Transcendence/Transcendence.png',
  8234: 'perk-images/Styles/Sorcery/Celerity/CelerityTemp.png',
  8233: 'perk-images/Styles/Sorcery/AbsoluteFocus/AbsoluteFocus.png',
  // Sorcery - Slot 3
  8237: 'perk-images/Styles/Sorcery/Scorch/Scorch.png',
  8232: 'perk-images/Styles/Sorcery/Waterwalking/Waterwalking.png',
  8236: 'perk-images/Styles/Sorcery/GatheringStorm/GatheringStorm.png',

  // Resolve - Slot 1
  8444: 'perk-images/Styles/Resolve/Demolish/Demolish.png',
  8463: 'perk-images/Styles/Resolve/FontOfLife/FontOfLife.png',
  8473: 'perk-images/Styles/Resolve/ShieldBash/ShieldBash.png',
  // Resolve - Slot 2
  8429: 'perk-images/Styles/Resolve/Conditioning/Conditioning.png',
  8444: 'perk-images/Styles/Resolve/SecondWind/SecondWind.png',
  8473: 'perk-images/Styles/Resolve/BonePlating/BonePlating.png',
  // Resolve - Slot 3
  8451: 'perk-images/Styles/Resolve/Overgrowth/Overgrowth.png',
  8453: 'perk-images/Styles/Resolve/Revitalize/Revitalize.png',
  8242: 'perk-images/Styles/Sorcery/Unflinching/Unflinching.png',

  // Inspiration - Slot 1
  8306: 'perk-images/Styles/Inspiration/HextechFlashtraption/HextechFlashtraption.png',
  8304: 'perk-images/Styles/Inspiration/MagicalFootwear/MagicalFootwear.png',
  8313: 'perk-images/Styles/Inspiration/PerfectTiming/AlchemistCabinet.png',
  // Inspiration - Slot 2
  8321: 'perk-images/Styles/Inspiration/FuturesMarket/FuturesMarket.png',
  8316: 'perk-images/Styles/Inspiration/MinionDematerializer/MinionDematerializer.png',
  8345: 'perk-images/Styles/Inspiration/BiscuitDelivery/BiscuitDelivery.png',
  // Inspiration - Slot 3
  8347: 'perk-images/Styles/Inspiration/CosmicInsight/CosmicInsight.png',
  8410: 'perk-images/Styles/Resolve/ApproachVelocity/ApproachVelocity.png',
  8352: 'perk-images/Styles/Inspiration/TimeWarpTonic/TimeWarpTonic.png',
}

// Map tree ID → path DataDragon
const RUNE_TREE_PATHS = {
  8000: 'perk-images/Styles/7201_Precision.png',
  8100: 'perk-images/Styles/7200_Domination.png',
  8200: 'perk-images/Styles/7202_Sorcery.png',
  8300: 'perk-images/Styles/7203_Whimsy.png',     // Inspiration
  8400: 'perk-images/Styles/7204_Resolve.png',
}

export function getRuneIcon(runeId, type = 'keystone') {
  if (!runeId) return null
  const path = type === 'tree' ? RUNE_TREE_PATHS[runeId] : RUNE_KEYSTONE_PATHS[runeId]
  if (!path) return null
  // Proxy via le backend (sinon CORS sur ddragon)
  const url = `https://ddragon.leagueoflegends.com/cdn/img/${path}`
  return `${api.defaults.baseURL}/players/proxy/icon?url=${encodeURIComponent(url)}`
}

export function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const m = Math.floor(diff / 60000)
  const h = Math.floor(diff / 3600000)
  const d = Math.floor(h / 24)
  if (d > 0) return `il y a ${d}j`
  if (h > 0) return `il y a ${h}h`
  if (m > 0) return `il y a ${m}m`
  return 'à l\'instant'
}

/* ─── Champions ─── */
export function getChampIcon(name) {
  if (!name || name === '???' || name === '??') return null
  const ddUrl = `https://ddragon.leagueoflegends.com/cdn/${CHAMP_VERSION}/img/champion/${name}.png`
  return `${api.defaults.baseURL}/players/proxy/icon?url=${encodeURIComponent(ddUrl)}`
}

export function resolveChampName(p, champMap = {}) {
  if (p.championName?.trim()) return p.championName.trim()
  if (p.championId && champMap[String(p.championId)]) return champMap[String(p.championId)]
  return null
}

/* ─── Tier image (Community Dragon, gratuit & fiable) ─── */
export function getTierImage(tier) {
  if (!tier) return null
  const t = tier.toLowerCase()
  return `https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-mini-crests/${t}.png`
}

export function getRankLabel(tier, rank, lp) {
  if (!tier) return 'Non classé'
  const tierCap = tier.charAt(0) + tier.slice(1).toLowerCase()
  if (APEX_TIERS.has(tier)) return `${tierCap} · ${lp ?? 0} LP`
  return `${tierCap} ${rank ?? ''} · ${lp ?? 0} LP`
}

/* ─── Match aggregation pour top champions ─── */
export function groupByChampion(matches, limit = 5) {
  const map = {}
  matches.forEach(m => {
    if (!map[m.champion]) {
      map[m.champion] = { games: 0, wins: 0, kills: 0, deaths: 0, assists: 0, cs: 0, duration: 0 }
    }
    const c = map[m.champion]
    c.games++
    if (m.win) c.wins++
    c.kills    += m.kills
    c.deaths   += m.deaths
    c.assists  += m.assists
    c.cs       += m.cs
    c.duration += m.duration
  })
  return Object.entries(map)
    .map(([name, s]) => ({
      name,
      games:    s.games,
      wins:     s.wins,
      losses:   s.games - s.wins,
      winrate:  Math.round((s.wins / s.games) * 100),
      kda:      s.deaths === 0 ? '∞' : ((s.kills + s.assists) / s.deaths).toFixed(2),
      cs_min:   ((s.cs / (s.duration / 60)) || 0).toFixed(1),
      avg_k:    (s.kills / s.games).toFixed(1),
      avg_d:    (s.deaths / s.games).toFixed(1),
      avg_a:    (s.assists / s.games).toFixed(1),
    }))
    .sort((a, b) => b.games - a.games)
    .slice(0, limit)
}

/* ─── Spells / Items / Runes (DDragon assets, proxiés) ─── */
export function getSpellIcon(spellId) {
  // Map des IDs Riot vers les fichiers DDragon
  const SPELL_MAP = {
    1: 'SummonerBoost',     3: 'SummonerExhaust',  4: 'SummonerFlash',
    6: 'SummonerHaste',     7: 'SummonerHeal',     11: 'SummonerSmite',
    12: 'SummonerTeleport', 13: 'SummonerMana',    14: 'SummonerDot',
    21: 'SummonerBarrier',  32: 'SummonerSnowball',
  }
  const name = SPELL_MAP[spellId]
  if (!name) return null
  const url = `https://ddragon.leagueoflegends.com/cdn/${CHAMP_VERSION}/img/spell/${name}.png`
  return `${api.defaults.baseURL}/players/proxy/icon?url=${encodeURIComponent(url)}`
}

export function getItemIcon(itemId) {
  if (!itemId || itemId === 0) return null
  const url = `https://ddragon.leagueoflegends.com/cdn/${CHAMP_VERSION}/img/item/${itemId}.png`
  return `${api.defaults.baseURL}/players/proxy/icon?url=${encodeURIComponent(url)}`
}
