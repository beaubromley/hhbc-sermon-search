// "Did you mean...?" built from the `vocab` table (every word spoken 3+ times, with counts).
import { execute } from '../tursoClient'

function distance(a, b) {
  const prev = Array.from({ length: b.length + 1 }, (_, i) => i)
  for (let i = 1; i <= a.length; i++) {
    let diag = prev[0]
    prev[0] = i
    for (let j = 1; j <= b.length; j++) {
      const tmp = prev[j]
      prev[j] = Math.min(prev[j] + 1, prev[j - 1] + 1, diag + (a[i - 1] === b[j - 1] ? 0 : 1))
      diag = tmp
    }
  }
  return prev[b.length]
}

async function suggestWord(word) {
  const w = word.toLowerCase()
  if (w.length < 4 || !/^[a-z']+$/.test(w)) return null
  const known = await execute('SELECT cnt FROM vocab WHERE term = ?', [w])
  if (known.length > 0) return null

  const maxDist = w.length <= 5 ? 1 : 2
  const candidates = await execute(
    `SELECT term, cnt FROM vocab
     WHERE substr(term, 1, 1) = ? AND length(term) BETWEEN ? AND ?
     ORDER BY cnt DESC LIMIT 1500`,
    [w[0], w.length - maxDist, w.length + maxDist]
  )
  let best = null
  for (const c of candidates) {
    const d = distance(w, c.term)
    if (d > maxDist) continue
    if (!best || d < best.d || (d === best.d && c.cnt > best.cnt)) best = { term: c.term, d, cnt: c.cnt }
  }
  return best ? best.term : null
}

// Returns a corrected query string, or null if nothing looks misspelled.
export async function suggestQuery(query) {
  try {
    const parts = query.split(/(\s+|"[^"]*")/)
    let changed = false
    const out = []
    for (const part of parts) {
      if (!part || /^\s+$/.test(part) || part.startsWith('"')) {
        out.push(part)
        continue
      }
      const fix = await suggestWord(part)
      if (fix) changed = true
      out.push(fix || part)
    }
    return changed ? out.join('') : null
  } catch (err) {
    console.warn('Spell suggestion failed:', err)
    return null
  }
}
