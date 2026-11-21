<template>
  <div id="app">
    <header>
      <router-link to="/"><img :src="logo" alt="HHBC Sermon Search" class="logo"></router-link>
      <button class="theme-toggle" :title="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'" @click="toggleTheme">
        {{ theme === 'dark' ? '☀' : '☾' }}
      </button>
    </header>

    <nav class="tabs">
      <router-link v-for="tab in tabs" :key="tab.to" :to="tab.to" class="tab" active-class="active" :exact-active-class="tab.exact ? 'active' : ''">
        {{ tab.name }}
      </router-link>
    </nav>

    <main>
      <router-view v-slot="{ Component }">
        <keep-alive include="SearchView,VideoListView,BibleHeatMapView">
          <component :is="Component" :speakers="speakers" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<script>
import logo from './assets/download.png'
import { getTheme, saveTheme } from './lib/storage'

export default {
  name: 'App',
  data() {
    return {
      logo,
      theme: 'light',
      tabs: [
        { to: '/', name: 'Home', exact: true },
        { to: '/videos', name: 'Video List' },
        { to: '/bible', name: 'Bible Heat Map' },
        { to: '/speakers', name: 'Speakers' },
        { to: '/series', name: 'Series' },
        { to: '/saved', name: 'Saved' }
      ],
      speakers: {}
    }
  },
  async mounted() {
    this.theme = getTheme()
    this.applyTheme()
    await this.loadSpeakers()
  },
  methods: {
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark'
      saveTheme(this.theme)
      this.applyTheme()
    },

    applyTheme() {
      document.documentElement.setAttribute('data-theme', this.theme)
    },

    async loadSpeakers() {
      try {
        const response = await fetch(`${import.meta.env.BASE_URL}data/speakers.json`)
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
  position: relative;
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
  text-decoration: none;
  white-space: nowrap;
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

.theme-toggle {
  position: absolute;
  top: 0.75rem;
  right: 0;
  background: none;
  border: 1px solid #d0d4dc;
  border-radius: 50%;
  width: 2.25rem;
  height: 2.25rem;
  font-size: 1.1rem;
  cursor: pointer;
  color: #31333F;
}

.theme-toggle:hover {
  border-color: #0068c9;
}

/* Dark mode: invert the whole page, then flip media back so images/video look normal. */
html[data-theme='dark'] {
  filter: invert(1) hue-rotate(180deg);
}

html[data-theme='dark'] img,
html[data-theme='dark'] video,
html[data-theme='dark'] iframe {
  filter: invert(1) hue-rotate(180deg);
}

/* The logo is one dark color on white, so let it invert with the page (light text, dark background). */
html[data-theme='dark'] .logo {
  filter: none;
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
    overflow-x: auto;
  }

  .tab {
    padding: 0.5rem 0.75rem;
    font-size: 0.9rem;
  }
}
</style>
