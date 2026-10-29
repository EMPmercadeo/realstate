# Tareas para Antigravity: imágenes "así quedará" de la residencia

Proyecto: conversión del antiguo Instituto Superior Publies Educa (David, Chiriquí) en una residencia de retiro y cuidado de adultos mayores. El sitio web ya tiene un recorrido 3D; estas imágenes muestran cada espacio terminado a partir de la foto real actual.

## Reglas para todas las imágenes

1. Usa el modelo de generación de imágenes (Nano Banana / Gemini imagen) en modo **edición a partir de la foto de referencia**, no generación desde cero.
2. Conserva exactamente la foto original: mismo encuadre, misma perspectiva, mismas paredes, ventanas, piso, techo e iluminación. Solo cambia el mobiliario y el uso del espacio según el prompt.
3. Resultado fotorrealista, como fotografía de arquitectura de interiores: luz natural suave, nada de personas, nada de texto ni logos, sin marcas de agua.
4. Resolución: la máxima que permita el modelo, mínimo 1536 px de ancho, formato horizontal.
5. Guarda cada resultado en `web/public/fotos-despues/` con el nombre indicado. Si el modelo genera varias variantes, guarda la mejor con el nombre indicado y las demás con sufijo `-b`, `-c`.
6. Guarda también una copia de la foto original en `web/public/fotos-antes/` con el mismo nombre.
7. Al terminar, crea `docs/fotos-generadas.md` con una tabla: nombre, foto origen, prompt usado, observaciones.

Fotos de origen: carpeta `docs/fotos-antes/` (ya copiadas) y la carpeta de descargas `drive-download-20261028T233606Z-1-001`.

---

## 1. Sala de hospitalización (edificio gris, piso alto, antes salón de conferencias)

- Foto origen: `docs/fotos-antes/salon-conferencias.jpg` (original `20240320_155112.jpg`)
- Guardar como: `hospitalizacion.jpg`
- Prompt:

> Edita esta foto manteniendo exactamente la misma habitación, paredes grises claras, ventanas con rejas, cielo raso con lámparas y la misma perspectiva. Quita las mesas largas con manteles, las sillas rojas, el podio y la pantalla de proyección. Conviértela en una sala de hospitalización de una residencia de adultos mayores de alta calidad: 10 camas hospitalarias eléctricas blancas con barandales de aluminio, colchón con sábanas celestes y almohada blanca, dispuestas en dos filas de cinco contra las paredes laterales con pasillo central amplio; junto a cada cama una mesita de noche de madera clara con ruedas; sobre la cabecera de cada cama una lámpara LED lineal empotrada en la pared; donde estaba el podio, una estación de enfermería con mostrador blanco curvo, computadora y carrito de medicamentos. Cortinas separadoras de tela color crema recogidas. Piso de cerámica limpio y brillante. Fotografía de arquitectura interior, realista, luz natural de las ventanas más luz blanca de techo.

## 2. Salón #2, movilidad reducida (edificio gris, piso alto)

- Foto origen: `docs/fotos-antes/salon-conferencias-2.jpg` (original `20240320_155114.jpg`)
- Guardar como: `salon-2.jpg`
- Prompt:

> Misma habitación y misma perspectiva que la foto; quita mesas, manteles, sillas rojas y pantalla. Conviértela en una habitación compartida para 4 residentes con movilidad reducida: 4 camas hospitalarias con barandales bajos, sábanas color beige y cobija doblada al pie, cada una con su mesita de noche de madera y una silla de ruedas plegada al lado; una butaca reclinable gris junto a la ventana; pequeñas plantas en macetas; cuadros sencillos de paisajes de Chiriquí en las paredes; luz natural cálida. Fotografía realista de interiores, sin personas.

## 3. Área de refrigerios (edificio gris, antes refresquería)

- Foto origen: `docs/fotos-antes/refresqueria.jpg` (original `20240325_150037.jpg`)
- Guardar como: `refrigerios.jpg`
- Prompt:

> Conserva el espacio, las rejas de la ventana y el piso. Sustituye las mesas plegables con mantel azul por 4 mesas redondas de madera clara con sillas acolchadas de respaldo alto aptas para adultos mayores, una barra de servicio con cafetera, dispensador de agua y canasta de frutas, una vitrina pequeña de refrigerios, y una pizarra de menú sin texto legible. Plantas de interior en las esquinas. Luz natural de media mañana. Fotografía realista de interiores.

## 4. Cocina (edificio gris)

- Foto origen: `docs/fotos-antes/cocina.jpg` (original `20240325_144502.jpg`)
- Guardar como: `cocina.jpg`
- Prompt:

> Misma cocina y encuadre. Mantén el mesón de granito y el fregadero. Convierte el espacio en una cocina institucional limpia y ordenada para preparación de alimentos de una residencia de adultos mayores: estufa industrial de acero inoxidable de 6 quemadores en lugar de la estufa pequeña, campana extractora de acero, estantería de acero inoxidable con ollas y recipientes ordenados, refrigerador grande de acero, utensilios colgados, todo impecable. Sin personas, sin texto. Fotografía realista.

## 5. Terraza (edificio gris, piso alto)

- Foto origen: `docs/fotos-antes/terraza.jpg` (original `20240325_151848.jpg`)
- Guardar como: `terraza.jpg`
- Prompt:

> Misma terraza de concreto, misma baranda blanca con detalles azules y los mismos árboles detrás. Conviértela en un área recreativa al aire libre para adultos mayores: piso con deck de madera sintética color miel, una pérgola de madera con tela sombra cubriendo la mitad del espacio, 3 juegos de mesas redondas con sillas de ratán sintético y cojines beige, 2 tumbonas, jardineras largas con plantas tropicales (heliconias, crotos, palmas pequeñas), luces colgantes tipo guirnalda apagadas, un pasamanos adicional de acero a lo largo de la baranda. Cielo despejado, luz de tarde. Fotografía realista de arquitectura.

## 6. Baño accesible con regadera (edificio gris, planta baja)

- Foto origen: `docs/fotos-antes/bano.jpg` (original `20240320_144815.jpg`)
- Guardar como: `bano-accesible.jpg`
- Prompt:

> Mismo baño, mismos azulejos rojos y blancos, mismo encuadre. Añade una regadera de obra sin escalón con piso antideslizante gris, banco de ducha abatible de acero y madera, barras de apoyo de acero inoxidable junto al inodoro y en la ducha, asiento de inodoro elevado, lavamanos accesible con espejo inclinado, dispensadores de jabón y papel, cortina de ducha blanca recogida. Todo limpio y nuevo. Fotografía realista, sin personas.

## 7. Comedor y sala de familiares (casa amarilla)

- Foto origen: `docs/fotos-antes/comedor-casa.jpg` (original `WhatsApp Image 2026-10-28 at 2.42.27 PM.jpeg`)
- Guardar como: `comedor.jpg`
- Prompt:

> Mismo comedor de la casa, mismas paredes, ventanas de vidrio y piso. Reemplaza la mesa con mantel de encaje por dos mesas rectangulares de madera clara con sillas acolchadas con apoyabrazos, un aparador con vajilla, un rincón de estar con dos sillones de tela verde oliva y una mesa de centro para visitas de familiares, cuadros de paisajes, una planta grande en maceta, iluminación cálida. Ambiente hogareño y luminoso. Fotografía realista de interiores.

## 8. Sala de terapia (casa amarilla, antes laboratorio de simulación)

- Foto origen: `docs/fotos-antes/sala-terapia.jpg` (original `WhatsApp Image 2026-10-28 at 2.42.55 PM.jpeg`)
- Guardar como: `terapia.jpg`
- Prompt:

> Misma sala, misma pared de piedra con ventana y mismo piso. Quita el sofá, las sillas de mimbre y la mesita. Conviértela en una sala de fisioterapia y terapia ocupacional para adultos mayores: 2 camillas de terapia tapizadas en azul, barras paralelas de madera para marcha, una bicicleta estática, pelotas de terapia, un espejo grande de pared, estantería con bandas elásticas y pesas ligeras, colchonetas, pared de piedra intacta. Luz natural, ambiente limpio. Fotografía realista.

## 9. Cuarto privado VIP (casa amarilla)

- Foto origen: `docs/fotos-antes/cuarto-vip.jpg` (original `WhatsApp Image 2026-10-28 at 2.41.54 PM (1).jpeg`)
- Guardar como: `cuarto-vip.jpg`
- Prompt:

> Misma habitación, misma ventana, aire acondicionado y clóset de madera. Reemplaza la cama por una cama individual ajustable de aspecto hogareño con cabecera tapizada en lino gris, ropa de cama blanca y una manta tejida color arena, mesita de noche con lámpara, una butaca cómoda junto a la ventana, cortinas blancas livianas, barra de apoyo discreta junto a la cama, cuadro sencillo y una planta pequeña. Habitación ordenada, luminosa, estilo hotel boutique tranquilo. Fotografía realista.

## 10. Recepción (casa amarilla)

- Foto origen: `docs/fotos-antes/recepcion.jpg` (original `WhatsApp Image 2026-10-28 at 2.42.54 PM (3).jpeg`)
- Guardar como: `recepcion.jpg`
- Prompt:

> Misma sala, mismas paredes amarillas claras, arcos y ventana con arco. Quita el pendón publicitario y el televisor. Conviértela en la recepción de una residencia de retiro: mostrador de recepción de madera clara con frente de listones, dos sillones de cuero color camel y una mesa baja para visitantes, planta de interior grande, cuadros de paisajes de las tierras altas de Chiriquí, lámpara de pie cálida, piso brillante. Sin texto ni logos. Fotografía realista de interiores.

## 11. Gazebo de juegos (jardín)

- Foto origen: `docs/fotos-antes/jardin.jpg` (original `WhatsApp Image 2026-10-28 at 2.40.58 PM.jpeg`)
- Guardar como: `gazebo.jpg`
- Prompt:

> Conserva el jardín, el camino de losas de piedra, los setos y los árboles de la foto. Añade al fondo, sobre el césped, un gazebo octogonal de madera con techo de tejas de barro, piso de concreto pulido y 4 mesas pequeñas con sillas para jugar dominó y cartas, con una rampa de acceso suave con barandal. Alrededor, bancas de jardín y faroles bajos. Luz de tarde tropical. Fotografía realista de paisajismo.

## 12. Terapia acuática (jardín)

- Foto origen: `docs/fotos-antes/jardin-2.jpg` (original `WhatsApp Image 2026-10-28 at 2.40.57 PM (1).jpeg`)
- Guardar como: `terapia-acuatica.jpg`
- Prompt:

> Conserva el jardín y los árboles de la foto. Añade en el centro una piscina circular de hidroterapia de 4 metros de diámetro, poco profunda, con agua tibia en movimiento, borde de piedra clara, barandales de acero inoxidable y escalera con pasamanos para entrar sin esfuerzo, bajo una pérgola de madera con techo de policarbonato traslúcido. Alrededor, piso antideslizante, dos tumbonas y plantas tropicales. Luz natural suave. Fotografía realista.
