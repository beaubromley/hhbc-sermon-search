// Query-term highlighting and snippets. Matching is stem-aware to mirror the
// server's porter-stemmed full-text index ("forgive" also marks forgiving/forgiveness).

const escapeRe = (t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const escapeHtml = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

// Cheap suffix stripper, good enough to find the shared prefix of word forms.
export function stem(word) {
  let w = word.toLowerCase()
  if (w.length > 4) w = w.replace(/(ing|ed|es|s|ly)$/, '')
  if (w.length > 4 && w.endsWith('e')) w = w.slice(0, -1)
  return w
}

// Split a search query into { words, phrases } (quoted text is a phrase).
export function queryTerms(query) {
  const phrases = []
  const rest = (query || '').replace(/"([^"]+)"/g, (_, p) => {
    if (p.trim()) phrases.push(p.trim())
    return ' '
  })
  const words = rest
    .replace(/[":*(){}^~+\-\\]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 0)
  return { words, phrases }
}

export function buildMatcher(query) {
  const { words, phrases } = queryTerms(query)
  const parts = [
    ...phrases.map(p => escapeRe(p).replace(/\s+/g, '\\s+')),
    ...words.map(w => `\\b${escapeRe(stem(w))}\\w*`)
  ]
  if (parts.length === 0) return null
  parts.sort((a, b) => b.length - a.length)
  return new RegExp(`(${parts.join('|')})`, 'gi')
}

export function highlight(text, query) {
  const safe = escapeHtml(text)
  const re = buildMatcher(query)
  return re ? safe.replace(re, '<strong>$1</strong>') : safe
}

// Trim long text to a window around the first match.
export function snippet(text, query, max = 200) {
  if (text.length <= max) return text
  const re = buildMatcher(query)
  const m = re ? new RegExp(re.source, 'i').exec(text) : null
  if (!m || m.index + m[0].length <= max - 20) return text.substring(0, max) + '...'
  let start = Math.max(0, m.index - 60)
  const space = text.indexOf(' ', start)
  if (start > 0 && space !== -1 && space < m.index) start = space + 1
  return '...' + text.substring(start, start + max) + (start + max < text.length ? '...' : '')
}
