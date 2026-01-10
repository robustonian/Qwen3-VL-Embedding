import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, resolve(__dirname, '..'), '')
  const apiPort = env.VITE_API_PORT || '8000'
  const apiTarget = `http://localhost:${apiPort}`

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true
        },
        '/v1': {
          target: apiTarget,
          changeOrigin: true
        },
        '/files': {
          target: apiTarget,
          changeOrigin: true
        }
      }
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets'
    }
  }
})
