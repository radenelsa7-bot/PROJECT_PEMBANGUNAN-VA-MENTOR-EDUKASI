import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Frontend jalan di http://localhost:5173, backend FastAPI di http://localhost:8000
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
});
