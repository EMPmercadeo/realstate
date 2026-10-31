# Fase de realismo — "como Astra" (iniciada el 30-10-2026)

Referencia que pidió Ernesto: https://developers.openai.com/blog/architectural-visualization-with-astra
Ahí usaron **Blender + Cycles** para las imágenes y el video, texturas y plantas reales, y Unreal solo para una
aplicación de Mac descargable. Decisión de Ernesto (30-10): **Blender para imágenes y video, y la web sigue en
Three.js** con la luz de Cycles horneada en las texturas. Unreal no se usa (no se convierte a Three.js y en el
navegador exige servidores pagos).

## Cómo se trabaja
Ciclo por muestra: render → comparar con la foto real (`web/public/fotos-reales`, `docs/fotos-antes`) → anotar qué
falta → corregir → volver a renderizar. Primero una muestra (frente de la casa amarilla, acceso y recepción);
cuando se apruebe, la misma calidad pasa al resto.

Todo es aditivo: `realismo.py` abre `build/bloqueo/bloqueo.blend` (el modelo de las etapas 2–4) y guarda
`build/muestra/realismo.blend`. No cambia medidas ni la web.

| Archivo | Qué hace |
|---|---|
| `blender/realismo.py` | Materiales de fachada procedurales (repello con manchas y suciedad que sube del piso, teja metálica con escalón, baldosa, piedra, hierro, asfalto, tierra con pasto), cielo y sol calibrados, biseles en los cantos, roseta del medallón, faroles del portón, jardineras, arbustos, palmas y árboles, anillo de árboles del entorno. |
| `blender/vegetacion.py` | Plantas 3D por código: palma real (tronco anillado, capitel verde, frondas con pinnas), areca, arbusto con hojas y flores (alamanda amarilla, ixora roja), árbol de copa con tarjetas, hierba. |
| `blender/gen_tarjetas.py` | Hace las texturas de copa (`copa_mango.png`, `copa_fina.png`) renderizando hojas 3D desde arriba. |
| `blender/muestra_vistas.py` | Renderiza las vistas de la muestra (`m_frente`, `m_acceso`, `m_recepcion`) desde cualquier .blend. |
| `blender/lamina_muestra.py` | Lámina foto real · antes · después. |
| `blender/arboles_satelite.py` | Árboles fuera del lote donde el satélite muestra copa, y casas vecinas donde muestra techos. |
| `blender/video_muestra.py` | Video caminando a 1,60 m (24 mm) de la calle a la recepción; la exposición cambia al entrar. |
| `blender/hornear_web.py` | Prueba web: une el frente, le hace UV de luz, hornea con Cycles (color + sol + cielo + rebotes) y exporta GLB. |
| `blender/plantas_web.py` | Plantas del frente con color en los vértices (livianas) y JSON con el sol y las vistas para la página. |

## Luz (medida, no a ojo)
Con el cielo físico a fuerza 1, el sol equivale a una lámpara de 135 (medido en una escena de prueba).
Se dejó el cielo en 0,0625 (el mismo nivel de antes, así los interiores no cambian) y el sol en su valor físico
(135 × 0,0625 ≈ 8,4; antes 2,6). Exposición exterior −0,35 con AgX. Sol de media mañana desde el frente
izquierdo de la casa, como en la foto de la fachada.

## En la PC con la RTX 3080 (PowerShell dentro de `realstate`)
```
$b = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
& $b -b -P blender\gen_tarjetas.py
& $b -b -P blender\realismo.py
& $b -b -P blender\muestra_vistas.py -- --blend build/muestra/realismo.blend --sufijo final --ancho 1920 --muestras 256 --gpu
python blender\lamina_muestra.py m_frente final
```
Si en `assets\pbr` están las texturas de ambientCG (ver `docs/PLAN-GPU.md`) los interiores las usan.

## Video y web en la PC (RTX 3080)
```
& $b -b -P blender\video_muestra.py -- --gpu --ancho 1920 --muestras 128
& $b -b -P blender\hornear_web.py -- --zona frente --atlas 8192 --muestras 256 --gpu
& $b -b -P blender\plantas_web.py -- --zona frente
```
El video queda en `build\video_muestra\recorrido_muestra.mp4` (se puede cortar y reanudar). La prueba web en
`build\web_horneado\` (`frente.glb`, `frente_plantas.glb`, `frente.json`). Vista previa publicada como artifact
"Recorrido horneado Altos" (atlas de 2048 por falta de memoria en la nube).

## Bitácora de la muestra (foto real contra modelo)
| Vuelta | Qué se vio mal | Qué se hizo |
|---|---|---|
| 1 | Todo plano: colores lisos, cielo lavado, sin plantas | Materiales procedurales, cielo físico, primeras plantas |
| 2 | Escena oscura, cielo azul marino | Luz medida: sol físico 8,4 con cielo 0,0625, exposición −0,35 |
| 3–5 | Copas hechas de "rosetas", pasto de alfombra | Tarjetas hechas con hojas 3D en manojos irregulares, pasto con zonas secas |
| 4 | Cantos perfectos, medallón liso | Biseles de 1,2 cm en 850 piezas, roseta en relieve, faroles |
| 7 | Borde del techo rojo (en la foto es blanco), portón recto | Fascia blanca, pasamanos curvo con anillos, baldosa anaranjada |
| 8 | Viga diagonal falsa en el cielo de la recepción | Se borran los cantos de techo que quedaban dentro de la casa |
| 9–15 | Árboles tapando el gris, entorno vacío, calle de tierra gris | Árboles del satélite solo fuera del lote, palmas en la orilla, casas vecinas, colinas, calle de tierra |

## Diferencias de forma que quedan (son del modelo, no del acabado)
- Atrás de la casa: el techo de la torre visto desde el patio no coincide con la foto; falta el toldo rojo y el
  tanque. Se corrige con medidas reales.
- La foto `recepcion.jpg` no es la recepción (es un cuarto con cama): no se usa para comparar.

## Siguiente
1. Ernesto aprueba la muestra o dice qué cambiar.
2. Recepción y demás interiores: piso brillante, luz cálida de lámparas, menos sobreexposición.
3. Extender a todo el lote: edificio gris, patio de grava, gazebo, tina, huerto.
4. Web: hornear la luz de Cycles en texturas (UV de luz por pieza) y cargarlas en Three.js sin luces en vivo.
5. Video del recorrido (Cycles en la 3080), 30 s, cámara a 1,60 m.
