// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://realstatepanama.com',
  redirects: { '/avances': '/interiores' },
  integrations: [// el índice del blog sale del sitemap mientras no haya artículos publicados (hoy va con noindex)
  sitemap({ filter: (p) => !p.includes('/avances') && !/\/blog\/?$/.test(p) })],
  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'en'],
    routing: { prefixDefaultLocale: false },
  },
});
