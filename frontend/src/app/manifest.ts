import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'GraftAI',
    short_name: 'GraftAI',
    description: 'AI-powered scheduling that handles timezones, conflicts, and back-and-forth.',
    start_url: '/dashboard',
    display: 'standalone',
    background_color: '#FFFFFF',
    theme_color: '#FFFFFF',
    icons: [
      {
        src: '/icon.png',
        sizes: '192x192',
        type: 'image/png',
      },
      {
        src: '/icon.png',
        sizes: '512x512',
        type: 'image/png',
      },
    ],
  };
}
