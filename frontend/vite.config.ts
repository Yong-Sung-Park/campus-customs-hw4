import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Native file events were sometimes missed on Windows (stale modules after edits); polling is reliable.
    watch: { usePolling: true, interval: 300 },
    // Forward API calls and product images to FastAPI so the browser sees one origin.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000',
    },
  },
})
