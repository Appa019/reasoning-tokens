# Scene 7 of video 02 (8 s), still at dusk in the corridor: Carla hands the manager the day's invoice, a paper roll;
# insert of its top ("reasoning tokens"); he holds it up and the roll drops, unrolls to the floor and rolls off
# towards us. He looks down the whole length of it, then at us. End.
# ~/.local/opt/blender-4.2.23-linux-x64/blender -b -P cena7.py -- still N | anim | poses
# Output: ../saida/cena7/ (f_0001.png ... f_0096.png at 12 fps)
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
SAIDA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "saida", "cena7"))
N_QUADROS = 96
PLANO_B, PLANO_C = 29, 45  # insert on the invoice top, wide on the corridor
TROCA, QUEDA = 15, 33  # roll changes hands; he lets the roll drop
X0 = S.X0

sala = S.montar()
S.baixar(sala, S.BASE_PERSIANA)
ana, beto, ger, carla = (A.montar_boneco(n) for n in ("ana_a", "beto", "gerente", "carla"))


def rumo(v):
    """Rig z rotation that points the puppet (rest pose faces -y) along v."""
    return math.atan2(v.x, -v.y)


GER_LOC = Vector((X0 - 0.1, -1.2, 0))
for c, loc in ((ger, GER_LOC), (carla, Vector((X0 - 0.75, -1.35, 0))), (ana, Vector((X0 + 0.5, -1.0, 0))),
               (beto, Vector((X0 + 0.95, -0.75, 0)))):
    c["rig"].location = loc
    c["rig"].rotation_euler.z = 0.0 if c is ger else rumo(GER_LOC - loc) * 0.6
bpy.context.view_layer.update()


def no_corpo(c, local):
    return c["rig"].matrix_world @ Vector(local)


# ------------------------------------------------------------------ dusk, as at the end of scene 6
sol = bpy.data.lights.new("sol_tarde", "SUN")
sol.color, sol.angle, sol.energy = (1.0, 0.42, 0.16), math.radians(1.5), 4.5
sol_obj = bpy.data.objects.new("sol_tarde", sol)
M.sc.collection.objects.link(sol_obj)
sol_obj.location = (X0 - 3, -2, 2)
M.mirar(sol_obj, sol_obj.location + Vector((1.0, 0.45, -0.22)))
sala["key"].energy, sala["key"].color = 70, (1.0, 0.6, 0.38)
bpy.data.lights["fill_sala"].energy, bpy.data.lights["fill_sala"].color = 45, (0.55, 0.65, 1.0)
sala["minuto"].rotation_euler.y = 45 / 60 * math.tau
sala["hora"].rotation_euler.y = (17 + 45 / 60) / 12 * math.tau
VISTA = M.sc.view_settings

# ------------------------------------------------------------------ the invoice
LARG = 0.26
TOPO = no_corpo(ger, (0, -0.32, 1.22))  # top edge, held in both hands
Y_PAPEL = TOPO.y
CABECA_H = 0.17  # printed header block: room for his hands above the title
Z_ROLO0 = TOPO.z - CABECA_H


def papel(nome, eixo):
    """White paper printed with rows of grey "items": the rows are laid out in world space along eixo ("Y" or "Z"),
    so the paper can grow (scale) without stretching its print, as paper that unrolls and then lies still."""
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.8
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(nt.nodes.new("ShaderNodeNewGeometry").outputs["Position"], sep.inputs[0])

    def op(tipo, a, c=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = tipo
        for i, v in enumerate((a, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    linha = op("DIVIDE", sep.outputs[eixo], 0.028)
    barra = op("LESS_THAN", op("FRACT", linha), 0.32)
    sorte = op("FRACT", op("MULTIPLY", op("SINE", op("MULTIPLY", op("FLOOR", linha), 12.9898)), 43758.5))
    x = op("SUBTRACT", sep.outputs["X"], TOPO.x)
    esq = op("MULTIPLY", op("GREATER_THAN", x, -0.11), op("LESS_THAN", x, op("ADD", -0.105, op("MULTIPLY", sorte, 0.07))))
    dir_ = op("MULTIPLY", op("GREATER_THAN", x, 0.055), op("LESS_THAN", x, 0.11))
    tinta = op("MULTIPLY", barra, op("MAXIMUM", esq, dir_))
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value, mix.inputs["B"].default_value = M.rgb("#FFFFFF"), M.rgb("#9AA3AD")
    nt.links.new(tinta, mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    return m


BRANCO = M.simples("fatura_topo", "#FFFFFF", 0.8)
TINTA = M.simples("tinta_fatura", "#1B1B1F", 0.5)
cabeca = [M.caixa("fatura_cabeca", TOPO - Vector((0, 0, CABECA_H / 2)), (LARG, 0.002, CABECA_H), BRANCO, bev=0)]
cabeca.append(M.texto("fatura_titulo", "reasoning tokens", TOPO + Vector((0, -0.0015, -0.115)), 0.026, TINTA))
cabeca.append(M.caixa("fatura_regua", TOPO + Vector((0, -0.0015, -0.145)), (LARG - 0.04, 0.0005, 0.002), TINTA, bev=0))
# hanging part grows down from the header; the floor part grows along -y from where the paper touches down
pend = M.caixa("fatura_pend", (0, 0, 0), (LARG, 0.002, 1.0), papel("fatura_pend", "Z"), bev=0)
chao = M.caixa("fatura_chao", (0, 0, 0), (LARG, 1.0, 0.002), papel("fatura_chao", "Y"), bev=0)
R0, R1, TOTAL = 0.034, 0.02, 4.6
rolo = M.cilindro("fatura_rolo", (0, 0, 0), 1.0, LARG, BRANCO, rot=(0, math.pi / 2, 0), bev=0.0)
bpy.context.view_layer.update()
rolo.rotation_mode = "ZYX"  # spin about its own axis first, then lay it along x


def desenrolado(f):
    """(hanging length, floor length) of paper off the roll at frame f."""
    if f < QUEDA:
        return 0.0, 0.0
    t = (f - QUEDA) / 12
    queda = 0.5 * 7.8 * t * t  # a bit under g: stop-motion fall over a few frames
    if queda < Z_ROLO0:
        return queda, 0.0
    t0 = math.sqrt(2 * Z_ROLO0 / 7.8)
    tau, v0, a = t - t0, 2.6, 1.0
    tau = min(tau, v0 / a)
    return Z_ROLO0, v0 * tau - 0.5 * a * tau * tau


def pos_rolo(f):
    """Places the roll and both paper pieces for frame f (from QUEDA on)."""
    lv, lc = desenrolado(f)
    r = math.sqrt(max(R1 * R1, R0 * R0 - (R0 * R0 - R1 * R1) * (lv + lc) / TOTAL))
    rolo.scale = (r, r, 1.0)
    rolo.rotation_euler = (0, math.pi / 2, -(lv + lc) / r)
    pend.scale.z = max(lv, 0.0001)
    pend.location = (TOPO.x, Y_PAPEL, Z_ROLO0 - lv / 2)
    chao.scale.y = max(lc, 0.0001)
    chao.location = (TOPO.x, Y_PAPEL - lc / 2, 0.001)
    chao.hide_render = lc <= 0
    if lc <= 0:
        rolo.location = (TOPO.x, Y_PAPEL - r, Z_ROLO0 - lv)
    else:
        rolo.location = (TOPO.x, Y_PAPEL - lc, r)


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


camera("7a", (X0 - 0.4, -3.3, 1.45), (X0 - 0.42, -1.25, 1.2), 40, 2.1, 1)
camera("7b", TOPO + Vector((0, -0.6, 0.0)), TOPO - Vector((0, 0, 0.12)), 50, 0.6, PLANO_B, 4.0)
camera("7c", (X0 - 0.05, -4.4, 0.8), (X0 - 0.05, -1.0, 0.95), 28, 3.2, PLANO_C)

# ------------------------------------------------------------------ animation (12 fps, every frame hand-posed)
PISCA = {"ana": (20, 88), "beto": (14, 60), "ger": (8, 76), "carla": (24, 90)}


def braco_livre(c, lado, s):
    mira(c, f"braco.{lado}", (s * 0.08, 0.02, -1))
    mira(c, f"antebraco.{lado}", (s * 0.05, -0.12, -1))
    mira(c, f"mao.{lado}", (0, -0.05, -1), 90 * s)


def ponta_dedos(c):
    bpy.context.view_layer.update()
    mw = c["rig"].matrix_world
    mao = osso(c, "mao.R")
    a, b = mw @ mao.head, mw @ mao.tail
    return b + (b - a).normalized() * 0.03


def rampa(f, ini, n):
    return min(1.0, max(0.0, (f - ini) / n))


ENTREGA = (no_corpo(carla, (-0.2, -0.3, 1.05)) + no_corpo(ger, (-0.2, -0.3, 1.05))) / 2


def pose(f):
    VISTA.exposure = -0.7
    for k, c in (("ana", ana), ("beto", beto), ("ger", ger), ("carla", carla)):
        rosto(c, f, None, PISCA[k])
        girar(c, "peito", (0.012 * math.sin(f / 4 + len(k)), 0.0, 0.0))
    for c in (ana, beto):
        braco_livre(c, "L", 1)
        braco_livre(c, "R", -1)
    braco_livre(carla, "L", 1)
    # Carla holds the roll out to him; he takes it, then holds the invoice up by its top corners
    k_carla = rampa(f, 3, 5) if f <= TROCA else 1.0 - rampa(f, TROCA, 4)
    alcancar(carla, "R", no_corpo(carla, (-0.22, -0.12, 0.95)).lerp(ENTREGA, k_carla),
             polo=no_corpo(carla, (-1, 0.3, -1)) - no_corpo(carla, (0, 0, 0)))
    mira(carla, "mao.R", Vector((0, 0, -1)).lerp(ENTREGA - no_corpo(carla, (0, 0, 1.05)), k_carla), 90)
    if f < PLANO_B:
        braco_livre(ger, "L", 1)
        k = rampa(f, 9, 5) if f <= TROCA else 1.0
        peito = no_corpo(ger, (-0.12, -0.3, 1.1))
        alvo = no_corpo(ger, (-0.22, -0.05, 0.92)).lerp(ENTREGA, k) if f <= TROCA else ENTREGA.lerp(peito, rampa(f, TROCA, 5))
        alcancar(ger, "R", alvo, polo=no_corpo(ger, (-1, 0.5, -1)) - no_corpo(ger, (0, 0, 0)))
        mira(ger, "mao.R", Vector((0.3, -1, 0.2)), 90)
        dono = carla if f <= TROCA else ger
        rolo.location = ponta_dedos(dono)
        rolo.scale, rolo.rotation_euler = (R0, R0, 1.0), (0, math.pi / 2, 0)
        for o in (pend, chao):
            o.hide_render = True
        for o in cabeca:
            o.hide_render = True
        girar(ger, "cabeca", (0.15, -0.55, 0.0))
    else:
        for lado, s in (("L", 1), ("R", -1)):
            alcancar(ger, lado, TOPO + Vector((s * 0.2, 0.03, -0.02)),  # wrists outside the edges: pinches the corners
                     polo=no_corpo(ger, (s * 1, 0.3, -1)) - no_corpo(ger, (0, 0, 0)))
            mira(ger, f"mao.{lado}", Vector((-s * 1, 0, 0.5)), 90 * s)
        for o in cabeca:
            o.hide_render = False
        pend.hide_render = f < QUEDA
        pos_rolo(f)
        if f < QUEDA:
            rolo.location = (TOPO.x, Y_PAPEL - R0, Z_ROLO0)
        # he reads the header, watches it roll away down the corridor, then looks up at us
        cab = (0.3, 0.0, 0.0) if f < 50 else ((0.55, 0.0, 0.0) if f < 82 else (0.0, 0.0, 0.0))
        girar(ger, "cabeca", cab)
    # the others: at the hand-over, then the paper on the floor
    no_chao = f >= 48
    girar(carla, "cabeca", (0.45, 0.3, 0.0) if no_chao else (0.05, 0.3, 0.0))
    girar(ana, "cabeca", (0.45, -0.2, 0.0) if no_chao else (0.0, -0.35, 0.0))
    girar(beto, "cabeca", (0.45, -0.35, 0.0) if no_chao and f < 84 else (0.0, -0.5, 0.0))


extras = [(o, "hide_render") for o in cabeca + [pend, chao]]
extras += [(rolo, "location"), (rolo, "scale"), (rolo, "rotation_euler"), (pend, "location"), (pend, "scale"),
           (chao, "location"), (chao, "scale"), (VISTA, "exposure")]
gravar([ana, beto, ger, carla], N_QUADROS, pose, {}, extras)
renderizar(ARGS, SAIDA, "6 14 22 32 38 50 62 90")
