/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Make the value compile-time from env; no localhost default in prod builds
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '', // leave empty if not provided
  },
};

module.exports = nextConfig;
