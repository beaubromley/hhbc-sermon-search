// All ~1,900 sermons, fetched once and shared by the speaker, series, saved and sermon pages.
import { execute } from '../tursoClient'
import { detectSeriesPrefix } from './series'

let cache = null

export function loadVideos() {
  if (!cache) {
    cache = execute('SELECT video_id, title, duration, url, date_published FROM videos ORDER BY date_published DESC')
      .then(rows => rows.map(r => ({
        id: String(r.video_id),
        title: r.title,
        duration: r.duration,
        url: r.url,
        date: (r.date_published || '').substring(0, 10),
        series: detectSeriesPrefix(r.title || '')
      })))
      .catch(err => {
        cache = null
        throw err
      })
  }
  return cache
}

// series name -> sermons, oldest first. Only names with 2+ sermons count as a series.
export function groupSeries(videos) {
  const map = new Map()
  for (const v of videos) {
    if (!v.series) continue
    if (!map.has(v.series)) map.set(v.series, [])
    map.get(v.series).push(v)
  }
  for (const [name, list] of [...map]) {
    if (list.length < 2) map.delete(name)
    else list.sort((a, b) => a.date.localeCompare(b.date))
  }
  return map
}
