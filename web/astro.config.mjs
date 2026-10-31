// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  // TODO: dominio real de la clienta
  site: 'https://residencia-altos.example.com',
  integrations: [sitemap({ filter: (p) => !p.includes('/avances') })],
  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'en'],
    routing: { prefixDefaultLocale: false },
  },
});
