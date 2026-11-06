import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': { target: process.env.API_PROXY_TARGET || 'http://127.0.0.1:8000', changeOrigin: true } } },
  test: { environment: 'jsdom', globals: true, include: ['src/**/*.test.ts', 'src/**/*.test.tsx'] },
});
