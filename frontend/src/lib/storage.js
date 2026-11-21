// Per-browser conveniences (recent searches, saved sermons). Never required for the site to work.
function read(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function write(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* storage blocked or full: ignore */
  }
}

export function getRecents() {
  return read('hhbc-recents', [])
}

export function addRecent(query) {
  const q = query.trim()
  if (q.length < 3) return getRecents()
  const list = [q, ...getRecents().filter(r => r.toLowerCase() !== q.toLowerCase())].slice(0, 8)
  write('hhbc-recents', list)
  return list
}

export function clearRecents() {
  write('hhbc-recents', [])
  return []
}

export function getFavorites() {
  return read('hhbc-favorites', [])
}

export function isFavorite(id) {
  return getFavorites().includes(String(id))
}

// Returns the new saved state (true = now saved).
export function toggleFavorite(id) {
  const key = String(id)
  const list = getFavorites()
  const next = list.includes(key) ? list.filter(x => x !== key) : [key, ...list]
  write('hhbc-favorites', next)
  return next.includes(key)
}

export function getTheme() {
  const saved = read('hhbc-theme', null)
  if (saved) return saved
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function saveTheme(theme) {
  write('hhbc-theme', theme)
}
