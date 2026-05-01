/* ───────────── CONSTANTES PARTAGÉES ───────────── */

/* ─── Tiers ─── */
export const TIER_COLORS = {
  CHALLENGER: '#f4c430', GRANDMASTER: '#ef4444', MASTER: '#a78bfa',
  DIAMOND: '#378add', EMERALD: '#65BD62', PLATINUM: '#00b4d8',
  GOLD: '#e2b147', SILVER: '#9ca3af', BRONZE: '#cd7f32', IRON: '#6b7280',
}

/* Tiers sans rank (image unique) */
export const APEX_TIERS = new Set(['CHALLENGER', 'GRANDMASTER', 'MASTER'])

/* ─── Queues ─── */
export const QUEUE_NAMES = {
  420: 'Ranked Solo',
  440: 'Ranked Flex',
  400: 'Normal Draft',
  430: 'Normal Blind',
  450: 'ARAM',
  700: 'Clash',
  900: 'URF',
  1700: 'Arena',
}

/* ─── Rôles ─── */
export const ROLE_LABELS = {
  TOP: 'Top', JUNGLE: 'Jungle', MID: 'Mid', MIDDLE: 'Mid',
  ADC: 'Bot', BOTTOM: 'Bot', SUPPORT: 'Support', UTILITY: 'Support', FILL: 'Fill',
}

export const ROLE_ICONS = {
  TOP: '⬆', JUNGLE: '🌲', MID: '✦', MIDDLE: '✦',
  ADC: '🏹', BOTTOM: '🏹', SUPPORT: '✚', UTILITY: '✚', FILL: '?',
}

/* ─── Régions Riot officielles ─── */
export const REGION_LABELS = {
  EUW: 'EUW', EUNE: 'EUNE', NA: 'NA', KR: 'KR',
  BR: 'BR', JP: 'JP', LAN: 'LAN', LAS: 'LAS', OCE: 'OCE', TR: 'TR', RU: 'RU',
}

/* ─── DDragon ─── */
export const CHAMP_VERSION = '16.9.1'