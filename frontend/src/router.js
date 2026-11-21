import { createRouter, createWebHashHistory } from 'vue-router'
import SearchView from './views/SearchView.vue'
import VideoListView from './views/VideoListView.vue'
import BibleHeatMapView from './views/BibleHeatMapView.vue'

// Hash history keeps every URL working on static hosting (no server rewrites needed).
export default createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'search', component: SearchView },
    { path: '/videos', name: 'videos', component: VideoListView },
    { path: '/bible', name: 'bible', component: BibleHeatMapView },
    { path: '/speakers', name: 'speakers', component: () => import('./views/SpeakersView.vue') },
    { path: '/speaker/:name', name: 'speaker', component: () => import('./views/SpeakerView.vue') },
    { path: '/series/:name?', name: 'series', component: () => import('./views/SeriesView.vue') },
    { path: '/saved', name: 'saved', component: () => import('./views/SavedView.vue') },
    { path: '/sermon/:id', name: 'sermon', component: () => import('./views/SermonView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ],
  scrollBehavior(to, from, saved) {
    if (saved) return saved
    return { top: 0 }
  }
})
