import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/*.test.tsx"],
    reporters: ["default", "junit"],
    outputFile: `${process.env.QWS_EVIDENCE_DIR ?? "../evidence/checkpoint1c"}/vitest.xml`,
  },
});
