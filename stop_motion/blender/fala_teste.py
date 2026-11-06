# Talking test for an AI-sculpted puppet: raises a hand, says a line, blinks, tilts the head, clay boil.
# Blinks and mouth shapes are replacement faces (AI edits of its face, saida/rostos/<nome>/troca_*.png) projected on
# the head. FALA is one mouth shape per frame from frame 16: x/m closed, o, a, e, i (i falls back to e).
# NOME=beto FALA=xeeooxx ~/.local/opt/blender-4.2.23-linux-x64/blender -b -P fala_teste.py -- still N | anim | poses
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Quaternion, Vector  # noqa: E402

import boneco3d as A  # noqa: E402
import massinha as M  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
NOME = os.environ.get("NOME", "ana_a")
GLB = os.path.normpath(os.path.join(AQUI, "..", "saida", "conceito", f"{NOME}.glb"))
SAIDA = os.path.normpath(os.path.join(AQUI, "..", "saida", "fala", NOME))
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODO = ARGS[0] if ARGS else "still"
N_QUADROS = 48
random.seed(7)

ana = A.importar(GLB, 1.9)
# the projector must be measured on the same full mesh the face set was rendered from (rostos.py)
PROJ = A.projetor(ana, 1.62, 0.42) if NOME == "ana_a" else A.projetor(ana)
OSSOS = A.ossos(ana)
A.decimar(ana)
A.material_boneco(ana)
domos = A.olhos_de_vidro(ana)
rig = A.esqueleto(ana, OSSOS)
for d_ in domos:
    A._no_osso(d_, rig, "cabeca")
ROSTOS = os.path.normpath(os.path.join(AQUI, "..", "saida", "rostos", NOME))
FACES = A.rostos(ana, PROJ, {n: os.path.join(ROSTOS, f"troca_{n}.png") for n in
                             ("olhos_fechados", "olhos_meio", "boca_a", "boca_o", "boca_e", "boca_i")
                             if os.path.exists(os.path.join(ROSTOS, f"troca_{n}.png"))})
# clay boil: a faint surface shimmer tied to the jittering anchor, like a puppet re-handled every frame
d = ana.modifiers.new("boil", "DISPLACE")
d.texture, d.texture_coords, d.texture_coords_object = M.TEX_ARGILA, "OBJECT", M.BOIL_BONECO
d.strength, d.mid_level = 0.0015, 0.5

M.caixa("chao", (0, 0, -0.05), (8, 8, 0.1), M.clay("chao", "#9AA4AE", rough=0.9, boneco=False, bump=0.3), bev=0)
M.caixa("fundo", (0, 2.0, 2.0), (8, 0.1, 4.2), M.clay("fundo", "#C9D6CF", rough=0.9, boneco=False, bump=0.3), bev=0)
KEY = M.luz("key", (-1.8, -2.4, 2.9), (0, 0, 1.4), 700, 0.6, (1.0, 0.86, 0.72))
M.luz("fill", (2.4, -2.0, 1.6), (0, 0, 1.3), 110, 3.0, (0.82, 0.9, 1.0))
M.luz("rim", (1.2, 1.5, 2.6), (0, 0, 1.5), 300, 0.8, (1.0, 0.95, 0.88))
w = bpy.data.worlds.new("mundo")
M.sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = M.rgb("#DCE1E6")
w.node_tree.nodes["Background"].inputs[1].default_value = 0.1

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
M.sc.collection.objects.link(cam)
M.sc.camera = cam
cam.location = (-0.45, -2.3, 1.45)
M.mirar(cam, (0, 0, 1.3))
cam.data.lens = 50
cam.data.dof.use_dof, cam.data.dof.aperture_fstop = True, 2.8
cam.data.dof.focus_distance = (cam.location - Vector((0, -0.15, 1.6))).length

# ---------------------------------------------------------------- animation
P = rig.pose.bones
BOCAS = {"o": "boca_o", "a": "boca_a", "e": "boca_e", "i": "boca_i" if "boca_i" in FACES else "boca_e"}
FALA_INI, FALA = 16, os.environ.get("FALA", "xooxoommeeaooeoox")  # default: Ana, "Só um minuto."
PISCA = (9, 38)
MAO = {13: 0.35, 14: 0.7, 15: 1.0}  # hand coming up, then held; going down at the end
for f in range(40, 44):
    MAO[f] = 1.0 - (f - 39) * 0.25
SEM_BOCA = os.environ.get("SEM_BOCA") == "1"  # talk with head moves only, painted mouth stays closed
TORCAO = float(os.environ.get("TORCAO", "90"))  # wrist twist (degrees) so the palm faces the camera


def apontar(pb, direcao, torcao=0.0):
    """Local rotation that points the bone along a world direction (parents already posed), plus a twist about it."""
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()
    R = (rig.matrix_world @ pb.matrix).to_3x3().normalized()
    q = (R @ Vector((0, 1, 0))).rotation_difference(Vector(direcao).normalized())
    local = (R.inverted() @ q.to_matrix() @ R).to_quaternion() @ Quaternion((0, 1, 0), math.radians(torcao))
    pb.rotation_quaternion = local
    return local


# "one minute" gesture: elbow by the side, forearm up in front, palm out
ALVO = {"braco.R": apontar(P["braco.R"], (-0.2, -0.4, -1)), "antebraco.R": apontar(P["antebraco.R"], (-0.1, -0.5, 1))}
ALVO["mao.R"] = apontar(P["mao.R"], (0, -0.15, 1), TORCAO)
for nome in ALVO:
    P[nome].rotation_quaternion = (1, 0, 0, 0)


def pose(f):
    som = FALA[f - FALA_INI] if FALA_INI <= f < FALA_INI + len(FALA) and not SEM_BOCA else "x"
    olho = "olhos_fechados" if f in PISCA else ("olhos_meio" if any(abs(f - p) == 1 for p in PISCA) else None)
    for nome, liga in FACES.items():
        liga.outputs[0].default_value = float(nome in (olho, BOCAS.get(som)))
    for d_ in domos:  # no glass shine over a closed lid
        d_.hide_render = olho is not None
    k = MAO.get(f, 1.0 if 15 < f < 40 else 0.0)
    for nome, alvo in ALVO.items():
        P[nome].rotation_quaternion = Quaternion().slerp(alvo, k)
    falando = FALA_INI <= f < FALA_INI + len(FALA)
    P["cabeca"].rotation_euler = (0.05 if falando and f % 4 < 2 else 0.0, 0.0, -0.12 if f >= 15 else 0.0)
    P["pescoco"].rotation_euler = (0.0, 0.06 if f >= 15 else 0.0, 0.0)
    P["peito"].rotation_euler = (0.012 * math.sin(f / 4), 0.0, 0.0)  # breathing


chaves = [(pb, "rotation_quaternion" if pb.name in ALVO else "rotation_euler") for pb in P]
chaves += [(d_, "hide_render") for d_ in domos] + [(n.outputs[0], "default_value") for n in FACES.values()]
for f in range(1, N_QUADROS + 1):
    pose(f)
    rig.location = Vector([random.uniform(-0.001, 0.001) for _ in range(3)])
    M.BOIL_BONECO.location = Vector([random.uniform(-0.004, 0.004) for _ in range(3)])
    KEY.energy = 700 * random.uniform(0.985, 1.015)
    for o, prop in chaves + [(rig, "location"), (M.BOIL_BONECO, "location")]:
        o.keyframe_insert(prop, frame=f)
    KEY.keyframe_insert("energy", frame=f)
for ad in ([o.animation_data for o in bpy.data.objects if o.animation_data] + [KEY.animation_data]
           + [m.node_tree.animation_data for m in ana.data.materials if m.node_tree.animation_data]):
    for fc in ad.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
M.sc.frame_start, M.sc.frame_end = 1, N_QUADROS

r = M.configurar_render(int(os.environ.get("AMOSTRAS", "64")))
os.makedirs(SAIDA, exist_ok=True)
if MODO == "poses":  # fast workbench check of the key poses
    M.sc.render.engine = "BLENDER_WORKBENCH"
    M.sc.display.shading.color_type = "TEXTURE"
    r.resolution_percentage = 50
    for f in [int(x) for x in os.environ.get("QUADROS", "1 9 15 22 30").split()]:
        M.sc.frame_set(f)
        r.filepath = os.path.join(SAIDA, f"pose_{f:02d}_t{int(TORCAO)}.png")
        bpy.ops.render.render(write_still=True)
elif MODO == "still":
    f = int(ARGS[1]) if len(ARGS) > 1 else 22
    M.sc.frame_set(f)
    r.filepath = os.path.join(SAIDA, f"still_{f:02d}.png")
    bpy.ops.render.render(write_still=True)
else:
    if SEM_BOCA:  # only the talking frames differ from the main render
        M.sc.frame_start, M.sc.frame_end = FALA_INI, FALA_INI + len(FALA) - 1
    r.filepath = os.path.join(SAIDA, "sb_" if SEM_BOCA else "f_")
    bpy.ops.render.render(animation=True)
print("OK", MODO, SAIDA)
