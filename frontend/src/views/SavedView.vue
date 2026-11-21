<template>
  <div class="page">
    <h2>Saved Sermons</h2>
    <p class="note">Saved on this device only. Use ☆ Save on any sermon page.</p>
    <div v-if="loading" class="state-msg">Loading...</div>
    <SermonList v-else :items="items" empty="No saved sermons yet." />
  </div>
</template>

<script>
import SermonList from '../components/SermonList.vue'
import { loadVideos } from '../lib/videos'
import { getFavorites } from '../lib/storage'

export default {
  name: 'SavedView',
  components: { SermonList },
  props: { speakers: { type: Object, required: true } },
  data() {
    return { loading: true, items: [] }
  },
  // Re-read on every visit (this view is not kept alive).
  async mounted() {
    try {
      const byId = new Map((await loadVideos()).map(v => [v.id, v]))
      this.items = getFavorites()
        .map(id => byId.get(id))
        .filter(Boolean)
        .map(v => ({ id: v.id, title: v.title, date: v.date, speaker: this.speakers[v.id] || '' }))
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
  margin-bottom: 0.5rem;
  color: #31333F;
  font-size: 2rem;
  font-weight: 600;
}

.note {
  color: #808495;
  margin-bottom: 1rem;
}

.state-msg {
  color: #808495;
  font-style: italic;
}
</style>
