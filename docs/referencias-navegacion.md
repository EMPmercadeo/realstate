# Referencias de navegación para el recorrido 3D (09-11-2026)

Investigación de cómo navegan los recorridos virtuales inmobiliarios actuales, base del rediseño de `/recorrido`.
Solo lo verificado en la documentación de cada producto; lo que no se pudo confirmar va marcado.

## Patrones que se repiten

| Patrón | Quién lo usa | Qué se hizo aquí |
| --- | --- | --- |
| Moverse tocando el piso (círculo o halo), no joystick; el marcador se oculta donde no se puede avanzar | Matterport, iGUIDE, Kuula, Oculo, rooom, Ricoh, Street View | Caminar: tocar/clic en el piso, anillo blanco, no cruza muros. Se quitó el joystick |
| Arrastrar para mirar, pellizcar para acercar, teclado como atajo | Ricoh, Street View, rooom (WASD), Cupix (WASD) | Arrastrar mira; W A S D y flechas caminan |
| Selector de vista con texto (Maqueta / Plano / Interior) en una sola barra abajo | Matterport (barra inferior desde julio 2026), Cupix | Barra: Maqueta · Caminar · Planos |
| Tira de miniaturas abajo con ▶; en celular se pliega | Matterport (Highlight Reel), Ricoh, Kuula, CloudPano | Tira de 13 paradas con ▶; en el celular se pliega al tocar el modelo |
| Recorrido guiado corto (30–90 s) con progreso y CTA al final | Matterport (buenas prácticas, barra de progreso, CTA final), iGUIDE Autoplay | 13 paradas, barra de progreso en la miniatura, "Solicitar información" al terminar |
| Selector de piso pegado al modelo | iGUIDE, Metareal, Ricoh, Matterport | Pila de niveles a la derecha (botón en el celular) |
| Etiquetas solo del piso elegido, sin saturar | Matterport (etiquetas en maqueta), iGUIDE | Etiquetas solo del nivel elegido; máx. 7 en celular |
| Ayuda de gestos solo la primera vez | Matterport (help para usuarios nuevos), model-viewer | Aviso que se va solo a los 6 s o al primer gesto |
| Hoja inferior con X visible, sin hojas apiladas | NN/g (bottom sheets) | "Todos los espacios" como hoja en el celular, con X |
| Botones de 44 pt / 48 dp como mínimo | Apple HIG / Material (vía Adrian Roselli) | Controles de 44 px o más |

No encontrado en la documentación (no se afirma): la posición exacta del selector de piso de Matterport en el
celular y si el Highlight Reel cambió con la barra de 2026. Ningún producto grande tiene un estándar de
"antes/después": aquí va como comparador en un modal, solo cuando el espacio tiene el par de fotos.

## Fuentes

- Matterport — Highlight Reel: https://support.matterport.com/hc/en-us/articles/229858088-What-is-a-Highlight-Reel-
- Matterport — buenas prácticas del tour guiado: https://support.matterport.com/hc/en-us/articles/222595887-Guided-Tour-Best-Practices
- Matterport — controles: https://support.matterport.com/hc/en-us/articles/212625278-Toggle-Controls-for-3D-Showcase
- Matterport — barra inferior nueva (21-07-2026): https://matterport.com/blog/refreshing-the-way-to-explore-your-digital-twins
- Matterport — etiquetas en la maqueta: https://matterport.com/blog/dollhouse-view-just-got-upgrade
- Matterport — Showcase 3.0 (barra de progreso): https://matterport.com/blog/offer-clients-smoother-more-intuitive-experience-showcase-30
- iGUIDE — visor 3D: https://help.youriguide.com/hc/en-us/articles/35800233014674-iGUIDE-3D-Tour-Viewer-Updates
- Ricoh360 Tours — visor: https://help.ricoh360.com/hc/articles/360058178333
- 3DVista — efecto radar en el plano: https://www.3dvista.com/en/kb/faqs/interactivity/what-is-the-radar-effect-on-floor-plans/
- Cupix — navegación en el plano: https://support.cupix.works/support/solutions/articles/70000105466-navigation-in-plan-viewer
- Kuula — recorridos: https://blog.kuula.co/howto-walkthrough
- Oculo — círculos en el piso: https://help.oculo.ai/knowledge/new-navigation-in-360-viewer-floor-circles
- rooom — interacciones: https://help.rooom.com/hc/en-us/articles/4469000666385-Navigation-interactions
- Google Street View: https://support.google.com/maps/answer/3093484
- Zillow 3D Home (plano como navegación): https://www.inman.com/2021/02/17/heres-a-first-look-at-zillow-3d-home-tours-newest-features/
- NN/g — bottom sheets: https://www.nngroup.com/articles/bottom-sheet/
- Tamaño de los objetivos táctiles: https://adrianroselli.com/2019/06/target-size-and-2-5-5.html
