import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
    // SPA fallback: serve index.html for /admin and other routes
    historyApiFallback: true,
  },
  // Ensure /admin path resolves to index.html in preview too
  appType: 'spa',
})
