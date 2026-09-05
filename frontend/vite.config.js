import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // PyWebView loads the built index.html straight off disk (file://), not from
  // an HTTP server, so asset paths must be relative to dist/, not site-root-absolute.
  base: './',
  server: {
    port: 5180,
    strictPort: true,
  },
})
