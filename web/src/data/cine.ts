// Recorrido cinematográfico: la cámara vuela por la propiedad siguiendo esta ruta
// (coordenadas del visor: x = x del sitio, y = altura, z = -y del sitio).
// Cada parada se muestra cuando el progreso del scroll pasa por su `u`.
// Con N puntos de ruta, u = i/(N-1) cae exactamente en el punto i.
export interface PuntoRuta { pos: number[]; target: number[] }
export interface ParadaCine {
  u: number; id: string; etiqueta: string; eyebrow: string; titulo: string; texto: string;
  tags?: string[]; foto?: string; fotoAntes?: string;
  cta?: { principal: { label: string; href: string }; secundaria?: { label: string; href: string } };
}

export const RUTA: PuntoRuta[] = [
  { pos: [100, 42, -6], target: [16, 3, -42] },      // 0.00 llegada aérea desde el sureste
  { pos: [80, 26, -34], target: [18, 3, -52] },
  { pos: [60, 12, -58], target: [26, 3, -60] },      // bajando a la calle
  { pos: [34, 3.8, -52.5], target: [16, 3.2, -60] },  // en el portón (pasa sobre la cerca)
  { pos: [27, 2.8, -48], target: [15, 3.2, -59] },     // frente al porche (3/4)
  { pos: [32.5, 5.8, -48], target: [15, 2.2, -42] }, // hacia el jardín
  { pos: [31, 7, -30], target: [15, 1.5, -42] },     // gazebo y piscina
  { pos: [34, 11, -46], target: [13, 3, -22] },      // balcón del edificio gris desde el jardín
  { pos: [40, 4.2, -4], target: [17, 3.8, -15] },    // fachada y terraza
  { pos: [44, 22, 2], target: [15, 4, -30] },        // subiendo
  { pos: [92, 46, 30], target: [15, 3, -42] },       // vista final
];

export const PARADAS_CINE: ParadaCine[] = [
  { u: 0.0, id: 'llegada', etiqueta: 'Llegada', eyebrow: 'Altos de San Cristóbal · David, Chiriquí', titulo: 'Una residencia de retiro lista para abrir.', texto: 'Dos edificios y 2.500 m² cercados, a minutos del centro de David. Haz scroll para sobrevolar el proyecto terminado.', tags: ['2.500 m²', '27 residentes', 'Llave en mano'] },
  { u: 0.3, id: 'entrada', etiqueta: 'Entrada', eyebrow: 'Acceso principal', titulo: 'Portón eléctrico y entrada techada.', texto: 'El porche de arcos recibe a familiares y ambulancias bajo techo, con rampa y pasamanos para movilidad reducida.', tags: ['Rampa', 'Descenso cubierto', 'Cerca perimetral'], foto: '/fotos-reales/porche-arcos.jpg' },
  { u: 0.4, id: 'casa', etiqueta: 'Casa principal', eyebrow: 'Casa principal · dos niveles', titulo: 'Recepción, consultorio, comedor y terapia.', texto: 'Todo lo administrativo y social en la casa amarilla: admisión, consultorio médico, comedor para 27 residentes, sala de terapia y tres cuartos privados.', tags: ['Consultorio', 'Comedor', '3 cuartos privados'], foto: '/fotos-despues/comedor.jpg', fotoAntes: '/fotos-antes/comedor.jpg' },
  { u: 0.6, id: 'jardin', etiqueta: 'Jardín', eyebrow: 'Jardín central', titulo: 'Gazebo, huerto y terapia acuática.', texto: 'Un campus al aire libre: gazebo de juegos, huerto cercado y piscina de terapia con pérgola. Caminos sin escalones entre los dos edificios.', tags: ['Gazebo', 'Huerto', 'Terapia acuática'], foto: '/fotos-despues/gazebo.jpg', fotoAntes: '/fotos-antes/gazebo.jpg' },
  { u: 0.7, id: 'hospitalizacion', etiqueta: 'Hospitalización', eyebrow: 'Edificio de hospitalización', titulo: '24 camas en cuatro salas.', texto: 'Dos niveles con estación de enfermería en cada piso, camas eléctricas con rieles, panel de luz individual y baños accesibles.', tags: ['24 camas', 'Enfermería 24 h', 'Oxígeno'], foto: '/fotos-despues/hospitalizacion.jpg', fotoAntes: '/fotos-antes/hospitalizacion.jpg' },
  { u: 0.8, id: 'terraza', etiqueta: 'Terraza', eyebrow: 'Piso alto', titulo: 'Terraza de refrigerios con vista al jardín.', texto: 'Techada y ventilada, para merendar, recibir visitas y tomar el sol de la tarde.', tags: ['Techada', 'Baranda', 'Refrigerios'], foto: '/fotos-despues/terraza.jpg', fotoAntes: '/fotos-antes/terraza.jpg' },
  { u: 1.0, id: 'final', etiqueta: 'Inversión', eyebrow: 'Proyecto llave en mano', titulo: 'Lista para operar. Lista para invertir.', texto: 'Propiedad adecuada y equipada según el programa de espacios, con licencia sanitaria en trámite. Solicita el expediente completo.', cta: { principal: { label: 'Solicitar expediente', href: '#inversionistas' }, secundaria: { label: 'Explorar libremente en 3D', href: '/recorrido' } } },
];
