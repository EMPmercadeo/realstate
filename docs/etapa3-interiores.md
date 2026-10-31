# Etapa 3 · Interiores y conexión vertical (30-10-2026)

Segundo punto de revisión del encargo `INSTRUCCIONES_PARA_CLAUDE.md`: relaciones de cuartos y puertas,
planos esquemáticos por nivel, conexión vertical probada. Sigue en materiales neutros.

## Qué cambió en el modelo
- Los edificios ya no son bloques macizos: muros exteriores de 20 cm hacia adentro con **huecos reales**
  donde están las ventanas y puertas de las fachadas, tabiques interiores de 12 cm, piso terminado, losa
  de entrepiso con hueco de escalera y cielo raso.
- **Escaleras interiores en U caminables** en los dos edificios (la de la casa como en la foto de paredes
  verdes; la del gris como en las fotos con "SALIDA" y bloques de vidrio). Contrahuella ≈ 17,5 cm,
  huella 31–34 cm, descanso a media altura, pasamanos en el lado interior y barandas en el borde del hueco.
- Puertas interiores con marco (vano libre de 0,90 m; 1,20 m en salones, comedor, recepción y terapia).
- Puertas exteriores con la hoja abierta hacia adentro para poder pasar.
- Edificio gris: la terraza alta del lado del jardín queda cerrada con verjas de piso a techo.
- Una luz de área por cuarto (colección `Luces_interior`, apagada en las vistas de fachada).

## Archivos
| Archivo | Qué hace |
|---|---|
| `blender/interiores.py` | Datos de cuartos por nivel, escaleras y supuestos; calcula muros, puertas, losas y escalones (sin Blender) y los construye en Blender. |
| `blender/fachadas.py` | Ahora registra cada ventana y puerta como hueco real y llama a `interiores.construir`. |
| `blender/bloqueo.py` | Además de lo anterior: exporta `interiores.json`, corre la prueba de recorrido y hace cortes (`axo_*`) y vistas interiores (`int_*`). |
| `blender/planos.py` | Dibuja los planos esquemáticos desde `interiores.json` (no necesita Blender). |
| `build/bloqueo/planos_etapa3.jpg` | Lámina con los 4 planos, supuestos y resultado de la prueba de subida. |
| `build/bloqueo/interiores_etapa3.jpg` | Cortes sin cubierta y vistas desde adentro. |

Regenerar (PowerShell, dentro de `realstate`):
```
& $b -b -P blender\bloqueo.py -- --solo axo_casa_pb,int_casa_escalera --muestras 32 --ancho 1280
python blender\planos.py
```

## Prueba de subida (sin selector de piso)
`bloqueo.py` recorre a pie dos rutas con rayos sobre el modelo: busca el piso bajo cada punto (cada 10 cm),
mide el salto entre puntos, la altura libre hasta el techo y si algo se interpone a 0,45 m y 1,50 m.
- Casa amarilla: calle → puerta principal → recepción → comedor → pasillo → escalera → vestíbulo alto →
  oficina del gerente → balcón. 33,5 m, de 0,03 a 3,15 m. Escalón máx. 0,20 m · altura libre mín. 2,04 m ·
  0 choques.
- Edificio gris: calle → acceso → pasillo → estar → escalera → eje alto → Hospitalización → terraza.
  28,9 m, de 0,00 a 3,20 m. Escalón máx. 0,20 m · altura libre mín. 2,04 m · 0 choques.
- Con el mobiliario de referencia la ruta rodea la mesa del comedor y el escritorio del gerente.
- Primera corrida: falló (el piso alto tapaba el hueco de la escalera y quedaba una rendija de 5 cm en el
  último escalón del gris). Corregido y repetido.
- Esto prueba la geometría en Blender. La caminata en el navegador (colisiones, celular) es la etapa 4.

## Supuestos
Los mismos 12 de la lámina (`interiores.SUPUESTOS`). Los más importantes:
- La distribución es una lectura de los croquis; no fija muros reales.
- Casa: escalera interior ubicada en la torre junto al pasillo; planta alta = gerente + baño + recámara alta.
- Gris: escalera interior al norte; salones y hospitalización hacia el jardín, servicios hacia la calle.
- Capacidad sigue pendiente (24 camas en el gris + 3–4 cuartos en la casa vs 26/28). Colocando camas de
  0,95 × 2,0 m con paso libre en las puertas y ~0,9 m entre camas enfrentadas, con estas medidas estimadas
  caben **16 de 24**: Salón A 2 de 4, Salón B 4 de 6, Salón 2 3 de 4, Hospitalización 7 de 10. Las medidas
  son proporcionales al satélite, no un levantamiento: hay que medir en sitio antes de ofrecer una capacidad.
- Mobiliario: bloques neutros de referencia (camas, mesas, escritorios, mostradores, cocina) solo para leer
  el uso y la escala; no es el amueblado final.
- No hay ascensor ni rampa entre niveles: el acceso de encamados a la planta alta sigue sin resolver.
