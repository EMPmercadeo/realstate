// Manifiesto en tiempo de build de los archivos opcionales de web/public/ (clips, fotos "después"…).
// Se pasa al cliente en un data-attribute para no sondear archivos inexistentes (404 en consola).
// Ojo: al empaquetar, import.meta.url apunta a dist/…, no a src/: se busca public/ desde la carpeta del
// proyecto (donde corre `astro build`) y, si no está, relativo a este archivo.
import { readdirSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

function carpetaPublica(): string | null {
  const candidatas = [join(process.cwd(), 'public'), join(process.cwd(), 'web', 'public')];
  try { candidatas.push(fileURLToPath(new URL('../../public/', import.meta.url))); } catch { /* sin URL de archivo */ }
  return candidatas.find((d) => existsSync(join(d, 'favicon.svg')) || existsSync(join(d, 'modelo'))) ?? null;
}

export function listarPublicos(...carpetas: string[]): string[] {
  const out: string[] = [];
  const pub = carpetaPublica();
  if (!pub) return out;
  for (const c of carpetas) {
    try {
      for (const f of readdirSync(join(pub, c))) if (!f.startsWith('.')) out.push(`/${c}/${f}`);
    } catch { /* carpeta ausente */ }
  }
  return out;
}
