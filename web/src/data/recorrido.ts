// Paradas del recorrido cinematográfico (scroll-world).
// Cada parada tiene una foto real ("antes") y, cuando exista, la imagen "después"
// generada con Nano Banana. Si en /clips/<id>.mp4 hay un video, el motor lo usa
// como vuelo de cámara (scrub por scroll) en lugar de la transición de fotos.
//
// Convenciones de archivos (todo en web/public/):
//   fotos-reales/<archivo>.jpg      foto real (antes)
//   fotos-despues/<archivo>.jpg     imagen "así quedará" (después)
//   clips/<id>.mp4                  clip 16:9 (escritorio)   — opcional
//   clips/<id>-m.mp4                clip 9:16 (móvil)        — opcional
//   clips/<id>-despues-m.jpg        póster vertical          — opcional

export interface Parada {
  id: string;
  etiqueta: string;          // nombre corto en la ruta / nav
  eyebrow: string;
  titulo: string;
  texto: string;
  tags?: string[];
  antes: string;             // ruta de la foto real
  despues?: string;          // ruta de la imagen "después" (se detecta si existe)
  acento?: string;           // color de acento de la parada
  scroll?: number;           // alturas de pantalla que dura la parada (default 1.35)
  posicion?: string;         // object-position de la imagen (p. ej. "center 40%")
  cta?: { principal: { label: string; href: string }; secundaria?: { label: string; href: string } };
}

export const PARADAS: Parada[] = [
  {
    id: 'llegada',
    etiqueta: 'Llegada',
    eyebrow: 'Altos de San Cristóbal · David, Chiriquí',
    titulo: 'Una residencia de retiro lista para abrir.',
    texto: 'Dos edificios y 2.500 m² cercados, a minutos del centro de David. Haz scroll para recorrer el proyecto terminado.',
    tags: ['2.500 m²', '27 residentes', 'Llave en mano'],
    antes: '/fotos-reales/fachada-frontal.jpg',
    despues: '/fotos-despues/fachada.jpg',
    acento: '#c99a3c',
    scroll: 1.6,
    posicion: 'center 55%',
  },
  {
    id: 'entrada',
    etiqueta: 'Entrada',
    eyebrow: 'Casa principal',
    titulo: 'Entrada techada, sin escalones.',
    texto: 'El porche de arcos recibe a familiares y ambulancias bajo techo. Rampa, pasamanos y señalización para movilidad reducida.',
    tags: ['Rampa de acceso', 'Descenso cubierto', 'Portón eléctrico'],
    antes: '/fotos-reales/porche-arcos.jpg',
    despues: '/fotos-despues/porche.jpg',
    acento: '#c99a3c',
  },
  {
    id: 'recepcion',
    etiqueta: 'Recepción',
    eyebrow: 'Primer nivel',
    titulo: 'Recepción, consultorio y terapia.',
    texto: 'Admisión, consultorio médico y sala de terapia física en el mismo nivel, con baño accesible y pasillos amplios.',
    tags: ['Consultorio', 'Terapia física', 'Baño accesible'],
    antes: '/fotos-antes/recepcion.jpg',
    despues: '/fotos-despues/recepcion.jpg',
    acento: '#2c6b50',
  },
  {
    id: 'comedor',
    etiqueta: 'Comedor',
    eyebrow: 'Casa principal',
    titulo: 'Comedor y cocina para 27 residentes.',
    texto: 'Mesas para cuatro con espacio de silla de ruedas, cocina industrial contigua y área de refrigerios en el piso alto.',
    tags: ['Cocina equipada', 'Refrigerios', 'Luz natural'],
    antes: '/fotos-antes/comedor.jpg',
    despues: '/fotos-despues/comedor.jpg',
    acento: '#2c6b50',
  },
  {
    id: 'edificio-gris',
    etiqueta: 'Hospitalización',
    eyebrow: 'Segundo edificio',
    titulo: 'El edificio de hospitalización.',
    texto: 'Dos niveles, cuatro salas y terraza con baranda. Pensado para cuidado continuo con estación de enfermería en cada piso.',
    tags: ['24 camas', '4 salas', 'Enfermería 24 h'],
    antes: '/fotos-reales/edificio-gris.jpg',
    despues: '/fotos-despues/edificio-gris.jpg',
    acento: '#3b6ea5',
    posicion: 'center 45%',
  },
  {
    id: 'hospitalizacion',
    etiqueta: 'Salas',
    eyebrow: 'Sala #1 · 10 camas',
    titulo: 'Camas hospitalarias con luz propia.',
    texto: 'Cada cama con rieles, mesa de noche, panel de luz LED y cortina de privacidad. Estación de enfermería a la vista.',
    tags: ['Rieles y ruedas', 'Oxígeno', 'Timbre por cama'],
    antes: '/fotos-antes/hospitalizacion.jpg',
    despues: '/fotos-despues/hospitalizacion.jpg',
    acento: '#3b6ea5',
  },
  {
    id: 'terraza',
    etiqueta: 'Terraza',
    eyebrow: 'Piso alto',
    titulo: 'Terraza de refrigerios y descanso.',
    texto: 'Techada y ventilada, con vista a los jardines. Para merendar, recibir visitas y tomar el sol de la tarde.',
    tags: ['Techada', 'Vista al jardín', 'Baranda'],
    antes: '/fotos-antes/terraza.jpg',
    despues: '/fotos-despues/terraza.jpg',
    acento: '#c99a3c',
  },
  {
    id: 'jardin',
    etiqueta: 'Jardín',
    eyebrow: 'Jardín central',
    titulo: 'Gazebo, huerto y terapia acuática.',
    texto: 'Un campus al aire libre: gazebo de juegos, huerto cercado y piscina de terapia. Todo dentro de un terreno de 2.500 m².',
    tags: ['Gazebo', 'Huerto', 'Terapia acuática'],
    antes: '/fotos-antes/gazebo.jpg',
    despues: '/fotos-despues/gazebo.jpg',
    acento: '#2c6b50',
    scroll: 1.6,
    cta: {
      principal: { label: 'Solicitar expediente', href: '#inversionistas' },
      secundaria: { label: 'Ver datos del proyecto', href: '#proyecto' },
    },
  },
];
