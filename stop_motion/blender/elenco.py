# Posing and keying helpers shared by every scene: aim bones, sit, faces (mouth/blink swaps), and the stop-motion
# frame baking (per-frame keys, hand jitter, clay boil, light flicker, constant interpolation), plus the render modes.
import math
import os
import random

import bpy
from mathutils import Quaternion, Vector

import boneco3d as A
import massinha as M

BOCAS = {"o": "boca_o", "a": "boca_a", "e": "boca_e", "i": "boca_e"}


def osso(c, nome):
    return c["rig"].pose.bones[nome]


def mira(c, nome, direcao, torcao=0.0):
    return A.apontar(c["rig"], osso(c, nome), direcao, torcao)


def sentar(c, x, y, assento=0.5):
    """Thighs forward, shins down; hips on the seat at (x, y, assento)."""
    for l, s in (("L", 1), ("R", -1)):
        mira(c, f"coxa.{l}", (s * 0.06, -1, -0.08))
        mira(c, f"canela.{l}", (0, -0.12, -1))
    bpy.context.view_layer.update()
    z_quadril = (c["rig"].matrix_world @ osso(c, "quadril").head).z
    c["rig"].location = (x, y, assento - z_quadril)


def em_repouso(c, torcao=90.0):
    """Forearms on the desk top, hands palm down. Returns the pose as {bone: quaternion}."""
    q = {}
    for l, s in (("L", 1), ("R", -1)):
        q[f"braco.{l}"] = mira(c, f"braco.{l}", (s * 0.12, -0.55, -1))
        q[f"antebraco.{l}"] = mira(c, f"antebraco.{l}", (-s * 0.25, -1, 0.05))
        q[f"mao.{l}"] = mira(c, f"mao.{l}", (-s * 0.1, -1, -0.15), torcao * s)
    return q


def girar(c, nome, rot):
    pb = osso(c, nome)
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = rot


def misturar(c, base, alvo, k):
    for nome in alvo:
        pb = osso(c, nome)
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = base.get(nome, Quaternion()).slerp(alvo[nome], k)  # missing base = rest


def rosto(c, f, fala=None, piscas=()):
    """Swaps in the replacement face for frame f: fala = (first frame, one mouth letter per frame), x = closed."""
    som = "x"
    if fala and fala[0] <= f < fala[0] + len(fala[1]):
        som = fala[1][f - fala[0]]
    olho = "olhos_fechados" if f in piscas else ("olhos_meio" if any(abs(f - p) == 1 for p in piscas) else None)
    for nome, liga in c["faces"].items():
        liga.outputs[0].default_value = float(nome in (olho, BOCAS.get(som)))
    for d in c["domos"]:
        d.hide_render = olho is not None


def alcancar(c, lado, alvo, polo=(0, 0, -1)):
    """Two-bone IK: places the wrist (end of antebraco) at the world point alvo, elbow bending towards polo."""
    rig = c["rig"]
    bpy.context.view_layer.update()
    mw = rig.matrix_world
    b1, b2 = osso(c, f"braco.{lado}"), osso(c, f"antebraco.{lado}")
    a = (mw @ b1.bone.tail_local - mw @ b1.bone.head_local).length
    b = (mw @ b2.bone.tail_local - mw @ b2.bone.head_local).length
    s = mw @ b1.head
    t = Vector(alvo) - s
    d = min(max(t.length, abs(a - b) + 1e-3), a + b - 1e-3)
    u = t.normalized()
    v = Vector(polo) - Vector(polo).project(u)
    v = v.normalized() if v.length > 1e-6 else u.orthogonal().normalized()
    cos_a = (a * a + d * d - b * b) / (2 * a * d)
    cotovelo = s + a * (cos_a * u + (1 - cos_a * cos_a) ** 0.5 * v)
    q1 = mira(c, f"braco.{lado}", cotovelo - s)
    q2 = mira(c, f"antebraco.{lado}", s + u * d - cotovelo)
    return q1, q2


def andar(c, direcao, fase, passada=0.35):
    """Stop-motion walk pose heading along a world xy direction at a cycle phase (radians): legs and arms swing in
    opposition, the knee folds on the leg that swings through. The caller turns and moves the rig."""
    d = Vector((direcao[0], direcao[1], 0)).normalized()
    esq = Vector((-d.y, d.x, 0))  # the puppet's left when facing d
    baixo = Vector((0, 0, -1))
    sn, cs = math.sin(fase), math.cos(fase)
    for lado, s in (("L", 1), ("R", -1)):
        coxa = baixo + d * (passada * s * sn) + esq * (0.04 * s)
        mira(c, f"coxa.{lado}", coxa)
        mira(c, f"canela.{lado}", coxa - d * (0.35 * max(0.0, s * cs)))
        braco = baixo - d * (0.3 * s * sn) + esq * (0.12 * s)
        mira(c, f"braco.{lado}", braco)
        mira(c, f"antebraco.{lado}", braco + d * 0.25)


def gravar(elenco, n_quadros, pose, luzes, extras=()):
    """Bakes one hand-posed pose per frame: pose(f) poses everyone (and may move rigs); then hand jitter, clay boil
    and light flicker are added. luzes = {light data: base energy}; extras = (object, property) pairs that pose(f)
    changes and must be keyed."""
    random.seed(5)
    chaves = list(extras)
    for c in elenco:
        for pb in c["rig"].pose.bones:  # both: a bone's rotation mode is only settled once pose(f) has run
            chaves += [(pb, "rotation_quaternion"), (pb, "rotation_euler")]
        chaves += [(d, "hide_render") for d in c["domos"]] + [(n.outputs[0], "default_value") for n in c["faces"].values()]
    base = {id(c): (Vector(c["rig"].location), c["rig"].rotation_euler.z) for c in elenco}
    for f in range(1, n_quadros + 1):
        for c in elenco:
            c["rig"].location, c["rig"].rotation_euler.z = base[id(c)]
        pose(f)
        for c in elenco:
            c["rig"].location += Vector([random.uniform(-0.001, 0.001) for _ in range(3)])
            c["rig"].rotation_euler.z += random.uniform(-0.003, 0.003)
            c["rig"].keyframe_insert("location", frame=f)
            c["rig"].keyframe_insert("rotation_euler", frame=f)
        M.BOIL_BONECO.location = Vector([random.uniform(-0.004, 0.004) for _ in range(3)])
        M.BOIL_BONECO.keyframe_insert("location", frame=f)
        for luz, energia in luzes.items():
            luz.energy = energia * random.uniform(0.985, 1.015)
            luz.keyframe_insert("energy", frame=f)
        for o, prop in chaves:
            o.keyframe_insert(prop, frame=f)
    ads = [o.animation_data for o in bpy.data.objects if o.animation_data] + [lz.animation_data for lz in luzes]
    ads += [m.node_tree.animation_data for m in bpy.data.materials if m.node_tree and m.node_tree.animation_data]
    for ad in ads:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
    M.sc.frame_start, M.sc.frame_end = 1, n_quadros


def renderizar(args, saida, poses_padrao="1 12 30 45"):
    """poses = workbench check of a few frames | still N | anim (f_0001.png ...; env FAIXA limits the range)."""
    modo = args[0] if args else "still"
    r = M.configurar_render(int(os.environ.get("AMOSTRAS", "64")))
    os.makedirs(saida, exist_ok=True)
    if modo == "poses":
        M.sc.render.engine = "BLENDER_WORKBENCH"
        M.sc.display.shading.color_type = "TEXTURE"
        r.resolution_percentage = 50
        for f in [int(x) for x in os.environ.get("QUADROS", poses_padrao).split()]:
            M.sc.frame_set(f)
            r.filepath = os.path.join(saida, f"pose_{f:02d}.png")
            bpy.ops.render.render(write_still=True)
    elif modo == "still":
        f = int(args[1]) if len(args) > 1 else 1
        M.sc.frame_set(f)
        r.filepath = os.path.join(saida, f"still_{f:02d}.png")
        bpy.ops.render.render(write_still=True)
    else:
        if os.environ.get("FAIXA"):  # re-render only part of the shot, e.g. FAIXA="17 34"
            M.sc.frame_start, M.sc.frame_end = map(int, os.environ["FAIXA"].split())
        r.filepath = os.path.join(saida, "f_")
        bpy.ops.render.render(animation=True)
    print("OK", modo, saida)
