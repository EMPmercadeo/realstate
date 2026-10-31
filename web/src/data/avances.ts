// Avance del modelo 3D (etapa 4, 30-10-2026): vistas interiores renderizadas desde el modelo de Blender
// (realstate/blender, build/bloqueo/int_*.png). Nombres según lo que pidió la propietaria.
export interface Vista { f: string; t: string; d: string }

export const FECHA = '30 de octubre de 2026';

export const GRIS: Vista[] = [
  { f: 'int_gris_hosp', t: 'Personas encamadas', d: '10 camas de hospital con barandales, luz sobre cada cama y estación de enfermería al fondo.' },
  { f: 'int_gris_hosp2', t: 'Personas encamadas', d: 'Vista desde la puerta del pasillo, hacia las ventanas del jardín.' },
  { f: 'int_gris_salon2', t: 'Salón amarillo', d: '4 camas para personas con movilidad reducida, con mesita y silla de ruedas.' },
  { f: 'int_gris_refrigerios', t: 'Área de coffee break', d: 'Terraza de arriba, cerrada con verjas: mesas, barra de café y frutas.' },
  { f: 'int_gris_salonB', t: 'Salón grande 2', d: '6 camas para personas que deambulan, con roperos y mesitas.' },
  { f: 'int_gris_salonA', t: 'Salón grande 1', d: '2 camas para personas que deambulan.' },
  { f: 'int_gris_bano_acc', t: 'Baño accesible para usuarios', d: 'Regadera a ras de piso con asiento abatible y barras de apoyo.' },
  { f: 'int_gris_deposito', t: 'Depósito y ropería', d: 'La antigua biblioteca, con estantes para ropa de cama e insumos.' },
  { f: 'int_gris_cocina', t: 'Cocineta del área de coffee break', d: 'Meseta de granito sobre base de bloque, como la actual.' },
  { f: 'int_gris_acceso', t: 'Acceso y pasillo', d: 'Entrada del edificio gris, pasillo y escalera interior.' },
];

export const CASA: Vista[] = [
  { f: 'int_casa_recepcion', t: 'Recepción 24 h', d: 'En la entrada principal, con mostrador y sala de espera.' },
  { f: 'int_casa_comedor', t: 'Comedor y TV', d: 'Mesa de comedor, sala con televisor y acceso a los cuartos.' },
  { f: 'int_casa_vip', t: 'Cuarto privado', d: 'Uno de los semiprivados, el de puertas corredizas de vidrio.' },
  { f: 'int_casa_semipriv', t: 'Cuarto privado', d: 'Semiprivado con escritorio y ropero; comparte baño.' },
  { f: 'int_casa_suite', t: 'Suite', d: 'Cuarto privado con baño y clóset propios.' },
  { f: 'int_casa_recamara', t: 'Recámara alta', d: 'Cuarto privado de la planta alta, con baño propio y salida al balcón.' },
  { f: 'int_casa_terapia', t: 'Terapia con familiares', d: 'Camilla, barras paralelas, bicicleta y material de terapia.' },
  { f: 'int_casa_talleres', t: 'Talleres', d: 'Pintura, acuarela y costura, detrás del área de terapia.' },
  { f: 'int_casa_consultorio', t: 'Consultorio de salud', d: 'Escritorio, camilla de examen y lavamanos.' },
  { f: 'int_casa_cocina', t: 'Cocina', d: 'Toda en acero inoxidable, con cocina industrial y campana.' },
  { f: 'int_casa_bano', t: 'Baño para huéspedes', d: 'Compartido por los dos cuartos semiprivados.' },
];

// Imagen "así quedará" de Antigravity (web/public/fotos-despues) frente al mismo uso en el modelo
export const PARES: [string, string, string][] = [
  ['hospitalizacion', 'int_gris_hosp', 'Personas encamadas'],
  ['salon-2', 'int_gris_salon2', 'Salón amarillo'],
  ['refrigerios', 'int_gris_refrigerios', 'Área de coffee break'],
  ['bano-accesible', 'int_gris_bano_acc', 'Baño accesible'],
  ['comedor', 'int_casa_comedor', 'Comedor'],
  ['terapia', 'int_casa_terapia', 'Terapia'],
  ['cocina', 'int_gris_cocina', 'Cocineta del edificio gris'],
];

export const PLANOS: [string, string][] = [
  ['plano_gris_pa', 'Edificio gris · planta alta'],
  ['plano_gris_pb', 'Edificio gris · planta baja'],
  ['plano_casa_pb', 'Casa amarilla · planta baja'],
  ['plano_casa_pa', 'Casa amarilla · planta alta'],
];

export const CAMAS: [string, string][] = [
  ['Personas encamadas (edificio gris, arriba)', '10'],
  ['Salón amarillo · movilidad reducida', '4'],
  ['Salones grandes de abajo · personas que deambulan', '2 + 6'],
  ['Casa amarilla · 4 cuartos privados', '4'],
];
