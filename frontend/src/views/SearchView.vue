<template>
  <div class="search-view">
    <h2>Sermon Search</h2>

    <div class="search-box">
      <input
        ref="searchInput"
        v-model="searchQuery"
        @input="handleSearch"
        type="text"
        placeholder="Enter search here"
        class="search-input"
      >
    </div>

    <div class="search-filters">
      <div class="filter-row">
        <div class="filter-group">
          <label>Speaker</label>
          <select v-model="filters.speaker" @change="handleSearch">
            <option value="">All Speakers</option>
            <option v-for="speaker in uniqueSpeakers" :key="speaker" :value="speaker">
              {{ speaker }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Start Date</label>
          <input type="month" v-model="filters.dateFrom" @change="handleSearch" min="2015-01" :max="filters.dateTo || currentMonth">
        </div>

        <div class="filter-group">
          <label>End Date</label>
          <input type="month" v-model="filters.dateTo" @change="handleSearch" :min="filters.dateFrom || '2015-01'" :max="currentMonth">
        </div>

        <button v-if="filters.speaker || filters.dateFrom || filters.dateTo" @click="clearFilters" class="clear-btn">Clear Filters</button>
      </div>
    </div>

    <div v-if="speakerStats" class="speaker-stats">
      <strong>{{ filters.speaker }}</strong> — {{ speakerStats.count }} sermons, {{ speakerStats.firstYear }}–{{ speakerStats.lastYear }}
    </div>

    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <p>Searching...</p>
    </div>

    <div v-else-if="results.length > 0" class="results">
      <div class="results-summary">
        <h3>Found {{ results.length }} matches{{ searchTime ? ` in ${searchTime}s` : '' }}</h3>
        <div class="stats">
          <span>Title Matches: {{ titleMatches }}</span>
          <span>Transcript Matches: {{ transcriptMatches }}{{ transcriptMatches >= 1000 ? '+' : '' }}</span>
        </div>
        <p v-if="transcriptMatches >= 1000" class="truncation-notice">
          Showing first 1,000 transcript matches — try a more specific search or use quotes for exact phrases
        </p>
      </div>

      <div v-if="yearDistribution.length > 1" class="results-timeline">
        <div class="timeline-label">Results by year:</div>
        <div class="timeline-bars">
          <div
            v-for="yd in yearDistribution"
            :key="yd.year"
            class="timeline-bar-wrapper"
            :class="{ 'timeline-active': isYearActive(yd.year) }"
            @click="toggleYearFilter(yd.year)"
            :title="`${yd.year}: ${yd.count} matches — click to filter`"
          >
            <div class="timeline-bar" :style="{ height: yd.pct + '%' }"></div>
            <span class="timeline-year">{{ String(yd.year).slice(2) }}</span>
          </div>
        </div>
      </div>

      <div class="results-tabs">
        <button
          :class="['result-tab', { active: resultTab === 'all' }]"
          @click="resultTab = 'all'"
        >
          All Results ({{ results.length }})
        </button>
        <button
          :class="['result-tab', { active: resultTab === 'titles' }]"
          @click="resultTab = 'titles'"
        >
          Title Matches ({{ titleMatches }})
        </button>
        <button
          :class="['result-tab', { active: resultTab === 'transcripts' }]"
          @click="resultTab = 'transcripts'"
        >
          Transcript Matches ({{ transcriptMatches }})
        </button>
      </div>

      <div class="results-table">
        <table>
          <thead>
            <tr>
              <th class="col-type" @click="sortBy('type')" style="cursor: pointer;">
                Type {{ sortColumn === 'type' ? (sortDirection === 'asc' ? '▲' : '▼') : '' }}
              </th>
              <th class="col-date" @click="sortBy('date')" style="cursor: pointer;">
                Date {{ sortColumn === 'date' ? (sortDirection === 'asc' ? '▲' : '▼') : '' }}
              </th>
              <th class="col-match">Match</th>
              <th class="col-title" @click="sortBy('title')" style="cursor: pointer;">
                Video Title {{ sortColumn === 'title' ? (sortDirection === 'asc' ? '▲' : '▼') : '' }}
              </th>
              <th class="col-time" @click="sortBy('timestamp')" style="cursor: pointer;">
                Time {{ sortColumn === 'timestamp' ? (sortDirection === 'asc' ? '▲' : '▼') : '' }}
              </th>
              <th class="col-speaker" @click="sortBy('speaker')" style="cursor: pointer;">
                Speaker {{ sortColumn === 'speaker' ? (sortDirection === 'asc' ? '▲' : '▼') : '' }}
              </th>
              <th class="col-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(result, index) in displayResults" :key="'r'+index">
              <tr v-if="!result._hidden" :class="{ 'group-child': result._isGroupChild }">
                <td>
                  <span :class="result.type === 'Title' ? 'badge-title' : 'badge-transcript'">
                    {{ result.type }}
                  </span>
                </td>
                <td>{{ result.date }}</td>
                <td class="match-text">
                  <div v-html="result.matchHtml"></div>
                  <button
                    v-if="result._seriesSize > 1"
                    @click="toggleSeriesGroup(result._seriesPrefix)"
                    class="group-toggle series-toggle"
                  >
                    {{ expandedSeries.has(result._seriesPrefix) ? '▲ Collapse series' : `▼ ${result._seriesSize - 1} more in "${result._seriesPrefix}" series` }}
                  </button>
                  <button
                    v-if="result._groupSize > 1"
                    @click="toggleVideoGroup(result.videoId)"
                    class="group-toggle"
                  >
                    {{ expandedVideos.has(result.videoId) ? '▲ Collapse' : `▼ ${result._groupSize - 1} more from this sermon` }}
                  </button>
                </td>
                <td class="title-cell"><a href="#" @click.prevent="openTranscript(result)">{{ result.title }}</a></td>
                <td>{{ result.timestamp }}</td>
                <td>{{ result.speaker }}</td>
                <td class="actions-cell">
                  <button
                    v-if="result.type === 'Transcript'"
                    @click="toggleContext(index)"
                    class="context-btn"
                    :title="expandedContext === index ? 'Hide context' : 'Show surrounding context'"
                  >{{ expandedContext === index ? '−' : '+' }}</button>
                  <a :href="result.url" target="_blank" class="watch-link" title="Watch video">▶</a>
                  <button @click="copyLink(result, index)" class="copy-btn" title="Copy link">
                    {{ copiedIndex === index ? '✓' : '🔗' }}
                  </button>
                </td>
              </tr>
              <tr v-if="expandedContext === index" class="context-row">
                <td colspan="7" class="context-panel">
                  <div v-if="contextLoading" class="context-loading">Loading context...</div>
                  <div v-else class="context-segments">
                    <div
                      v-for="seg in contextSegments"
                      :key="seg.start_time"
                      class="context-segment"
                      :class="{ 'context-current': Math.abs(seg.start_time - result.startTime) < 1 }"
                    >
                      <a :href="seg.vimeo_url" target="_blank" class="context-time">{{ formatTimestamp(seg.start_time) }}</a>
                      <span v-html="highlightMatches(seg.text, searchQuery)"></span>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else-if="searchQuery.length >= 2" class="no-results">
      No matches found for "{{ searchQuery }}"
    </div>

    <div v-else class="instructions">
      <p>Enter at least 2 characters to search</p>
      <p class="hint">Try searching for topics like "faith", "prayer", "salvation", or Bible references</p>
      <p class="hint">Use quotes for exact phrases: "born again"</p>
    </div>

    <div v-if="transcriptModal.open" class="modal-overlay" @click.self="closeTranscript">
      <div class="modal-content">
        <div class="modal-header">
          <div>
            <h3>{{ transcriptModal.title }}</h3>
            <div class="modal-meta">
              {{ transcriptModal.speaker }} — {{ transcriptModal.date }}
              <a :href="transcriptModal.videoUrl" target="_blank" class="modal-watch">▶ Watch</a>
              <button v-if="transcriptModal.segments.length" @click="copyTranscript" class="modal-copy">{{ transcriptCopied ? '✓ Copied' : 'Copy Transcript' }}</button>
            </div>
          </div>
          <button @click="closeTranscript" class="modal-close">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="transcriptModal.loading" class="context-loading">Loading transcript...</div>
          <div v-else class="transcript-flow">
            <div
              v-for="seg in transcriptModal.segments"
              :key="seg.start_time"
              class="transcript-line"
            >
              <a :href="seg.vimeo_url" target="_blank" class="transcript-time">{{ formatTimestamp(seg.start_time) }}</a>
              <span v-html="highlightMatches(seg.text, searchQuery)"></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <button
      v-show="showBackToTop"
      @click="scrollToTop"
      class="back-to-top"
      title="Back to top"
    >↑</button>
  </div>
</template>

<script>
import { execute } from '../tursoClient'

export default {
  name: 'SearchView',
  props: {
    speakers: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      searchQuery: '',
      results: [],
      loading: false,
      searchTime: null,
      resultTab: 'all',
      searchTimeout: null,
      sortColumn: 'date',
      sortDirection: 'desc',
      filters: {
        speaker: '',
        dateFrom: '',
        dateTo: ''
      },
      copiedIndex: null,
      showBackToTop: false,
      expandedVideos: new Set(),
      expandedSeries: new Set(),
      expandedContext: null,
      contextSegments: [],
      contextLoading: false,
      speakerStats: null,
      transcriptCopied: false,
      transcriptModal: {
        open: false,
        title: '',
        speaker: '',
        date: '',
        videoUrl: '',
        videoId: null,
        segments: [],
        loading: false
      }
    }
  },
  computed: {
    uniqueSpeakers() {
      const speakers = [...new Set(Object.values(this.speakers))].filter(s => s)
      return speakers.sort()
    },
    currentMonth() {
      const d = new Date()
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    },
    titleMatches() {
      return this.results.filter(r => r.type === 'Title').length
    },
    transcriptMatches() {
      return this.results.filter(r => r.type === 'Transcript').length
    },
    filteredResults() {
      let filtered = this.results

      if (this.resultTab === 'titles') {
        filtered = filtered.filter(r => r.type === 'Title')
      } else if (this.resultTab === 'transcripts') {
        filtered = filtered.filter(r => r.type === 'Transcript')
      }

      return this.sortResults(filtered)
    },
    displayResults() {
      const sorted = this.filteredResults
      const videoSeen = {}
      const seriesSeen = {}
      const display = []

      for (const result of sorted) {
        if (result.type === 'Title') {
          const prefix = this.detectSeriesPrefix(result.title)
          if (prefix) {
            if (!seriesSeen[prefix]) {
              seriesSeen[prefix] = { firstIdx: display.length, count: 0 }
            }
            seriesSeen[prefix].count++

            if (seriesSeen[prefix].count === 1) {
              display.push({ ...result, _groupSize: 0, _seriesSize: 0, _seriesPrefix: prefix, _hidden: false, _isGroupChild: false })
            } else {
              display.push({
                ...result,
                _groupSize: 0,
                _seriesSize: 0,
                _seriesPrefix: prefix,
                _hidden: !this.expandedSeries.has(prefix),
                _isGroupChild: true
              })
            }
          } else {
            display.push({ ...result, _groupSize: 0, _seriesSize: 0, _seriesPrefix: null, _hidden: false, _isGroupChild: false })
          }
        } else {
          const vid = result.videoId
          if (!videoSeen[vid]) {
            videoSeen[vid] = { firstIdx: display.length, count: 0 }
          }
          videoSeen[vid].count++

          if (videoSeen[vid].count === 1) {
            display.push({ ...result, _groupSize: 0, _seriesSize: 0, _seriesPrefix: null, _hidden: false, _isGroupChild: false })
          } else {
            display.push({
              ...result,
              _groupSize: 0,
              _seriesSize: 0,
              _seriesPrefix: null,
              _hidden: !this.expandedVideos.has(vid),
              _isGroupChild: true
            })
          }
        }
      }

      // Set _groupSize on first result of each video group
      for (const vid of Object.keys(videoSeen)) {
        if (videoSeen[vid].count > 1) {
          display[videoSeen[vid].firstIdx]._groupSize = videoSeen[vid].count
        }
      }

      // Set _seriesSize on first result of each series group
      for (const prefix of Object.keys(seriesSeen)) {
        if (seriesSeen[prefix].count > 1) {
          display[seriesSeen[prefix].firstIdx]._seriesSize = seriesSeen[prefix].count
        }
      }

      return display
    },
    yearDistribution() {
      const counts = {}
      for (const r of this.results) {
        const year = parseInt(r.date.substring(0, 4))
        if (year) counts[year] = (counts[year] || 0) + 1
      }
      const years = Object.keys(counts).map(Number).sort()
      if (years.length <= 1) return []
      const max = Math.max(...Object.values(counts))
      return years.map(y => ({
        year: y,
        count: counts[y],
        pct: Math.max(5, Math.round((counts[y] / max) * 100))
      }))
    }
  },
  mounted() {
    window.addEventListener('keydown', this.handleKeydown)
    window.addEventListener('scroll', this.handleScroll)
    this.restoreFromUrl()
  },
  beforeUnmount() {
    window.removeEventListener('keydown', this.handleKeydown)
    window.removeEventListener('scroll', this.handleScroll)
  },
  watch: {
    'filters.speaker'() {
      this.updateSpeakerStats()
    }
  },
  methods: {
    restoreFromUrl() {
      const params = new URLSearchParams(window.location.search)
      const q = params.get('q')
      const speaker = params.get('speaker')
      const dateFrom = params.get('from')
      const dateTo = params.get('to')

      if (q) this.searchQuery = q
      if (speaker) this.filters.speaker = speaker
      if (dateFrom) this.filters.dateFrom = dateFrom
      if (dateTo) this.filters.dateTo = dateTo

      if (q && q.length >= 2) {
        this.loading = true
        setTimeout(async () => {
          await this.performSearch()
          this.loading = false
        }, 100)
      }
    },

    updateUrl() {
      const params = new URLSearchParams()
      if (this.searchQuery.length >= 2) params.set('q', this.searchQuery)
      if (this.filters.speaker) params.set('speaker', this.filters.speaker)
      if (this.filters.dateFrom) params.set('from', this.filters.dateFrom)
      if (this.filters.dateTo) params.set('to', this.filters.dateTo)

      const qs = params.toString()
      const url = window.location.pathname + (qs ? '?' + qs : '')
      history.replaceState(null, '', url)
    },

    handleKeydown(e) {
      if (e.key === 'Escape' && this.transcriptModal.open) {
        this.closeTranscript()
      } else if (e.key === '/' && document.activeElement !== this.$refs.searchInput) {
        e.preventDefault()
        this.$refs.searchInput.focus()
      } else if (e.key === 'Escape' && document.activeElement === this.$refs.searchInput) {
        this.$refs.searchInput.blur()
      }
    },

    handleScroll() {
      this.showBackToTop = window.scrollY > 300
    },

    scrollToTop() {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    },

    handleSearch() {
      if (this.searchQuery.length < 2) {
        this.results = []
        this.loading = false
        this.updateUrl()
        return
      }

      this.loading = true
      this.expandedContext = null
      this.expandedVideos = new Set()
      this.expandedSeries = new Set()

      clearTimeout(this.searchTimeout)
      this.searchTimeout = setTimeout(async () => {
        await this.performSearch()
        this.loading = false
        this.updateUrl()
      }, 500)
    },

    buildFtsQuery(query) {
      const parts = []
      const phraseRegex = /"([^"]+)"/g
      let match
      let lastIndex = 0

      while ((match = phraseRegex.exec(query)) !== null) {
        const before = query.substring(lastIndex, match.index)
        const words = before.replace(/[":*(){}^~+\-\\]/g, ' ').split(/\s+/).filter(w => w.length > 0)
        words.forEach(w => parts.push(`text:${w}*`))

        const phrase = match[1].replace(/[*(){}^~+\-\\]/g, ' ').trim()
        if (phrase.length > 0) {
          parts.push(`text:"${phrase}"`)
        }
        lastIndex = phraseRegex.lastIndex
      }

      const remaining = query.substring(lastIndex)
      const words = remaining.replace(/[":*(){}^~+\-\\]/g, ' ').split(/\s+/).filter(w => w.length > 0)
      words.forEach(w => parts.push(`text:${w}*`))

      return parts.length > 0 ? parts.join(' ') : null
    },

    highlightMatches(text, query) {
      const safe = text.replace(/</g, '&lt;').replace(/>/g, '&gt;')

      const terms = []
      const phraseRegex = /"([^"]+)"/g
      let match
      let lastIndex = 0

      while ((match = phraseRegex.exec(query)) !== null) {
        const before = query.substring(lastIndex, match.index)
        before.split(/\s+/).filter(w => w.length > 0 && !/^[":*(){}^~+\-\\]+$/.test(w)).forEach(w => {
          terms.push(w.replace(/[":*(){}^~+\-\\]/g, ''))
        })
        terms.push(match[1].trim())
        lastIndex = phraseRegex.lastIndex
      }

      const remaining = query.substring(lastIndex)
      remaining.split(/\s+/).filter(w => w.length > 0 && !/^[":*(){}^~+\-\\]+$/.test(w)).forEach(w => {
        terms.push(w.replace(/[":*(){}^~+\-\\]/g, ''))
      })

      if (terms.length === 0) return safe

      const sorted = [...terms].sort((a, b) => b.length - a.length)
      const escaped = sorted.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
      const regex = new RegExp(`(${escaped.join('|')})`, 'gi')

      return safe.replace(regex, '<strong>$1</strong>')
    },

    clearFilters() {
      this.filters = { speaker: '', dateFrom: '', dateTo: '' }
      this.handleSearch()
    },

    isYearActive(year) {
      return this.filters.dateFrom === `${year}-01` && this.filters.dateTo === `${year}-12`
    },

    toggleYearFilter(year) {
      if (this.isYearActive(year)) {
        this.filters.dateFrom = ''
        this.filters.dateTo = ''
      } else {
        this.filters.dateFrom = `${year}-01`
        this.filters.dateTo = `${year}-12`
      }
      this.handleSearch()
    },

    async copyLink(result, index) {
      try {
        await navigator.clipboard.writeText(result.url)
      } catch {
        const textarea = document.createElement('textarea')
        textarea.value = result.url
        textarea.style.position = 'fixed'
        textarea.style.left = '-9999px'
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
      }
      this.copiedIndex = index
      setTimeout(() => { this.copiedIndex = null }, 1500)
    },

    async copyTranscript() {
      const text = this.transcriptModal.segments.map(s => s.text).join(' ')
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
      this.transcriptCopied = true
      setTimeout(() => { this.transcriptCopied = false }, 1500)
    },

    toggleVideoGroup(videoId) {
      const newSet = new Set(this.expandedVideos)
      if (newSet.has(videoId)) {
        newSet.delete(videoId)
      } else {
        newSet.add(videoId)
      }
      this.expandedVideos = newSet
    },

    detectSeriesPrefix(title) {
      const original = title.trim()
      // Try patterns that may have subtitles after the number (strip number + everything after)
      const patterns = [
        /\s*[-–—]\s*(?:Part|Pt\.?|Week|Session|Lesson)\s+\d+.*/i,
        /\s*(?:Part|Pt\.?|Week|Session|Lesson)\s+\d+.*/i,
        /\s*[-–—]\s*#\s*\d+.*/i,
        /\s*#\s*\d+.*/i,
        /\s*\(\s*(?:Part|Pt\.?)?\s*\d+\s*\).*/i,
        /\s*[-–—]\s*\d+\s*[-–—:].*/,
        /\s+\d+\s*$/,
      ]
      for (const pattern of patterns) {
        const prefix = original.replace(pattern, '').trim()
        if (prefix !== original && prefix.length > 2) {
          return prefix
        }
      }
      return null
    },

    toggleSeriesGroup(prefix) {
      const newSet = new Set(this.expandedSeries)
      if (newSet.has(prefix)) {
        newSet.delete(prefix)
      } else {
        newSet.add(prefix)
      }
      this.expandedSeries = newSet
    },

    async openTranscript(result) {
      this.transcriptModal.open = true
      this.transcriptModal.title = result.title
      this.transcriptModal.speaker = result.speaker
      this.transcriptModal.date = result.date
      this.transcriptModal.videoUrl = result.url
      this.transcriptModal.videoId = result.videoId
      this.transcriptModal.loading = true
      this.transcriptModal.segments = []
      document.body.style.overflow = 'hidden'

      try {
        const rows = await execute(
          `SELECT text, start_time, vimeo_url FROM transcript_segments
           WHERE video_id = ? ORDER BY start_time`,
          [result.videoId]
        )
        this.transcriptModal.segments = rows
      } catch (err) {
        console.error('Transcript load error:', err)
      }

      this.transcriptModal.loading = false
    },

    closeTranscript() {
      this.transcriptModal.open = false
      document.body.style.overflow = ''
    },

    async toggleContext(index) {
      if (this.expandedContext === index) {
        this.expandedContext = null
        this.contextSegments = []
        return
      }

      this.expandedContext = index
      this.contextLoading = true
      this.contextSegments = []

      const result = this.displayResults[index]
      const windowSec = 60

      try {
        const rows = await execute(
          `SELECT text, start_time, vimeo_url FROM transcript_segments
           WHERE video_id = ? AND start_time BETWEEN ? AND ?
           ORDER BY start_time`,
          [result.videoId, result.startTime - windowSec, result.startTime + windowSec]
        )
        this.contextSegments = rows.map(r => ({
          text: r.text,
          start_time: r.start_time,
          vimeo_url: r.vimeo_url
        }))
      } catch (err) {
        console.error('Context fetch error:', err)
      }

      this.contextLoading = false
    },

    async updateSpeakerStats() {
      if (!this.filters.speaker) {
        this.speakerStats = null
        return
      }

      const videoIds = Object.keys(this.speakers).filter(id => this.speakers[id] === this.filters.speaker)
      if (videoIds.length === 0) {
        this.speakerStats = null
        return
      }

      const placeholders = videoIds.map(() => '?').join(',')
      try {
        const rows = await execute(
          `SELECT COUNT(*) as count, MIN(date_published) as first_date, MAX(date_published) as last_date
           FROM videos WHERE video_id IN (${placeholders})`,
          videoIds
        )
        if (rows.length > 0) {
          this.speakerStats = {
            count: rows[0].count,
            firstYear: rows[0].first_date ? rows[0].first_date.substring(0, 4) : '?',
            lastYear: rows[0].last_date ? rows[0].last_date.substring(0, 4) : '?'
          }
        }
      } catch (err) {
        console.error('Speaker stats error:', err)
      }
    },

    async performSearch() {
      const query = this.searchQuery.trim()
      const start = performance.now()

      try {
        const ftsExpr = this.buildFtsQuery(query)

        let titleFilterSql = ''
        let transcriptFilterSql = ''
        const titleParams = [`%${query}%`]
        const transcriptParams = ftsExpr ? [ftsExpr] : []

        if (this.filters.speaker) {
          const videoIds = Object.keys(this.speakers).filter(id => this.speakers[id] === this.filters.speaker)
          if (videoIds.length > 0) {
            const placeholders = videoIds.map(() => '?').join(',')
            titleFilterSql += ` AND video_id IN (${placeholders})`
            transcriptFilterSql += ` AND ts.video_id IN (${placeholders})`
            titleParams.push(...videoIds)
            transcriptParams.push(...videoIds)
          } else {
            this.results = []
            this.searchTime = '0.0'
            return
          }
        }

        if (this.filters.dateFrom) {
          titleFilterSql += ` AND date_published >= ?`
          transcriptFilterSql += ` AND v.date_published >= ?`
          titleParams.push(this.filters.dateFrom)
          transcriptParams.push(this.filters.dateFrom)
        }

        if (this.filters.dateTo) {
          titleFilterSql += ` AND date_published <= ?`
          transcriptFilterSql += ` AND v.date_published <= ?`
          titleParams.push(this.filters.dateTo + '-31')
          transcriptParams.push(this.filters.dateTo + '-31')
        }

        const [titleRows, transcriptRows] = await Promise.all([
          execute(
            `SELECT video_id, title, date_published, url
             FROM videos
             WHERE title LIKE ?${titleFilterSql}
             ORDER BY date_published DESC`,
            titleParams
          ),
          ftsExpr ? execute(
            `SELECT ts.video_id, v.title, v.date_published, ts.start_time, ts.text, ts.vimeo_url
             FROM transcript_fts fts
             JOIN transcript_segments ts ON fts.rowid = ts.rowid
             JOIN videos v ON ts.video_id = v.video_id
             WHERE transcript_fts MATCH ?${transcriptFilterSql}
             LIMIT 1000`,
            transcriptParams
          ) : Promise.resolve([])
        ])

        const results = []

        titleRows.forEach(row => {
          const matchText = `Title contains: "${query}"`
          results.push({
            type: 'Title',
            date: row.date_published.substring(0, 10),
            speaker: this.speakers[row.video_id] || 'Unknown',
            title: row.title,
            timestamp: '00:00:00',
            match: matchText,
            matchHtml: this.highlightMatches(matchText, query),
            url: row.url,
            videoId: row.video_id,
            startTime: 0,
            score: 10
          })
        })

        transcriptRows.forEach(row => {
          const matchText = row.text.substring(0, 200) + (row.text.length > 200 ? '...' : '')
          results.push({
            type: 'Transcript',
            date: row.date_published.substring(0, 10),
            speaker: this.speakers[row.video_id] || 'Unknown',
            title: row.title,
            timestamp: this.formatTimestamp(row.start_time),
            match: matchText,
            matchHtml: this.highlightMatches(matchText, query),
            url: row.vimeo_url,
            videoId: row.video_id,
            startTime: row.start_time,
            score: 1
          })
        })

        this.results = results
        this.searchTime = ((performance.now() - start) / 1000).toFixed(1)
      } catch (error) {
        console.error('Search error:', error)
      }
    },

    sortBy(column) {
      if (this.sortColumn === column) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc'
      } else {
        this.sortColumn = column
        this.sortDirection = 'desc'
      }
    },

    sortResults(results) {
      const sorted = [...results]

      sorted.sort((a, b) => {
        if (a.type !== b.type) {
          return a.type === 'Transcript' ? -1 : 1
        }

        let aVal = a[this.sortColumn]
        let bVal = b[this.sortColumn]

        if (this.sortColumn === 'date') {
          aVal = new Date(aVal)
          bVal = new Date(bVal)
        } else if (this.sortColumn === 'timestamp') {
          aVal = this.timestampToSeconds(aVal)
          bVal = this.timestampToSeconds(bVal)
        }

        if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1
        if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1
        return 0
      })

      return sorted
    },

    timestampToSeconds(timestamp) {
      const parts = timestamp.split(':')
      return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2])
    },

    formatTimestamp(seconds) {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const secs = Math.floor(seconds % 60)
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
  }
}
</script>

<style scoped>
.search-view {
  max-width: 100%;
  padding: 0 1rem;
}

h2 {
  margin-bottom: 1.5rem;
  color: #31333F;
  font-size: 2rem;
  font-weight: 600;
}

.search-box {
  margin-bottom: 1.5rem;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  font-family: "Source Sans Pro", sans-serif;
  border: 1px solid #d3d8e0;
  border-radius: 0.25rem;
  transition: border-color 0.2s;
  background-color: #ffffff;
}

.search-input:focus {
  outline: none;
  border-color: #ff2b2b;
  box-shadow: 0 0 0 1px #ff2b2b;
}

.loading {
  text-align: center;
  padding: 40px 20px;
  color: #31333F;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 15px;
  border: 4px solid #f0f2f6;
  border-top: 4px solid #ff2b2b;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading p {
  font-size: 1rem;
  margin: 10px 0;
}

/* Speaker stats card */
.speaker-stats {
  background: #e8f0fe;
  padding: 0.75rem 1.25rem;
  border-radius: 0.25rem;
  margin-bottom: 1rem;
  font-size: 0.95rem;
  color: #1a3e72;
  border-left: 3px solid #0068c9;
}

/* Results timeline */
.results-timeline {
  display: flex;
  align-items: end;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: #f8f9fb;
  border-radius: 0.25rem;
}

.timeline-label {
  font-size: 0.8rem;
  color: #808495;
  white-space: nowrap;
  padding-bottom: 1rem;
}

.timeline-bars {
  display: flex;
  align-items: end;
  gap: 2px;
  flex: 1;
  height: 50px;
}

.timeline-bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  height: 100%;
  cursor: pointer;
  justify-content: end;
}

.timeline-bar {
  width: 100%;
  max-width: 28px;
  background: #0068c9;
  border-radius: 2px 2px 0 0;
  transition: background 0.2s;
  min-height: 2px;
}

.timeline-bar-wrapper:hover .timeline-bar {
  background: #ff2b2b;
}

.timeline-bar-wrapper.timeline-active .timeline-bar {
  background: #ff2b2b;
}

.timeline-year {
  font-size: 0.65rem;
  color: #808495;
  margin-top: 2px;
}

.results-summary {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  padding: 20px;
  border-radius: 0.25rem;
  margin-bottom: 1.5rem;
  border-left: 4px solid #28a745;
}

.results-summary h3 {
  color: #155724;
  margin-bottom: 10px;
  font-size: 1.1rem;
  font-weight: 600;
}

.stats {
  display: flex;
  gap: 30px;
  color: #155724;
  font-size: 0.95rem;
}

.stats span {
  padding: 5px 10px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 4px;
}

.truncation-notice {
  margin-top: 8px;
  font-size: 0.85rem;
  color: #856404;
  font-style: italic;
}

.search-filters {
  background: #f0f2f6;
  padding: 1rem 1.5rem;
  border-radius: 0.25rem;
  margin-bottom: 1.5rem;
}

.search-filters .filter-row {
  display: flex;
  gap: 1rem;
  align-items: end;
}

.search-filters .filter-group {
  display: flex;
  flex-direction: column;
}

.search-filters .filter-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #31333F;
  margin-bottom: 0.5rem;
}

.search-filters .filter-group select,
.search-filters .filter-group input[type="month"] {
  padding: 0.5rem;
  font-size: 0.95rem;
  font-family: "Source Sans Pro", sans-serif;
  border: 1px solid #d3d8e0;
  border-radius: 0.25rem;
  background: white;
  width: 180px;
}

.search-filters .clear-btn {
  padding: 0.5rem 1rem;
  background: #ff2b2b;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-family: "Source Sans Pro", sans-serif;
  font-size: 0.95rem;
  transition: background 0.2s;
  height: fit-content;
}

.search-filters .clear-btn:hover {
  background: #d92020;
}

.results-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.result-tab {
  padding: 0.5rem 1rem;
  background: #f0f2f6;
  border: 1px solid #d3d8e0;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.95rem;
  font-family: "Source Sans Pro", sans-serif;
  color: #31333F;
}

.result-tab:hover {
  background: #e6e9ef;
  border-color: #cbd5e0;
}

.result-tab.active {
  background: #0068c9;
  color: white;
  border-color: #0068c9;
  font-weight: 500;
}

.results-table {
  overflow-x: auto;
  background: white;
  border: 1px solid #e6e9ef;
  border-radius: 0.25rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

thead {
  background: #f0f2f6;
  position: sticky;
  top: 0;
  z-index: 10;
}

th {
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #31333F;
  border-bottom: 2px solid #e6e9ef;
  white-space: nowrap;
  font-size: 0.875rem;
}

th.col-type { width: 80px; }
th.col-date { width: 100px; }
th.col-match { width: 35%; }
th.col-title { width: 30%; }
th.col-time { width: 80px; }
th.col-speaker { width: 120px; }
th.col-actions { width: 80px; }

td {
  padding: 0.75rem;
  border-bottom: 1px solid #f0f2f6;
  vertical-align: top;
  color: #31333F;
}

tr:hover {
  background: #fafbfc;
}

tr.group-child {
  background: #f8fafc;
}

tr.group-child td {
  border-left: 3px solid #0068c9;
}

.badge-title {
  background: #0068c9;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.badge-transcript {
  background: #28a745;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.title-cell {
  font-weight: 500;
  color: #31333F;
}

.match-text {
  line-height: 1.5;
  color: #555;
  overflow-wrap: break-word;
}

.match-text :deep(strong) {
  color: #d63200;
  font-weight: 700;
}

.group-toggle {
  display: block;
  margin-top: 0.5rem;
  background: none;
  border: none;
  color: #0068c9;
  cursor: pointer;
  font-size: 0.85rem;
  font-family: "Source Sans Pro", sans-serif;
  padding: 0;
}

.group-toggle:hover {
  text-decoration: underline;
}

.series-toggle {
  color: #7c3aed;
}

.actions-cell {
  white-space: nowrap;
}

.context-btn {
  background: #f0f2f6;
  border: 1px solid #d3d8e0;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.9rem;
  width: 22px;
  height: 22px;
  line-height: 18px;
  text-align: center;
  padding: 0;
  margin-right: 0.25rem;
  vertical-align: middle;
  transition: all 0.2s;
  font-weight: 700;
  color: #31333F;
}

.context-btn:hover {
  background: #e6e9ef;
  border-color: #0068c9;
  color: #0068c9;
}

.watch-link {
  color: #0068c9;
  text-decoration: none;
  font-size: 1.2rem;
  transition: all 0.2s;
  display: inline-block;
}

.watch-link:hover {
  color: #ff2b2b;
  transform: scale(1.15);
}

.copy-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0 0.25rem;
  margin-left: 0.25rem;
  transition: transform 0.2s;
  vertical-align: middle;
}

.copy-btn:hover {
  transform: scale(1.15);
}

/* Context expansion panel */
.context-row td {
  padding: 0;
  background: #f8f9fb;
}

.context-panel {
  padding: 1rem 1.5rem !important;
  border-left: 3px solid #28a745;
}

.context-loading {
  color: #808495;
  font-style: italic;
  font-size: 0.9rem;
}

.context-segments {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.context-segment {
  display: flex;
  gap: 0.75rem;
  font-size: 0.9rem;
  line-height: 1.5;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.context-segment.context-current {
  background: #fff3cd;
  border-left: 3px solid #ffc107;
}

.context-time {
  color: #0068c9;
  text-decoration: none;
  font-size: 0.8rem;
  white-space: nowrap;
  padding-top: 2px;
  font-family: monospace;
}

.context-time:hover {
  text-decoration: underline;
}

.context-segment :deep(strong) {
  color: #d63200;
  font-weight: 700;
}

.back-to-top {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #0068c9;
  color: white;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: background 0.2s, transform 0.2s;
  z-index: 100;
}

.back-to-top:hover {
  background: #005bb5;
  transform: scale(1.1);
}

.no-results {
  text-align: center;
  padding: 60px 20px;
  color: #31333F;
  font-size: 1rem;
}

.instructions {
  text-align: center;
  padding: 60px 20px;
  color: #31333F;
}

.instructions p {
  margin: 10px 0;
  font-size: 1.05rem;
}

.instructions .hint {
  color: #808495;
  font-size: 0.95rem;
  font-style: normal;
}

/* Title cell link */
.title-cell a {
  color: #0068c9;
  text-decoration: none;
  font-weight: 500;
}

.title-cell a:hover {
  text-decoration: underline;
  color: #005bb5;
}

/* Transcript modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.modal-content {
  background: white;
  border-radius: 0.5rem;
  width: 100%;
  max-width: 800px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e6e9ef;
  flex-shrink: 0;
}

.modal-header h3 {
  font-size: 1.15rem;
  color: #31333F;
  margin-bottom: 0.25rem;
}

.modal-meta {
  font-size: 0.9rem;
  color: #808495;
}

.modal-watch {
  color: #0068c9;
  text-decoration: none;
  margin-left: 0.75rem;
  font-weight: 500;
}

.modal-watch:hover {
  text-decoration: underline;
}

.modal-copy {
  background: none;
  border: 1px solid #0068c9;
  color: #0068c9;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  margin-left: 0.75rem;
  font-size: 0.85rem;
  cursor: pointer;
}

.modal-copy:hover {
  background: #0068c9;
  color: white;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #808495;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  transition: all 0.2s;
  line-height: 1;
}

.modal-close:hover {
  background: #f0f2f6;
  color: #31333F;
}

.modal-body {
  overflow-y: auto;
  padding: 1.25rem 1.5rem;
  flex: 1;
}

.transcript-flow {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.transcript-line {
  display: flex;
  gap: 0.75rem;
  padding: 0.35rem 0.5rem;
  border-radius: 0.25rem;
  line-height: 1.6;
  font-size: 0.95rem;
}

.transcript-line:hover {
  background: #f8f9fb;
}

.transcript-time {
  color: #0068c9;
  text-decoration: none;
  font-size: 0.8rem;
  white-space: nowrap;
  padding-top: 3px;
  font-family: monospace;
  flex-shrink: 0;
}

.transcript-time:hover {
  text-decoration: underline;
}

.transcript-line :deep(strong) {
  color: #d63200;
  font-weight: 700;
}

@media (max-width: 768px) {
  .search-view {
    padding: 0;
  }

  .search-filters .filter-row {
    flex-wrap: wrap;
  }

  .search-filters .filter-group {
    width: 100%;
  }

  .search-filters .filter-group select,
  .search-filters .filter-group input[type="month"] {
    width: 100%;
  }

  .search-filters .clear-btn {
    width: fit-content;
  }

  .results-table {
    font-size: 0.85rem;
  }

  th, td {
    padding: 0.5rem;
  }

  .match-text {
    max-width: 200px;
  }

  .stats {
    flex-direction: column;
    gap: 0.5rem;
  }

  .results-timeline {
    flex-direction: column;
    align-items: stretch;
  }

  .timeline-label {
    padding-bottom: 0;
  }

  .modal-overlay {
    padding: 1rem;
  }

  .modal-content {
    max-height: 90vh;
  }
}
</style>
