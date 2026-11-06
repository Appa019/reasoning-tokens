# Office set for video 02, clay stop-motion look: walls, window with blinds, whiteboard, clock, poster, cabinet,
# plant, shelf, desk with laptops and props, lights. Shared by every scene.
import math
import random

import bpy
from mathutils import Vector

from massinha import (PAPEL, PRETO, TINTA, bastao, blob, caixa, cilindro, clay, luz, mirar, rgb, sc, simples,
                      toro, vazio)


def montar():
    """Builds the room; returns the key light (its energy flickers per frame)."""
    random.seed(11)
    parede = clay("parede", "#C9D6CF", rough=0.85, bump=0.35, var=0.06, boneco=False)
    caixa("chao", (0, 0.5, -0.05), (9, 8, 0.1), clay("carpete", "#6F7A86", rough=0.95, sulcos="carpete", var=0.05, boneco=False), bev=0)
    # back wall with a window opening on the left
    for nome, loc, dim in (("parede_e", (-3.4, 1.8, 1.75), (3.3, 0.1, 3.5)), ("parede_d", (1.95, 1.8, 1.75), (6.0, 0.1, 3.5)),
                           ("parede_b", (-1.4, 1.8, 0.55), (0.75, 0.1, 1.1)), ("parede_c", (-1.4, 1.8, 2.8), (0.75, 0.1, 1.4))):
        caixa(nome, loc, dim, parede, bev=0)
    caixa("rodape", (0, 1.74, 0.06), (9, 0.03, 0.12), clay("rodape", "#8F9AA3", boneco=False), bev=0.005)
    branco_tinta = clay("batente", "#EEF0EE", rough=0.5, boneco=False, bump=0.5)
    for nome, loc, dim in (("jan_e", (-1.76, 1.76, 1.6), (0.04, 0.06, 1.04)), ("jan_d", (-1.04, 1.76, 1.6), (0.04, 0.06, 1.04)),
                           ("jan_c", (-1.4, 1.76, 2.1), (0.76, 0.06, 0.04)), ("jan_b", (-1.4, 1.74, 1.1), (0.8, 0.1, 0.04))):
        caixa(nome, loc, dim, branco_tinta, bev=0.006)
    persiana = clay("persiana", "#E9E6DC", rough=0.6, boneco=False, bump=0.3)
    for i in range(17):
        caixa(f"lamina{i}", (-1.4, 1.73, 1.15 + i * 0.056), (0.7, 0.05, 0.006), persiana, bev=0.002, rot=(0.7, 0, 0))
    bastao("cordao", (-1.1, 1.7, 2.08), (-1.1, 1.7, 1.3), 0.004, simples("cordao", "#DDD8CC", 0.8))
    bpy.ops.mesh.primitive_plane_add(size=4, location=(-1.4, 2.8, 1.7), rotation=(math.pi / 2, 0, 0))
    bpy.context.active_object.data.materials.append(simples("ceu", "#BFD9F2", emissao=1.5))

    # whiteboard with marker tray and faded old scribbles
    alu = simples("aluminio", "#AEB3B8", 0.35, metal=0.8)
    caixa("quadro_moldura", (-0.25, 1.73, 1.66), (1.3, 0.04, 0.84), alu, bev=0.012)
    caixa("quadro", (-0.25, 1.71, 1.66), (1.22, 0.025, 0.76), simples("quadro", "#FBFBF9", 0.15), bev=0.006)
    caixa("bandeja", (-0.25, 1.68, 1.23), (0.9, 0.08, 0.025), alu, bev=0.006)
    for i, cor in enumerate(("#B42318", "#1F4E8C", "#1B1B1F")):
        bastao(f"pincel{i}", (-0.45 + i * 0.13, 1.66, 1.255), (-0.35 + i * 0.13, 1.66, 1.255), 0.014, clay(f"pincel{i}", cor, boneco=False))
    bastao("seta_q", (-0.15, 1.695, 1.62), (0.2, 1.695, 1.78), 0.006, simples("marcador", "#9FB4CC", 0.6))

    # clock, poster with a bar chart, filing cabinet, plant
    cilindro("relogio_aro", (0.95, 1.74, 2.18), 0.19, 0.05, clay("relogio_aro", "#2B2B2E", boneco=False), rot=(math.pi / 2, 0, 0))
    cilindro("relogio", (0.95, 1.715, 2.18), 0.17, 0.03, simples("relogio", "#FAFAF7", 0.3), rot=(math.pi / 2, 0, 0))
    for i in range(12):
        a = i / 12 * math.tau
        caixa(f"marca{i}", (0.95 + 0.145 * math.sin(a), 1.697, 2.18 + 0.145 * math.cos(a)), (0.008, 0.004, 0.025), TINTA, bev=0, rot=(0, a, 0))
    PONTEIRO = vazio("ponteiro_min", (0.95, 1.69, 2.18))
    caixa("pmin", (0.95, 1.69, 2.235), (0.012, 0.006, 0.12), TINTA, PONTEIRO, bev=0.002)
    caixa("phora", (0.985, 1.69, 2.18), (0.075, 0.006, 0.014), TINTA, bev=0.002)
    caixa("poster", (1.75, 1.745, 1.55), (0.62, 0.01, 0.8), PAPEL, bev=0.003)
    for i, (h, cor) in enumerate(((0.18, "#9FB4CC"), (0.27, "#9FB4CC"), (0.33, "#9FB4CC"), (0.5, "#B42318"))):
        caixa(f"barra{i}", (1.55 + i * 0.13, 1.738, 1.27 + h / 2), (0.08, 0.006, h), simples(f"barra{cor}", cor, 0.6), bev=0)
    metal = clay("arquivo", "#9AA1A8", rough=0.4, boneco=False, bump=0.4)
    caixa("arquivo", (1.62, 1.42, 0.52), (0.5, 0.55, 1.04), metal, bev=0.02)
    for i in range(3):
        caixa(f"gaveta{i}", (1.62, 1.14, 0.2 + i * 0.32), (0.44, 0.02, 0.28), metal, bev=0.01)
        caixa(f"puxador{i}", (1.62, 1.12, 0.29 + i * 0.32), (0.14, 0.03, 0.025), alu, bev=0.008)
    for i, cor in enumerate(("#1F4E8C", "#B42318", "#D9A43B")):
        caixa(f"pasta{i}", (1.45 + i * 0.09, 1.42, 1.19), (0.07, 0.3, 0.3), clay(f"pasta{i}", cor, boneco=False), bev=0.006)
    cilindro("vaso", (-1.75, 1.25, 0.24), 0.17, 0.48, clay("vaso", "#B5643C", boneco=False), bev=0.02)
    cilindro("terra", (-1.75, 1.25, 0.47), 0.15, 0.02, clay("terra", "#3B2A1E", rough=0.95, boneco=False), bev=0)
    verde = clay("folha", "#4E7D45", rough=0.55, boneco=False)
    for i in range(11):
        a = i / 11 * math.tau + random.uniform(-0.2, 0.2)
        incl = random.uniform(0.35, 0.75)
        comp = random.uniform(0.2, 0.3)
        base = Vector((-1.75, 1.25, 0.5))
        d = Vector((math.cos(a) * math.sin(incl), math.sin(a) * math.sin(incl), math.cos(incl)))
        blob(f"folha{i}", base + d * comp, (0.065, 0.016, comp), verde, rot=d.to_track_quat("Z", "Y").to_euler())


    # ceiling with a fluorescent panel, shelf with binders and a small trophy
    caixa("teto", (0, 0.2, 3.05), (9, 8, 0.1), clay("teto", "#E4E8EA", rough=0.9, boneco=False, bump=0.2), bev=0)
    caixa("luminaria", (-0.2, 0.9, 2.995), (1.3, 0.35, 0.02), simples("luminaria", "#FFF8EC", 0.4, emissao=1.5), bev=0.005)
    caixa("prateleira", (-0.25, 1.62, 2.32), (1.1, 0.26, 0.035), clay("prateleira", "#B98B5E", boneco=False, bump=0.3), bev=0.008)
    for i, (cor, h) in enumerate((("#1F4E8C", 0.28), ("#B42318", 0.3), ("#D9A43B", 0.27), ("#4F8A5B", 0.29), ("#1F4E8C", 0.28))):
        caixa(f"fichario{i}", (-0.7 + i * 0.075, 1.62, 2.34 + h / 2), (0.065, 0.22, h), clay(f"fichario{cor}", cor, boneco=False), bev=0.006,
              rot=(0, 0.12 if i == 4 else 0, 0))
    ouro = simples("ouro", "#C9A548", 0.3, metal=1.0)
    cilindro("trofeu_base", (0.12, 1.62, 2.37), 0.05, 0.04, clay("trofeu_base", "#2B211C", boneco=False))
    cilindro("trofeu_haste", (0.12, 1.62, 2.43), 0.012, 0.08, ouro, bev=0.003)
    blob("trofeu_taca", (0.12, 1.62, 2.52), (0.055, 0.055, 0.06), ouro, forca=0)

    # desk and everything on it
    mesa = clay("mesa", "#C79A6B", rough=0.6, sulcos="madeira", cor2="#B98B5E", boneco=False, bump=0.3)
    caixa("mesa_tampo", (-0.2, 0.05, 0.74), (1.9, 0.85, 0.06), mesa, bev=0.02)
    caixa("mesa_frente", (-0.2, -0.33, 0.38), (1.8, 0.04, 0.68), mesa, bev=0.015)
    for x in (-0.75, 0.35):
        caixa(f"gav{x}", (x, -0.355, 0.56), (0.5, 0.02, 0.2), mesa, bev=0.01)
        blob(f"maçaneta{x}", (x, -0.372, 0.56), (0.022, 0.018, 0.022), simples("ouro", "#C9A548", 0.3, metal=1.0), forca=0)
    cadeira = clay("cadeira", "#3A3F47", rough=0.8, boneco=False, bump=0.8)
    for x in (-0.6, 0.2):
        caixa(f"cadeira{x}", (x, 0.7, 1.02), (0.54, 0.1, 0.66), cadeira, bev=0.05)
    cinza = clay("notebook", "#5C6168", rough=0.4, boneco=False, bump=0.4)
    tela = simples("tela", "#CFE3FF", 0.3, emissao=1.6)
    for x, rz in ((-1.02, 0.45), (0.58, -0.45)):
        base = vazio(f"note{x}", (x, 0.12, 0.775))
        caixa(f"note_base{x}", (x, 0.12, 0.785), (0.36, 0.25, 0.02), cinza, base, bev=0.006)
        caixa(f"note_tecl{x}", (x, 0.1, 0.796), (0.3, 0.12, 0.004), PRETO, base, bev=0.001)
        tampa = vazio(f"note_tampa{x}", (x, 0.245, 0.79), base)
        caixa(f"note_tela{x}", (x, 0.245, 0.905), (0.36, 0.015, 0.23), cinza, tampa, bev=0.006)
        caixa(f"note_luz{x}", (x, 0.255, 0.905), (0.32, 0.004, 0.19), tela, tampa, bev=0)
        tampa.rotation_euler.x = -0.22
        base.rotation_euler.z = rz
    caixa("postit_tampa", (0.66, 0.22, 0.95), (0.07, 0.004, 0.07), simples("postit", "#F2D64B", 0.7), bev=0.001, rot=(-0.2, 0, -0.45))
    for i in range(6):
        caixa(f"papel{i}", (-0.42 + random.uniform(-0.01, 0.01), -0.12, 0.775 + i * 0.006), (0.21, 0.29, 0.005), PAPEL,
              bev=0.001, rot=(0, 0, random.uniform(-0.12, 0.12)))
    cilindro("porta_canetas", (-0.16, 0.02, 0.83), 0.045, 0.12, clay("porta", "#2E3A4A", boneco=False))
    for i, (cor, dx, dy) in enumerate((("#B42318", -0.015, 0.0), ("#1F4E8C", 0.015, 0.01), ("#1B1B1F", 0.0, -0.015))):
        bastao(f"caneta{i}", (-0.16 + dx, 0.02 + dy, 0.8), (-0.16 + dx * 3, 0.02 + dy * 3, 0.97), 0.009, clay(f"caneta{i}", cor, boneco=False))
    caneca = clay("caneca", "#B42318", rough=0.35, boneco=False, bump=0.4)
    cilindro("caneca", (0.05, -0.12, 0.83), 0.048, 0.12, caneca)
    toro("alca", (0.105, -0.12, 0.835), 0.032, 0.01, caneca, rot=(math.pi / 2, 0, 0))
    cilindro("cafe", (0.05, -0.12, 0.887), 0.04, 0.005, clay("cafe", "#3B2414", rough=0.15, boneco=False), bev=0)
    calc = clay("calc", "#2F3237", boneco=False, bump=0.4)
    caixa("calculadora", (-0.72, -0.16, 0.785), (0.12, 0.18, 0.02), calc, bev=0.006, rot=(0, 0, 0.25))
    for i in range(4):
        for j in range(4):
            blob(f"tecla{i}{j}", (-0.72 + (i - 1.5) * 0.025 - (j - 1.5) * 0.006, -0.19 + (j - 1.5) * 0.026 + (i - 1.5) * 0.006, 0.797),
                 (0.009, 0.009, 0.005), clay("tecla", "#D8D8D2", boneco=False), forca=0)
    caixa("visor", (-0.705, -0.105, 0.797), (0.09, 0.035, 0.004), simples("visor", "#9DB59A", 0.4), bev=0.001, rot=(0, 0, 0.25))

    key = luz("key", (-2.0, -2.3, 3.0), (0, 0.3, 1.0), 650, 0.6, (1.0, 0.86, 0.72))
    luz("fill", (2.8, -2.0, 1.6), (0, 0.3, 1.0), 90, 3.0, (0.82, 0.9, 1.0))
    spot = bpy.data.lights.new("rim", "SPOT")
    spot.energy, spot.spot_size, spot.spot_blend, spot.shadow_soft_size, spot.color = 260, math.radians(38), 0.6, 0.15, (1.0, 0.95, 0.88)
    rim = bpy.data.objects.new("rim", spot)
    sc.collection.objects.link(rim)
    rim.location = (0.6, 1.45, 2.6)
    mirar(rim, (-0.1, 0.35, 1.15))
    sol = bpy.data.objects.new("sol", bpy.data.lights.new("sol", "SUN"))
    sc.collection.objects.link(sol)
    sol.data.energy, sol.data.angle, sol.data.color = 3.2, math.radians(0.6), (1.0, 0.93, 0.8)
    sol.rotation_euler = Vector((0.45, -1.0, -0.6)).to_track_quat("-Z", "Y").to_euler()
    w = bpy.data.worlds.new("mundo")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = rgb("#DCE1E6")
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.08
    return key
