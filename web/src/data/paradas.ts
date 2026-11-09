// Paradas del recorrido 3D (/recorrido): la tira de miniaturas de abajo y el recorrido guiado.
// `id` es una vista del visor: 'sitio', 'calle', 'gris-ext', las de VISTAS_EXTRA o '<cuarto>@<edificio>'.
// Las miniaturas viven en public/mini/ (las de interiores salen de los renders de public/avances).
// Nombres según la propietaria: nunca "pacientes" ni "hospitalizados".

export interface Parada3D {
  id: string;
  nombre: string;
  lugar: string;
  texto: string;
  mini: string;
  datos?: string[];
  espera?: number;          // segundos en el recorrido guiado (sin contar el vuelo)
}

// vistas que no salen de residencia.json (coordenadas del visor: x, altura, z)
export const VISTAS_EXTRA: Record<string, { pos: number[]; target: number[]; nombre: string; detalle?: string }> = {
  jardin: { pos: [18.2, 12, -0.3], target: [-4.9, 0.8, 8.8], nombre: 'Jardín interno', detalle: 'Entre los dos edificios' },
  'gris-jardin': { pos: [18.2, 7, 43.6], target: [-13.3, 3.5, 29.1], nombre: 'Edificio gris desde el jardín' },
};

export const PARADAS_3D: Parada3D[] = [
  {
    id: 'sitio', nombre: 'Vista general', lugar: 'Altos de San Cristóbal · David, Chiriquí', mini: '/mini/sitio.jpg',
    texto: 'Terreno cercado de 2.500 m²: la casa amarilla al frente, el edificio gris atrás y el jardín interno entre los dos.',
    datos: ['2.500 m²', '2 edificios', '26 camas'], espera: 5,
  },
  {
    id: 'calle', nombre: 'Entrada principal', lugar: 'Casa amarilla · frente a la C.A', mini: '/mini/calle.jpg',
    texto: 'La casa amarilla recibe a familias y huéspedes desde la calle principal. La propiedad ya tiene cerca perimetral y portones eléctricos.',
    datos: ['Portones eléctricos', 'Cerca perimetral'], espera: 4,
  },
  {
    id: 'recepcion@amarilla', nombre: 'Recepción 24 h', lugar: 'Casa amarilla · planta baja', mini: '/mini/int_casa_recepcion.jpg',
    texto: 'En la entrada principal, atendida las 24 horas: aquí se recibe a las familias, a los huéspedes y a quienes vienen por el día.',
    espera: 4,
  },
  {
    id: 'comedor@amarilla', nombre: 'Comedor y TV', lugar: 'Casa amarilla · planta baja', mini: '/mini/int_casa_comedor.jpg',
    texto: 'El área social de la casa amarilla. La cocina de al lado prepara la comida para los dos edificios.',
    espera: 4,
  },
  {
    id: 'terapia@amarilla', nombre: 'Terapia con familiares', lugar: 'Casa amarilla · planta baja', mini: '/mini/int_casa_terapia.jpg',
    texto: 'En el antiguo laboratorio, con los talleres de pintura, acuarela y costura detrás. La familia participa en la terapia de cada persona.',
    espera: 4,
  },
  {
    id: 'suite@amarilla', nombre: 'Cuartos privados', lugar: 'Casa amarilla', mini: '/mini/int_casa_suite.jpg',
    texto: 'Cuatro cuartos privados tipo hotel: dos semiprivados que comparten baño, la suite y la recámara alta con baño propio. También sirven para estadías temporales.',
    datos: ['4 cuartos', 'Estadías temporales'], espera: 5,
  },
  {
    id: 'jardin', nombre: 'Jardín interno', lugar: 'Entre los dos edificios', mini: '/mini/jardin.jpg',
    texto: 'Camino de baldosa con rampas y barandas. La propuesta suma un gazebo de juegos, una tina de hidroterapia donde estaba el mango y un huerto cercado.',
    datos: ['Gazebo', 'Hidroterapia', 'Huerto'], espera: 5,
  },
  {
    id: 'gris-ext', nombre: 'Edificio gris', lugar: 'Dos niveles · cuidado continuo', mini: '/mini/gris-ext.jpg',
    texto: 'La parte asistencial: 22 camas en dos niveles. Se entra por la puerta café, bajo la galería con verjas.',
    datos: ['22 camas', '2 niveles'], espera: 4,
  },
  {
    id: 'salonA@gris', nombre: 'Salones de abajo', lugar: 'Edificio gris · planta baja', mini: '/mini/int_gris_salonA.jpg',
    texto: 'Dos salones grandes, mitad y mitad, para personas que deambulan: 4 camas en cada uno, con mesita y ropero.',
    datos: ['4 + 4 camas'], espera: 4,
  },
  {
    id: 'hosp@gris', nombre: 'Personas encamadas', lugar: 'Edificio gris · planta alta', mini: '/mini/int_gris_hosp.jpg',
    texto: 'El antiguo salón de conferencias: 10 camas de hospital con barandales, mesita y luz sobre cada cama, y la estación de enfermería donde estaba el podio.',
    datos: ['10 camas', 'Enfermería'], espera: 6,
  },
  {
    id: 'salon2@gris', nombre: 'Salón amarillo', lugar: 'Edificio gris · planta alta', mini: '/mini/int_gris_salon2.jpg',
    texto: 'Para personas con movilidad reducida: 4 camas, baño nuevo adentro y dos puertas a la terraza.',
    datos: ['4 camas', 'Baño propio'], espera: 5,
  },
  {
    id: 'galeria@gris', nombre: 'Área de coffee break', lugar: 'Edificio gris · planta alta', mini: '/mini/int_gris_refrigerios.jpg',
    texto: 'La galería en L con verjas, de canto a canto entre la cocineta y la biblioteca: área recreativa y del té, con mesas, barra de café y estar.',
    espera: 5,
  },
  {
    id: 'terraza@gris', nombre: 'Terraza al aire libre', lugar: 'Edificio gris · planta alta', mini: '/mini/terraza.jpg',
    texto: 'Terraza al aire libre para personas que deambulan o caminan, del lado del jardín.',
    espera: 4,
  },
];

// Render de interiores (public/avances) de cada cuarto del modelo, para la ficha del visor.
export const RENDER_CUARTO: Record<string, string> = {
  'acceso@gris': 'int_gris_acceso', 'pasillo@gris': 'int_gris_vestibulo', 'salonA@gris': 'int_gris_salonA',
  'salonB@gris': 'int_gris_salonB', 'bano_acc@gris': 'int_gris_bano_acc', 'oficina2@gris': 'int_gris_oficina2',
  'hosp@gris': 'int_gris_hosp', 'salon2@gris': 'int_gris_salon2', 'bano_s2@gris': 'int_gris_bano_s2',
  'galeria@gris': 'int_gris_refrigerios', 'cocina@gris': 'int_gris_cocina', 'biblioteca@gris': 'int_gris_biblioteca',
  'recepcion@amarilla': 'int_casa_recepcion', 'comedor@amarilla': 'int_casa_comedor', 'vip@amarilla': 'int_casa_vip',
  'semipriv@amarilla': 'int_casa_semipriv', 'suite@amarilla': 'int_casa_suite', 'recamara@amarilla': 'int_casa_recamara',
  'terapia@amarilla': 'int_casa_terapia', 'talleres@amarilla': 'int_casa_talleres', 'consultorio@amarilla': 'int_casa_consultorio',
  'cocina@amarilla': 'int_casa_cocina', 'bano1@amarilla': 'int_casa_bano',
};

// Planos (public/avances/plano_*.png) por edificio y piso
export const PLANOS_VISOR: { id: string; ed: string; piso: number; t: string; f: string }[] = [
  { id: 'amarilla:1', ed: 'amarilla', piso: 1, t: 'Casa amarilla · planta baja', f: '/avances/plano_casa_pb.png' },
  { id: 'amarilla:2', ed: 'amarilla', piso: 2, t: 'Casa amarilla · planta alta', f: '/avances/plano_casa_pa.png' },
  { id: 'gris:1', ed: 'gris', piso: 1, t: 'Edificio gris · planta baja', f: '/avances/plano_gris_pb.png' },
  { id: 'gris:2', ed: 'gris', piso: 2, t: 'Edificio gris · planta alta', f: '/avances/plano_gris_pa.png' },
];
