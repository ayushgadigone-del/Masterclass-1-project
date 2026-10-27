/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export — enables `next build` to produce a plain HTML/CSS/JS site
  // that can be hosted on GitHub Pages (or any static host) with no Node server.
  output: "export",

  // GitHub Pages serves from /legal-rights-navigator/ (the repo name).
  // In local dev (no BASE_PATH set) this is empty so localhost:3000 still works.
  basePath: process.env.BASE_PATH ?? "",
  assetPrefix: process.env.BASE_PATH ?? "",

  // Static export does not support the built-in Image Optimization API.
  images: { unoptimized: true },

  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  },
};

module.exports = nextConfig;
