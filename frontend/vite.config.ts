/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// The backend URL the dev server proxies /api to (docker-compose uses nginx instead).
const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Read VITE_* flags from the repo-root .env shared with the backend
  envDir: "..",
  server: {
    port: 5173,
    proxy: { "/api": { target: backendUrl, changeOrigin: true } },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
  },
});
