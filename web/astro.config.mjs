// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://realstatepanama.com',
  redirects: { '/avances': '/interiores' },
  integrations: [sitemap({ filter: (p) => !p.includes('/avances') })],
  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'en'],
    routing: { prefixDefaultLocale: false },
  },
});
