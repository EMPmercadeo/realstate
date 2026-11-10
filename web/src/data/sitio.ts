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

// Contacto para "Solicitar información". Se cambia aquí y todo el sitio lo usa.
//   whatsapp: solo dígitos con código de país, p. ej. '50760001234' (vacío = no se muestra)
//   correo:   adonde llegan las solicitudes del formulario de /contacto
//   envio:    servicio que entrega el formulario a ese correo sin abrir el programa de correo del visitante
//             (FormSubmit; la primera vez manda un correo de activación a `correo` y hay que aceptarlo).
//             Si falla o aún no está activado, el formulario abre el correo del visitante como respaldo.
export const CONTACTO = {
  whatsapp: '50763176183',
  correo: 'empsignature@gmail.com',
  // código que FormSubmit asigna al correo (va en lugar de la dirección, para no exponerla en el envío)
  envio: 'https://formsubmit.co/ajax/5c0d7c8c5e200c16b90d3ab694c8fed7',
  mensaje: 'Hola, me interesa la Residencia Altos de San Cristóbal (David, Chiriquí). ¿Me envían el expediente para inversionistas?',
};

export const hayContacto = !!(CONTACTO.whatsapp || CONTACTO.correo);

// Todos los botones "Solicitar información" llevan a la página del formulario.
export function enlaceContacto(): string {
  return '/contacto';
}

export function enlaceWhatsapp(texto = CONTACTO.mensaje): string {
  return CONTACTO.whatsapp ? `https://wa.me/${CONTACTO.whatsapp}?text=${encodeURIComponent(texto)}` : '';
}
