import api from '../../api/client'

/* ─── Fetch DDragon (version + liste champions) ─── */
export async function fetchDDragonData() {
  const versions = await fetch('https://ddragon.leagueoflegends.com/api/versions.json').then(r => r.json())
  const version  = versions[0]
  const json     = await fetch(`https://ddragon.leagueoflegends.com/cdn/${version}/data/en_US/champion.json`).then(r => r.json())
  // d.data = { Aatrox: {id, key, name, ...}, ... }
  const champions = Object.values(json.data).map(c => ({
    id:    c.id,        // "Aatrox" — matche le name côté backend
    key:   c.key,       // numeric ID
    name:  c.name,      // "Aatrox" — display name
    title: c.title,
    tags:  c.tags,      // ["Fighter", "Tank"]
  }))
  champions.sort((a, b) => a.name.localeCompare(b.name))
  return { version, champions }
}

/* ─── Icône champion (proxy backend, cohérent projet) ─── */
export function getChampIcon(championId, version) {
  if (!championId || !version) return null
  const ddUrl = `https://ddragon.leagueoflegends.com/cdn/${version}/img/champion/${championId}.png`
  return `${api.defaults.baseURL}/players/proxy/icon?url=${encodeURIComponent(ddUrl)}`
}

/* ─── Splash art (pour reveal de fin) ─── */
export function getChampSplash(championId) {
  if (!championId) return null
  return `https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${championId}_0.jpg`
}

/* ─── Helpers state ─── */
export function getSideKey(side) {
  return side === 'BLUE' ? 'blue' : 'red'
}

export function getAllPicked(state) {
  if (!state) return new Set()
  const all = new Set()
  for (const s of ['blue', 'red']) {
    for (const c of state[s]?.bans  ?? []) all.add(c)
    for (const c of state[s]?.picks ?? []) all.add(c)
  }
  return all
}