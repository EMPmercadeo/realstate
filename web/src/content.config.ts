import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * Blog multipaís. Cada post vive en src/content/blog/<pais>/<slug>.md
 * y el pipeline de generación (Python) escribe aquí por lotes.
 */
const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    titulo: z.string(),
    resumen: z.string().max(200),
    fecha: z.coerce.date(),
    pais: z.string(), // "Estados Unidos", "Canadá", "España", ...
    idioma: z.enum(['es', 'en']).default('es'),
    categoria: z.string().default('retiro-en-panama'),
    keywords: z.array(z.string()).default([]),
    buyerPersona: z.string().optional(),
    borrador: z.boolean().default(false),
  }),
});

export const collections = { blog };
