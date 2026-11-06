# Scene 3 of video 02 (11 s): inside the glass room (the camera sees it, the manager doesn't) Ana fills the whiteboard,
# "wait...", wipes it, starts again; outside, the manager and Beto wait and Beto watches the clock jump; back inside
# the board is full of overthinking that lands on "6". The board never mentions Joe. On-screen text is English.
# ~/.local/opt/blender-4.2.23-linux-x64/blender -b -P cena3.py -- still N | anim | poses
# Output: ../saida/cena3/ (f_0001.png ... f_0132.png at 12 fps)
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import boneco3d as A  # noqa: E402
import massinha as M  # noqa: E402
import sala_vidro as S  # noqa: E402
from elenco import alcancar, girar, gravar, mira, osso, renderizar, rosto  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAIDA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "saida", "cena3"))
N_QUADROS = 132
PLANO_B, PLANO_C = 55, 85  # 3b corridor, 3c back at the board
X0 = S.X0
Y_QUADRO = 2.543  # whiteboard surface

sala = S.montar()
S.baixar(sala, S.BASE_PERSIANA)  # blind shut since scene 2
bpy.data.lights["teto_sala"].energy = 90  # right above her at the board: at full power it bleaches her hair
dentro = M.luz("key_quadro", (X0 + 1.2, 0.9, 2.5), (X0 - 0.2, 2.5, 1.4), 110, 0.8, (1.0, 0.9, 0.78))  # blind blocks the outside key

# ------------------------------------------------------------------ the board: each line is a stack of prefixes ("2", "2 +", ...)
# shown one at a time, so the writing grows like handwriting with real kerning
CAVEAT = os.path.expanduser("~/.local/share/fonts/caveat/Caveat.ttf")
FONTE_MAO = bpy.data.fonts.load(CAVEAT)
AZUL = M.simples("marcador_azul", "#1F4E8C", 0.6)
VERMELHO = M.simples("marcador_verm", "#B42318", 0.6)
X_LINHA = X0 - 0.6
# id: (text, z, size, colour, first frame, frames per 2 characters, frame it is wiped (or None))
LINHAS = {
    "a1": ("2 + 3 = 5", 1.88, 0.15, AZUL, 4, 2, 37),
    "a2": ("wait...", 1.72, 0.15, AZUL, 21, 2, 42),
    "a3": ("2 + 3 =", 1.88, 0.15, AZUL, 46, 2, PLANO_C),
    "c1": ("2 + 3 = 5 ?", 1.88, 0.15, AZUL, PLANO_C, 0, None),
    "c2": ("what if we round...", 1.72, 0.15, AZUL, PLANO_C, 0, None),
    "c3": ("2.4 + 3.4 ≈ 6", 1.56, 0.15, AZUL, PLANO_C, 0, None),
    "c4": ("checks out.", 1.40, 0.15, AZUL, 88, 2, None),
    "c5": ("= 6", 1.2, 0.22, VERMELHO, 100, 3, None),
}
prefixos = {}
for k, (txt, z, tam, mat, *_r) in LINHAS.items():
    prefixos[k] = []
    for n in range(2, len(txt) + 2, 2):
        o = M.texto(f"{k}_{n}", txt[:n], (X_LINHA, Y_QUADRO - 0.002, z), tam, mat)
        o.data.font, o.data.align_x = FONTE_MAO, "LEFT"
        prefixos[k].append(o)
bpy.context.view_layer.update()
# the red ring around the answer
anel = M.toro("anel", (X_LINHA + 0.11, Y_QUADRO - 0.004, 1.2), 0.15, 0.007, VERMELHO, rot=(math.pi / 2, 0, 0), esc=(1.0, 0.7, 1.0))


def ponta(k, f):
    """(visible prefix index or None, pen point) for line k at frame f."""
    txt, z, tam, mat, ini, passo, apaga = LINHAS[k]
    if f < ini or (apaga and f >= apaga):
        return None, None
    n = len(prefixos[k])
    i = n - 1 if passo == 0 else min(n - 1, (f - ini) // passo)
    o = prefixos[k][i]
    return i, Vector((max((o.matrix_world @ Vector(c)).x for c in o.bound_box) + 0.01, Y_QUADRO, z - 0.02))


def escrevendo(f):
    """Pen point if Ana is writing at frame f."""
    for k, (txt, z, tam, mat, ini, passo, apaga) in LINHAS.items():
        if passo and ini <= f < ini + passo * len(prefixos[k]):
            return ponta(k, f)[1]
    return None


# ------------------------------------------------------------------ cast
ana, beto, ger = (A.montar_boneco(n) for n in ("ana_a", "beto", "gerente"))
pincel = M.cilindro("pincel_ana", (0, 0, 0), 0.012, 0.13, M.clay("pincel_ana", "#1F4E8C", boneco=False))
bpy.context.view_layer.update()
mao = osso(ana, "mao.R")
mw = ana["rig"].matrix_world
cabo, dedos = mw @ mao.head, mw @ mao.tail
pincel.location = dedos + (dedos - cabo).normalized() * 0.01
pincel.rotation_euler = (dedos - cabo).to_track_quat("Z", "Y").to_euler()
A._no_osso(pincel, ana["rig"], "mao.R")

ana["rig"].rotation_euler.z = math.pi  # faces the board (+y)
ana["rig"].location = (X0 - 0.75, 2.15, 0)
for c, loc, rz in ((ger, (X0 - 0.5, -0.85, 0), -0.2), (beto, (X0 + 0.45, -0.8, 0), 0.2)):
    c["rig"].location, c["rig"].rotation_euler.z = loc, rz
bpy.context.view_layer.update()


def no_corpo(c, local):
    """World point from the puppet's own frame (rest pose faces -y, its right hand on -x)."""
    return c["rig"].matrix_world @ Vector(local)


# cameras
def camera(nome, loc, alvo, lente, foco, f0, fstop=2.0):
    cam = bpy.data.objects.new(nome, bpy.data.cameras.new(nome))
    M.sc.collection.objects.link(cam)
    cam.location = loc
    M.mirar(cam, alvo)
    cam.data.lens = lente
    cam.data.dof.use_dof, cam.data.dof.focus_distance, cam.data.dof.aperture_fstop = True, foco, fstop
    M.sc.timeline_markers.new(nome, frame=f0).camera = cam
    return cam


camera("3a", (X0 + 0.3, 0.45, 1.45), (X0 - 0.15, 2.5, 1.5), 30, 2.0, 1, 2.8)
camera("3b", (X0 + 0.15, -3.2, 1.45), (X0, 0.0, 1.45), 38, 2.4, PLANO_B, 2.8)
camera("3c", (X0 + 0.35, 0.95, 1.5), (X0 - 0.45, 2.35, 1.42), 28, 1.6, PLANO_C, 2.8)
M.sc.camera = bpy.data.objects["3a"]

# ------------------------------------------------------------------ animation (12 fps, every frame hand-posed)
PISCA = {"beto": (58, 75), "ger": (62, 80)}
ESTADO = {"x": X0 - 0.75}


def braco_livre(c, lado, s):
    mira(c, f"braco.{lado}", (s * 0.08, 0.02, -1))
    mira(c, f"antebraco.{lado}", (s * 0.05, -0.12, -1))
    mira(c, f"mao.{lado}", (0, -0.05, -1), 90 * s)


def pose_ana(f):
    rosto(ana, f)
    girar(ana, "peito", (0.012 * math.sin(f / 4), 0.0, 0.0))
    braco_livre(ana, "L", 1)
    alvo = escrevendo(f)
    if alvo is None and 32 <= f < 45:  # wiping: rubs across line 1, then line 2
        z = 1.88 if f < 38 else 1.72
        alvo = Vector((X_LINHA + 0.15 + 0.22 * ((f % 4) / 3), Y_QUADRO, z))
    if alvo is None and 106 <= f < 112:  # rings the answer
        a = (f - 106) / 5 * math.tau
        alvo = Vector((X_LINHA + 0.11 + 0.15 * math.cos(a), Y_QUADRO, 1.2 + 0.1 * math.sin(a)))
    pausa = alvo is None
    if not pausa and abs(alvo.x - 0.28 - ESTADO["x"]) > 0.18:  # shuffles sideways when the pen gets too far
        ESTADO["x"] = alvo.x - 0.28
    ana["rig"].location = (ESTADO["x"], 1.95 if pausa else 2.15, 0)
    if pausa:  # steps back, hand to the chin, looks at the board
        bpy.context.view_layer.update()
        alcancar(ana, "R", no_corpo(ana, (-0.05, -0.2, 1.38)), polo=no_corpo(ana, (-1, 0, -0.5)) - no_corpo(ana, (0, 0, 0)))
        mira(ana, "mao.R", no_corpo(ana, (0.05, -0.1, 1.5)) - no_corpo(ana, (-0.05, -0.2, 1.38)), 90)
        satisfeita = f >= 118
        girar(ana, "cabeca", (0.05, -0.5 if satisfeita else 0.0, 0.0 if satisfeita else 0.18))
        return
    bpy.context.view_layer.update()
    pulso = alvo - Vector((0, 0.11, 0.06))
    alcancar(ana, "R", pulso, polo=Vector((0.6, -0.2, -1)))
    mira(ana, "mao.R", alvo - pulso, 90)
    girar(ana, "cabeca", (-0.05, 0.0, 0.0))


def pose_fora(f):
    """Corridor: the manager waits looking at the shut blind, Beto keeps checking the clock above the door."""
    rosto(beto, f, None, PISCA["beto"])
    rosto(ger, f, None, PISCA["ger"])
    for c, fase in ((beto, 1), (ger, 3)):
        girar(c, "peito", (0.012 * math.sin(f / 4 + fase), 0.0, 0.0))
        braco_livre(c, "L", 1)
        braco_livre(c, "R", -1)
    olha_relogio = 59 <= f < 70 or 75 <= f < 81
    # head euler: x > 0 looks down, y > 0 turns towards +x (rest pose faces -y); the clock is up behind Beto's right
    girar(beto, "cabeca", (-0.4, -1.0, 0.0) if olha_relogio else (0.0, -0.25, 0.08))
    girar(beto, "peito", (0.0, -0.35 if olha_relogio else 0.0, 0.0))
    girar(ger, "cabeca", (0.08, 0.6 if f < 72 else 0.9, 0.0))  # at the blind, then at Beto


def pose(f):
    pose_ana(f)
    pose_fora(f)
    # time passes in jumps: 10:05 when we leave the board, 10:20 then 10:40 while Beto watches
    minutos = 5 if f < 66 else (20 if f < 78 else 40)
    sala["minuto"].rotation_euler.y = minutos / 60 * math.tau
    sala["hora"].rotation_euler.y = (10 + minutos / 60) / 12 * math.tau
    for k, objs in prefixos.items():
        i, _ = ponta(k, f)
        for j, o in enumerate(objs):
            o.hide_render = j != i
    anel.hide_render = f < 110


extras = [(o, "hide_render") for objs in prefixos.values() for o in objs]
extras += [(anel, "hide_render"), (sala["minuto"], "rotation_euler"), (sala["hora"], "rotation_euler")]
gravar([ana, beto, ger], N_QUADROS, pose, {sala["key"]: 600, dentro: 110}, extras)
renderizar(ARGS, SAIDA, "10 18 40 50 70 95 112 125")
