"""Prepara la carpeta publish/ (rutas relativas) a partir de web/dist para publicarla como artefacto."""
import glob, os, json, shutil
ROOT = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(ROOT, 'publish')
shutil.rmtree(P, ignore_errors=True)
os.makedirs(os.path.join(P, 'modelo'))
shutil.copytree(os.path.join(ROOT, 'web/dist/_astro'), os.path.join(P, 'assets'))
shutil.copytree(os.path.join(ROOT, 'web/public/draco'), os.path.join(P, 'draco'))
for f in ('draco_encoder.js',):
    try: os.remove(os.path.join(P, 'draco', f))
    except FileNotFoundError: pass
shutil.copy(os.path.join(ROOT, 'web/public/modelo/escena.glb'), os.path.join(P, 'modelo/escena.wasm'))
for d in ('fotos-antes', 'fotos-despues'):
    shutil.copytree(os.path.join(ROOT, 'web/public', d), os.path.join(P, d))
s = open(os.path.join(ROOT, 'web/dist/recorrido/index.html')).read().replace('"/_astro/', '"assets/')
for a, b in [('href="/"', 'href="#"'), ('href="/#proyecto"', 'href="#"'), ('href="/#espacios"', 'href="#"'), ('href="/blog"', 'href="#"'), ('href="/recorrido"', 'href="#"')]:
    s = s.replace(a, b)
s = s.replace('<title>Recorrido 3D · Residencia Altos de San Cristóbal</title>', '<title>Recorrido 3D Residencia</title>').replace('<body>', '<body data-base="./">')
open(os.path.join(P, 'index.html'), 'w').write(s)
for f in glob.glob(os.path.join(P, 'assets/*.js')):
    t = open(f).read().replace('`/draco/`', '`draco/`').replace('"/draco/"', '"draco/"').replace('modelo/escena.glb', 'modelo/escena.wasm')
    open(f, 'w').write(t)
files = {}
for f in glob.glob(os.path.join(P, 'assets/*')): files['assets/' + os.path.basename(f)] = f
for n in ('draco_decoder.js', 'draco_decoder.wasm', 'draco_wasm_wrapper.js'): files['draco/' + n] = os.path.join(P, 'draco', n)
files['modelo/escena.wasm'] = os.path.join(P, 'modelo/escena.wasm')
for d in ('fotos-antes', 'fotos-despues'):
    for f in glob.glob(os.path.join(P, d, '*.jpg')): files[f'{d}/{os.path.basename(f)}'] = f
json.dump(files, open(os.path.join(P, 'files.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in files.items() if k.startswith('assets') or k.startswith('modelo')}))
