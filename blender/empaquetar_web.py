"""
Deja la prueba web lista para celular (sin Blender; Python normal + Node):
  1. gltfpack cuantiza la geometría (KHR_mesh_quantization, three.js lo lee sin decodificador extra).
  2. El binario se mete dentro del JSON (los artifacts no sirven .bin ni .glb) y el mapa de luz queda aparte
     como JPG, que el navegador baja y decodifica en paralelo.
Antes: correr hornear_web.py y plantas_web.py.  Uso:  python blender/empaquetar_web.py
Resultado en build/web_horneado/: casa.gltf.json, plantas.gltf.json, frente_luz.jpg, frente.json
Medido en un celular emulado (4G, CPU 4x más lenta): de 13,5 MB a 4,2 MB y la casa aparece en 4 s en vez de 15 s.
"""
import os, json, base64, subprocess, shutil

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'web_horneado')
npx = shutil.which('npx') or shutil.which('npx.cmd')
for src, tmp, dst, extra in (('frente_sn.gltf', 'frente_q.gltf', 'casa.gltf.json', ['-tr']),
                             ('frente_plantas.glb', 'frente_plantas_q.gltf', 'plantas.gltf.json', [])):
    subprocess.run([npx, '--yes', 'gltfpack@0.24.0', '-i', src, '-o', tmp, '-kn', '-km'] + extra, cwd=D, check=True)
    g = json.load(open(os.path.join(D, tmp)))
    for b in g['buffers']:
        if 'uri' in b and not b['uri'].startswith('data:'):
            b['uri'] = 'data:application/octet-stream;base64,' + base64.b64encode(open(os.path.join(D, b['uri']), 'rb').read()).decode()
    json.dump(g, open(os.path.join(D, dst), 'w'), separators=(',', ':'))
    print(dst, round(os.path.getsize(os.path.join(D, dst)) / 1e6, 2), 'MB')
