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
    tags: ['2.500 m²', '26 camas', 'Llave en mano'],
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
    texto: 'El porche de arcos recibe a familiares y ambulancias bajo techo. Rampas con baranda, descansos accesibles y estacionamiento para personas con movilidad reducida.',
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
    texto: 'Recepción las 24 horas, consultorio de salud y sala de terapia con familiares en el mismo nivel, con talleres y pasillos amplios.',
    tags: ['Recepción 24 h', 'Consultorio', 'Terapia con familiares'],
    antes: '/fotos-antes/recepcion.jpg',
    despues: '/fotos-despues/recepcion.jpg',
    acento: '#2c6b50',
  },
  {
    id: 'comedor',
    etiqueta: 'Comedor',
    eyebrow: 'Casa principal',
    titulo: 'Comedor y cocina para 26 residentes.',
    texto: 'Comedor con área de TV y espacio para silla de ruedas; la cocina, de acero inoxidable, prepara la comida de los dos edificios.',
    tags: ['Cocina de acero inoxidable', 'Comedor y TV', 'Luz natural'],
    antes: '/fotos-antes/comedor.jpg',
    despues: '/fotos-despues/comedor.jpg',
    acento: '#2c6b50',
  },
  {
    id: 'edificio-gris',
    etiqueta: 'Edificio gris',
    eyebrow: 'Segundo edificio',
    titulo: 'El edificio de cuidado continuo.',
    texto: 'Dos niveles: personas encamadas y salón amarillo arriba, con la galería en L de verjas como área recreativa; abajo, los dos salones de las personas que deambulan, oficinas y baño accesible.',
    tags: ['22 camas', '4 salones', 'Enfermería 24 h'],
    antes: '/fotos-reales/edificio-gris.jpg',
    despues: '/fotos-despues/edificio-gris.jpg',
    acento: '#3b6ea5',
    posicion: 'center 45%',
  },
  {
    id: 'hospitalizacion',
    etiqueta: 'Salas',
    eyebrow: 'Personas encamadas · 10 camas',
    titulo: 'Camas hospitalarias con luz propia.',
    texto: 'Cada cama con barandales, mesita y luz sobre la cabecera. Estación de enfermería a la vista, donde estaba el podio.',
    tags: ['Rieles y ruedas', 'Oxígeno', 'Timbre por cama'],
    antes: '/fotos-antes/hospitalizacion.jpg',
    despues: '/fotos-despues/hospitalizacion.jpg',
    acento: '#3b6ea5',
  },
  {
    id: 'terraza',
    etiqueta: 'Terraza',
    eyebrow: 'Piso alto',
    titulo: 'Área recreativa y de coffee break.',
    texto: 'La galería en L con verjas del piso alto, techada y ventilada, de canto a canto: para merendar, recibir visitas y tomar el sol de la tarde. Sigue en la terraza al aire libre del lado del jardín.',
    tags: ['Techada', 'Vista al jardín', 'Baranda'],
    antes: '/fotos-antes/terraza.jpg',
    despues: '/fotos-despues/terraza.jpg',
    acento: '#c99a3c',
  },
  {
    id: 'jardin',
    etiqueta: 'Jardín',
    eyebrow: 'Jardín central',
    titulo: 'Gazebo, huerto y tina de hidroterapia.',
    texto: 'Un campus al aire libre: gazebo de juegos, huerto cercado y tina de hidroterapia con agua tibia en movimiento, unidos por caminos y rampas accesibles.',
    tags: ['Gazebo', 'Huerto', 'Hidroterapia'],
    antes: '/fotos-antes/gazebo.jpg',
    despues: '/fotos-despues/gazebo.jpg',
    acento: '#2c6b50',
    scroll: 1.6,
    cta: {
      principal: { label: 'Solicitar expediente', href: '/contacto' },
      secundaria: { label: 'Ver datos del proyecto', href: '#proyecto' },
    },
  },
];
