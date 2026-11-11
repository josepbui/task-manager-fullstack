/** @type {import('next').NextConfig} */
const nextConfig = {
  // ─── Transpile ESM-only packages ───────────────────────────────────────────
  transpilePackages: [
    "@lit-protocol/lit-node-client",
    "@lit-protocol/auth-helpers",
    "@irys/web-upload",
    "@irys/web-upload-ethereum",
  ],

  // ─── API Rewrites ──────────────────────────────────────────────────────────
  async rewrites() {
    return [
      {
        source: '/api/tasks/:path*',
        destination: 'http://127.0.0.1:8000/tasks/:path*',
      },
    ];
  },

  // ─── Webpack customisation ──────────────────────────────────────────────────
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Node built-ins referenced by crypto/wallet SDKs — exclude from browser bundle
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
        stream: false,
        path: false,
        os: false,
        http: false,
        https: false,
        zlib: false,
        child_process: false,
        worker_threads: false,
      };
    }

    // pdfjs-dist ships its own worker — prevent webpack from processing it
    config.module.rules.push({
      test: /pdf\.worker(\.(min))?\.m?js$/,
      type: "asset/resource",
    });

    return config;
  },

  // ─── Security headers ───────────────────────────────────────────────────────
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
};

export default nextConfig;

