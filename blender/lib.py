"""Helpers para construir la escena con bpy (Blender 5.x como módulo)."""
import os, math
import bpy, bmesh
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEX = os.path.join(ROOT, 'assets', 'textures', 'gen')
_mats = {}
_imgs = {}


def img(path):
    if path not in _imgs:
        im = bpy.data.images.load(path, check_existing=True)
        _imgs[path] = im
    return _imgs[path]


def mat(name, tex=None, color=(0.8, 0.8, 0.8, 1), rough=0.6, metal=0.0, scale=1.0,
        normal_strength=1.0, emission=None, alpha=None, transmission=None, ior=1.45, tint=None):
    """Material Principled. tex = nombre base en assets/textures/gen (usa _color/_rough/_normal)."""
    key = (name, tex, scale)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['IOR'].default_value = ior
    bsdf.inputs['Base Color'].default_value = color
    if emission:
        bsdf.inputs['Emission Color'].default_value = emission[0]
        bsdf.inputs['Emission Strength'].default_value = emission[1]
    if alpha is not None:
        bsdf.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND'
    if transmission is not None:
        bsdf.inputs['Transmission Weight'].default_value = transmission
    if tex:
        uv = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (scale, scale, scale)
        nt.links.new(uv.outputs['UV'], mp.inputs['Vector'])
        c = nt.nodes.new('ShaderNodeTexImage'); c.image = img(f'{TEX}/{tex}_color.jpg')
        nt.links.new(mp.outputs['Vector'], c.inputs['Vector'])
        if tint:
            mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0
            mix.inputs[6].default_value = tint
            nt.links.new(c.outputs['Color'], mix.inputs[7])
            nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])
        else:
            nt.links.new(c.outputs['Color'], bsdf.inputs['Base Color'])
        rp = f'{TEX}/{tex}_rough.jpg'
        if os.path.exists(rp):
            r = nt.nodes.new('ShaderNodeTexImage'); r.image = img(rp); r.image.colorspace_settings.name = 'Non-Color'
            nt.links.new(mp.outputs['Vector'], r.inputs['Vector'])
            nt.links.new(r.outputs['Color'], bsdf.inputs['Roughness'])
        npth = f'{TEX}/{tex}_normal.jpg'
        if os.path.exists(npth):
            n = nt.nodes.new('ShaderNodeTexImage'); n.image = img(npth); n.image.colorspace_settings.name = 'Non-Color'
            nt.links.new(mp.outputs['Vector'], n.inputs['Vector'])
            nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = normal_strength
            nt.links.new(n.outputs['Color'], nm.inputs['Color'])
            nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    _mats[key] = m
    return m


# ---------- colecciones ----------
def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def link(obj, c):
    for uc in obj.users_collection:
        uc.objects.unlink(obj)
    c.objects.link(obj)
    return obj


# ---------- UV box ----------
def box_uv(obj, scale=1.0):
    me = obj.data
    bm = bmesh.new(); bm.from_mesh(me)
    uv_layer = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    mw = obj.matrix_world
    for f in bm.faces:
        n = (mw.to_3x3() @ f.normal)
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for l in f.loops:
            p = mw @ l.vert.co
            if az >= ax and az >= ay:
                u, v = p.x, p.y
            elif ax >= ay:
                u, v = p.y, p.z
            else:
                u, v = p.x, p.z
            l[uv_layer].uv = (u / scale, v / scale)
    bm.to_mesh(me); bm.free()


# ---------- primitivas ----------
def mesh_obj(name, verts, faces, m=None, c=None, uv_scale=1.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    (c or bpy.context.scene.collection).objects.link(ob)
    if m:
        me.materials.append(m)
    box_uv(ob, uv_scale)
    return ob


def box(name, size, loc, m=None, c=None, uv_scale=1.0, rot=0.0):
    """Caja con esquina mínima en loc (x,y,z) y tamaño (sx,sy,sz)."""
    sx, sy, sz = size
    x, y, z = loc
    v = [(0, 0, 0), (sx, 0, 0), (sx, sy, 0), (0, sy, 0), (0, 0, sz), (sx, 0, sz), (sx, sy, sz), (0, sy, sz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = mesh_obj(name, v, f, m, c, uv_scale)
    ob.location = (x, y, z)
    if rot:
        ob.rotation_euler = (0, 0, rot)
    bpy.context.view_layer.update()
    box_uv(ob, uv_scale)
    return ob


def cbox(name, size, center, m=None, c=None, uv_scale=1.0, rot=0.0):
    sx, sy, sz = size
    cx, cy, cz = center
    return box(name, size, (cx - sx / 2, cy - sy / 2, cz - sz / 2), m, c, uv_scale, rot)


def cylinder(name, r, h, loc, m=None, c=None, segs=24, r2=None, uv_scale=1.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    (c or bpy.context.scene.collection).objects.link(ob)
    ob.location = (loc[0], loc[1], loc[2] + h / 2)
    if m:
        me.materials.append(m)
    bpy.context.view_layer.update()
    box_uv(ob, uv_scale)
    return ob


def sphere(name, r, loc, m=None, c=None, subdiv=2):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    (c or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    if m:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    bpy.context.view_layer.update()
    box_uv(ob, 1.0)
    return ob


def cut(target, cutters):
    """Resta cutters (objetos) del target con boolean y los borra."""
    for cu in cutters:
        mod = target.modifiers.new('cut', 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = cu
        mod.solver = 'EXACT'
    bpy.context.view_layer.objects.active = target
    for nm in [m.name for m in target.modifiers]:
        bpy.ops.object.modifier_apply(modifier=nm)
    for cu in cutters:
        bpy.data.objects.remove(cu, do_unlink=True)
    box_uv(target, target.get('uv_scale', 1.0))
    return target


def join(objs, name):
    """Une objetos en uno y deja el origen del resultado en el (0,0,0) del mundo."""
    if not objs:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return ob


def smooth(ob, angle=35):
    for p in ob.data.polygons:
        p.use_smooth = True
    mod = ob.modifiers.new('bevel', 'BEVEL')
    mod.width = 0.02
    mod.segments = 2
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(angle)


def set_parent(ob, parent):
    """Parenta conservando las coordenadas locales (el hijo se mueve con el padre)."""
    ob.parent = parent
    ob.matrix_parent_inverse.identity()


def empty(name, loc=(0, 0, 0), rot=0.0, c=None):
    e = bpy.data.objects.new(name, None)
    (c or bpy.context.scene.collection).objects.link(e)
    e.location = loc
    e.rotation_euler = (0, 0, rot)
    return e


def leaf_mat(name, png):
    """Material de follaje con alpha (imagen RGBA)."""
    key = ('leaf', name)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(png)
    nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(t.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 0.8
    try:
        m.surface_render_method = 'DITHERED'
    except Exception:
        m.blend_method = 'HASHED'
    m.use_backface_culling = False
    _mats[key] = m
    return m


def card(name, w, h, m, c=None, pivot='bottom'):
    """Plano vertical w×h con UV 0..1 (pivot en la base o en el centro)."""
    z0 = 0 if pivot == 'bottom' else -h / 2
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, 0, z0), (w / 2, 0, z0), (w / 2, 0, z0 + h), (-w / 2, 0, z0 + h)], [], [(0, 1, 2, 3)])
    me.update()
    uv = me.uv_layers.new(name='UVMap')
    for i, co in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = co
    ob = bpy.data.objects.new(name, me)
    (c or bpy.context.scene.collection).objects.link(ob)
    me.materials.append(m)
    return ob
