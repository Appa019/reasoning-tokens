# Scene 6 of video 02 (11 s): Ana walks into the glass room; cut on the same framing to late afternoon (clock at
# 5:40, warm low light, Beto yawning); she comes out and sticks a post-it with the figure on Carla's tablet; insert of
# the spreadsheet, the total turns green; Carla: "It balances."
# ~/.local/opt/blender-4.2.23-linux-x64/blender -b -P cena6.py -- still N | anim | poses
# Output: ../saida/cena6/ (f_0001.png ... f_0132.png at 12 fps)
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
SAIDA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "saida", "cena6"))
N_QUADROS = 132
TARDE, PLANO_C, PLANO_D = 47, 89, 109  # cut to late afternoon, spreadsheet insert, two-shot
TROCA = 82  # frame the post-it lands on the tablet
VERDE = 98  # frame the total turns green
X0 = S.X0
VALOR = "$3.84M"

sala = S.montar()
S.baixar(sala, S.BASE_PERSIANA)
ana, beto, ger, carla = (A.montar_boneco(n) for n in ("ana_a", "beto", "gerente", "carla"))

# ------------------------------------------------------------------ blocking (manager and Beto where scene 4 left them)
GER_LOC, BETO_LOC, CARLA_LOC = Vector((X0 - 0.3, -0.75, 0)), Vector((X0 + 0.45, -0.8, 0)), Vector((X0 - 0.7, -1.45, 0))
ENTRA = [Vector((X0 - 1.4, -1.1, 0)), Vector((X0 + 1.0, -1.15, 0)), Vector((X0 + 1.15, 0.45, 0)), Vector((X0 + 0.2, 1.2, 0))]
SAI = [Vector((X0 + 1.15, 0.45, 0)), Vector((X0 + 1.0, -1.2, 0)), Vector((X0 - 0.05, -1.6, 0))]
VEL_ENTRA, VEL_SAI, INICIO_ENTRA, INICIO_SAI = 0.13, 0.11, 2, 50


def rumo(v):
    """Rig z rotation that points the puppet (rest pose faces -y) along v."""
    return math.atan2(v.x, -v.y)


ROT_CARLA = rumo(SAI[-1] - CARLA_LOC)
ROT_ANA_FINAL = rumo(CARLA_LOC - SAI[-1])
ger["rig"].location, ger["rig"].rotation_euler.z = GER_LOC, -0.2
beto["rig"].location, beto["rig"].rotation_euler.z = BETO_LOC, 0.2
carla["rig"].location, carla["rig"].rotation_euler.z = CARLA_LOC, ROT_CARLA
ana["rig"].location = ENTRA[0]
bpy.context.view_layer.update()


def no_corpo(c, local):
    return c["rig"].matrix_world @ Vector(local)


def no_caminho(caminho, dist):
    """(position, heading) at a distance along a path; None heading once arrived."""
    for a, b in zip(caminho, caminho[1:]):
        seg = (b - a).length
        if dist <= seg:
            return a + (b - a) * (dist / seg), b - a
        dist -= seg
    return caminho[-1], None


# ------------------------------------------------------------------ Carla's tablet, screen tilted up towards her face
FONTE_MAO = bpy.data.fonts.load(os.path.expanduser("~/.local/share/fonts/caveat/Caveat.ttf"))
TABLET = no_corpo(carla, (0, -0.28, 1.02))
R = Matrix.Rotation(ROT_CARLA, 3, "Z") @ Matrix.Rotation(-0.9, 3, "X") @ Matrix.Rotation(math.pi, 3, "Z")
U, V, N = R.col[0], R.col[1], R.col[2]  # reading right, reading up, screen normal (as Carla reads it)
ROT = R.to_euler()
M.caixa("tablet", TABLET, (0.26, 0.18, 0.012), M.clay("tablet", "#2B2B2E", boneco=False, bump=0.3), bev=0.006, rot=ROT)
TELA = TABLET + N * 0.0065
M.caixa("tablet_tela", TELA, (0.235, 0.16, 0.002), M.simples("planilha", "#FFFFFF", 0.4, emissao=0.9), bev=0, rot=ROT)


def na_tela(u, v, h=0.0):
    return TELA + U * u + V * v + N * (0.0012 + h)


# spreadsheet: header bar, five rows of grey "figures", a total row whose cell carries the figure
cinza = M.simples("planilha_dado", "#AEB6BF", 0.5, emissao=0.3)
linha = M.simples("planilha_grade", "#D5DAE0", 0.5, emissao=0.3)
M.caixa("planilha_topo", na_tela(0, 0.067), (0.235, 0.022, 0.0008), M.simples("planilha_topo", "#1E7B4E", 0.4, emissao=0.6), bev=0, rot=ROT)
for i in range(6):
    v = 0.04 - i * 0.022
    M.caixa(f"planilha_linha{i}", na_tela(0, v - 0.011), (0.22, 0.0012, 0.0006), linha, bev=0, rot=ROT)
    if i < 5:
        M.caixa(f"planilha_rot{i}", na_tela(-0.065, v), (0.06 + 0.012 * (i % 3), 0.006, 0.0006), cinza, bev=0, rot=ROT)
        M.caixa(f"planilha_num{i}", na_tela(0.075, v), (0.035 + 0.008 * ((i + 1) % 2), 0.006, 0.0006), cinza, bev=0, rot=ROT)
total = M.caixa("planilha_total", na_tela(0.06, -0.068), (0.09, 0.02, 0.0006), M.simples("total_neutro", "#E9EDF1", 0.5, emissao=0.3), bev=0, rot=ROT)
total_ok = M.caixa("planilha_total_ok", na_tela(0.06, -0.068, 0.0002), (0.09, 0.02, 0.0006), M.simples("total_ok", "#BDEBCF", 0.5, emissao=0.5), bev=0, rot=ROT)
t = M.texto("planilha_valor", VALOR, na_tela(0.06, -0.068, 0.0008), 0.016, M.simples("tinta_planilha", "#1B1B1F", 0.5), rot=ROT)
verde = M.simples("check_verde", "#1E7B4E", 0.4, emissao=0.4)
check = [M.caixa("check_a", na_tela(-0.012, -0.071, 0.0008), (0.008, 0.0025, 0.0006), verde, bev=0,
                 rot=(R @ Matrix.Rotation(-0.8, 3, "Z")).to_euler()),
         M.caixa("check_b", na_tela(-0.004, -0.067, 0.0008), (0.016, 0.0025, 0.0006), verde, bev=0,
                 rot=(R @ Matrix.Rotation(0.9, 3, "Z")).to_euler())]

# post-it: stuck on the screen corner on Ana's side, and the one in her hand before that
AMARELO = M.simples("postit_c6", "#F2D64B", 0.7)
TINTA = M.simples("tinta_postit", "#1B1B1F", 0.5)
lado_ana = 1 if U.dot(SAI[-1] - CARLA_LOC) > 0 else -1
COLA = na_tela(lado_ana * 0.072, 0.035, 0.002)
rot_cola = (R @ Matrix.Rotation(-0.12 * lado_ana, 3, "Z")).to_euler()
NA_TELA = [M.caixa("postit_tela", COLA, (0.07, 0.07, 0.002), AMARELO, bev=0.001, rot=rot_cola)]
txt = M.texto("postit_tela_txt", VALOR, COLA + N * 0.0013, 0.02, TINTA, rot=rot_cola)
txt.data.font = FONTE_MAO
NA_TELA.append(txt)


def postit_na_mao(c, nome):
    """Post-it pinched at the right fingertips, the figure on both faces."""
    bpy.context.view_layer.update()
    mw = c["rig"].matrix_world
    mao = osso(c, "mao.R")
    a, b = mw @ mao.head, mw @ mao.tail
    dedos = (b - a).normalized()
    centro = b + dedos * 0.03
    x = Vector((1, 0, 0))
    cima = (dedos - dedos.project(x)).normalized()
    partes = [M.caixa(nome, centro, (0.07, 0.07, 0.003), AMARELO, bev=0.001,
                      rot=Matrix((cima.cross(x), cima, x)).transposed().to_euler())]
    for sinal in (1, -1):
        n = x * sinal
        o = M.texto(f"{nome}_txt_{sinal}", VALOR, centro + n * 0.0025, 0.02, TINTA,
                    rot=Matrix((cima.cross(n), cima, n)).transposed().to_euler())
        o.data.font = FONTE_MAO
        partes.append(o)
    for o in partes:
        A._no_osso(o, c["rig"], "mao.R")
    return partes


NA_MAO = postit_na_mao(ana, "postit_ana")

# ------------------------------------------------------------------ late-afternoon light: a low warm sun from the left
sol = bpy.data.lights.new("sol_tarde", "SUN")  # parallel, low and hard: long shadows across the corridor
sol.color, sol.angle = (1.0, 0.42, 0.16), math.radians(1.5)
sol_obj = bpy.data.objects.new("sol_tarde", sol)
M.sc.collection.objects.link(sol_obj)
sol_obj.location = (X0 - 3, -2, 2)
M.mirar(sol_obj, sol_obj.location + Vector((1.0, 0.45, -0.22)))
VISTA = M.sc.view_settings
KEY_LUZ, FILL = sala["key"], bpy.data.lights["fill_sala"]


def luz_do_dia(f):
    tarde = f >= TARDE
    sol.energy = 4.5 if tarde else 0
    VISTA.exposure = -0.7 if tarde else -0.3
    KEY_LUZ.energy = 70 if tarde else 600
    KEY_LUZ.color = (1.0, 0.6, 0.38) if tarde else (1.0, 0.86, 0.72)
    FILL.energy = 45 if tarde else 90
    FILL.color = (0.55, 0.65, 1.0) if tarde else (0.82, 0.9, 1.0)
    minutos = 50 if not tarde else 40
    hora = 10 if not tarde else 17
    sala["minuto"].rotation_euler.y = minutos / 60 * math.tau
    sala["hora"].rotation_euler.y = (hora + minutos / 60) / 12 * math.tau


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


camera("6a", (X0 + 0.15, -4.3, 1.5), (X0 + 0.15, -0.4, 1.2), 30, 3.6, 1)  # same framing on both sides of the cut
M.sc.timeline_markers.new("6b", frame=TARDE).camera = bpy.data.objects["6a"]
camera("6c", TELA + N * 0.24 + V * 0.02, TELA - V * 0.005, 30, 0.24, PLANO_C, 4.0)  # from where her eyes are: her body is hidden in the insert
camera("6d", (X0 - 0.3, -3.6, 1.45), (X0 - 0.38, -1.5, 1.35), 40, 2.1, PLANO_D)

# ------------------------------------------------------------------ animation (12 fps, every frame hand-posed)
FALA = {"carla": (112, "ixaaaeexx")}  # "It balances."
PISCA = {"ana": (12, 95), "beto": (30, 120), "ger": (20, 72, 126), "carla": (40, 100, 128)}


def braco_livre(c, lado, s):
    mira(c, f"braco.{lado}", (s * 0.08, 0.02, -1))
    mira(c, f"antebraco.{lado}", (s * 0.05, -0.12, -1))
    mira(c, f"mao.{lado}", (0, -0.05, -1), 90 * s)


def em_pe(c):
    for nome in ("coxa.L", "coxa.R", "canela.L", "canela.R"):
        osso(c, nome).rotation_mode = "QUATERNION"
        osso(c, nome).rotation_quaternion = (1, 0, 0, 0)


def caminhar(c, caminho, dist):
    """Walk pose along a path; False once arrived (rig left at the end point)."""
    pos, rumo_v = no_caminho(caminho, dist)
    c["rig"].location = pos
    if rumo_v is None:
        return False
    fase = dist / 0.8 * math.tau
    c["rig"].location = pos + Vector((0, 0, 0.012 * abs(math.cos(fase))))
    c["rig"].rotation_euler.z = rumo(rumo_v)
    bpy.context.view_layer.update()
    andar(c, rumo_v, fase)
    mira(c, "mao.R", (0, 0, -1), 90)
    mira(c, "mao.L", (0, 0, -1), -90)
    girar(c, "cabeca", (0.0, 0.0, 0.0))
    return True


def pose_ana(f):
    rosto(ana, f, None, PISCA["ana"])
    fora = 44 < f < TARDE  # behind the blind: out of the shot
    ana["obj"].hide_render = fora
    for d in ana["domos"]:
        d.hide_render = d.hide_render or fora
    if f < TARDE:
        if not caminhar(ana, ENTRA, max(0, f - INICIO_ENTRA) * VEL_ENTRA):
            em_pe(ana)
        return
    if f < INICIO_SAI:
        ana["rig"].location, ana["rig"].rotation_euler.z = SAI[0], rumo(SAI[1] - SAI[0])
        em_pe(ana)
        bpy.context.view_layer.update()
        braco_livre(ana, "L", 1)
        braco_livre(ana, "R", -1)
        return
    if caminhar(ana, SAI, (f - INICIO_SAI) * VEL_SAI):
        return
    # arrived: turns to Carla in two frames, presses the post-it onto the screen corner, hand back down
    chegou = INICIO_SAI + int(sum((b - a).length for a, b in zip(SAI, SAI[1:])) / VEL_SAI) + 1
    ultimo = rumo(SAI[-1] - SAI[-2])
    k = min(1.0, (f - chegou + 1) / 3)
    ana["rig"].rotation_euler.z = ultimo + (ROT_ANA_FINAL - ultimo) * k
    em_pe(ana)
    bpy.context.view_layer.update()
    braco_livre(ana, "L", 1)
    solta = no_corpo(ana, (-0.22, -0.12, 0.95))
    pulso = COLA - (COLA - no_corpo(ana, (0, 0, COLA.z))).normalized() * 0.11 + N * 0.03
    sobe = min(1.0, max(0.0, (f - (TROCA - 4)) / 4)) if f <= TROCA else max(0.0, 1.0 - (f - TROCA) / 4)
    alcancar(ana, "R", solta.lerp(pulso, sobe), polo=no_corpo(ana, (-1, 0.3, -1)) - no_corpo(ana, (0, 0, 0)))
    mira(ana, "mao.R", Vector((0, 0, -1)).lerp((COLA - pulso).normalized(), sobe), 90)
    girar(ana, "cabeca", (0.2 if f < PLANO_D + 8 else 0.0, 0.0, 0.0))  # at the tablet, then at Carla


def pose_ger(f):
    rosto(ger, f, None, PISCA["ger"])
    braco_livre(ger, "L", 1)
    braco_livre(ger, "R", -1)
    if f < TARDE:
        cab = (0.0, 0.35 if f < 20 else 0.7, 0.0)  # follows Ana to the door
    elif f < INICIO_SAI + 2:
        cab = (0.15, 0.0, 0.1)  # tired, looking at the floor
    elif f < TROCA:
        cab = (0.0, 0.6, 0.0)  # the door opens
    else:
        cab = (0.1, -0.5, 0.0)  # at the tablet
    girar(ger, "cabeca", cab)
    girar(ger, "peito", (0.012 * math.sin(f / 4 + 3), 0.0, 0.0))


def pose_beto(f):
    boceja = TARDE + 6 <= f < TARDE + 14
    rosto(beto, f, (TARDE + 6, "oooooooo") if boceja else None, PISCA["beto"])
    braco_livre(beto, "L", 1)
    braco_livre(beto, "R", -1)
    if f < TARDE:
        cab = (0.0, 0.7, 0.0)
    elif boceja:
        cab = (-0.3, 0.0, 0.1)  # yawn: head back
    elif f < INICIO_SAI + 10:
        cab = (0.2, 0.0, -0.15)  # nodding off
    else:
        cab = (0.0, -0.5, 0.0)  # the hand-over
    girar(beto, "cabeca", cab)
    girar(beto, "peito", (0.012 * math.sin(f / 4 + 1), 0.0, 0.0))


def pose_carla(f):
    rosto(carla, f, FALA["carla"] if f >= PLANO_D else None, PISCA["carla"])
    escondida = PLANO_C <= f < PLANO_D  # the insert camera sits where her head is
    carla["obj"].hide_render = escondida
    for d in carla["domos"]:
        d.hide_render = d.hide_render or escondida
    for lado, s in (("L", 1), ("R", -1)):
        alcancar(carla, lado, TABLET + (no_corpo(carla, (s * 0.15, -0.28, 1.0)) - no_corpo(carla, (0, -0.28, 1.0))),
                 polo=no_corpo(carla, (s * 1, 0.5, -1)) - no_corpo(carla, (0, 0, 0)))
    aceno = {121: 0.12, 122: 0.0, 123: 0.12}.get(f, 0.0)  # nods
    if f < TROCA or f > PLANO_D + 8:
        cab = (aceno, 0.0 if f > PLANO_D + 8 else 0.25, 0.0)  # at Ana (or the door), then towards Ana again
    else:
        cab = (0.35, 0.0, 0.0)  # reads the tablet
    girar(carla, "cabeca", cab)
    girar(carla, "peito", (0.012 * math.sin(f / 4 + 4), 0.0, 0.0))


def pose(f):
    luz_do_dia(f)
    sala["porta"].rotation_euler.z = porta(f)
    pose_ana(f)
    pose_ger(f)
    pose_beto(f)
    pose_carla(f)
    for o in NA_MAO:
        o.hide_render = not (TARDE <= f <= TROCA)
    for o in NA_TELA:
        o.hide_render = f <= TROCA
    total_ok.hide_render = f < VERDE
    for o in check:
        o.hide_render = f < VERDE + 2


def porta(f):
    aberta = {26: 0.4, 27: 0.8, 28: 1.1}  # she pulls it as she reaches it
    fecha = {39: 0.9, 40: 0.5, 41: 0.2}
    if f < TARDE:
        if f in aberta:
            return aberta[f]
        if f in fecha:
            return fecha[f]
        return 1.3 if 28 < f < 39 else 0.0
    return {INICIO_SAI - 2: 0.4, INICIO_SAI - 1: 0.8, INICIO_SAI: 1.1}.get(f, 1.3 if f > INICIO_SAI else 0.0)


extras = [(o, "hide_render") for o in NA_MAO + NA_TELA + check + [total_ok, ana["obj"], carla["obj"]]]
extras += [(sala["porta"], "rotation_euler"), (sala["minuto"], "rotation_euler"), (sala["hora"], "rotation_euler")]
extras += [(VISTA, "exposure"), (sol, "energy"), (KEY_LUZ, "energy"), (KEY_LUZ, "color"), (FILL, "energy"), (FILL, "color")]
gravar([ana, beto, ger, carla], N_QUADROS, pose, {}, extras)
renderizar(ARGS, SAIDA, "10 25 40 55 70 84 100 118")
