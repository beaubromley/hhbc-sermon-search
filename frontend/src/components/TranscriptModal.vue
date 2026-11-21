<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <div>
          <h3>{{ video.title }}</h3>
          <div class="modal-meta">
            {{ video.speaker }} — {{ video.date }}
            <a :href="video.videoUrl" target="_blank" class="modal-watch">▶ Watch</a>
            <button v-if="segments.length" @click="copyTranscript" class="modal-copy">{{ copied ? '✓ Copied' : 'Copy Transcript' }}</button>
          </div>
        </div>
        <button @click="$emit('close')" class="modal-close">✕</button>
      </div>
      <div class="modal-body">
        <div v-if="loading" class="context-loading">Loading transcript...</div>
        <div v-else class="transcript-flow">
          <div v-for="seg in segments" :key="seg.start_time" class="transcript-line">
            <a :href="seg.vimeo_url" target="_blank" class="transcript-time">{{ formatTimestamp(seg.start_time) }}</a>
            <span v-if="highlight" v-html="highlight(seg.text)"></span>
            <span v-else>{{ seg.text }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { fetchTranscript } from '../tursoClient'
import { formatTimestamp } from '../format'

// Full-transcript reader shared by every tab.
// Props: video {title, speaker, date, videoUrl, videoId}; optional highlight(text) -> HTML.
export default {
  name: 'TranscriptModal',
  props: {
    video: { type: Object, required: true },
    highlight: { type: Function, default: null }
  },
  emits: ['close'],
  data() {
    return { segments: [], loading: true, copied: false }
  },
  async mounted() {
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', this.onKeydown)
    try {
      this.segments = await fetchTranscript(this.video.videoId)
    } catch (err) {
      console.error('Transcript load error:', err)
    }
    this.loading = false
  },
  beforeUnmount() {
    document.body.style.overflow = ''
    document.removeEventListener('keydown', this.onKeydown)
  },
  methods: {
    formatTimestamp,
    onKeydown(e) {
      if (e.key === 'Escape') this.$emit('close')
    },
    async copyTranscript() {
      const text = this.segments.map(s => s.text).join(' ')
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
      this.copied = true
      setTimeout(() => { this.copied = false }, 1500)
    }
  }
}
</script>

<style scoped>
.context-loading {
  color: #808495;
  font-style: italic;
  font-size: 0.9rem;
}

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
  .modal-overlay {
    padding: 1rem;
  }

  .modal-content {
    max-height: 90vh;
  }
}
</style>
