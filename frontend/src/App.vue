<template>
  <div id="app">
    <header>
      <img src="./assets/download.png" alt="HHBC Sermon Search" class="logo" v-if="logoExists">
      <h1 v-else>HHBC Sermon Search</h1>
    </header>

    <nav class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab', { active: currentTab === tab.id }]"
        @click="currentTab = tab.id"
      >
        {{ tab.name }}
      </button>
    </nav>

    <main>
      <SearchView v-if="currentTab === 'search'" :speakers="speakers" />
      <VideoListView v-if="currentTab === 'videos'" :speakers="speakers" />
      <BibleHeatMapView v-if="currentTab === 'bible'" :speakers="speakers" />
    </main>
  </div>
</template>

<script>
import SearchView from './views/SearchView.vue'
import VideoListView from './views/VideoListView.vue'
import BibleHeatMapView from './views/BibleHeatMapView.vue'

export default {
  name: 'App',
  components: {
    SearchView,
    VideoListView,
    BibleHeatMapView
  },
  data() {
    return {
      currentTab: 'search',
      logoExists: false,
      tabs: [
        { id: 'search', name: 'Home' },
        { id: 'videos', name: 'Video List' },
        { id: 'bible', name: 'Bible Heat Map' }
      ],
      speakers: {}
    }
  },
  async mounted() {
    this.checkLogo()
    await this.loadSpeakers()

    // If URL has search params, ensure we're on the search tab
    const params = new URLSearchParams(window.location.search)
    if (params.get('q')) {
      this.currentTab = 'search'
    }
  },
  methods: {
    checkLogo() {
      const img = new Image()
      img.onload = () => { this.logoExists = true }
      img.onerror = () => { this.logoExists = false }
      img.src = require('./assets/download.png')
    },

    async loadSpeakers() {
      try {
        const basePath = process.env.NODE_ENV === 'production' ? '/hhbc-sermon-search/' : '/'
        const response = await fetch(`${basePath}data/speakers.json`)
        if (response.ok) {
          this.speakers = await response.json()
        }
      } catch (error) {
        console.warn('Could not load speakers.json:', error)
      }
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: "Source Sans Pro", -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: #ffffff;
  color: #262730;
}

#app {
  max-width: 100%;
  margin: 0 auto;
  padding: 1rem 2rem;
  background-color: white;
  min-height: 100vh;
}

header {
  text-align: center;
  padding: 1rem 0 2rem 0;
  border-bottom: 1px solid #e6e9ef;
}

.logo {
  max-width: 800px;
  width: 100%;
  height: auto;
}

h1 {
  color: #1f77b4;
  font-size: 2.5rem;
  font-weight: 700;
}

.tabs {
  display: flex;
  gap: 0;
  padding: 0;
  margin: 1.5rem 0;
  border-bottom: 1px solid #e6e9ef;
}

.tab {
  padding: 0.75rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 400;
  color: #31333F;
  transition: all 0.2s;
  font-family: "Source Sans Pro", sans-serif;
}

.tab:hover {
  color: #ff2b2b;
  border-bottom-color: #ff2b2b;
}

.tab.active {
  color: #ff2b2b;
  border-bottom-color: #ff2b2b;
  font-weight: 600;
}

main {
  padding: 0;
  max-width: 100%;
}

@media (max-width: 768px) {
  #app {
    padding: 0.5rem 0.75rem;
  }

  header {
    padding: 0.5rem 0 1rem 0;
  }

  .tabs {
    margin: 0.75rem 0;
  }

  .tab {
    padding: 0.5rem 0.75rem;
    font-size: 0.9rem;
  }
}
</style>
