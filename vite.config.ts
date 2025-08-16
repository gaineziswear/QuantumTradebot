import { defineConfig, Plugin } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { createServer } from "./server";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    proxy: {
      // Proxy API calls to Python backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // Proxy WebSocket connections
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      }
    },
    fs: {
      allow: ["./client", "./shared", "./src"],
      deny: [".env", ".env.*", "*.{crt,pem}", "**/.git/**", "server/**"],
    },
  },
  build: {
    outDir: "dist/spa",
    rollupOptions: {
      output: {
        manualChunks: {
          // Core React libraries
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],

          // UI component libraries
          'ui-vendor': [
            '@radix-ui/react-dialog',
            '@radix-ui/react-tabs',
            '@radix-ui/react-toast',
            '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-popover',
            '@radix-ui/react-select'
          ],

          // Chart and visualization libraries
          'chart-vendor': ['recharts', 'framer-motion'],

          // Utility libraries
          'utils-vendor': [
            'clsx',
            'tailwind-merge',
            'date-fns',
            'lucide-react'
          ],

          // Query and state management
          'query-vendor': ['@tanstack/react-query']
        }
      }
    },
    chunkSizeWarningLimit: 600, // Slightly higher limit for crypto trading app
    sourcemap: false, // Disable sourcemaps in production for smaller builds
  },
  plugins: [react(), expressPlugin()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./client"),
      "@shared": path.resolve(__dirname, "./shared"),
    },
  },
}));

function expressPlugin(): Plugin {
  return {
    name: "express-plugin",
    apply: "serve", // Only apply during development (serve mode)
    configureServer(viteServer) {
      const app = createServer();

      // Add Express app as middleware to Vite dev server
      viteServer.middlewares.use(app);

      console.log('🚀 Express server with SSE support integrated');
    },
  };
}
