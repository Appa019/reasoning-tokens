# Scene 5 of video 02 (8 s, dialogue in English): insert of the manager's hand turning the EFFORT knob from LOW to MAX;
# "Close the 2027 budget with these 14 constraints." Beto, instantly: "Three million." Carla: "It doesn't balance."
# ~/.local/opt/blender-4.2.23-linux-x64/blender -b -P cena5.py -- still N | anim | poses
# Output: ../saida/cena5/ (f_0001.png ... f_0096.png at 12 fps)
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import boneco3d as A  # noqa: E402
import escritorio  # noqa: E402
import massinha as M  # noqa: E402
from elenco import alcancar, em_repouso, girar, gravar, mira, misturar, osso, renderizar, rosto, sentar  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAIDA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "saida", "cena5"))
N_QUADROS = 96
PLANO_B, PLANO_C, PLANO_D = 25, 61, 77  # wide question, Beto, Carla

KEY = escritorio.montar()

# ------------------------------------------------------------------ the effort knob: a small console on the desk corner
BOTAO = Vector((0.55, -0.24, 0.775))
escuro = M.clay("console", "#2F3237", boneco=False, bump=0.4)
M.caixa("console", BOTAO + Vector((0, 0, 0.025)), (0.2, 0.15, 0.05), escuro, bev=0.01)
claro = M.simples("legenda_botao", "#E9ECEF", 0.5)
TOPO = BOTAO.z + 0.051
for i in range(11):  # tick marks over the 270 degree sweep
    phi = math.radians(135 - 27 * i)
    d = Vector((-math.sin(phi), math.cos(phi), 0))
    M.caixa(f"marca_botao{i}", BOTAO + d * 0.056 + Vector((0, 0, 0.051)), (0.004, 0.012, 0.002), claro, bev=0,
            rot=(0, 0, phi))
for nome, txt, phi, raio, tam in (("rot_low", "LOW", 135, 0.075, 0.016), ("rot_max", "MAX", -135, 0.075, 0.016),
                                  ("rot_effort", "EFFORT", 180, 0.066, 0.013)):  # in front: behind the dial it is hidden
    d = Vector((-math.sin(math.radians(phi)), math.cos(math.radians(phi)), 0))
    M.texto(nome, txt, BOTAO + d * raio + Vector((0, 0, 0.0515)), tam, claro, rot=(0, 0, 0))
DIAL = M.vazio("dial", BOTAO + Vector((0, 0, 0.05)))
M.cilindro("dial_corpo", BOTAO + Vector((0, 0, 0.068)), 0.032, 0.036, M.clay("dial", "#B42318", boneco=False, bump=0.4), DIAL, bev=0.006)
M.caixa("dial_ponteiro", BOTAO + Vector((0, 0.018, 0.088)), (0.006, 0.022, 0.003), claro, DIAL, bev=0)
LOW, MAX = math.radians(135), math.radians(-135)

# ------------------------------------------------------------------ cast
ana, beto, ger, carla = (A.montar_boneco(n) for n in ("ana_a", "beto", "gerente", "carla"))
sentar(ana, -0.6, 0.42)
sentar(beto, 0.2, 0.42)
REP = {"ana": em_repouso(ana), "beto": em_repouso(beto)}
ger["rig"].location, ger["rig"].rotation_euler.z = (0.88, -0.62, 0), math.radians(-55)
carla["rig"].location, carla["rig"].rotation_euler.z = (-1.35, -0.45, 0), 0.64  # turned to the desk, face to camera
bpy.context.view_layer.update()


def no_corpo(c, local):
    return c["rig"].matrix_world @ Vector(local)


def braco_livre(c, lado, s):
    mira(c, f"braco.{lado}", (s * 0.08, 0.02, -1))
    mira(c, f"antebraco.{lado}", (s * 0.05, -0.12, -1))
    mira(c, f"mao.{lado}", (0, -0.05, -1), 90 * s)


# Carla holds a tablet in front of her (finance), both hands on its sides
TABLET = no_corpo(carla, (0, -0.28, 1.02))
tablet = M.caixa("tablet", TABLET, (0.26, 0.18, 0.012), M.clay("tablet", "#2B2B2E", boneco=False, bump=0.3), bev=0.006,
                 rot=(0.9, 0, carla["rig"].rotation_euler.z))
normal_tablet = tablet.rotation_euler.to_matrix() @ Vector((0, 0, 1))
M.caixa("tablet_tela", TABLET + normal_tablet * 0.0065, (0.23, 0.15, 0.002), M.simples("tablet_tela", "#CFE3FF", 0.3, emissao=0.8),
        bev=0, rot=tuple(tablet.rotation_euler))


# cameras
def camera(nome, loc, alvo, lente, foco, f0, fstop=2.8):
    cam = bpy.data.objects.new(nome, bpy.data.cameras.new(nome))
    M.sc.collection.objects.link(cam)
    cam.location = loc
    M.mirar(cam, alvo)
    cam.data.lens = lente
    cam.data.dof.use_dof, cam.data.dof.focus_distance, cam.data.dof.aperture_fstop = True, foco, fstop
    M.sc.timeline_markers.new(nome, frame=f0).camera = cam
    return cam


camera("5a", BOTAO + Vector((-0.06, -0.38, 0.36)), BOTAO + Vector((0, 0.01, 0.06)), 45, 0.52, 1, 4.0)
camera("5b", (-0.2, -3.8, 1.35), (-0.2, 0.2, 1.2), 36, 3.9, PLANO_B)
camera("5c", (0.38, -1.55, 1.35), (0.2, 0.42, 1.25), 50, 1.95, PLANO_C, 2.0)
camera("5d", (-0.65, -1.8, 1.6), (-1.35, -0.45, 1.55), 50, 1.55, PLANO_D, 2.0)

# ------------------------------------------------------------------ animation (12 fps, every frame hand-posed)
FALA = {"ger": (27, "ooxxexeeieeieeaexixixooiioxaaexx"),  # "Close the 2027 budget with these 14 constraints."
        "beto": (63, "iiixiioox"),                       # "Three million."
        "carla": (80, "ixaaexaaaex")}                    # "It doesn't balance."
PISCA = {"ana": (40, 70), "beto": (30, 58, 88), "ger": (22, 66), "carla": (35, 92)}
CLIQUES = {6: 0.12, 8: 0.3, 10: 0.45, 12: 0.62, 14: 0.8, 16: 1.0}  # dial turns in clicks


def dial(f):
    k = 0.0
    for q, v in sorted(CLIQUES.items()):
        if f >= q:
            k = v
    return LOW + (MAX - LOW) * k


def pose(f):
    for k, c in (("ana", ana), ("beto", beto), ("ger", ger), ("carla", carla)):
        rosto(c, f, FALA.get(k), PISCA[k])
    respira = 0.012 * math.sin(f / 4)
    # the knob: his hand comes down on it, turns it click by click, stays there while he asks
    phi = dial(f)
    DIAL.rotation_euler.z = phi
    bpy.context.view_layer.update()
    braco_livre(ger, "L", 1)
    na_mao = f < 22
    if na_mao:
        topo = BOTAO + Vector((0, 0, 0.13))
        chega = {1: 0.0, 2: 0.4, 3: 0.75}.get(f, 1.0)
        alvo = no_corpo(ger, (-0.25, -0.1, 0.95)).lerp(topo, chega)
        alcancar(ger, "R", alvo, polo=no_corpo(ger, (-1, 0.4, -1)) - no_corpo(ger, (0, 0, 0)))
        mira(ger, "mao.R", (0.05, 0.1, -1), 90 + 0.3 * math.degrees(phi - LOW))  # a wrist only turns so far: fingers re-grip
        girar(ger, "coluna", (0.18 * chega, 0.0, 0.0))
    else:
        braco_livre(ger, "R", -1)
        girar(ger, "coluna", (0.0, 0.0, 0.0))
    falando = 27 <= f < 59
    girar(ger, "cabeca", (0.08 if falando and f % 4 < 2 else 0.0, -0.15 if f < 70 else 0.6, 0.0))
    # Beto: snaps back the answer with a smug little lean; Ana watches the manager, then Carla
    misturar(ana, {}, REP["ana"], 1.0)
    misturar(beto, {}, REP["beto"], 1.0)
    girar(beto, "cabeca", (-0.06 if 63 <= f < 72 else 0.0, 0.3 if f < 77 else -0.4, 0.0))
    girar(beto, "peito", (respira, 0.1 if 63 <= f < 76 else 0.0, 0.0))
    girar(ana, "cabeca", (0.0, 0.25 if f < 77 else -0.45, 0.0))
    girar(ana, "peito", (0.012 * math.sin(f / 4 + 2), 0.0, 0.0))
    # Carla: tablet up, reads it, shakes her head on "It doesn't balance."
    for lado, s in (("L", 1), ("R", -1)):
        alcancar(carla, lado, TABLET + (no_corpo(carla, (s * 0.15, -0.28, 1.0)) - no_corpo(carla, (0, -0.28, 1.0))),
                 polo=no_corpo(carla, (s * 1, 0.5, -1)) - no_corpo(carla, (0, 0, 0)))
    nao = {80: 0.25, 81: -0.25, 82: 0.25, 83: -0.2, 84: 0.1}.get(f, 0.0)
    girar(carla, "cabeca", (0.3 if f < 78 else 0.0, nao + (0.0 if f >= 78 else 0.2), 0.0))
    girar(carla, "peito", (0.012 * math.sin(f / 4 + 4), 0.0, 0.0))


extras = [(DIAL, "rotation_euler")]
gravar([ana, beto, ger, carla], N_QUADROS, pose, {KEY: 650}, extras)
renderizar(ARGS, SAIDA, "4 12 20 40 66 85")
