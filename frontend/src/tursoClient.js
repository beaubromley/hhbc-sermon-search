// Turso database client for HHBC Sermon Search
// Uses the Turso HTTP API with a read-only token (safe for frontend)

const TURSO_URL = process.env.VUE_APP_TURSO_URL
const TURSO_TOKEN = process.env.VUE_APP_TURSO_TOKEN

function unwrapValue(cell) {
  if (!cell || cell.type === 'null') return null
  if (cell.type === 'integer') return parseInt(cell.value)
  if (cell.type === 'float') return parseFloat(cell.value)
  return cell.value
}

function wrapArg(arg) {
  if (arg === null || arg === undefined) return { type: 'null', value: null }
  if (typeof arg === 'number' && Number.isInteger(arg)) return { type: 'integer', value: String(arg) }
  if (typeof arg === 'number') return { type: 'float', value: arg }
  return { type: 'text', value: String(arg) }
}

// Fire a warmup query immediately on import to establish the connection,
// wake up the Turso instance, and prime the SQLite page cache.
const warmupStart = performance.now()
console.log('[Turso] Warmup query sent...')
fetch(`${TURSO_URL}/v2/pipeline`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${TURSO_TOKEN}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    requests: [
      { type: 'execute', stmt: { sql: 'SELECT 1' } },
      { type: 'close' }
    ]
  })
}).then(() => {
  console.log(`[Turso] Warmup complete in ${(performance.now() - warmupStart).toFixed(0)}ms`)
}).catch((err) => {
  console.warn(`[Turso] Warmup failed: ${err.message}`)
})

// Short label for logging (first 60 chars of SQL)
function sqlLabel(sql) {
  return sql.replace(/\s+/g, ' ').trim().substring(0, 60)
}

export async function execute(sql, args = []) {
  const start = performance.now()
  const label = sqlLabel(sql)
  console.log(`[Turso] Query: ${label}...`)

  const response = await fetch(`${TURSO_URL}/v2/pipeline`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TURSO_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      requests: [
        { type: 'execute', stmt: { sql, args: args.map(wrapArg) } },
        { type: 'close' }
      ]
    })
  })

  if (!response.ok) {
    console.error(`[Turso] Query FAILED (${response.status}) in ${(performance.now() - start).toFixed(0)}ms`)
    throw new Error(`Database query failed: ${response.status}`)
  }

  const data = await response.json()
  const result = data.results[0]

  if (result.type === 'error') {
    console.error(`[Turso] SQL error: ${result.error.message}`)
    throw new Error(result.error.message)
  }

  const rows = result.response.result.rows
  const elapsed = (performance.now() - start).toFixed(0)
  console.log(`[Turso] ${rows.length} rows in ${elapsed}ms — ${label}`)

  const cols = result.response.result.cols.map(c => c.name)
  return rows.map(row => {
    const obj = {}
    row.forEach((cell, i) => {
      obj[cols[i]] = unwrapValue(cell)
    })
    return obj
  })
}
