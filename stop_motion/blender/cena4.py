# Scene 4 of video 02 (9 s): the glass door opens, Ana walks out to the manager and hands him a post-it; insert of
# the post-it ("6", underlined so it can't be read as 9); he looks at it, then at Beto.
# ~/.local/opt/blender-4.2.23-linux-x64/blender -b -P cena4.py -- still N | anim | poses
# Output: ../saida/cena4/ (f_0001.png ... f_0108.png at 12 fps)
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import boneco3d as A  # noqa: E402
import massinha as M  # noqa: E402
import sala_vidro as S  # noqa: E402
from elenco import alcancar, andar, girar, gravar, mira, osso, renderizar, rosto  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAIDA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "saida", "cena4"))
N_QUADROS = 108
PLANO_B, PLANO_C, PLANO_D = 45, 81, 93  # hand-over, post-it insert, he looks at Beto
TROCA = 55  # frame the post-it changes hands
X0 = S.X0

sala = S.montar()
S.baixar(sala, S.BASE_PERSIANA)
ana, beto, ger = (A.montar_boneco(n) for n in ("ana_a", "beto", "gerente"))

# ------------------------------------------------------------------ post-its, built on the rest pose and pinned to each right hand
AMARELO = M.simples("postit_c4", "#F2D64B", 0.7)
TINTA = M.simples("tinta_postit", "#1B1B1F", 0.5)
FONTE_MAO = bpy.data.fonts.load(os.path.expanduser("~/.local/share/fonts/caveat/Caveat.ttf"))


def postit(c, nome):
    """Post-it pinched at the right fingertips, its faces across the palm; "6" on both faces, upright when the
    fingers point up."""
    bpy.context.view_layer.update()
    mw = c["rig"].matrix_world
    mao = osso(c, "mao.R")
    a, b = mw @ mao.head, mw @ mao.tail
    dedos = (b - a).normalized()
    centro = b + dedos * 0.03
    x = Vector((1, 0, 0))
    cima = dedos  # measured: with this rig the digit reads upright (not as a 9) when he holds the card up
    cima = (cima - cima.project(x)).normalized()
    partes = [M.caixa(nome, centro, (0.076, 0.076, 0.003), AMARELO, bev=0.001,
                      rot=Matrix((cima.cross(x), cima, x)).transposed().to_euler())]
    for sinal in (1, -1):
        n = x * sinal
        rot = Matrix((cima.cross(n), cima, n)).transposed().to_euler()
        t = M.texto(f"{nome}_6_{sinal}", "6", centro + n * 0.0025, 0.07, TINTA, rot=rot)
        t.data.font = FONTE_MAO
        partes.append(t)
        partes.append(M.caixa(f"{nome}_sub_{sinal}", centro + n * 0.0025 - cima * 0.03, (0.03, 0.004, 0.001), TINTA, bev=0, rot=rot))
    for o in partes:
        A._no_osso(o, c["rig"], "mao.R")
    return partes


POSTIT_ANA, POSTIT_GER = postit(ana, "postit_ana"), postit(ger, "postit_ger")

# ------------------------------------------------------------------ blocking
GER_LOC, BETO_LOC = Vector((X0 - 0.5, -0.85, 0)), Vector((X0 + 0.45, -0.8, 0))
ger["rig"].location, ger["rig"].rotation_euler.z = GER_LOC, -0.2
beto["rig"].location, beto["rig"].rotation_euler.z = BETO_LOC, 0.2
ana["rig"].location = (X0 + 1.15, 0.45, 0)
CAMINHO = [Vector((X0 + 1.15, 0.45, 0)), Vector((X0 + 1.0, -1.2, 0)), Vector((X0 + 0.0, -1.32, 0))]
VEL, INICIO_PASSOS = 0.08, 8  # metres per frame, first walking frame


def rumo(v):
    """Rig z rotation that points the puppet (rest pose faces -y) along v."""
    return math.atan2(v.x, -v.y)


ANA_PARA_GER = GER_LOC - CAMINHO[-1]
ROT_ANA_FINAL, ROT_GER_FINAL = rumo(ANA_PARA_GER), rumo(-ANA_PARA_GER)
ENTREGA = (CAMINHO[-1] + GER_LOC) / 2 + Vector((0, 0, 1.12))  # hand-over point between them


def no_caminho(dist):
    """(position, heading) at a distance along the path; None heading once arrived."""
    for a, b in zip(CAMINHO, CAMINHO[1:]):
        seg = (b - a).length
        if dist <= seg:
            return a + (b - a) * (dist / seg), b - a
        dist -= seg
    return CAMINHO[-1], None


def no_corpo(c, local):
    return c["rig"].matrix_world @ Vector(local)


# ------------------------------------------------------------------ cameras
def camera(nome, loc, alvo, lente, foco, f0, fstop=2.8):
    cam = bpy.data.objects.new(nome, bpy.data.cameras.new(nome))
    M.sc.collection.objects.link(cam)
    cam.location = loc
    M.mirar(cam, alvo)
    cam.data.lens = lente
    cam.data.dof.use_dof, cam.data.dof.focus_distance, cam.data.dof.aperture_fstop = True, foco, fstop
    M.sc.timeline_markers.new(nome, frame=f0).camera = cam
    return cam


meio = (CAMINHO[-1] + GER_LOC) / 2
lado = Vector((-ANA_PARA_GER.y, ANA_PARA_GER.x, 0)).normalized()
lado = lado if lado.y < 0 else -lado  # the side facing the corridor
camera("4a", (X0 + 0.3, -4.3, 1.5), (X0 + 0.3, -0.4, 1.2), 30, 3.6, 1)
camera("4b", meio + lado * 2.0 + Vector((0, 0, 1.45)), meio + Vector((0, 0, 1.3)), 42, 2.0, PLANO_B)
camera("4d", (X0 - 0.05, -3.7, 1.5), (X0 - 0.05, -0.9, 1.35), 38, 2.8, PLANO_D)  # all three: he looks over at Beto

# ------------------------------------------------------------------ animation (12 fps, every frame hand-posed)
PISCA = {"ana": (20, 70), "beto": (12, 50, 88), "ger": (30, 66, 101)}


def braco_livre(c, lado, s):
    mira(c, f"braco.{lado}", (s * 0.08, 0.02, -1))
    mira(c, f"antebraco.{lado}", (s * 0.05, -0.12, -1))
    mira(c, f"mao.{lado}", (0, -0.05, -1), 90 * s)


def mistura(a, b, k):
    return a.lerp(b, max(0.0, min(1.0, k)))


def pose_ana(f):
    rosto(ana, f, None, PISCA["ana"])
    dist = max(0, f - INICIO_PASSOS) * VEL
    pos, rumo_v = no_caminho(dist)
    if rumo_v is not None:
        fase = dist / 0.8 * math.tau
        ana["rig"].location = pos + Vector((0, 0, 0.012 * abs(math.cos(fase))))
        ana["rig"].rotation_euler.z = rumo(rumo_v)
        bpy.context.view_layer.update()
        andar(ana, rumo_v, fase)
        mira(ana, "mao.R", (0, 0, -1), 90)
        mira(ana, "mao.L", (0, 0, -1), -90)
        girar(ana, "cabeca", (0.0, 0.0, 0.0))
        return
    # arrived: a two-frame stop-motion turn to face him, then the hand-over
    chegou = INICIO_PASSOS + int(sum((b - a).length for a, b in zip(CAMINHO, CAMINHO[1:])) / VEL) + 1
    ultimo = rumo(CAMINHO[-1] - CAMINHO[-2])
    k = min(1.0, (f - chegou + 1) / 3)
    ana["rig"].location = pos
    ana["rig"].rotation_euler.z = ultimo + (ROT_ANA_FINAL - ultimo) * k
    for nome in ("coxa.L", "coxa.R", "canela.L", "canela.R"):
        osso(ana, nome).rotation_mode = "QUATERNION"
        osso(ana, nome).rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()
    braco_livre(ana, "L", 1)
    solta = no_corpo(ana, (-0.22, -0.12, 0.95))
    sobe = {46: 0.3, 47: 0.6, 48: 0.85}.get(f, 1.0 if 49 <= f < TROCA + 1 else 0.0)
    if f > TROCA:
        sobe = max(0.0, 1.0 - (f - TROCA) / 4)
    alvo = mistura(solta, ENTREGA + (CAMINHO[-1] - GER_LOC).normalized() * 0.1, sobe)
    alcancar(ana, "R", alvo, polo=no_corpo(ana, (-1, 0.3, -1)) - no_corpo(ana, (0, 0, 0)))
    mira(ana, "mao.R", mistura(Vector((0, 0, -1)), (GER_LOC - CAMINHO[-1]).normalized(), sobe), 90)
    girar(ana, "cabeca", (-0.08 if f >= PLANO_B else 0.0, 0.0, 0.0))


def pose_ger(f):
    rosto(ger, f, None, PISCA["ger"])
    vira = {42: 0.4, 43: 0.8}.get(f, 1.0 if f >= 44 else 0.0)
    ger["rig"].rotation_euler.z = -0.2 + (ROT_GER_FINAL + 0.2) * vira
    bpy.context.view_layer.update()
    braco_livre(ger, "L", 1)
    solta = no_corpo(ger, (-0.22, -0.05, 0.92))
    olhar = no_corpo(ger, (-0.06, -0.3, 1.3))  # card held up in front of his face
    if f < 50:
        alvo, k_dedos = solta, 0.0
    elif f <= TROCA:
        alvo, k_dedos = mistura(solta, ENTREGA, (f - 49) / 4), 0.5
    else:
        alvo, k_dedos = mistura(ENTREGA, olhar, (f - TROCA) / 5), 1.0
    alcancar(ger, "R", alvo, polo=no_corpo(ger, (-1, 0.5, -1)) - no_corpo(ger, (0, 0, 0)))
    mira(ger, "mao.R", mistura(Vector((0, 0, -1)), Vector((0, 0, 1)), k_dedos), 90)
    # head: the door, Ana walking up, the post-it, then Beto
    if f < 20:
        cab = (0.05, 0.7, 0.0)
    elif f < 44:
        cab = (0.0, 0.35, 0.0)
    elif f < 96 and f > TROCA + 2:
        cab = (0.25, 0.0, 0.0)  # x > 0 looks down: at the post-it
    elif f >= 96:
        cab = (0.0, 0.7, 0.0)  # y > 0 turns towards +x: Beto
    else:
        cab = (-0.1, 0.0, 0.0)
    girar(ger, "cabeca", cab)
    girar(ger, "peito", (0.012 * math.sin(f / 4 + 3), 0.0, 0.0))


def pose_beto(f):
    rosto(beto, f, None, PISCA["beto"])
    braco_livre(beto, "L", 1)
    braco_livre(beto, "R", -1)
    if f < 30:
        cab = (0.05, 0.7, 0.0)  # the door, on his left
    elif f < 98:
        cab = (0.0, -0.45, 0.0)  # the hand-over
    else:
        cab = (-0.35, 0.0, 0.0)  # caught: studies the ceiling
    girar(beto, "cabeca", cab)
    girar(beto, "peito", (0.012 * math.sin(f / 4 + 1), 0.0, 0.0))


def pose(f):
    sala["porta"].rotation_euler.z = {3: 0.3, 4: 0.7, 5: 1.0, 6: 1.2}.get(f, 1.3 if f > 6 else 0.0)
    pose_ana(f)
    pose_ger(f)
    pose_beto(f)
    for o in POSTIT_ANA:
        o.hide_render = f > TROCA
    for o in POSTIT_GER:
        o.hide_render = f <= TROCA


# insert camera on the post-it: pose the frame, then frame the card from his eyes' side
pose(PLANO_C + 4)
bpy.context.view_layer.update()
cartao = POSTIT_GER[0].matrix_world.translation.copy()
normal = (POSTIT_GER[0].matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
cabeca = ger["rig"].matrix_world @ osso(ger, "cabeca").head
normal = normal if normal.dot(cabeca - cartao) > 0 else -normal  # the face he is reading
camera("4c", cartao + normal * 0.13 + Vector((0, 0, 0.02)), cartao, 30, 0.13, PLANO_C, 4.0)  # just in front of his glasses

extras = [(o, "hide_render") for o in POSTIT_ANA + POSTIT_GER] + [(sala["porta"], "rotation_euler")]
gravar([ana, beto, ger], N_QUADROS, pose, {sala["key"]: 600}, extras)
renderizar(ARGS, SAIDA, "6 20 36 44 50 60 86 100")
