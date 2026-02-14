<template>
  <div class="bible-heatmap-view">
    <h2>Bible Heat Map</h2>

    <div class="filters">
      <div class="filter-row">
        <div class="filter-group">
          <label>Speaker</label>
          <select v-model="filters.speaker" @change="loadData">
            <option value="">All Speakers</option>
            <option v-for="speaker in uniqueSpeakers" :key="speaker" :value="speaker">
              {{ speaker }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Year</label>
          <select v-model="filters.year" @change="loadData">
            <option value="">All Years</option>
            <option v-for="year in uniqueYears" :key="year" :value="year">
              {{ year }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Testament</label>
          <select v-model="filters.testament" @change="loadData">
            <option value="both">Both</option>
            <option value="old">Old Testament</option>
            <option value="new">New Testament</option>
          </select>
        </div>

        <button @click="clearFilters" class="clear-btn">Clear Filters</button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      Loading Bible references...
    </div>

    <div v-else-if="bookCounts.length > 0">
      <!-- Old Testament -->
      <div v-if="filters.testament === 'both' || filters.testament === 'old'" class="testament-section">
        <h3>Old Testament</h3>

        <div class="heatmap-row">
          <div
            v-for="book in oldTestamentBooks.slice(0, 13)"
            :key="book"
            :class="['book-cell', getHeatClass(bookCounts.find(b => b.book === book)?.count || 0)]"
            :title="`${book}: ${bookCounts.find(b => b.book === book)?.count || 0} references`"
            @click="selectBook(book)"
          >
            <div class="book-abbrev">{{ getAbbreviation(book) }}</div>
            <div class="book-count">{{ bookCounts.find(b => b.book === book)?.count || 0 }}</div>
          </div>
        </div>

        <div class="heatmap-row">
          <div
            v-for="book in oldTestamentBooks.slice(13, 26)"
            :key="book"
            :class="['book-cell', getHeatClass(bookCounts.find(b => b.book === book)?.count || 0)]"
            :title="`${book}: ${bookCounts.find(b => b.book === book)?.count || 0} references`"
            @click="selectBook(book)"
          >
            <div class="book-abbrev">{{ getAbbreviation(book) }}</div>
            <div class="book-count">{{ bookCounts.find(b => b.book === book)?.count || 0 }}</div>
          </div>
        </div>

        <div class="heatmap-row">
          <div
            v-for="book in oldTestamentBooks.slice(26, 39)"
            :key="book"
            :class="['book-cell', getHeatClass(bookCounts.find(b => b.book === book)?.count || 0)]"
            :title="`${book}: ${bookCounts.find(b => b.book === book)?.count || 0} references`"
            @click="selectBook(book)"
          >
            <div class="book-abbrev">{{ getAbbreviation(book) }}</div>
            <div class="book-count">{{ bookCounts.find(b => b.book === book)?.count || 0 }}</div>
          </div>
        </div>
      </div>

      <!-- New Testament -->
      <div v-if="filters.testament === 'both' || filters.testament === 'new'" class="testament-section">
        <h3>New Testament</h3>

        <div class="heatmap-row">
          <div
            v-for="book in newTestamentBooks.slice(0, 9)"
            :key="book"
            :class="['book-cell', getHeatClass(bookCounts.find(b => b.book === book)?.count || 0)]"
            :title="`${book}: ${bookCounts.find(b => b.book === book)?.count || 0} references`"
            @click="selectBook(book)"
          >
            <div class="book-abbrev">{{ getAbbreviation(book) }}</div>
            <div class="book-count">{{ bookCounts.find(b => b.book === book)?.count || 0 }}</div>
          </div>
        </div>

        <div class="heatmap-row">
          <div
            v-for="book in newTestamentBooks.slice(9, 18)"
            :key="book"
            :class="['book-cell', getHeatClass(bookCounts.find(b => b.book === book)?.count || 0)]"
            :title="`${book}: ${bookCounts.find(b => b.book === book)?.count || 0} references`"
            @click="selectBook(book)"
          >
            <div class="book-abbrev">{{ getAbbreviation(book) }}</div>
            <div class="book-count">{{ bookCounts.find(b => b.book === book)?.count || 0 }}</div>
          </div>
        </div>

        <div class="heatmap-row">
          <div
            v-for="book in newTestamentBooks.slice(18, 27)"
            :key="book"
            :class="['book-cell', getHeatClass(bookCounts.find(b => b.book === book)?.count || 0)]"
            :title="`${book}: ${bookCounts.find(b => b.book === book)?.count || 0} references`"
            @click="selectBook(book)"
          >
            <div class="book-abbrev">{{ getAbbreviation(book) }}</div>
            <div class="book-count">{{ bookCounts.find(b => b.book === book)?.count || 0 }}</div>
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div class="legend">
        <h4>Reference Count</h4>
        <div class="legend-items">
          <div class="legend-item">
            <div class="legend-box heat-0"></div>
            <span>0</span>
          </div>
          <div class="legend-item">
            <div class="legend-box heat-1"></div>
            <span>1-50</span>
          </div>
          <div class="legend-item">
            <div class="legend-box heat-2"></div>
            <span>51-200</span>
          </div>
          <div class="legend-item">
            <div class="legend-box heat-3"></div>
            <span>201-500</span>
          </div>
          <div class="legend-item">
            <div class="legend-box heat-4"></div>
            <span>501-1500</span>
          </div>
          <div class="legend-item">
            <div class="legend-box heat-5"></div>
            <span>1501+</span>
          </div>
        </div>
      </div>

      <!-- Book Details Modal -->
      <div v-if="selectedBook" class="book-details">
        <div class="details-header">
          <h3>{{ selectedBook }}</h3>
          <button @click="selectedBook = null" class="close-btn">✕</button>
        </div>

        <div class="details-content">
          <p class="details-summary">
            <strong>{{ getTotalReferences(selectedBook) }}</strong> total references
          </p>

        <h4>Chapter Breakdown</h4>
        <div class="chapter-list">
          <div
            v-for="chapter in getChapterBreakdown()"
            :key="chapter.chapter"
            class="chapter-item"
          >
            <div
              class="chapter-header"
              @click="toggleChapter(chapter.chapter)"
            >
              <span class="chapter-number">Chapter {{ chapter.chapter || 'General' }}</span>
              <div class="chapter-right">
                <span class="chapter-count">{{ chapter.count }} references</span>
                <span class="chapter-toggle">{{ isChapterExpanded(chapter.chapter) ? '▼' : '▶' }}</span>
              </div>
            </div>

            <div v-if="isChapterExpanded(chapter.chapter)" class="chapter-sermons">
              <div
                v-for="sermon in getChapterSermons(selectedBook, chapter.chapter)"
                :key="sermon.url"
                class="chapter-sermon-item"
              >
                <div class="sermon-content">
                  <a href="#" @click.prevent="openTranscript(sermon)" class="sermon-title-link">{{ sermon.title }}</a>
                  <span class="sermon-actions">
                    <a :href="sermon.watchUrl" target="_blank" class="action-link" title="Watch">▶</a>
                    <a href="#" @click.prevent="openTranscript(sermon)" class="action-link" title="Read transcript">📄</a>
                  </span>
                  <p v-if="sermon.context" class="sermon-context">{{ sermon.context }}</p>
                </div>
                <span class="sermon-date">{{ sermon.date }}</span>
              </div>
              <div v-if="getChapterSermons(selectedBook, chapter.chapter).length === 0" class="loading-sermons">
                Loading...
              </div>
            </div>
          </div>
        </div>

          <h4>Recent Sermons (Top 10)</h4>
          <div class="sermon-list">
            <div v-for="sermon in getSermons()" :key="sermon.url" class="sermon-item">
              <a href="#" @click.prevent="openTranscript(sermon)" class="sermon-title-link">{{ sermon.title }}</a>
              <span class="sermon-actions">
                <a :href="sermon.url" target="_blank" class="action-link" title="Watch">▶</a>
                <a href="#" @click.prevent="openTranscript(sermon)" class="action-link" title="Read transcript">📄</a>
              </span>
              <span class="sermon-date">{{ sermon.date }}</span>
            </div>
          </div>
        </div>
      </div>

    </div>

    <div v-else class="no-results">
      No Bible references found
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
  name: 'BibleHeatMapView',
  props: {
    speakers: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      loading: true,
      filters: {
        speaker: '',
        year: '',
        testament: 'both'
      },
      bookCounts: [],
      selectedBook: null,
      bookChapters: [],
      bookSermons: [],
      expandedChapters: [],
      chapterSermonsCache: {},
      uniqueSpeakers: [],
      uniqueYears: [],
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
      },
      oldTestamentBooks: [
        'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
        'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
        '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
        'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs',
        'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah',
        'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel',
        'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk',
        'Zephaniah', 'Haggai', 'Zechariah', 'Malachi'
      ],
      newTestamentBooks: [
        'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans',
        '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
        'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
        '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
        'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John',
        'Jude', 'Revelation'
      ],
      bookAbbreviations: {
        'Genesis': 'Gen', 'Exodus': 'Exod', 'Leviticus': 'Lev', 'Numbers': 'Num',
        'Deuteronomy': 'Deut', 'Joshua': 'Josh', 'Judges': 'Judg', 'Ruth': 'Ruth',
        '1 Samuel': '1Sam', '2 Samuel': '2Sam', '1 Kings': '1Kgs', '2 Kings': '2Kgs',
        '1 Chronicles': '1Chr', '2 Chronicles': '2Chr', 'Ezra': 'Ezra',
        'Nehemiah': 'Neh', 'Esther': 'Esth', 'Job': 'Job', 'Psalms': 'Ps',
        'Proverbs': 'Prov', 'Ecclesiastes': 'Eccl', 'Song of Solomon': 'Song',
        'Isaiah': 'Isa', 'Jeremiah': 'Jer', 'Lamentations': 'Lam',
        'Ezekiel': 'Ezek', 'Daniel': 'Dan', 'Hosea': 'Hos', 'Joel': 'Joel',
        'Amos': 'Amos', 'Obadiah': 'Obad', 'Jonah': 'Jonah', 'Micah': 'Mic',
        'Nahum': 'Nah', 'Habakkuk': 'Hab', 'Zephaniah': 'Zeph',
        'Haggai': 'Hag', 'Zechariah': 'Zech', 'Malachi': 'Mal',
        'Matthew': 'Matt', 'Mark': 'Mark', 'Luke': 'Luke', 'John': 'John',
        'Acts': 'Acts', 'Romans': 'Rom', '1 Corinthians': '1Cor',
        '2 Corinthians': '2Cor', 'Galatians': 'Gal', 'Ephesians': 'Eph',
        'Philippians': 'Phil', 'Colossians': 'Col', '1 Thessalonians': '1Thess',
        '2 Thessalonians': '2Thess', '1 Timothy': '1Tim', '2 Timothy': '2Tim',
        'Titus': 'Titus', 'Philemon': 'Phlm', 'Hebrews': 'Heb',
        'James': 'Jas', '1 Peter': '1Pet', '2 Peter': '2Pet',
        '1 John': '1John', '2 John': '2John', '3 John': '3John',
        'Jude': 'Jude', 'Revelation': 'Rev'
      }
    }
  },
  async mounted() {
    await this.loadFilters()
    await this.loadData()
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
    async loadFilters() {
      try {
        const speakerRows = await execute(`
          SELECT DISTINCT v.video_id
          FROM videos v
          JOIN bible_references br ON v.video_id = br.video_id
        `)

        const speakers = new Set()
        speakerRows.forEach(row => {
          const speaker = this.speakers[row.video_id]
          if (speaker && speaker !== 'Unknown') {
            speakers.add(speaker)
          }
        })
        this.uniqueSpeakers = Array.from(speakers).sort()

        const yearRows = await execute(`
          SELECT DISTINCT strftime('%Y', v.date_published) as year
          FROM videos v
          JOIN bible_references br ON v.video_id = br.video_id
          ORDER BY year DESC
        `)
        this.uniqueYears = yearRows.map(row => row.year)
      } catch (error) {
        console.error('Error loading filters:', error)
      }
    },

    async loadData() {
      this.loading = true

      try {
        // Use GROUP BY server-side — returns ~66 rows instead of 50K+
        let sql = `
          SELECT br.book, COUNT(*) as count
          FROM bible_references br
          JOIN videos v ON br.video_id = v.video_id
          WHERE 1=1
        `
        const params = []

        if (this.filters.speaker) {
          const videoIds = Object.keys(this.speakers).filter(id => this.speakers[id] === this.filters.speaker)
          if (videoIds.length > 0) {
            sql += ` AND br.video_id IN (${videoIds.map(() => '?').join(',')})`
            params.push(...videoIds)
          }
        }

        if (this.filters.year) {
          sql += ` AND strftime('%Y', v.date_published) = ?`
          params.push(this.filters.year)
        }

        sql += ` GROUP BY br.book`

        const rows = await execute(sql, params)
        this.bookCounts = rows.map(row => ({ book: row.book, count: row.count }))

        this.loading = false
      } catch (error) {
        console.error('Error loading Bible references:', error)
        this.loading = false
      }
    },

    clearFilters() {
      this.filters = {
        speaker: '',
        year: '',
        testament: 'both'
      }
      this.loadData()
    },

    getAbbreviation(book) {
      return this.bookAbbreviations[book] || book.substring(0, 4)
    },

    getHeatClass(count) {
      if (count === 0) return 'heat-0'
      if (count <= 50) return 'heat-1'
      if (count <= 200) return 'heat-2'
      if (count <= 500) return 'heat-3'
      if (count <= 1500) return 'heat-4'
      return 'heat-5'
    },

    async selectBook(book) {
      this.selectedBook = book
      this.expandedChapters = []
      this.chapterSermonsCache = {}
      this.bookChapters = []
      this.bookSermons = []

      // Fetch chapter breakdown server-side
      const chapterRows = await execute(`
        SELECT COALESCE(CAST(br.chapter AS TEXT), 'General') as chapter, COUNT(*) as count
        FROM bible_references br
        WHERE br.book = ?
        GROUP BY br.chapter
        ORDER BY CASE WHEN br.chapter IS NULL THEN 999999 ELSE br.chapter END
      `, [book])
      this.bookChapters = chapterRows.map(row => ({ chapter: row.chapter, count: row.count }))

      // Fetch top 10 sermons server-side
      const sermonRows = await execute(`
        SELECT DISTINCT v.video_id, v.title, v.date_published, v.url
        FROM bible_references br
        JOIN videos v ON br.video_id = v.video_id
        WHERE br.book = ?
        ORDER BY v.date_published DESC
        LIMIT 10
      `, [book])
      this.bookSermons = sermonRows.map(row => ({
        title: row.title,
        date: row.date_published.substring(0, 10),
        url: row.url,
        videoId: row.video_id
      }))
    },

    async toggleChapter(chapter) {
      const index = this.expandedChapters.indexOf(chapter)
      if (index > -1) {
        this.expandedChapters.splice(index, 1)
      } else {
        this.expandedChapters.push(chapter)
        await this.fetchChapterSermons(this.selectedBook, chapter)
      }
    },

    async fetchChapterSermons(book, chapter) {
      const key = `${book}:${chapter}`
      if (this.chapterSermonsCache[key]) return

      let sql = `
        SELECT br.video_id, v.title, v.date_published, br.start_time, br.context
        FROM bible_references br
        JOIN videos v ON br.video_id = v.video_id
        WHERE br.book = ?
      `
      const params = [book]

      if (chapter === 'General' || !chapter) {
        sql += ` AND (br.chapter IS NULL OR br.chapter = '')`
      } else {
        sql += ` AND br.chapter = ?`
        params.push(parseInt(chapter))
      }

      sql += ` ORDER BY v.date_published DESC`

      const rows = await execute(sql, params)

      this.chapterSermonsCache[key] = rows.map(row => {
        const timestamp = row.start_time ? Math.floor(row.start_time) : 0
        return {
          title: row.title,
          date: row.date_published.substring(0, 10),
          videoId: row.video_id,
          url: `https://player.vimeo.com/video/${row.video_id}#t=${timestamp}s`,
          watchUrl: `https://player.vimeo.com/video/${row.video_id}#t=${timestamp}s`,
          context: row.context || ''
        }
      })
    },

    getChapterSermons(book, chapter) {
      return this.chapterSermonsCache[`${book}:${chapter}`] || []
    },

    isChapterExpanded(chapter) {
      return this.expandedChapters.some(c => String(c) === String(chapter))
    },

    getTotalReferences(book) {
      const found = this.bookCounts.find(b => b.book === book)
      return found ? found.count : 0
    },

    getChapterBreakdown() {
      return this.bookChapters
    },

    getSermons() {
      return this.bookSermons
    },

    formatTimestamp(seconds) {
      const h = Math.floor(seconds / 3600)
      const m = Math.floor((seconds % 3600) / 60)
      const s = Math.floor(seconds % 60)
      if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
      return `${m}:${String(s).padStart(2, '0')}`
    },

    async openTranscript(sermon) {
      this.transcriptModal.open = true
      this.transcriptModal.title = sermon.title
      this.transcriptModal.speaker = this.speakers[sermon.videoId] || 'Unknown'
      this.transcriptModal.date = sermon.date
      this.transcriptModal.videoUrl = sermon.url || sermon.watchUrl
      this.transcriptModal.videoId = sermon.videoId
      this.transcriptModal.loading = true
      this.transcriptModal.segments = []
      document.body.style.overflow = 'hidden'

      try {
        const rows = await execute(
          `SELECT text, start_time, vimeo_url FROM transcript_segments
           WHERE video_id = ? ORDER BY start_time`,
          [sermon.videoId]
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
.bible-heatmap-view {
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

.loading {
  text-align: center;
  padding: 40px;
  color: #31333F;
}

.testament-section {
  margin-bottom: 3rem;
}

.testament-section h3 {
  color: #31333F;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.heatmap-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  flex-wrap: nowrap;
}

.book-cell {
  flex: 1;
  min-width: 0;
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border: 1px solid #d3d8e0;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0.25rem;
}

.book-cell:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  z-index: 10;
}

.book-abbrev {
  font-size: 0.7rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 0.25rem;
  line-height: 1;
}

.book-count {
  font-size: 0.85rem;
  font-weight: 700;
  line-height: 1;
}

.heat-0 {
  background: #ffffff;
  color: #666;
  border: 1px solid #ddd;
}

.heat-1 {
  background: #f7fcf5;
  color: #31333F;
}

.heat-2 {
  background: #c7e9c0;
  color: #31333F;
}

.heat-3 {
  background: #74c476;
  color: #31333F;
}

.heat-4 {
  background: #31a354;
  color: white;
}

.heat-5 {
  background: #006d2c;
  color: white;
}

.legend {
  background: #f0f2f6;
  padding: 1rem;
  border-radius: 0.25rem;
  margin-bottom: 2rem;
}

.legend h4 {
  color: #31333F;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.legend-items {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-box {
  width: 30px;
  height: 30px;
  border: 1px solid #d3d8e0;
  border-radius: 0.25rem;
}

.book-details {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border: 1px solid #d3d8e0;
  border-radius: 0.5rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  z-index: 1000;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e6e9ef;
  background: #f0f2f6;
  position: sticky;
  top: 0;
  z-index: 10;
}

.details-header h3 {
  color: #31333F;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #31333F;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.25rem;
  transition: background 0.2s;
}

.close-btn:hover {
  background: #e6e9ef;
}

.details-content {
  padding: 1.5rem;
}

.details-summary {
  font-size: 1.1rem;
  color: #31333F;
  margin-bottom: 1.5rem;
}

.details-content h4 {
  color: #31333F;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 1.5rem 0 0.75rem 0;
}

.chapter-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.chapter-item {
  border-radius: 0.25rem;
  overflow: hidden;
  border: 1px solid #e6e9ef;
  background: white;
}

.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f0f2f6;
  cursor: pointer;
  transition: background 0.2s;
  user-select: none;
}

.chapter-header:hover {
  background: #e6e9ef;
}

.chapter-number {
  font-weight: 500;
  color: #31333F;
  flex: 1;
}

.chapter-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.chapter-count {
  color: #808495;
  font-size: 0.875rem;
}

.chapter-toggle {
  color: #31333F;
  font-size: 0.75rem;
  width: 16px;
  text-align: center;
  font-weight: bold;
}

.chapter-sermons {
  background: white;
  border-top: 1px solid #e6e9ef;
  padding: 0.5rem 0;
}

.chapter-sermon-item {
  display: flex;
  justify-content: space-between;
  align-items: start;
  padding: 0.75rem 1rem;
  gap: 1rem;
  transition: background 0.2s;
}

.chapter-sermon-item:hover {
  background: #fafbfc;
}

.sermon-content {
  flex: 1;
}

.chapter-sermon-item a {
  color: #0068c9;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.95rem;
  line-height: 1.4;
  display: block;
  margin-bottom: 0.25rem;
}

.chapter-sermon-item a:hover {
  color: #ff2b2b;
  text-decoration: underline;
}

.sermon-context {
  font-size: 0.85rem;
  color: #808495;
  line-height: 1.4;
  margin: 0;
  font-style: italic;
}

.sermon-date {
  color: #808495;
  font-size: 0.8rem;
  white-space: nowrap;
  line-height: 1.4;
}

.sermon-list .sermon-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f2f6;
}

.sermon-list .sermon-item a {
  color: #0068c9;
  text-decoration: none;
  font-weight: 500;
}

.sermon-list .sermon-item a:hover {
  color: #ff2b2b;
  text-decoration: underline;
}

.loading-sermons {
  text-align: center;
  padding: 1rem;
  color: #808495;
  font-size: 0.9rem;
}

.no-results {
  text-align: center;
  padding: 60px 20px;
  color: #31333F;
}

.sermon-title-link {
  color: #0068c9;
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
}

.sermon-title-link:hover {
  text-decoration: underline;
}

.sermon-actions {
  display: inline-flex;
  gap: 0.5rem;
  margin-left: 0.5rem;
}

.action-link {
  color: #0068c9;
  text-decoration: none;
  font-size: 0.85rem;
}

.action-link:hover {
  color: #ff2b2b;
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
  .heatmap-row {
    gap: 0.25rem;
  }

  .book-abbrev {
    font-size: 0.6rem;
  }

  .book-count {
    font-size: 0.7rem;
  }

  .legend-items {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
