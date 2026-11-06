# Scene 2 of video 02 (5 s): insert of Ana's laptop with Joe's e-mail "Ana, it's 6."; Ana reads it and makes up her
# mind; cut to the glass meeting room, where she pulls the cord and the blind comes down over her.
# ~/.local/opt/blender-4.2.23-linux-x64/blender -b -P cena2.py -- still N | anim | poses
# Output: ../saida/cena2/ (f_0001.png ... f_0060.png at 12 fps)
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Quaternion, Vector  # noqa: E402

import boneco3d as A  # noqa: E402
import escritorio  # noqa: E402
import massinha as M  # noqa: E402
import sala_vidro as S  # noqa: E402
from elenco import alcancar, em_repouso, girar, gravar, mira, misturar, osso, renderizar, rosto, sentar  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAIDA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "saida", "cena2"))
N_QUADROS = 60
PLANO_B, PLANO_C = 17, 35  # first frames of shots 2b (Ana reads) and 2c (glass room)

KEY = escritorio.montar()
sala = S.montar()

# Ana's laptop turned to face her, with Joe's e-mail on screen (replaces the scene-1 laptop at that spot); only the
# text the story needs, in English
for o in [o for o in bpy.data.objects if o.name.endswith("-1.02")]:
    bpy.data.objects.remove(o)
P = Vector((-1.0, 0.1, 0.775))
cinza = M.clay("notebook_ana", "#5C6168", rough=0.4, boneco=False, bump=0.4)
base = M.vazio("note_ana", P)
M.caixa("note_ana_base", (P.x, P.y, 0.785), (0.36, 0.25, 0.02), cinza, base, bev=0.006)
M.caixa("note_ana_tecl", (P.x, P.y + 0.02, 0.796), (0.3, 0.12, 0.004), M.PRETO, base, bev=0.001)
tampa = M.vazio("note_ana_tampa", (P.x, P.y - 0.125, 0.79), base)
M.caixa("note_ana_tela", (P.x, P.y - 0.125, 0.905), (0.36, 0.015, 0.23), cinza, tampa, bev=0.006)
ys = P.y - 0.1155  # screen surface, facing +y (Ana)
tela = M.caixa("note_ana_luz", (P.x, ys, 0.905), (0.32, 0.004, 0.19), M.simples("tela_email", "#F4F6F8", 0.3, emissao=1.2), tampa, bev=0)
FRENTE = (math.pi / 2, 0, math.pi)  # text facing +y, reading towards -x


def na_tela(nome, corpo, u, v, tam, mat):
    """Text on the screen at (u right, v up) from its centre, left-aligned."""
    o = M.texto(nome, corpo, (P.x - u, ys + 0.0035, 0.905 + v), tam, mat, tampa, FRENTE)
    o.data.align_x = "LEFT"
    return o


azul = M.simples("barra_email", "#1F4E8C", 0.4, emissao=0.8)
tinta = M.simples("tinta_email", "#1B1B1F", 0.5)
M.caixa("email_barra", (P.x, ys + 0.0015, 0.905 + 0.0825), (0.32, 0.002, 0.025), azul, tampa, bev=0)
M.cilindro("email_avatar", (P.x + 0.105, ys + 0.003, 0.905 + 0.04), 0.014, 0.002, M.simples("avatar", "#D9A43B", 0.5),
           tampa, rot=(math.pi / 2, 0, 0), bev=0)
na_tela("email_de", "Joe", -0.08, 0.038, 0.02, tinta)
na_tela("email_corpo", "Ana, it's 6.", -0.12, -0.03, 0.034, tinta)
tampa.rotation_euler.x = 0.22
base.rotation_euler.z = -0.86

ana, beto = (A.montar_boneco(n) for n in ("ana_a", "beto"))
sentar(ana, -0.6, 0.42)
sentar(beto, 0.2, 0.42)
REP = {"ana": em_repouso(ana), "beto": em_repouso(beto)}
SENTADA = {f"{o}.{l}": osso(ana, f"{o}.{l}").rotation_quaternion.copy() for o in ("coxa", "canela") for l in "LR"}
LOC_MESA = Vector(ana["rig"].location)
LOC_SALA = Vector((S.X0 + 0.12, 0.42, 0.0))

# cameras: 2a insert on the screen, 2b medium on Ana, 2c outside the glass room
bpy.context.view_layer.update()
mw = tela.matrix_world
centro, normal = mw.translation.copy(), (mw.to_3x3() @ Vector((0, 1, 0))).normalized()


def camera(nome, loc, alvo, lente, foco, f0, fstop=2.0):
    cam = bpy.data.objects.new(nome, bpy.data.cameras.new(nome))
    M.sc.collection.objects.link(cam)
    cam.location = loc
    M.mirar(cam, alvo)
    cam.data.lens = lente
    cam.data.dof.use_dof, cam.data.dof.focus_distance, cam.data.dof.aperture_fstop = True, foco, fstop
    M.sc.timeline_markers.new(nome, frame=f0).camera = cam
    return cam


camera("2a", centro + normal * 0.45 + Vector((0, 0, 0.06)), centro - Vector((0, 0, 0.01)), 42, 0.45, 1, 4.0)
camera("2b", (-1.3, -0.62, 1.1), (-0.6, 0.42, 1.2), 40, 1.25, PLANO_B, 1.8)  # from behind her laptop lid
camera("2c", (S.X0 + 0.05, -2.7, 1.5), (S.X0 + 0.1, 0.5, 1.3), 40, 3.1, PLANO_C, 2.8)
M.sc.camera = bpy.data.objects["2a"]

# ------------------------------------------------------------------ animation (12 fps, every frame hand-posed)
PISCA = {"ana": (21, 30), "beto": (19, 33)}  # no blink in the wide glass-room shot: shut lids read as blank eyes
CORDAO_X = Vector((S.X_CORDAO, 0.13, 0))


def descida(f):
    """Bottom rail height in the glass-room shot: Ana pulls from f 38 to f 54, in uneven hand-animated steps."""
    k = min(max((f - 38) / 16, 0.0), 1.0)
    k = k * k * (3 - 2 * k)
    return S.TOPO_PERSIANA - k * (S.TOPO_PERSIANA - S.BASE_PERSIANA)


def pose(f):
    rosto(ana, f, None, PISCA["ana"])
    ana["obj"].hide_render = f < PLANO_B  # the insert camera sits where her body is
    for d in ana["domos"]:
        d.hide_render = d.hide_render or f < PLANO_B
    rosto(beto, f, None, PISCA["beto"])
    respira = 0.012 * math.sin(f / 4)
    # Beto at the desk the whole time, idle, looking at the (off-screen) manager
    misturar(beto, {}, REP["beto"], 1.0)
    girar(beto, "cabeca", (0.0, 0.0, -0.2))
    girar(beto, "peito", (0.012 * math.sin(f / 4 + 2), 0.0, 0.0))
    if f < PLANO_C:
        # at the desk: reads the screen (head to her right, down), takes it in, turns back to front, small nod
        ana["rig"].location = LOC_MESA
        misturar(ana, {}, {**REP["ana"], **SENTADA}, 1.0)
        olha = 1.0 if f < 26 else {26: 0.6, 27: 0.25}.get(f, 0.0)
        aceno = 0.07 if f in (30, 31) else 0.0  # nod: chin down
        girar(ana, "cabeca", (0.12 * olha + aceno, 0.0, 0.45 * olha - 0.2 * (1 - olha)))  # x > 0: looks down at the screen
        girar(ana, "peito", (respira + (0.06 if f >= 32 else 0.0), 0.0, 0.15 * olha))  # leans forward to get up
        return
    # glass room: standing behind the centre pane, left hand on the blind cord, pulls it down
    ana["rig"].location = LOC_SALA
    misturar(ana, {}, {k: Quaternion() for k in SENTADA}, 1.0)
    girar(ana, "peito", (respira, 0.0, 0.0))
    z = descida(f)
    sala["cordao"].scale.z = 0.45 + (S.TOPO_PERSIANA - z) * 0.4
    mao_z = S.TOPO_PERSIANA - sala["cordao"].scale.z - 0.08  # wrist just under the cord end, fingers around it
    alcancar(ana, "L", CORDAO_X + Vector((0, 0, mao_z)), polo=(1, 0.3, -1))
    bpy.context.view_layer.update()
    ante = osso(ana, "antebraco.L")
    mw = ana["rig"].matrix_world
    mira(ana, "mao.L", (mw @ ante.tail - mw @ ante.head).normalized() + Vector((0, -0.25, 0)), 0)  # wrist straight, palm to the cord
    mira(ana, "braco.R", (-0.12, 0.02, -1))
    mira(ana, "antebraco.R", (-0.05, -0.1, -1))
    mira(ana, "mao.R", (0, -0.05, -1), 90)
    olhar_cima = 0.12 if f < 46 else 0.0  # watches the blind come down, then looks at us as it covers her
    girar(ana, "cabeca", (olhar_cima, 0.0, -0.08))
    S.baixar(sala, z)


extras = [(ana["obj"], "hide_render")] + [(lam, "hide_render") for lam in sala["laminas"]] + [(sala["trilho"], "location"), (sala["cordao"], "scale")]
S.baixar(sala, S.TOPO_PERSIANA)
gravar([ana, beto], N_QUADROS, pose, {KEY: 650, sala["key"]: 600}, extras)
renderizar(ARGS, SAIDA, "8 20 30 40 50 58")
