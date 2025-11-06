import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['mwseguro.dr00p3r.top'],
    port: 3000,
    host: true
  }
})
