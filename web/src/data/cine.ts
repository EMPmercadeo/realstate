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

// Ruta sobre el modelo amueblado (residencia-exterior.glb): la casa amarilla da al noreste (C.A),
// el edificio gris queda al suroeste y el jardín interno entre los dos.
// 01-11-2026: coordenadas x/z multiplicadas por 1,21 (escala medida del satélite, ver docs/fase-mapa.md)
export const RUTA: PuntoRuta[] = [
  { pos: [94.5, 60.6, -77.5], target: [3.6, 2, 2.4] },          // 0.00 llegada aérea desde el noreste
  { pos: [70.2, 36.3, -67.8], target: [13.3, 3, -14.5] },
  { pos: [50.9, 11, -50.9], target: [21.8, 3, -21.8] },       // bajando hacia la C.A
  { pos: [35.1, 3.6, -37.5], target: [17, 3, -18.2] },      // 0.30 en el portón
  { pos: [37.5, 4.8, -15.7], target: [17, 2.8, -18.2] },    // 0.40 casa amarilla en 3/4
  { pos: [21.8, 18.2, -3.6], target: [7.3, 1.5, 10.9] },         // sobre la casa hacia el jardín
  { pos: [18.2, 12, -0.3], target: [-4.9, 0.8, 8.8] },     // 0.60 jardín interno: rampas, gazebo, tina, huerto
  { pos: [18.2, 7, 43.6], target: [-13.3, 3.5, 29.1] },       // 0.70 edificio gris desde el jardín
  { pos: [8.5, 6.2, 42.4], target: [-7.3, 4.3, 33.3] },     // 0.80 área de coffee break (terraza con verjas)
  { pos: [14.5, 26.6, 58.1], target: [-3.6, 2, 17] },         // subiendo
  { pos: [77.5, 63, 70.2], target: [3.6, 2, 2.4] },           // vista final
];

export const PARADAS_CINE: ParadaCine[] = [
  { u: 0.0, id: 'llegada', etiqueta: 'Llegada', eyebrow: 'Altos de San Cristóbal · David, Chiriquí', titulo: 'Una residencia de retiro lista para operar.', texto: 'Dos edificios en 2.500 m² cercados, a minutos del centro de David. Haz scroll para sobrevolar el proyecto.', tags: ['2.500 m²', '26 camas', 'Llave en mano'] },
  { u: 0.3, id: 'entrada', etiqueta: 'Entrada', eyebrow: 'Acceso principal · C.A', titulo: 'Cerca perimetral y portones eléctricos.', texto: 'La casa amarilla recibe a familias y huéspedes desde la calle principal. La propiedad ya tiene cerca, portones y seguridad.', tags: ['Portón eléctrico', 'Cerca perimetral'], foto: '/fotos-reales/porche-arcos.jpg' },
  { u: 0.4, id: 'casa', etiqueta: 'Casa amarilla', eyebrow: 'Casa amarilla · dos niveles', titulo: 'Recepción 24 h, comedor y terapia.', texto: 'Recepción, comedor y TV, terapia con familiares, talleres, consultorio de salud y cuatro cuartos privados para huéspedes.', tags: ['Recepción 24 h', 'Consultorio', '4 cuartos privados'], foto: '/fotos-despues/comedor.jpg', fotoAntes: '/fotos-antes/comedor.jpg' },
  { u: 0.6, id: 'jardin', etiqueta: 'Jardín', eyebrow: 'Jardín interno', titulo: 'Gazebo, huerto y tina de hidroterapia.', texto: 'Entre los dos edificios: gazebo de juegos, huerto con surcos y cerca, y una tina de hidroterapia con agua tibia en movimiento.', tags: ['Gazebo', 'Huerto', 'Hidroterapia'], foto: '/fotos-despues/gazebo.jpg', fotoAntes: '/fotos-antes/gazebo.jpg' },
  { u: 0.7, id: 'gris', etiqueta: 'Edificio gris', eyebrow: 'Edificio gris · cuidado continuo', titulo: '22 camas en dos niveles.', texto: 'Personas encamadas con estación de enfermería, salón amarillo para personas con movilidad reducida y salones para las que deambulan.', tags: ['22 camas', 'Enfermería', 'Baño accesible'], foto: '/fotos-despues/hospitalizacion.jpg', fotoAntes: '/fotos-antes/hospitalizacion.jpg' },
  { u: 0.8, id: 'terraza', etiqueta: 'Coffee break', eyebrow: 'Planta alta', titulo: 'Área de coffee break con vista al jardín.', texto: 'En la terraza con verjas del piso alto: mesas, barra de café y frutas para residentes y visitas.', tags: ['Terraza', 'Coffee break'], foto: '/fotos-despues/refrigerios.jpg', fotoAntes: '/fotos-antes/refrigerios.jpg' },
  { u: 1.0, id: 'final', etiqueta: 'Inversión', eyebrow: 'Proyecto llave en mano', titulo: 'Lista para operar. Lista para invertir.', texto: 'La propiedad se entrega adecuada y equipada según el programa de espacios. Solicita el expediente completo.', cta: { principal: { label: 'Solicitar expediente', href: '#inversionistas' }, secundaria: { label: 'Explorar libremente en 3D', href: '/recorrido' } } },
];
