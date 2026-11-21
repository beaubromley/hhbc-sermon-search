// Links into this site. Hash routing means every URL works on static hosting, even on refresh.
const base = import.meta.env.BASE_URL

export function sermonRoute(id, seconds, query) {
  const q = {}
  if (seconds) q.t = String(Math.floor(seconds))
  if (query) q.q = query
  return { name: 'sermon', params: { id: String(id) }, query: q }
}

// Absolute, shareable link to a sermon (optionally at a moment in it).
export function sermonUrl(id, seconds) {
  const t = seconds ? `?t=${Math.floor(seconds)}` : ''
  return `${window.location.origin}${base}#/sermon/${id}${t}`
}

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.left = '-9999px'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }
}
