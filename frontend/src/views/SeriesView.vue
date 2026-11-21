<template>
  <div class="page">
    <template v-if="current">
      <router-link to="/series" class="back-link">← All series</router-link>
      <h2>{{ current.name }}</h2>
      <p class="stats">{{ current.list.length }} sermons · {{ current.range }}</p>
      <SermonList :items="current.items" />
    </template>

    <template v-else>
      <h2>Sermon Series</h2>
      <input v-model="filter" type="text" placeholder="Filter series" class="filter-input">
      <div v-if="loading" class="state-msg">Loading...</div>
      <p v-else-if="routeName && !current" class="state-msg">Series not found.</p>
      <ul class="series-grid">
        <li v-for="s in shown" :key="s.name">
          <router-link :to="{ name: 'series', params: { name: s.name } }">
            <span class="name">{{ s.name }}</span>
            <span class="count">{{ s.count }} sermons · {{ s.range }}</span>
          </router-link>
        </li>
      </ul>
    </template>
  </div>
</template>

<script>
import SermonList from '../components/SermonList.vue'
import { loadVideos, groupSeries } from '../lib/videos'

function rangeOf(list) {
  const first = list[0].date.substring(0, 4)
  const last = list[list.length - 1].date.substring(0, 4)
  return first === last ? first : `${first}–${last}`
}

export default {
  name: 'SeriesView',
  components: { SermonList },
  props: { speakers: { type: Object, required: true } },
  data() {
    return { loading: true, series: new Map(), filter: '' }
  },
  computed: {
    routeName() {
      return this.$route.params.name || ''
    },
    current() {
      const list = this.series.get(this.routeName)
      if (!list) return null
      return {
        name: this.routeName,
        list,
        range: rangeOf(list),
        items: list.map(v => ({ id: v.id, title: v.title, date: v.date, speaker: this.speakers[v.id] || '' }))
      }
    },
    shown() {
      const f = this.filter.trim().toLowerCase()
      return [...this.series]
        .map(([name, list]) => ({ name, count: list.length, range: rangeOf(list), latest: list[list.length - 1].date }))
        .filter(s => !f || s.name.toLowerCase().includes(f))
        .sort((a, b) => b.latest.localeCompare(a.latest))
    }
  },
  async mounted() {
    try {
      this.series = groupSeries(await loadVideos())
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
  margin: 0.5rem 0 0.75rem;
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

.series-grid {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.5rem;
}

.series-grid a {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.6rem 0.8rem;
  border: 1px solid #e6e9ef;
  border-radius: 6px;
  text-decoration: none;
  color: #31333F;
}

.series-grid a:hover {
  border-color: #0068c9;
  background: #f8f9fb;
}

.count {
  color: #808495;
  font-size: 0.85rem;
}

.state-msg {
  color: #808495;
  font-style: italic;
}
</style>
