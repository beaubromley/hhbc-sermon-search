// Guess a series name from a sermon title ("Philippians - Part 3" -> "Philippians").
const PATTERNS = [
  /\s*[-–—]\s*(?:Part|Pt\.?|Week|Session|Lesson)\s+\d+.*/i,
  /\s*(?:Part|Pt\.?|Week|Session|Lesson)\s+\d+.*/i,
  /\s*[-–—]\s*#\s*\d+.*/i,
  /\s*#\s*\d+.*/i,
  /\s*\(\s*(?:Part|Pt\.?)?\s*\d+\s*\).*/i,
  /\s*[-–—]\s*\d+\s*[-–—:].*/,
  /\s+\d+\s*$/
]

export function detectSeriesPrefix(title) {
  const original = title.trim()
  for (const pattern of PATTERNS) {
    const prefix = original.replace(pattern, '').trim()
    if (prefix !== original && prefix.length > 2) return prefix
  }
  return null
}
