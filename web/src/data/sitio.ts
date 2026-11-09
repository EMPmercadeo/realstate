// Navegación del sitio y datos de contacto: un solo lugar para el menú de todas las páginas.

export const MENU = [
  { href: '/recorrido', t: 'Recorrido 3D' },
  { href: '/360', t: 'Vista 360°' },
  { href: '/interiores', t: 'Interiores y planos' },
  { href: '/#proyecto', t: 'El proyecto' },
] as const;

export const MENU_PIE = [
  { href: '/fotos', t: 'Recorrido en fotos' },
  { href: '/blog', t: 'Blog' },
] as const;

// Contacto para "Solicitar información". Se llena aquí y todo el sitio lo usa.
//   whatsapp: solo dígitos con código de país, p. ej. '50760001234'
//   correo:   p. ej. 'ventas@realstatepanama.com'
export const CONTACTO = {
  whatsapp: '',
  correo: '',
  mensaje: 'Hola, me interesa la Residencia Altos de San Cristóbal (David, Chiriquí). ¿Me envían el expediente para inversionistas?',
};

export const hayContacto = !!(CONTACTO.whatsapp || CONTACTO.correo);

export function enlaceContacto(): string {
  if (CONTACTO.whatsapp) return `https://wa.me/${CONTACTO.whatsapp}?text=${encodeURIComponent(CONTACTO.mensaje)}`;
  if (CONTACTO.correo) return `mailto:${CONTACTO.correo}?subject=${encodeURIComponent('Residencia Altos de San Cristóbal · expediente')}&body=${encodeURIComponent(CONTACTO.mensaje)}`;
  return '/#inversionistas';
}
