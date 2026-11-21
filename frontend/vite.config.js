import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// VITE_BASE lets the same build target GitHub Pages ("/hhbc-sermon-search/")
// or a root-hosted site (Vercel, default "/").
export default defineConfig({
  base: process.env.VITE_BASE || '/',
  plugins: [vue()],
  server: { port: 8082 }
})
