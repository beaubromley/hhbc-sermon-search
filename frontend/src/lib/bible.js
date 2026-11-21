// Bible book names + a parser for passage searches like "Romans 8:28" or "1 Cor 13".

export const BOOKS = [
  'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth',
  '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra',
  'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs', 'Ecclesiastes', 'Song of Solomon',
  'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos',
  'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah',
  'Malachi', 'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians',
  '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians',
  '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James',
  '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation'
]

const SHORT = {
  Genesis: 'gen ge gn', Exodus: 'exod ex exo', Leviticus: 'lev lv', Numbers: 'num nu nm',
  Deuteronomy: 'deut dt de', Joshua: 'josh jos', Judges: 'judg jdg jg', Ruth: 'ru',
  '1 Samuel': '1sam 1sa 1sm', '2 Samuel': '2sam 2sa 2sm', '1 Kings': '1kgs 1ki 1kg',
  '2 Kings': '2kgs 2ki 2kg', '1 Chronicles': '1chr 1ch', '2 Chronicles': '2chr 2ch',
  Nehemiah: 'neh', Esther: 'esth est', Psalms: 'psalm ps psa pss', Proverbs: 'prov pro pr',
  Ecclesiastes: 'eccl ecc eccles', 'Song of Solomon': 'song songs sos songofsongs',
  Isaiah: 'isa', Jeremiah: 'jer', Lamentations: 'lam', Ezekiel: 'ezek eze', Daniel: 'dan',
  Hosea: 'hos', Obadiah: 'obad', Jonah: 'jon', Micah: 'mic', Nahum: 'nah', Habakkuk: 'hab',
  Zephaniah: 'zeph', Haggai: 'hag', Zechariah: 'zech', Malachi: 'mal', Matthew: 'matt mt',
  Mark: 'mk mrk', Luke: 'lk', John: 'jn', Romans: 'rom ro', '1 Corinthians': '1cor 1co',
  '2 Corinthians': '2cor 2co', Galatians: 'gal', Ephesians: 'eph', Philippians: 'phil php',
  Colossians: 'col', '1 Thessalonians': '1thess 1th', '2 Thessalonians': '2thess 2th',
  '1 Timothy': '1tim 1ti', '2 Timothy': '2tim 2ti', Philemon: 'phlm phm', Hebrews: 'heb',
  James: 'jas jm', '1 Peter': '1pet 1pe', '2 Peter': '2pet 2pe', '1 John': '1jn 1jo',
  '2 John': '2jn', '3 John': '3jn', Revelation: 'rev revelations'
}

const LOOKUP = {}
for (const book of BOOKS) {
  LOOKUP[book.toLowerCase().replace(/\s+/g, '')] = book
  for (const alias of (SHORT[book] || '').split(' ')) {
    if (alias) LOOKUP[alias] = book
  }
}

const ORDINALS = { first: '1', second: '2', third: '3', i: '1', ii: '2', iii: '3' }

// "Romans 8:28" -> { book, chapter, verseStart, verseEnd, label }, or null.
// A chapter is required so plain names (John, Mark) still search normally.
export function parsePassage(query) {
  const m = /^\s*(?:(1|2|3|i{1,3}|first|second|third)\s*)?([a-z]+(?:\s+of\s+[a-z]+)?)\.?\s*(?:chapter\s+|ch\.?\s*)?(\d{1,3})(?:\s*[:.]\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?)?\s*$/i.exec(query || '')
  if (!m) return null
  const num = m[1] ? (ORDINALS[m[1].toLowerCase()] || m[1]) : ''
  const key = (num + m[2]).toLowerCase().replace(/\s+/g, '')
  const book = LOOKUP[key]
  if (!book) return null
  const chapter = parseInt(m[3], 10)
  const verseStart = m[4] ? parseInt(m[4], 10) : null
  const verseEnd = m[5] ? parseInt(m[5], 10) : null
  const label = `${book} ${chapter}${verseStart ? ':' + verseStart + (verseEnd ? '-' + verseEnd : '') : ''}`
  return { book, chapter, verseStart, verseEnd, label }
}
