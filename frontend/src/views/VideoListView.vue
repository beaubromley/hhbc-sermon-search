<template>
  <div class="video-list-view">
    <h2>Video List</h2>

    <div class="filters">
      <div class="filter-row">
        <div class="filter-group">
          <label>Speaker</label>
          <select v-model="filters.speaker" @change="applyFilters">
            <option value="">All Speakers</option>
            <option v-for="speaker in uniqueSpeakers" :key="speaker" :value="speaker">
              {{ speaker }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Year</label>
          <select v-model="filters.year" @change="applyFilters">
            <option value="">All Years</option>
            <option v-for="year in uniqueYears" :key="year" :value="year">
              {{ year }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Bible Book</label>
          <select v-model="filters.book" @change="applyFilters">
            <option value="">All Books</option>
            <option v-for="book in uniqueBooks" :key="book" :value="book">
              {{ book }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Topic</label>
          <select v-model="filters.topic" @change="applyFilters">
            <option value="">All Topics</option>
            <option v-for="topic in uniqueTopics" :key="topic" :value="topic">
              {{ topic }}
            </option>
          </select>
        </div>

        <button @click="clearFilters" class="clear-btn">Clear Filters</button>
      </div>
    </div>

    <div class="results-summary">
      <h3>{{ filteredVideos.length }} sermons</h3>
    </div>

    <div v-if="loading" class="loading">
      Loading videos...
    </div>

    <div v-else-if="filteredVideos.length > 0" class="video-table">
      <table>
        <thead>
          <tr>
            <th @click="sortBy('date')" class="sortable">
              Date {{ sortColumn === 'date' ? (sortDirection === 'asc' ? '▲' : '▼') : '' }}
            </th>
            <th @click="sortBy('speaker')" class="sortable">
              Speaker {{ sortColumn === 'speaker' ? (sortDirection === 'asc' ? '▲' : '▼') : '' }}
            </th>
            <th @click="sortBy('title')" class="sortable">
              Title {{ sortColumn === 'title' ? (sortDirection === 'asc' ? '▲' : '▼') : '' }}
            </th>
            <th>Duration</th>
            <th>Watch</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="video in paginatedVideos" :key="video.id">
            <td>{{ video.date }}</td>
            <td>{{ video.speaker }}</td>
            <td class="title-cell"><a href="#" @click.prevent="openTranscript(video)" class="title-link">{{ video.title }}</a></td>
            <td>{{ video.duration }}</td>
            <td>
              <a :href="video.url" target="_blank" class="watch-link" title="Watch video">▶</a>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="pagination" v-if="totalPages > 1">
        <button @click="currentPage--" :disabled="currentPage === 1">Previous</button>
        <span>Page {{ currentPage }} of {{ totalPages }}</span>
        <button @click="currentPage++" :disabled="currentPage === totalPages">Next</button>
      </div>
    </div>

    <div v-else class="no-results">
      No videos match the selected filters
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
              <span>{{ seg.text }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { execute } from '../tursoClient'

export default {
  name: 'VideoListView',
  props: {
    speakers: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      loading: true,
      videos: [],
      uniqueBooksList: [],
      uniqueTopicsList: [],
      filters: {
        speaker: '',
        year: '',
        book: '',
        topic: ''
      },
      filteredVideos: [],
      sortColumn: 'date',
      sortDirection: 'desc',
      currentPage: 1,
      perPage: 50,
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
      const speakers = [...new Set(this.videos.map(v => v.speaker))].filter(s => s)
      return speakers.sort()
    },
    uniqueYears() {
      const years = [...new Set(this.videos.map(v => new Date(v.date).getFullYear()))]
      return years.sort((a, b) => b - a)
    },
    uniqueBooks() {
      return this.uniqueBooksList
    },
    uniqueTopics() {
      return this.uniqueTopicsList
    },
    totalPages() {
      return Math.ceil(this.filteredVideos.length / this.perPage)
    },
    paginatedVideos() {
      const start = (this.currentPage - 1) * this.perPage
      const end = start + this.perPage
      return this.filteredVideos.slice(start, end)
    }
  },
  async mounted() {
    await this.loadVideos()
    this._onKeydown = (e) => {
      if (e.key === 'Escape' && this.transcriptModal.open) {
        this.closeTranscript()
      }
    }
    document.addEventListener('keydown', this._onKeydown)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this._onKeydown)
  },
  methods: {
    async loadVideos() {
      this.loading = true

      try {
        const videoRows = await execute(
          'SELECT video_id, title, date_published, duration, url FROM videos ORDER BY date_published DESC'
        )

        this.videos = videoRows.map(row => ({
          id: row.video_id,
          title: row.title,
          date: row.date_published.substring(0, 10),
          duration: this.formatDuration(row.duration),
          url: row.url,
          speaker: this.speakers[row.video_id] || 'Unknown'
        }))

        // Only fetch unique values for filter dropdowns (not all pairs)
        const bookRows = await execute(
          'SELECT DISTINCT book FROM bible_references ORDER BY book'
        )
        this.uniqueBooksList = bookRows.map(row => row.book)

        const topicRows = await execute(
          'SELECT DISTINCT topic FROM theological_topics ORDER BY topic'
        )
        this.uniqueTopicsList = topicRows.map(row => row.topic)

        this.filteredVideos = [...this.videos]
        this.loading = false

      } catch (error) {
        console.error('Error loading videos:', error)
        this.loading = false
      }
    },

    async applyFilters() {
      let filtered = [...this.videos]

      if (this.filters.speaker) {
        filtered = filtered.filter(v => v.speaker === this.filters.speaker)
      }

      if (this.filters.year) {
        filtered = filtered.filter(v => new Date(v.date).getFullYear() === parseInt(this.filters.year))
      }

      if (this.filters.book) {
        // Query Turso for matching video IDs on demand
        const rows = await execute(
          'SELECT DISTINCT video_id FROM bible_references WHERE book = ?',
          [this.filters.book]
        )
        const videoIds = new Set(rows.map(r => r.video_id))
        filtered = filtered.filter(v => videoIds.has(v.id))
      }

      if (this.filters.topic) {
        // Query Turso for matching video IDs on demand
        const rows = await execute(
          'SELECT DISTINCT video_id FROM theological_topics WHERE topic = ?',
          [this.filters.topic]
        )
        const videoIds = new Set(rows.map(r => r.video_id))
        filtered = filtered.filter(v => videoIds.has(v.id))
      }

      this.filteredVideos = filtered
      this.sortVideos()
      this.currentPage = 1
    },

    clearFilters() {
      this.filters = {
        speaker: '',
        year: '',
        book: '',
        topic: ''
      }
      this.applyFilters()
    },

    sortBy(column) {
      if (this.sortColumn === column) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc'
      } else {
        this.sortColumn = column
        this.sortDirection = 'desc'
      }
      this.sortVideos()
    },

    sortVideos() {
      this.filteredVideos.sort((a, b) => {
        let aVal = a[this.sortColumn]
        let bVal = b[this.sortColumn]

        if (this.sortColumn === 'date') {
          aVal = new Date(aVal)
          bVal = new Date(bVal)
        }

        if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1
        if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1
        return 0
      })
    },

    formatDuration(seconds) {
      if (!seconds) return '--'
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      if (hours > 0) {
        return `${hours}h ${minutes}m`
      }
      return `${minutes}m`
    },

    formatTimestamp(seconds) {
      const h = Math.floor(seconds / 3600)
      const m = Math.floor((seconds % 3600) / 60)
      const s = Math.floor(seconds % 60)
      if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
      return `${m}:${String(s).padStart(2, '0')}`
    },

    async openTranscript(video) {
      this.transcriptModal.open = true
      this.transcriptModal.title = video.title
      this.transcriptModal.speaker = video.speaker
      this.transcriptModal.date = video.date
      this.transcriptModal.videoUrl = video.url
      this.transcriptModal.videoId = video.id
      this.transcriptModal.loading = true
      this.transcriptModal.segments = []
      document.body.style.overflow = 'hidden'

      try {
        const rows = await execute(
          `SELECT text, start_time, vimeo_url FROM transcript_segments
           WHERE video_id = ? ORDER BY start_time`,
          [video.id]
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
    }
  }
}
</script>

<style scoped>
.video-list-view {
  max-width: 100%;
  padding: 0 1rem;
}

h2 {
  margin-bottom: 1.5rem;
  color: #31333F;
  font-size: 2rem;
  font-weight: 600;
}

.filters {
  background: #f0f2f6;
  padding: 1.5rem;
  border-radius: 0.25rem;
  margin-bottom: 1.5rem;
}

.filter-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  align-items: end;
}

.filter-group {
  display: flex;
  flex-direction: column;
}

.filter-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #31333F;
  margin-bottom: 0.5rem;
}

.filter-group select {
  padding: 0.5rem;
  font-size: 0.95rem;
  font-family: "Source Sans Pro", sans-serif;
  border: 1px solid #d3d8e0;
  border-radius: 0.25rem;
  background: white;
}

.clear-btn {
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

.clear-btn:hover {
  background: #d92020;
}

.results-summary {
  background: #e8f5e9;
  padding: 1rem 1.25rem;
  border-radius: 0.25rem;
  margin-bottom: 1.5rem;
  border-left: 4px solid #28a745;
}

.results-summary h3 {
  color: #155724;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #31333F;
}

.video-table {
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

th.sortable {
  cursor: pointer;
  user-select: none;
}

th.sortable:hover {
  background: #e6e9ef;
}

td {
  padding: 0.75rem;
  border-bottom: 1px solid #f0f2f6;
  color: #31333F;
}

tr:hover {
  background: #fafbfc;
}

.title-cell {
  max-width: 600px;
  font-weight: 500;
}

.title-link {
  color: #0068c9;
  text-decoration: none;
  cursor: pointer;
}

.title-link:hover {
  text-decoration: underline;
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

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: #f0f2f6;
}

.pagination button {
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid #d3d8e0;
  border-radius: 0.25rem;
  cursor: pointer;
  font-family: "Source Sans Pro", sans-serif;
  transition: all 0.2s;
}

.pagination button:hover:not(:disabled) {
  background: #e6e9ef;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination span {
  color: #31333F;
  font-weight: 500;
}

.no-results {
  text-align: center;
  padding: 60px 20px;
  color: #31333F;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 0.5rem;
  max-width: 800px;
  width: 90vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e6e9ef;
}

.modal-header h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
  color: #31333F;
}

.modal-meta {
  font-size: 0.9rem;
  color: #555;
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
  color: #555;
  padding: 0.25rem;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.context-loading {
  text-align: center;
  padding: 2rem;
  color: #555;
}

.transcript-flow {
  line-height: 1.7;
}

.transcript-line {
  margin-bottom: 0.5rem;
}

.transcript-time {
  font-family: monospace;
  font-size: 0.8rem;
  color: #0068c9;
  text-decoration: none;
  margin-right: 0.5rem;
  white-space: nowrap;
}

.transcript-time:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .video-list-view {
    padding: 0;
  }

  .filters {
    padding: 1rem;
  }

  .filter-row {
    grid-template-columns: 1fr;
  }

  .filter-group select {
    width: 100%;
  }

  .clear-btn {
    width: fit-content;
  }

  table {
    font-size: 0.85rem;
  }

  th, td {
    padding: 0.5rem;
  }
}
</style>
