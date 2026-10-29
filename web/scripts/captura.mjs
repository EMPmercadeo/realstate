// Captura una vista del visor 3D sin cabeza.
// uso: node scripts/captura.mjs <url> <salida.jpg> [ancho] [alto]
import { chromium } from '/opt/npm-tools/node_modules/playwright/index.mjs';
import fs from 'node:fs';
const [url, out, w = '1600', h = '900'] = process.argv.slice(2);
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
page.on('pageerror', (e) => console.error('pageerror', e.message));
page.on('console', (m) => { if (m.type() === 'error') console.error('console', m.text()); });
await page.goto(url, { waitUntil: 'load', timeout: 120000 });
await page.waitForFunction(() => window.__done === true, null, { timeout: 240000 });
const data = await page.evaluate(() => window.__snap());
fs.writeFileSync(out, Buffer.from(data.split(',')[1], 'base64'));
console.log('ok', out);
await browser.close();
