// Artículos publicables del blog: los marcados como `borrador: true` solo se ven en desarrollo.
import { getCollection } from 'astro:content';

export async function articulos() {
  const todos = await getCollection('blog', (p) => import.meta.env.DEV || !p.data.borrador);
  return todos.sort((a, b) => b.data.fecha.valueOf() - a.data.fecha.valueOf());
}

export const fechaLarga = (d: Date) =>
  d.toLocaleDateString('es-PA', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
