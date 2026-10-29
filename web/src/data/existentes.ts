// Manifiesto en tiempo de build de los archivos opcionales de web/public/ (clips, fotos "después"…).
// Se pasa al cliente en un data-attribute para no sondear archivos inexistentes (404 en consola).
import { readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export function listarPublicos(...carpetas: string[]): string[] {
  const out: string[] = [];
  for (const c of carpetas) {
    try {
      const dir = fileURLToPath(new URL(`../../public/${c}/`, import.meta.url));
      for (const f of readdirSync(dir)) if (!f.startsWith('.')) out.push(`/${c}/${f}`);
    } catch { /* carpeta ausente */ }
  }
  return out;
}
