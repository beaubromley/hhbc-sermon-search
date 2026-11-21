<template>
  <ul class="sermon-list">
    <li v-for="s in items" :key="s.id" class="sermon-row">
      <span class="sermon-date">{{ s.date }}</span>
      <div class="sermon-main">
        <router-link :to="s.to || sermonRoute(s.id)" class="sermon-title">{{ s.title }}</router-link>
        <div class="sermon-sub">
          <router-link v-if="s.speaker" :to="{ name: 'speaker', params: { name: s.speaker } }">{{ s.speaker }}</router-link>
          <span v-if="s.note" class="sermon-note">{{ s.note }}</span>
        </div>
      </div>
    </li>
    <li v-if="items.length === 0" class="sermon-empty">{{ empty }}</li>
  </ul>
</template>

<script>
import { sermonRoute } from '../lib/links'

export default {
  name: 'SermonList',
  props: {
    items: { type: Array, required: true },
    empty: { type: String, default: 'Nothing here yet.' }
  },
  methods: { sermonRoute }
}
</script>

<style scoped>
.sermon-list {
  list-style: none;
  border-top: 1px solid #e6e9ef;
}

.sermon-row {
  display: flex;
  gap: 1rem;
  padding: 0.7rem 0.25rem;
  border-bottom: 1px solid #e6e9ef;
}

.sermon-row:hover {
  background: #f8f9fb;
}

.sermon-date {
  color: #808495;
  font-size: 0.9rem;
  white-space: nowrap;
  min-width: 5.8rem;
  padding-top: 2px;
}

.sermon-title {
  color: #0068c9;
  text-decoration: none;
  font-weight: 500;
}

.sermon-title:hover {
  text-decoration: underline;
}

.sermon-sub {
  font-size: 0.85rem;
  color: #808495;
  margin-top: 0.15rem;
}

.sermon-sub a {
  color: #808495;
  text-decoration: none;
}

.sermon-sub a:hover {
  text-decoration: underline;
}

.sermon-note {
  margin-left: 0.6rem;
}

.sermon-empty {
  padding: 1.5rem 0.25rem;
  color: #808495;
  font-style: italic;
}
</style>
