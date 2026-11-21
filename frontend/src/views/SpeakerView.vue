<template>
  <div class="page">
    <router-link to="/speakers" class="back-link">← All speakers</router-link>
    <h2>{{ name }}</h2>
    <p v-if="!loading" class="stats">
      {{ items.length }} sermon{{ items.length === 1 ? '' : 's' }}<span v-if="range"> · {{ range }}</span>
    </p>
    <div v-if="loading" class="state-msg">Loading...</div>
    <template v-else>
      <input v-model="filter" type="text" placeholder="Filter this speaker's sermon titles" class="filter-input">
      <SermonList :items="shown" empty="No sermons match." />
    </template>
  </div>
</template>

<script>
import SermonList from '../components/SermonList.vue'
import { loadVideos } from '../lib/videos'

export default {
  name: 'SpeakerView',
  components: { SermonList },
  props: { speakers: { type: Object, required: true } },
  data() {
    return { loading: true, videos: [], filter: '' }
  },
  computed: {
    name() {
      return this.$route.params.name
    },
    items() {
      return this.videos
        .filter(v => this.speakers[v.id] === this.name)
        .map(v => ({ id: v.id, title: v.title, date: v.date }))
    },
    shown() {
      const f = this.filter.trim().toLowerCase()
      return f ? this.items.filter(s => s.title.toLowerCase().includes(f)) : this.items
    },
    range() {
      if (this.items.length === 0) return ''
      const first = this.items[this.items.length - 1].date.substring(0, 4)
      const last = this.items[0].date.substring(0, 4)
      return first === last ? first : `${first}–${last}`
    }
  },
  async mounted() {
    document.title = `${this.name} · HHBC Sermon Search`
    try {
      this.videos = await loadVideos()
    } catch (err) {
      console.error(err)
    }
    this.loading = false
  }
}
</script>

<style scoped>
.page {
  padding: 0 1rem 2rem;
}

.back-link {
  color: #0068c9;
  text-decoration: none;
  font-size: 0.95rem;
}

h2 {
  margin: 0.5rem 0 0.25rem;
  color: #31333F;
  font-size: 2rem;
  font-weight: 600;
}

.stats {
  color: #808495;
  margin-bottom: 1rem;
}

.filter-input {
  width: 100%;
  max-width: 24rem;
  padding: 0.55rem 0.75rem;
  border: 1px solid #d0d4dc;
  border-radius: 6px;
  font-size: 1rem;
  margin-bottom: 1rem;
}

.state-msg {
  color: #808495;
  font-style: italic;
}
</style>
