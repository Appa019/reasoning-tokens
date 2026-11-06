# Turns an AI-sculpted GLB (Hunyuan3D) into a stop-motion puppet: real scale, puppet materials, glass domes over the eyes.
import math
import os

import numpy as np
import bpy
from mathutils import Quaternion, Vector

import massinha as M


def importar(glb, altura):
    """Import, stand the mesh on the floor centred on the origin and scale it to `altura` metres."""
    antes = set(M.sc.objects)
    bpy.ops.import_scene.gltf(filepath=glb, merge_vertices=True)
    o = next(x for x in M.sc.objects if x not in antes and x.type == "MESH")
    bpy.context.view_layer.update()
    co = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mw = np.array(o.matrix_world)
    pts = co @ mw[:3, :3].T + mw[:3, 3]
    k = altura / (pts[:, 2].max() - pts[:, 2].min())
    o.scale = [s * k for s in o.scale]
    o.location = Vector(((mw[0, 3] - pts[:, 0].mean()) * k, (mw[1, 3] - pts[:, 1].mean()) * k,
                         (mw[2, 3] - pts[:, 2].min()) * k))
    for f in o.data.polygons:
        f.use_smooth = True
    bpy.context.view_layer.update()
    return o


def material_boneco(o):
    """Painted-silicone skin and wool: a little subsurface, fabric sheen, fine hand-made grain and fingerprints."""
    for m in o.data.materials:
        nt = m.node_tree
        N, L = nt.nodes, nt.links
        b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
        b.inputs["Roughness"].default_value = 0.62
        b.inputs["Subsurface Weight"].default_value = 0.12
        b.inputs["Subsurface Scale"].default_value = 0.006
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.25)
        b.inputs["Sheen Weight"].default_value = 0.35
        b.inputs["Sheen Roughness"].default_value = 0.45
        for e in list(b.inputs["Roughness"].links) + list(b.inputs["Metallic"].links):
            L.remove(e)
        b.inputs["Metallic"].default_value = 0.0
        tc = N.new("ShaderNodeTexCoord")
        grao = N.new("ShaderNodeTexNoise")
        grao.inputs["Scale"].default_value, grao.inputs["Detail"].default_value = 260.0, 6.0
        dig = N.new("ShaderNodeTexWave")
        dig.wave_type = "RINGS"
        dig.inputs["Scale"].default_value, dig.inputs["Distortion"].default_value = 140.0, 3.0
        mask = N.new("ShaderNodeTexNoise")
        mask.inputs["Scale"].default_value = 7.0
        for t in (grao, dig, mask):
            L.new(tc.outputs["Object"], t.inputs["Vector"])
        faixa = N.new("ShaderNodeMapRange")
        faixa.inputs["From Min"].default_value, faixa.inputs["From Max"].default_value = 0.56, 0.62
        L.new(mask.outputs["Fac"], faixa.inputs["Value"])
        mdig = N.new("ShaderNodeMath")
        mdig.operation = "MULTIPLY"
        L.new(dig.outputs["Fac"], mdig.inputs[0])
        L.new(faixa.outputs["Result"], mdig.inputs[1])
        soma = N.new("ShaderNodeMath")
        L.new(grao.outputs["Fac"], soma.inputs[0])
        L.new(mdig.outputs[0], soma.inputs[1])
        bump = N.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value, bump.inputs["Distance"].default_value = 0.1, 0.0015
        L.new(soma.outputs[0], bump.inputs["Height"])
        L.new(bump.outputs["Normal"], b.inputs["Normal"])


def _textura(o):
    m = o.data.materials[0]
    img = next(n.image for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(h, w, 4), w, h


def olhos_de_vidro(o, z0=None, z1=None, larg=0.12, passo=0.002):
    """Find the painted eyes by ray casting the face from the front (their whites; dark iris pixels as a fallback),
    then cap each eye with a clear glass dome sized from it."""
    if z0 is None:
        # altura_olhos() lands on the brows/fringe on these heads; the eyes sit up to ~7 cm below it
        zc = altura_olhos(o)
        z0, z1 = zc - 0.11, zc + 0.03
    tex, w, h = _textura(o)
    inv = o.matrix_world.inverted()
    me = o.data
    uv = me.uv_layers.active.data
    dg = bpy.context.evaluated_depsgraph_get()
    brancos, escuros = [], []
    for x in np.arange(-larg, larg, passo):
        for z in np.arange(z0, z1, passo):
            ini = inv @ Vector((x, -3.0, z))
            dirl = (inv.to_3x3() @ Vector((0, 1, 0))).normalized()
            ok, loc, nor, fi = o.ray_cast(ini, dirl, depsgraph=dg)
            if not ok:
                continue
            p = me.polygons[fi]
            vs = [me.vertices[i].co for i in p.vertices]
            # barycentric UV on the (triangle) face
            a, b, c = vs[0], vs[1], vs[2]
            v0, v1, v2 = b - a, c - a, loc - a
            d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
            den = d00 * d11 - d01 * d01 or 1e-12
            bv, bw = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
            u = (1 - bv - bw) * uv[p.loop_start].uv + bv * uv[p.loop_start + 1].uv + bw * uv[p.loop_start + 2].uv
            cor = tex[min(h - 1, int(u.y * h)), min(w - 1, int(u.x * w)), :3]
            mundo = o.matrix_world @ loc
            if mundo.y > -0.13:  # hair and the back of the head sit further back than the face
                continue
            if cor.max() < 0.55:  # iris / pupil, but also brows and lashes
                escuros.append(mundo)
            elif cor.min() > 0.6 and cor.max() - cor.min() < 0.15:  # neutral white: the sclera, nothing else up here
                brancos.append(mundo)
    # clear varnish, not a lens: reflections only (Fresnel-weighted gloss over transparent), so from a three-quarter
    # angle the painted eye is not refracted out of place and no lens rim shows on the brow
    vidro = bpy.data.materials.new("vidro_olho")
    vidro.use_nodes = True
    nt = vidro.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    brilho, transp, mix = (nt.nodes.new(t) for t in ("ShaderNodeBsdfGlossy", "ShaderNodeBsdfTransparent", "ShaderNodeMixShader"))
    fres = nt.nodes.new("ShaderNodeFresnel")
    brilho.inputs["Roughness"].default_value = 0.03
    fres.inputs["IOR"].default_value = 1.45
    nt.links.new(fres.outputs[0], mix.inputs[0])
    nt.links.new(transp.outputs[0], mix.inputs[1])
    nt.links.new(brilho.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    domos = []
    for lado in (-1, 1):
        # the sclera centres the dome on the eye; dark pixels (pulled up by the brows) only as a fallback
        pts = [p for p in brancos if p.x * lado > 0.006]
        if len(pts) < 20:
            pts = [p for p in escuros if p.x * lado > 0.006]
        if len(pts) < 6:
            print("eye not found on side", lado, len(pts))
            continue
        xs, zs, ys = (np.percentile([getattr(p, k) for p in pts], (5, 50, 95)) for k in "xzy")
        c = Vector(((xs[0] + xs[2]) / 2, ys[1], (zs[0] + zs[2]) / 2))
        r = min(0.045, (xs[2] - xs[0]) / 2 * 1.1)
        rz = min(r, max(0.6 * r, (zs[2] - zs[0]) / 2 * 1.15))
        d = M.blob(f"domo{lado}", (c.x, c.y + 0.003, c.z), (r, r * 0.3, rz), vidro, forca=0)  # seated on the eye
        d.visible_shadow = False
        domos.append(d)
        print("eye", lado, tuple(round(v, 3) for v in c), round(r, 3), round(rz, 3), len(pts))
    return domos


def decimar(o, faces=120_000):
    """Fewer triangles so automatic weights and per-frame booleans stay fast; UVs and texture are kept."""
    d = o.modifiers.new("dec", "DECIMATE")
    d.ratio = min(1.0, faces / len(o.data.polygons))
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=d.name)


def _pontos(o):
    co = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", co)
    mw = np.array(o.matrix_world)
    return co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]


def ossos(o):
    """Bone layout measured from horizontal slices of the A-pose mesh (the puppet faces -Y, +X is its left):
    crotch = top of the gap between the legs, armpit = top of the gap between arm and torso, hand bottom = lowest
    slice with that gap; joints placed with the ratios that fit Ana. Returns [(bone, parent, head, tail)]."""
    p = _pontos(o)
    pescoco, topo = medir_cabeca(o)
    virilha, axila, mao_z = 0.0, 0.0, None
    for z in np.arange(0.02 * topo, 0.75 * topo, 0.005):
        xs = np.sort(p[np.abs(p[:, 2] - z) < 0.004, 0])
        if len(xs) < 20:
            continue
        for a, b in zip(xs[:-1], xs[1:]):
            if b - a > 0.02 and a < 0 < b:
                virilha = z
            elif b - a > 0.02 and a > 0.05:  # gap on the puppet's left between torso and arm
                axila = z
                mao_z = z if mao_z is None else mao_z
    mao_z = mao_z or 0.35 * topo
    fatia = p[np.abs(p[:, 2] - (axila + 0.05)) < 0.01]
    meia = np.percentile(np.abs(fatia[:, 0]), 98)
    ombro = axila + 0.7 * (pescoco - axila)
    pulso = mao_z + 0.45 * (axila - mao_z)
    cotovelo = pulso + 0.45 * (ombro - pulso)

    def braco_x(z):  # centre of the arm at height z (between the gap and the outermost point)
        f = p[(np.abs(p[:, 2] - z) < 0.006) & (p[:, 0] > 0.05)]
        return float((np.sort(f[:, 0])[-1] + meia * 0.9) / 2) if len(f) else meia

    print("bones: crotch %.2f armpit %.2f hand %.2f neck %.2f top %.2f half-width %.2f" %
          (virilha, axila, mao_z, pescoco, topo, meia))
    xo, xc, xp, xm = 0.85 * meia, braco_x(cotovelo), braco_x(pulso), braco_x(mao_z + 0.02)
    b = [("quadril", None, (0, 0.01, virilha + 0.04), (0, 0.01, axila - 0.03)),
         ("coluna", "quadril", (0, 0.01, axila - 0.03), (0, 0.01, ombro - 0.07)),
         ("peito", "coluna", (0, 0.01, ombro - 0.07), (0, 0.01, pescoco - 0.06)),
         ("pescoco", "peito", (0, 0.01, pescoco - 0.06), (0, 0.0, pescoco + 0.04)),
         ("cabeca", "pescoco", (0, 0.0, pescoco + 0.04), (0, 0.0, topo - 0.04))]
    for s_, l in ((1, "L"), (-1, "R")):
        b += [(f"ombro.{l}", "peito", (s_ * 0.05, 0.01, ombro + 0.03), (s_ * xo, 0.01, ombro)),
              (f"braco.{l}", f"ombro.{l}", (s_ * xo, 0.01, ombro), (s_ * xc, 0.01, cotovelo)),
              (f"antebraco.{l}", f"braco.{l}", (s_ * xc, 0.01, cotovelo), (s_ * xp, 0.0, pulso)),
              (f"mao.{l}", f"antebraco.{l}", (s_ * xp, 0.0, pulso), (s_ * xm, -0.01, mao_z + 0.02)),
              (f"coxa.{l}", "quadril", (s_ * 0.1, 0.01, virilha + 0.04), (s_ * 0.12, 0.0, virilha * 0.53)),
              (f"canela.{l}", f"coxa.{l}", (s_ * 0.12, 0.0, virilha * 0.53), (s_ * 0.13, 0.03, 0.07))]
    return b


def esqueleto(o, lista=None):
    """Armature skinned to the puppet. Heat weighting fails on the AI mesh (open seams, overlapping shells), so the
    weights are solved on a watertight voxel proxy and transferred to the real mesh."""
    lista = lista or ossos(o)  # measure on the full mesh: slices of a decimated one are too sparse
    arm = bpy.data.objects.new("rig", bpy.data.armatures.new("rig"))
    M.sc.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    for nome, pai_, a, b in lista:
        e = eb.new(nome)
        e.head, e.tail = a, b
        if pai_:
            e.parent = eb[pai_]
            e.use_connect = (Vector(eb[pai_].tail) - Vector(a)).length < 1e-4
    bpy.ops.object.mode_set(mode="OBJECT")
    proxy = bpy.data.objects.new("proxy", o.data.copy())
    M.sc.collection.objects.link(proxy)
    proxy.matrix_world = o.matrix_world
    rm = proxy.modifiers.new("r", "REMESH")
    rm.mode, rm.voxel_size = "VOXEL", 0.01 / max(o.scale)
    bpy.context.view_layer.update()
    proxy.data = bpy.data.meshes.new_from_object(proxy.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    proxy.modifiers.clear()
    bpy.ops.object.select_all(action="DESELECT")
    proxy.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    for g in proxy.vertex_groups:
        o.vertex_groups.new(name=g.name)
    dt = o.modifiers.new("pesos", "DATA_TRANSFER")
    dt.object, dt.use_vert_data, dt.data_types_verts = proxy, True, {"VGROUP_WEIGHTS"}
    dt.vert_mapping, dt.layers_vgroup_select_src, dt.layers_vgroup_select_dst = "POLYINTERP_NEAREST", "ALL", "NAME"
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.modifier_apply(modifier=dt.name)
    bpy.data.objects.remove(proxy)
    _cabeca_rigida(o, arm)
    mw = o.matrix_world.copy()
    o.parent = arm
    o.matrix_world = mw
    o.modifiers.new("rig", "ARMATURE").object = arm
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
    return arm


def _cabeca_rigida(o, arm, abaixo=0.01, acima=0.04):
    """A puppet head is one rigid piece: above the neck joint the transferred weights (head blended with neck) are
    faded into the head bone, so the glass eye domes, parented to that bone, stay on the painted eyes when it turns."""
    zc = arm.data.bones["cabeca"].head_local.z
    g = o.vertex_groups["cabeca"]
    mw = o.matrix_world
    for v in o.data.vertices:
        k = min(max(((mw @ v.co).z - zc + abaixo) / (abaixo + acima), 0.0), 1.0)
        if k == 0.0:
            continue
        w = 0.0
        for ge in v.groups:
            if ge.group == g.index:
                w = ge.weight
            else:
                ge.weight *= 1.0 - k
        g.add([v.index], w * (1.0 - k) + k, "REPLACE")


def _amostrar(o, z0, z1, larg, cond, passo=0.002):
    """World points on the front of the mesh whose texture colour satisfies cond(rgb)."""
    tex, w, h = _textura(o)
    inv = o.matrix_world.inverted()
    me = o.data
    uv = me.uv_layers.active.data
    dg = bpy.context.evaluated_depsgraph_get()
    dirl = (inv.to_3x3() @ Vector((0, 1, 0))).normalized()
    pts = []
    for x in np.arange(-larg, larg, passo):
        for z in np.arange(z0, z1, passo):
            ok, loc, nor, fi = o.ray_cast(inv @ Vector((x, -3.0, z)), dirl, depsgraph=dg)
            if not ok:
                continue
            p = me.polygons[fi]
            u = uv[p.loop_start].uv
            if cond(tex[min(h - 1, int(u.y * h)), min(w - 1, int(u.x * w)), :3]):
                pts.append(o.matrix_world @ loc)
    return pts


def boca(o, arm, z0, z1):
    """Hidden cutter over the painted lips, parented to the head bone; scaling it per frame opens the mouth."""
    pts = _amostrar(o, z0, z1, 0.06, lambda c: c[0] > 0.6 and c[0] - c[1] > 0.17)
    c = sum(pts, Vector()) / len(pts)
    larg = (max(p.x for p in pts) - min(p.x for p in pts)) / 2
    print("mouth", tuple(round(v, 3) for v in c), round(larg, 3), len(pts))
    # deep, matte, almost black cavity so the opening reads as a hole, with upper teeth and a tongue inside
    interior = M.clay("boca_int", "#1E0707", rough=0.9, sss=0.0, bump=0.2)
    cut = M.blob("boca", (c.x, c.y + 0.012, c.z), (larg * 0.75, 0.035, 0.02), interior, forca=0)
    cut.hide_render, cut.display_type = True, "WIRE"
    dentes = M.blob("dentes", (c.x, c.y - 0.006, c.z + 0.011), (larg * 0.55, 0.012, 0.005), M.DENTE, forca=0)
    lingua = M.blob("lingua", (c.x, c.y + 0.004, c.z - 0.012), (larg * 0.5, 0.02, 0.008),
                    M.clay("lingua", "#8E3B3B", rough=0.5, sss=0.2), forca=0)
    M.pai(dentes, cut)
    M.pai(lingua, cut)
    _no_osso(cut, arm, "cabeca")
    b = o.modifiers.new("boca", "BOOLEAN")
    b.operation, b.solver, b.object, b.material_mode = "DIFFERENCE", "EXACT", cut, "TRANSFER"
    o.data.materials.append(interior)
    return cut, dentes


def _no_osso(obj, arm, osso):
    bpy.context.view_layer.update()
    mw = obj.matrix_world.copy()
    obj.parent, obj.parent_type, obj.parent_bone = arm, "BONE", osso
    bpy.context.view_layer.update()
    obj.matrix_world = mw


def palpebras(arm, domos, cor="#E9C3AE"):
    """Skin-coloured lids hugging the glass domes. Hidden while the eye is open; rotating the pivot about X closes them
    (pi/4 half, pi/2 shut)."""
    mat = M.clay("palpebra", cor, sss=0.2, bump=0.4, var=0.03)
    lids = []
    for d in domos:
        piv = M.vazio(d.name + "_piv", d.location)
        tampa = M.calota(d.name + "_lid", 1.0, d.location, mat, piv)
        piv.scale = Vector(d.dimensions) / 2 * 1.15
        _no_osso(piv, arm, "cabeca")
        _no_osso(d, arm, "cabeca")
        lids.append((piv, tampa))
    return lids


def medir_cabeca(o):
    """(neck z, top z): the neck is the narrowest horizontal slice between 65% and 85% of the height."""
    p = _pontos(o)
    topo = p[:, 2].max()
    zs = np.arange(0.65 * topo, 0.85 * topo, 0.01)
    larg = [np.ptp(p[np.abs(p[:, 2] - z) < 0.005, 0]) if np.any(np.abs(p[:, 2] - z) < 0.005) else 9 for z in zs]
    return float(zs[int(np.argmin(larg))]), float(topo)


def altura_olhos(o):
    pescoco, topo = medir_cabeca(o)
    return pescoco + 0.55 * (topo - pescoco)


def projetor(o, z=None, escala=None):
    """Orthographic camera framing the face head-on; the same camera renders the source and projects the edits.
    Pass the z/scale a face set was rendered with to reuse it; otherwise they come from the head measurements."""
    pescoco, topo = medir_cabeca(o)
    cam = bpy.data.objects.new("projetor", bpy.data.cameras.new("projetor"))
    M.sc.collection.objects.link(cam)
    cam.data.type, cam.data.ortho_scale = "ORTHO", escala or 0.9 * (topo - pescoco)
    cam.location = (0, -1.0, z or altura_olhos(o) - 0.04)
    print("projector", round(cam.location.z, 3), round(cam.data.ortho_scale, 3))
    cam.rotation_euler = (1.5707963, 0, 0)
    return cam


def rostos(o, proj, arquivos):
    """Replacement faces, like printed faces on a stop-motion puppet: each AI-edited face image (RGBA, alpha = the
    feathered zone that changed) is projected from the projector camera in rest pose, so it follows the head.
    Returns {name: Value node}; set a node to 1 to show that face on a frame."""
    up = o.modifiers.new("rosto_uv", "UV_PROJECT")
    o.data.uv_layers.new(name="proj")
    up.uv_layer, up.projector_count = "proj", 1
    up.projectors[0].object = proj
    o.modifiers.move(o.modifiers.find(up.name), 0)  # UVs from the rest pose, before the armature deforms the mesh
    chaves = {}
    for m in o.data.materials:
        nt = m.node_tree
        N, L = nt.nodes, nt.links
        b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
        cor = b.inputs["Base Color"].links[0].from_socket
        uvn = N.new("ShaderNodeUVMap")
        uvn.uv_map = "proj"
        # only surfaces facing the projector (the face), never the back of the head
        geo = N.new("ShaderNodeNewGeometry")  # world-space normal: the imported object carries a Y-up rotation
        sep = N.new("ShaderNodeSeparateXYZ")
        L.new(geo.outputs["Normal"], sep.inputs[0])
        frente = N.new("ShaderNodeMapRange")
        frente.inputs["From Min"].default_value, frente.inputs["From Max"].default_value = -0.45, -0.75
        L.new(sep.outputs["Y"], frente.inputs["Value"])
        for nome, caminho in arquivos.items():
            img = N.new("ShaderNodeTexImage")
            img.image = bpy.data.images.load(caminho, check_existing=True)
            img.extension = "CLIP"
            L.new(uvn.outputs["UV"], img.inputs["Vector"])
            liga = N.new("ShaderNodeValue")
            liga.name = liga.label = "liga_" + nome
            liga.outputs[0].default_value = 0.0
            f1 = N.new("ShaderNodeMath")
            f1.operation = "MULTIPLY"
            L.new(img.outputs["Alpha"], f1.inputs[0])
            L.new(liga.outputs[0], f1.inputs[1])
            f2 = N.new("ShaderNodeMath")
            f2.operation = "MULTIPLY"
            L.new(f1.outputs[0], f2.inputs[0])
            L.new(frente.outputs["Result"], f2.inputs[1])
            mix = N.new("ShaderNodeMixRGB")
            L.new(f2.outputs[0], mix.inputs["Fac"])
            L.new(cor, mix.inputs["Color1"])
            L.new(img.outputs["Color"], mix.inputs["Color2"])
            cor = mix.outputs["Color"]
            chaves[nome] = liga
        L.new(cor, b.inputs["Base Color"])
    return chaves


SAIDA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "saida"))
EXPRESSOES = ("olhos_fechados", "olhos_meio", "boca_a", "boca_o", "boca_e", "boca_i")


def montar_boneco(nome, altura=1.9):
    """Ready-to-animate puppet from saida/conceito/<nome>.glb and its face set in saida/rostos/<nome>/.
    Returns {"obj", "rig", "faces" (expression -> Value node), "domos"}."""
    o = importar(os.path.join(SAIDA, "conceito", f"{nome}.glb"), altura)
    o.name = nome
    # projector and bones are measured on the full mesh, like the face renders (rostos.py)
    proj = projetor(o, 1.62, 0.42) if nome == "ana_a" else projetor(o)
    lista = ossos(o)
    decimar(o)
    material_boneco(o)
    domos = olhos_de_vidro(o)
    rig = esqueleto(o, lista)
    rig.name = f"rig_{nome}"
    for d in domos:
        _no_osso(d, rig, "cabeca")
    M.pai(proj, rig)  # the face projection must travel with the puppet when it is placed in a set
    pasta = os.path.join(SAIDA, "rostos", nome)
    faces = rostos(o, proj, {n: os.path.join(pasta, f"troca_{n}.png") for n in EXPRESSOES
                             if os.path.exists(os.path.join(pasta, f"troca_{n}.png"))})
    # clay boil: a faint surface shimmer tied to the jittering anchor, like a puppet re-handled every frame
    d = o.modifiers.new("boil", "DISPLACE")
    d.texture, d.texture_coords, d.texture_coords_object = M.TEX_ARGILA, "OBJECT", M.BOIL_BONECO
    d.strength, d.mid_level = 0.0015, 0.5
    return {"obj": o, "rig": rig, "faces": faces, "domos": domos, "proj": proj}


def apontar(rig, pb, direcao, torcao=0.0):
    """Local rotation that points the bone along a world direction (parents already posed), plus a twist about it.
    Leaves the bone posed and returns the quaternion."""
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()
    R = (rig.matrix_world @ pb.matrix).to_3x3().normalized()
    q = (R @ Vector((0, 1, 0))).rotation_difference(Vector(direcao).normalized())
    local = (R.inverted() @ q.to_matrix() @ R).to_quaternion() @ Quaternion((0, 1, 0), math.radians(torcao))
    pb.rotation_quaternion = local
    return local
