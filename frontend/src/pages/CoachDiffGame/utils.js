import api from '../../api/client'

/* ─── Normalise un nom de champion vers son ID DDragon ─── */
/* "Xin Zhao" → "XinZhao", "Cho'Gath" → "ChoGath", "Dr. Mundo" → "DrMundo" */
function toChampId(name) {
  if (!name) return null
  return name.replace(/[\s'.\-]/g, '')
}

/* ─── Fetch DDragon (version + liste champions) ─── */
export async function fetchDDragonData() {
  const versions = await fetch('https://ddragon.leagueoflegends.com/api/versions.json').then(r => r.json())
  const version  = versions[0]
  const json     = await fetch(`https://ddragon.leagueoflegends.com/cdn/${version}/data/en_US/champion.json`).then(r => r.json())
  const champions = Object.values(json.data).map(c => ({
    id:    c.id,
    key:   c.key,
    name:  c.name,
    title: c.title,
    tags:  c.tags,
  }))
  champions.sort((a, b) => a.name.localeCompare(b.name))
  return { version, champions }
}

/* ─── Icône champion (square, pour grid/bans) ─── */
export function getChampIcon(championId, version) {
  const id = toChampId(championId)
  if (!id || !version) return null
  const ddUrl = `https://ddragon.leagueoflegends.com/cdn/${version}/img/champion/${id}.png`
  return `${api.defaults.baseURL}/players/proxy/icon?url=${encodeURIComponent(ddUrl)}`
}

/* ─── Loading splash (vertical, pour picks LoL-style) ─── */
export function getChampLoading(championId) {
  const id = toChampId(championId)
  if (!id) return null
  const ddUrl = `https://ddragon.leagueoflegends.com/cdn/img/champion/loading/${id}_0.jpg`
  return `${api.defaults.baseURL}/players/proxy/icon?url=${encodeURIComponent(ddUrl)}`
}

/* ─── Splash art (large, pour reveal de fin) ─── */
export function getChampSplash(championId) {
  const id = toChampId(championId)
  if (!id) return null
  return `https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${id}_0.jpg`
}

/* ─── Helpers state ─── */
export function getSideKey(side) { return side === 'BLUE' ? 'blue' : 'red' }

export function getAllPicked(state) {
  if (!state) return new Set()
  const all = new Set()
  for (const s of ['blue', 'red']) {
    for (const c of state[s]?.bans  ?? []) all.add(c)
    for (const c of state[s]?.picks ?? []) all.add(c)
  }
  return all
}