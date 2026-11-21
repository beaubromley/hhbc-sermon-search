<template>
  <div class="page">
    <h2>Speakers</h2>
    <input v-model="filter" type="text" placeholder="Filter speakers" class="filter-input">
    <div v-if="loading" class="state-msg">Loading...</div>
    <ul v-else class="speaker-grid">
      <li v-for="s in shown" :key="s.name">
        <router-link :to="{ name: 'speaker', params: { name: s.name } }">
          <span class="name">{{ s.name }}</span>
          <span class="count">{{ s.count }} sermon{{ s.count === 1 ? '' : 's' }}</span>
        </router-link>
      </li>
      <li v-if="shown.length === 0" class="state-msg">No speakers match.</li>
    </ul>
  </div>
</template>

<script>
import { loadVideos } from '../lib/videos'

export default {
  name: 'SpeakersView',
  props: { speakers: { type: Object, required: true } },
  data() {
    return { filter: '', loading: true, ids: new Set() }
  },
  computed: {
    shown() {
      const counts = {}
      for (const [id, name] of Object.entries(this.speakers)) {
        if (!name || name === 'Unknown' || !this.ids.has(String(id))) continue
        counts[name] = (counts[name] || 0) + 1
      }
      const f = this.filter.trim().toLowerCase()
      return Object.entries(counts)
        .map(([name, count]) => ({ name, count }))
        .filter(s => !f || s.name.toLowerCase().includes(f))
        .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
    }
  },
  async mounted() {
    try {
      this.ids = new Set((await loadVideos()).map(v => v.id))
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

h2 {
  margin-bottom: 1rem;
  color: #31333F;
  font-size: 2rem;
  font-weight: 600;
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

.speaker-grid {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 0.5rem;
}

.speaker-grid a {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.6rem 0.8rem;
  border: 1px solid #e6e9ef;
  border-radius: 6px;
  text-decoration: none;
  color: #31333F;
}

.speaker-grid a:hover {
  border-color: #0068c9;
  background: #f8f9fb;
}

.count {
  color: #808495;
  font-size: 0.85rem;
  white-space: nowrap;
}

.state-msg {
  color: #808495;
  font-style: italic;
}
</style>
