<template>
  <div class="sermon-view">
    <button class="back-link" @click="goBack">← Back</button>

    <div v-if="error" class="state-msg">{{ error }}</div>
    <div v-else-if="!video" class="state-msg">Loading sermon...</div>

    <template v-else>
      <header class="sermon-head">
        <h2>{{ video.title }}</h2>
        <div class="sermon-meta">
          <router-link v-if="speaker" :to="{ name: 'speaker', params: { name: speaker } }">{{ speaker }}</router-link>
          <span v-if="speaker"> · </span>{{ video.date }}
          <span v-if="video.duration"> · {{ Math.round(video.duration / 60) }} min</span>
          <span> · </span><a :href="vimeoUrl" target="_blank">Open on Vimeo ↗</a>
        </div>
        <div class="sermon-actions">
          <button @click="toggleSaved">{{ saved ? '★ Saved' : '☆ Save' }}</button>
          <button @click="shareMoment(currentTime, 'now')">{{ copied === 'now' ? '✓ Link copied' : '🔗 Share this moment' }}</button>
          <button v-if="segments.length" @click="copyTranscript">{{ copied === 'text' ? '✓ Copied' : 'Copy Transcript' }}</button>
        </div>
        <div v-if="series" class="series-nav">
          Series:
          <router-link :to="{ name: 'series', params: { name: series.name } }">{{ series.name }}</router-link>
          ({{ series.index + 1 }} of {{ series.total }})
          <router-link v-if="series.prev" :to="sermonRoute(series.prev.id)">← Previous</router-link>
          <router-link v-if="series.next" :to="sermonRoute(series.next.id)">Next →</router-link>
        </div>
      </header>

      <div class="layout">
        <div class="player-col">
          <div ref="playerEl" class="player"></div>
          <p v-if="playerFailed" class="player-fallback">
            This video can't be embedded here. <a :href="vimeoUrl" target="_blank">Watch it on Vimeo ↗</a>
          </p>
          <label class="follow"><input type="checkbox" v-model="follow"> Follow along in transcript</label>
          <p class="player-hint">Video not loading? <a :href="vimeoUrl" target="_blank">Open it on Vimeo ↗</a></p>

          <div v-if="related.length" class="related">
            <h3>Related sermons</h3>
            <SermonList :items="related" />
          </div>
        </div>

        <div class="transcript-col">
          <div v-if="loadingSegments" class="state-msg">Loading transcript...</div>
          <div v-else ref="transcriptEl" class="transcript">
            <div
              v-for="(seg, i) in segments"
              :key="seg.start_time"
              :ref="el => { if (el) lineEls[i] = el }"
              class="line"
              :class="{ active: i === activeIndex, target: i === targetIndex }"
            >
              <a href="#" class="time" @click.prevent="seek(seg.start_time)">{{ formatTimestamp(seg.start_time) }}</a>
              <span class="text" v-html="highlight(seg.text, query)"></span>
              <button class="share" title="Copy link to this moment" @click.stop="shareMoment(seg.start_time, i)">
                {{ copied === i ? '✓' : '🔗' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import Player from '@vimeo/player'
import SermonList from '../components/SermonList.vue'
import { execute, fetchTranscript } from '../tursoClient'
import { loadVideos, groupSeries } from '../lib/videos'
import { highlight } from '../lib/highlight'
import { formatTimestamp } from '../format'
import { isFavorite, toggleFavorite } from '../lib/storage'
import { sermonRoute, sermonUrl, copyText } from '../lib/links'

export default {
  name: 'SermonView',
  components: { SermonList },
  props: {
    speakers: { type: Object, required: true }
  },
  data() {
    return {
      video: null,
      allVideos: [],
      segments: [],
      loadingSegments: true,
      related: [],
      error: '',
      playerFailed: false,
      follow: true,
      activeIndex: -1,
      targetIndex: -1,
      currentTime: 0,
      saved: false,
      copied: null,
      lineEls: []
    }
  },
  computed: {
    id() {
      return String(this.$route.params.id)
    },
    query() {
      return this.$route.query.q || ''
    },
    speaker() {
      return this.speakers[this.id] || ''
    },
    vimeoUrl() {
      return `https://vimeo.com/${this.id}`
    },
    series() {
      if (!this.video || !this.video.series) return null
      const list = groupSeries(this.allVideos).get(this.video.series)
      if (!list) return null
      const index = list.findIndex(v => v.id === this.id)
      return {
        name: this.video.series,
        total: list.length,
        index,
        prev: index > 0 ? list[index - 1] : null,
        next: index < list.length - 1 ? list[index + 1] : null
      }
    }
  },
  watch: {
    // Navigating sermon -> sermon (series next/prev, related) reuses this component.
    id() {
      this.load()
    },
    '$route.query.t'() {
      this.applyTarget(true)
    }
  },
  mounted() {
    this.load()
  },
  beforeUnmount() {
    this.destroyPlayer()
  },
  methods: {
    formatTimestamp,
    highlight,
    sermonRoute,

    goBack() {
      if (window.history.length > 1) this.$router.back()
      else this.$router.push('/')
    },

    async load() {
      this.destroyPlayer()
      this.error = ''
      this.video = null
      this.segments = []
      this.related = []
      this.lineEls = []
      this.loadingSegments = true
      this.activeIndex = -1
      this.targetIndex = -1
      this.saved = isFavorite(this.id)

      try {
        this.allVideos = await loadVideos()
        this.video = this.allVideos.find(v => v.id === this.id) || null
        if (!this.video) {
          this.error = 'Sermon not found.'
          return
        }
        document.title = `${this.video.title} · HHBC Sermon Search`
        this.loadRelated()
        this.segments = await fetchTranscript(this.id)
      } catch (err) {
        console.error('Sermon load error:', err)
        this.error = 'Could not load this sermon. Please try again.'
        return
      } finally {
        this.loadingSegments = false
      }

      await this.$nextTick()
      this.initPlayer()
      this.applyTarget(false)
    },

    async loadRelated() {
      try {
        const rows = await execute(
          `SELECT br.video_id, COUNT(DISTINCT br.book || ':' || br.chapter) AS shared
           FROM bible_references br
           JOIN (SELECT DISTINCT book, chapter FROM bible_references
                 WHERE video_id = ? AND chapter IS NOT NULL) mine
             ON mine.book = br.book AND mine.chapter = br.chapter
           WHERE br.video_id != ?
           GROUP BY br.video_id
           ORDER BY shared DESC, br.video_id DESC
           LIMIT 8`,
          [this.id, this.id]
        )
        const byId = new Map(this.allVideos.map(v => [v.id, v]))
        this.related = rows
          .map(r => byId.get(String(r.video_id)) && {
            id: String(r.video_id),
            title: byId.get(String(r.video_id)).title,
            date: byId.get(String(r.video_id)).date,
            speaker: this.speakers[String(r.video_id)] || '',
            note: `${r.shared} shared passage${r.shared === 1 ? '' : 's'}`
          })
          .filter(Boolean)
      } catch (err) {
        console.warn('Related sermons failed:', err)
      }
    },

    initPlayer() {
      if (!this.$refs.playerEl) return
      try {
        this.player = new Player(this.$refs.playerEl, { id: Number(this.id), responsive: true })
        this.player.on('timeupdate', data => this.onTime(data.seconds))
        this.player.on('seeked', data => this.onTime(data.seconds))
        this.player.on('error', () => { this.playerFailed = true })
        this.player.ready().then(() => {
          const t = Number(this.$route.query.t)
          if (t) this.player.setCurrentTime(t).catch(() => {})
        }).catch(() => { this.playerFailed = true })
      } catch (err) {
        console.warn('Player init failed:', err)
        this.playerFailed = true
      }
    },

    destroyPlayer() {
      if (this.player) {
        try { this.player.destroy() } catch { /* already gone */ }
        this.player = null
      }
    },

    // Last transcript line that has started by `seconds`.
    indexAt(seconds) {
      let lo = 0
      let hi = this.segments.length - 1
      let found = -1
      while (lo <= hi) {
        const mid = (lo + hi) >> 1
        if (this.segments[mid].start_time <= seconds + 0.25) {
          found = mid
          lo = mid + 1
        } else {
          hi = mid - 1
        }
      }
      return found
    },

    onTime(seconds) {
      this.currentTime = seconds
      const idx = this.indexAt(seconds)
      if (idx === this.activeIndex) return
      this.activeIndex = idx
      if (this.follow && idx >= 0) this.scrollToLine(idx)
    },

    scrollToLine(idx) {
      const container = this.$refs.transcriptEl
      const el = this.lineEls[idx]
      if (!container || !el) return
      container.scrollTo({ top: el.offsetTop - container.clientHeight / 2, behavior: 'smooth' })
    },

    // Honour ?t= : highlight and scroll to that line, and cue the player there.
    applyTarget(cue) {
      const t = Number(this.$route.query.t)
      if (!t || this.segments.length === 0) {
        this.targetIndex = -1
        return
      }
      this.targetIndex = this.indexAt(t)
      this.$nextTick(() => this.scrollToLine(this.targetIndex))
      if (cue && this.player) this.player.setCurrentTime(t).catch(() => {})
    },

    seek(seconds) {
      if (!this.player) return
      this.onTime(seconds)
      this.player.setCurrentTime(seconds)
        .then(() => this.player.play().catch(() => { /* autoplay blocked: viewer can press play */ }))
        .catch(() => { this.playerFailed = true })
    },

    async shareMoment(seconds, marker) {
      await copyText(sermonUrl(this.id, seconds))
      this.copied = marker
      setTimeout(() => { this.copied = null }, 1500)
    },

    async copyTranscript() {
      await copyText(this.segments.map(s => s.text).join(' '))
      this.copied = 'text'
      setTimeout(() => { this.copied = null }, 1500)
    },

    toggleSaved() {
      this.saved = toggleFavorite(this.id)
    }
  }
}
</script>

<style scoped>
.sermon-view {
  padding: 0 1rem 2rem;
}

.back-link {
  background: none;
  border: none;
  color: #0068c9;
  cursor: pointer;
  font-size: 0.95rem;
  padding: 0.25rem 0;
  margin-bottom: 0.75rem;
}

.back-link:hover {
  text-decoration: underline;
}

.state-msg {
  color: #808495;
  font-style: italic;
  padding: 1rem 0;
}

h2 {
  font-size: 1.6rem;
  color: #31333F;
  margin-bottom: 0.35rem;
}

.sermon-meta {
  color: #808495;
  margin-bottom: 0.75rem;
}

.sermon-meta a {
  color: #0068c9;
  text-decoration: none;
}

.sermon-meta a:hover {
  text-decoration: underline;
}

.sermon-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.sermon-actions button {
  background: none;
  border: 1px solid #0068c9;
  color: #0068c9;
  padding: 0.3rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.sermon-actions button:hover {
  background: #0068c9;
  color: #fff;
}

.series-nav {
  font-size: 0.9rem;
  color: #808495;
  margin-bottom: 1rem;
}

.series-nav a {
  color: #0068c9;
  text-decoration: none;
  margin-left: 0.5rem;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 5fr) minmax(0, 6fr);
  gap: 1.5rem;
  align-items: start;
}

.player-col {
  position: sticky;
  top: 0.5rem;
  max-height: calc(100vh - 1rem);
  overflow-y: auto;
  background: #fff;
}

.player {
  background: #000;
  border-radius: 6px;
  overflow: hidden;
  min-height: 120px;
}

.player-fallback {
  margin-top: 0.5rem;
  color: #808495;
}

.follow {
  display: block;
  margin: 0.6rem 0 1rem;
  font-size: 0.9rem;
  color: #31333F;
}

.player-hint {
  font-size: 0.85rem;
  color: #808495;
  margin: -0.5rem 0 1rem;
}

.player-hint a {
  color: #0068c9;
}

.related h3 {
  font-size: 1.05rem;
  margin: 0.5rem 0;
  color: #31333F;
}

.transcript {
  max-height: calc(100vh - 8rem);
  overflow-y: auto;
  border: 1px solid #e6e9ef;
  border-radius: 6px;
  padding: 0.5rem;
  position: relative;
}

.line {
  display: flex;
  gap: 0.75rem;
  padding: 0.35rem 0.5rem;
  border-radius: 4px;
  line-height: 1.6;
  font-size: 0.95rem;
}

.line:hover {
  background: #f8f9fb;
}

.line.active {
  background: #e8f1fb;
}

.line.target {
  background: #fff4c2;
}

.time {
  color: #0068c9;
  text-decoration: none;
  font-family: monospace;
  font-size: 0.8rem;
  padding-top: 3px;
  white-space: nowrap;
  flex-shrink: 0;
}

.time:hover {
  text-decoration: underline;
}

.text {
  flex: 1;
}

.text :deep(strong) {
  color: #d63200;
  font-weight: 700;
}

.share {
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.line:hover .share,
.share:focus {
  opacity: 1;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .player-col {
    position: static;
    max-height: none;
  }

  .transcript {
    max-height: 60vh;
  }

  .share {
    opacity: 1;
  }
}
</style>
