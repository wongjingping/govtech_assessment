/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Rewrites API requests to the backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: (process.env.API_URL || 'http://api:8000') + '/:path*',
      },
    ];
  }
};

module.exports = nextConfig; 