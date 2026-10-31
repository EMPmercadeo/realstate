# Siguiente fase — punto de partida (actualizado 30-10-2026, noche)

Para un chat nuevo: leer primero `docs/contexto-proyecto.md` (fuente de verdad), luego este archivo y
`docs/etapa4-amueblado.md`. El trabajo se hace en Blender (scripts en `blender/`) y la web en `web/`.

## Dónde quedó
- **Modelo Blender**: `blender/bloqueo.py` → `build/bloqueo/bloqueo.blend`. Etapas hechas: terreno sobre el
  satélite (2.500 m²), fachadas, interiores con muros y escaleras, amueblado con 26 camas. Desde el 30-10 la
  casa tiene sus colores reales (amarillo ocre y teja terracota, como en las fotos).
- **Web** (https://residencia-altos.vercel.app):
  - `/recorrido`: maqueta 3D libre con el modelo amueblado (`web/public/modelo/residencia.glb`).
  - `/` (portada): sobrevuelo por scroll con el modelo nuevo en 3D en vivo (`residencia-exterior.glb`, ruta y
    textos en `web/src/data/cine.ts`). El video viejo (`clips/sobrevuelo.mp4`) quedó sin uso; si se renderiza
    uno nuevo se debe llamar `clips/sobrevuelo-v2.mp4` (y `-v2-m.mp4` para celular, `poster-v2.jpg`).
  - `/avances`: 21 vistas renderizadas, cuenta de camas y planos.
- **Regenerar la web después de cambiar el modelo** (PowerShell en `realstate`):
  ```
  $b = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
  & $b -b -P blender\bloqueo.py -- --solo ninguno
  & $b -b -P blender\web_muestras.py
  & $b -b -P blender\export_web.py
  ```

## Preguntas prioritarias para la propietaria
1. ¿Dónde va el gerente? (hoy: cuarto pequeño del fondo, planta alta de la casa, "por confirmar")
2. ¿10 u 8 personas encamadas? (caben 10, justas)
3. ¿Cuál es de verdad el cuarto de la foto con puertas de vidrio y arcos? (hoy: semiprivado 2)

## Cambios ya pedidos que faltan en el modelo
- Baño nuevo **dentro del salón amarillo**, al lado de la biblioteca (depósito y ropería). Revisar que sigan
  cabiendo las 4 camas.
- El servicio de la terraza (gris, planta alta) queda **solo con inodoro, sin regadera** (hoy el modelo lo
  nombra "Baño para usuarios (con regadera)").
- La cocineta del gris es apoyo para servir: la comida se cocina en la casa amarilla.

## Plan propuesto (en este orden)
1. **Medidas reales**: planos o medición en sitio de lo que más pesa: largo y ancho exterior de cada edificio,
   altura de piso a piso, ancho y huella de la escalera, y los salones con camas (encamados, salón amarillo,
   salones de abajo). Ajustar `blender/interiores.py`, `fachadas.py` y `amueblado.py`.
2. **Caminata realista en la web** (pedido de Ernesto): subir y bajar las escaleras caminando (gravedad y
   piso por raycast, sin botones de piso), chocar con todas las paredes y los muebles, cerrar las paredes
   que faltan junto a la escalera del edificio gris, altura de ojos ~1,60 m, joystick en celular.
3. **Exteriores**: gazebo con letrero "Área recreativa / juegos sociales", tina de hidroterapia donde estaba
   el mango, huerto con 3–4 surcos y cerca, vegetación del lote según fotos y satélite, caminos sin escalones.
4. **Video de la portada en alta calidad**: adaptar `blender/cine_render.py` al modelo nuevo y a la ruta de
   `web/src/data/cine.ts`, renderizar con Cycles en la RTX 3080 (16:9 y 9:16).
5. **Unreal Engine**: solo cuando las medidas estén confirmadas, y como extra (video premium o demo
   descargable para un inversionista). El modelo de Blender se lleva tal cual (Datasmith o FBX). No reemplaza
   al recorrido web, que es el que se comparte con un enlace.

## Textos del sitio que aún usan nombres viejos
`web/src/data/recorrido.ts` (página `/fotos`): "27 residentes", "hospitalización", "24 camas", "refrigerios".
La foto de recepción del sitio no es la real; falta la foto correcta.
