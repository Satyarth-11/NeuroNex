import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Inside Docker network, backend service is at http://backend:8000
const backendTarget = process.env.BACKEND_URL || 'http://backend:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3001,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
})
