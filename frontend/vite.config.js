import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Allow the Google OAuth popup to communicate with the opener window.
    // Without this, Chrome logs repeated "Cross-Origin-Opener-Policy would
    // block the window.closed call" warnings during the OAuth popup flow.
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin-allow-popups',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.js'],
  },
})
