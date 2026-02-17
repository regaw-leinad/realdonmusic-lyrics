// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://lyrics.danwager.com",
  image: {
    service: { entrypoint: "astro/assets/services/noop" },
  },
  vite: {
    plugins: [tailwindcss()],
  },
  integrations: [sitemap()],
});
