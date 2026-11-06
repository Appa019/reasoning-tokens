# Shared clay stop-motion toolkit: scene reset, clay materials, primitives, lights and Cycles/OptiX setup.
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector


FONTE = os.path.expanduser("~/.local/share/fonts/pptx-studio/Archivo-Bold.ttf")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def rgb(h):
    h = h.lstrip("#")
    return tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)) + (1.0,)


def vazio(nome, loc=(0, 0, 0), p=None):
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    e.location = loc
    return pai(e, p)


def pai(o, p):
    if p is None:
        return o
    bpy.context.view_layer.update()
    o.parent = p
    o.matrix_parent_inverse = p.matrix_world.inverted()
    return o


# Texture-space anchors: the puppets' anchor jitters every frame so the clay surface "boils" like hand-posed clay.
BOIL_BONECO = vazio("boil_boneco")
BOIL_SET = vazio("boil_set")
TEX_ARGILA = bpy.data.textures.new("argila", "CLOUDS")
TEX_ARGILA.noise_scale, TEX_ARGILA.noise_depth = 0.09, 2

MATS = {}


def clay(nome, cor, rough=0.5, sss=0.12, bump=1.0, sulcos=None, var=0.07, boneco=True, cor2=None):
    """Plasticine: subsurface, uneven colour, thumb dents, fine grain, scattered fingerprints, grime in creases."""
    if nome in MATS:
        return MATS[nome]
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    b.inputs["Subsurface Weight"].default_value = sss
    b.inputs["Subsurface Scale"].default_value = 0.02
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.25)
    b.inputs["Specular IOR Level"].default_value = 0.55
    tc = N.new("ShaderNodeTexCoord")
    tc.object = BOIL_BONECO if boneco else BOIL_SET
    co = tc.outputs["Object"]

    def tex(tipo, **inp):
        t = N.new(tipo)
        for k, v in inp.items():
            t.inputs[k].default_value = v
        L.new(co, t.inputs["Vector"])
        return t

    def op(oper, a, bb, clamp=False):
        n = N.new("ShaderNodeMath")
        n.operation, n.use_clamp = oper, clamp
        for i, x in enumerate((a, bb)):
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]

    def faixa(sock, de0, de1, para0=0.0, para1=1.0):
        n = N.new("ShaderNodeMapRange")
        n.clamp = True
        n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = de0, de1
        n.inputs["To Min"].default_value, n.inputs["To Max"].default_value = para0, para1
        L.new(sock, n.inputs["Value"])
        return n.outputs["Result"]

    # colour: base (or two-tone wood grain) times low-frequency unevenness, plus a little grime in creases
    if sulcos == "madeira":
        veio = tex("ShaderNodeTexWave", Scale=5.0, Distortion=4.0, Detail=2.0)
        veio.bands_direction = "Z"
        mixw = N.new("ShaderNodeMixRGB")
        mixw.inputs["Color1"].default_value, mixw.inputs["Color2"].default_value = rgb(cor), rgb(cor2 or cor)
        L.new(veio.outputs["Fac"], mixw.inputs["Fac"])
        base = mixw.outputs["Color"]
    else:
        base = None
    nv = tex("ShaderNodeTexNoise", Scale=4.0, Detail=3.0)
    mul = N.new("ShaderNodeMixRGB")
    mul.blend_type = "MULTIPLY"
    mul.inputs["Fac"].default_value = 1.0
    if base:
        L.new(base, mul.inputs["Color1"])
    else:
        mul.inputs["Color1"].default_value = rgb(cor)
    L.new(faixa(nv.outputs["Fac"], 0.3, 0.7, 1 - var, 1 + var), mul.inputs["Color2"])
    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.06
    L.new(mul.outputs["Color"], ao.inputs["Color"])
    suj = N.new("ShaderNodeMixRGB")
    suj.inputs["Fac"].default_value = 0.35
    L.new(mul.outputs["Color"], suj.inputs["Color1"])
    L.new(ao.outputs["Color"], suj.inputs["Color2"])
    # lint and dust picked up from fingers and the table: sparse dark specks
    pts = tex("ShaderNodeTexVoronoi", Scale=220.0)
    pts.feature = "F1"
    sel = tex("ShaderNodeTexNoise", Scale=60.0)
    cisco = N.new("ShaderNodeMixRGB")
    cisco.inputs["Color2"].default_value = (0.05, 0.045, 0.04, 1)
    L.new(op("MULTIPLY", faixa(pts.outputs["Distance"], 0.05, 0.09, 0.7, 0.0), faixa(sel.outputs["Fac"], 0.6, 0.64)),
          cisco.inputs["Fac"])
    L.new(suj.outputs["Color"], cisco.inputs["Color1"])
    L.new(cisco.outputs["Color"], b.inputs["Base Color"])

    # height: thumb dents + creases + grain + fingerprints in patches (+ hair strands / knit ribs)
    n1 = tex("ShaderNodeTexNoise", Scale=9.0, Detail=2.0)
    vo = tex("ShaderNodeTexVoronoi", Scale=14.0)
    vo.feature = "DISTANCE_TO_EDGE"
    n2 = tex("ShaderNodeTexNoise", Scale=180.0, Detail=6.0)
    dig = tex("ShaderNodeTexWave", Scale=90.0, Distortion=3.0)
    dig.wave_type = "RINGS"
    mask = tex("ShaderNodeTexNoise", Scale=5.0)
    h = op("MULTIPLY", n1.outputs["Fac"], 0.8)
    h = op("ADD", h, op("MULTIPLY", faixa(vo.outputs["Distance"], 0.0, 0.08), 0.08))
    h = op("ADD", h, op("MULTIPLY", n2.outputs["Fac"], 0.12))
    h = op("ADD", h, op("MULTIPLY", op("MULTIPLY", dig.outputs["Fac"], faixa(mask.outputs["Fac"], 0.46, 0.54)), 0.4))
    if sulcos == "cabelo":
        fio = tex("ShaderNodeTexWave", Scale=45.0, Distortion=2.5, Detail=2.0)
        fio.bands_direction = "X"
        h = op("ADD", h, op("MULTIPLY", fio.outputs["Fac"], 0.55))
    elif sulcos == "trico":
        rib = tex("ShaderNodeTexWave", Scale=55.0, Distortion=0.6)
        rib.bands_direction = "X"
        h = op("ADD", h, op("MULTIPLY", rib.outputs["Fac"], 0.35))
    elif sulcos == "carpete":
        h = op("ADD", h, op("MULTIPLY", tex("ShaderNodeTexNoise", Scale=600.0, Detail=4.0).outputs["Fac"], 0.6))
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.55 * bump
    bp.inputs["Distance"].default_value = 0.004
    L.new(h, bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    MATS[nome] = m
    return m


def simples(nome, cor, rough=0.4, emissao=0.0, metal=0.0):
    if nome in MATS:
        return MATS[nome]
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgb(cor)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emissao:
        b.inputs["Emission Color"].default_value = rgb(cor)
        b.inputs["Emission Strength"].default_value = emissao
    MATS[nome] = m
    return m


def _liso(o):
    for f in o.data.polygons:
        f.use_smooth = True


def _argila(o, forca=0.006):
    """Hand-made unevenness: subdivide, then push the surface with a clouds texture tied to the boil anchor."""
    o.modifiers.new("sub", "SUBSURF").levels = 1
    o.modifiers["sub"].render_levels = 2
    d = o.modifiers.new("disp", "DISPLACE")
    d.texture, d.texture_coords, d.texture_coords_object = TEX_ARGILA, "OBJECT", BOIL_BONECO
    d.strength, d.mid_level = forca, 0.5


def blob(nome, loc, esc, mat, p=None, rot=(0, 0, 0), forca=0.009):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name, o.scale = nome, esc
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _liso(o)
    if forca:
        _argila(o, forca)
    o.data.materials.append(mat)
    return pai(o, p)


def caixa(nome, loc, dim, mat, p=None, bev=0.02, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name, o.scale = nome, dim
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bev:
        md = o.modifiers.new("bev", "BEVEL")
        md.width, md.segments, md.limit_method = bev, 5, "NONE"
        md.harden_normals = True
    _liso(o)
    o.data.materials.append(mat)
    return pai(o, p)


def cilindro(nome, loc, r, h, mat, p=None, rot=(0, 0, 0), bev=0.008, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = nome
    if bev:
        md = o.modifiers.new("bev", "BEVEL")
        md.width, md.segments, md.limit_method = bev, 4, "ANGLE"
        md.harden_normals = True
    _liso(o)
    o.data.materials.append(mat)
    return pai(o, p)


def toro(nome, loc, R, r, mat, p=None, rot=(0, 0, 0), esc=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot,
                                     major_segments=48, minor_segments=12)
    o = bpy.context.active_object
    o.name, o.scale = nome, esc
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _liso(o)
    o.data.materials.append(mat)
    return pai(o, p)


def bastao(nome, a, b, r, mat, p=None):
    """Rounded rod between two points (pens, lanyard straps)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    o = blob(nome, (a + b) / 2, (r, r, d.length / 2), mat, None, rot=d.to_track_quat("Z", "Y").to_euler(), forca=0)
    return pai(o, p)


def calota(nome, raio, loc, mat, p=None):
    """Upper hemisphere shell, used as an eyelid that rotates around the eye centre."""
    me = bpy.data.meshes.new(nome)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=raio)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-5], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nome, me)
    sc.collection.objects.link(o)
    o.location = loc
    o.modifiers.new("sol", "SOLIDIFY").thickness = 0.006
    o.modifiers.new("sub", "SUBSURF").render_levels = 2
    _liso(o)
    o.data.materials.append(mat)
    return pai(o, p)


FONT = bpy.data.fonts.load(FONTE) if os.path.exists(FONTE) else None


def texto(nome, corpo, loc, tam, mat, p=None, rot=(math.pi / 2, 0, 0)):
    cu = bpy.data.curves.new(nome, "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y, cu.space_line = corpo, tam, "CENTER", "CENTER", 0.9
    if FONT:
        cu.font = FONT
    o = bpy.data.objects.new(nome, cu)
    sc.collection.objects.link(o)
    o.location, o.rotation_euler = loc, rot
    o.data.materials.append(mat)
    return pai(o, p)


def mirar(o, alvo):
    o.rotation_euler = (Vector(alvo) - o.location).to_track_quat("-Z", "Y").to_euler()


PRETO = clay("preto", "#141416", rough=0.25, sss=0.0, bump=0.4)
OLHO = clay("olho", "#F4F2EA", rough=0.18, sss=0.05, bump=0.25, var=0.02)
BOCA = clay("boca", "#3A1111", rough=0.45, sss=0.05)
DENTE = clay("dente", "#F3EFE2", rough=0.3, bump=0.3, var=0.02)
PAPEL = simples("papel", "#F7F7F4", rough=0.75)
TINTA = simples("tinta", "#151515", rough=0.6)


def luz(nome, loc, alvo, w, tam, cor=(1.0, 0.92, 0.82)):
    ld = bpy.data.lights.new(nome, "AREA")
    ld.energy, ld.size, ld.color = w, tam, cor
    o = bpy.data.objects.new(nome, ld)
    sc.collection.objects.link(o)
    o.location = loc
    mirar(o, alvo)
    return ld


def configurar_render(amostras, largura=1080, altura=1350):
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = largura, altura, 100
    r.fps = 12
    r.engine = "CYCLES"
    r.use_persistent_data = True
    cy = sc.cycles
    cy.device, cy.samples, cy.use_adaptive_sampling, cy.adaptive_threshold = "GPU", amostras, True, 0.02
    cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces = 6, 3, 3
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    cy.use_denoising, cy.denoiser = True, "OPTIX"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = -0.3
    sc.view_settings.look = "AgX - Punchy"
    return r
