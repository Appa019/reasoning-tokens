# Glass meeting room for video 02 (scenes 2 and 3): glass front with aluminium mullions, a venetian blind on the
# centre pane that Ana lowers by its cord, whiteboard on the back wall, small table, own lights.
# Built away from the office (x = X0) so both sets share one Blender scene.
import math

import bpy

from massinha import bastao, caixa, cilindro, clay, luz, pai, simples, vazio

X0 = 8.0  # room centre on x; front glass at y = 0, room interior at y > 0
TOPO_PERSIANA, BASE_PERSIANA = 2.3, 0.32
PASSO_LAMINA = 0.045
X_CORDAO = X0 + 0.54


def _vidro(nome="vidro", aspereza=0.03):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.86, 0.93, 0.92, 1)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = aspereza
    b.inputs["IOR"].default_value = 1.45
    return m


def montar():
    """Builds the room. Returns {"key": key light data, "laminas": [slat, top to bottom], "trilho": bottom rail,
    "cordao": cord pivot (scale z = length from the head rail down), "minuto"/"hora": clock hand pivots (rotation y,
    clockwise as seen from the corridor), "porta": door hinge (rotation z opens it)}."""
    parede = clay("parede_sala", "#C9D6CF", rough=0.85, bump=0.3, var=0.05, boneco=False)
    caixa("chao_sala", (X0, 0.0, -0.05), (6, 7, 0.1), clay("carpete_sala", "#6F7A86", rough=0.95, sulcos="carpete", var=0.05, boneco=False), bev=0)
    caixa("sala_fundo", (X0, 2.65, 1.4), (3.4, 0.1, 2.8), parede, bev=0)
    for s in (-1, 1):
        caixa(f"sala_lado{s}", (X0 + s * 1.7, 1.3, 1.4), (0.1, 2.7, 2.8), parede, bev=0)
    caixa("sala_teto", (X0, 1.3, 2.8), (3.5, 2.8, 0.1), clay("teto_sala", "#E4E8EA", rough=0.9, boneco=False, bump=0.2), bev=0)
    caixa("sala_bandeira", (X0, 0.0, 2.58), (3.5, 0.12, 0.44), parede, bev=0.01)
    caixa("teto_corredor", (X0, -2.0, 2.85), (6, 4.0, 0.1), clay("teto_corredor", "#E4E8EA", rough=0.9, boneco=False, bump=0.2), bev=0)
    caixa("sala_luminaria", (X0, 1.3, 2.745), (1.3, 0.45, 0.02), simples("luminaria_sala", "#FFF8EC", 0.4, emissao=1.5), bev=0.005)

    # glass front: three panes between aluminium mullions; glass casts no shadow so outside light reaches the room
    alu = simples("aluminio_sala", "#AEB3B8", 0.35, metal=0.8)
    vidro = _vidro()
    porta = []  # right pane is the door: pane, frosted band and handle swing on a hinge at the right mullion
    for x0, x1 in ((-1.65, -0.6), (-0.6, 0.6), (0.6, 1.65)):
        v = caixa(f"vidro{x0}", (X0 + (x0 + x1) / 2, 0.0, 1.19), (x1 - x0 - 0.04, 0.012, 2.3), vidro, bev=0)
        v.visible_shadow = False
        for poly in v.data.polygons:  # smooth normals on a thin box make the pane refract like a lens
            poly.use_smooth = False
        if x0 == 0.6:
            porta.append(v)
    jateado = _vidro("jateado", 0.35)  # frosted privacy band: tells the eye there is glass here
    for x0, x1 in ((-1.65, -0.6), (-0.6, 0.6), (0.6, 1.65)):
        j = caixa(f"jateado{x0}", (X0 + (x0 + x1) / 2, -0.008, 1.3), (x1 - x0 - 0.04, 0.002, 0.05), jateado, bev=0)
        j.visible_shadow = False
        for poly in j.data.polygons:
            poly.use_smooth = False
        if x0 == 0.6:
            porta.append(j)
    for x in (-1.65, -0.6, 0.6, 1.65):
        caixa(f"montante{x}", (X0 + x, 0.0, 1.19), (0.045, 0.06, 2.38), alu, bev=0.005)
    for z in (0.03, 2.36):
        caixa(f"travessa{z}", (X0, 0.0, z), (3.35, 0.06, 0.05), alu, bev=0.005)
    porta.append(caixa("puxador_porta", (X0 + 1.45, -0.04, 1.05), (0.02, 0.03, 0.5), alu, bev=0.006))
    dobradica = vazio("porta_dobradica", (X0 + 1.625, 0.0, 0.0))  # rotation z > 0 swings it out into the corridor
    for o in porta:
        pai(o, dobradica)
    # corridor wall continuing the glass front on both sides, so wide shots don't look into the void
    for s in (-1, 1):
        caixa(f"corredor{s}", (X0 + s * 3.2, 0.05, 1.4), (2.9, 0.1, 2.8), parede, bev=0)

    # venetian blind inside the centre pane, slats tilted shut; scenes hide the slats below the bottom rail
    persiana = clay("persiana_sala", "#D5D9DC", rough=0.6, boneco=False, bump=0.3)
    caixa("persiana_cabeca", (X0, 0.07, TOPO_PERSIANA + 0.02), (1.16, 0.06, 0.04), persiana, bev=0.008)
    n = int((TOPO_PERSIANA - BASE_PERSIANA) / PASSO_LAMINA)
    laminas = [caixa(f"lamina_sala{i}", (X0, 0.07, TOPO_PERSIANA - (i + 0.5) * PASSO_LAMINA), (1.12, 0.05, 0.003), persiana,
                     bev=0.001, rot=(1.25, 0, 0)) for i in range(n)]
    trilho = caixa("persiana_trilho", (X0, 0.07, TOPO_PERSIANA), (1.14, 0.03, 0.02), persiana, bev=0.006)
    cordao = vazio("cordao_sala", (X_CORDAO, 0.11, TOPO_PERSIANA))
    bastao("cordao_fio", (X_CORDAO, 0.11, TOPO_PERSIANA), (X_CORDAO, 0.11, TOPO_PERSIANA - 1), 0.005,
           simples("cordao_sala", "#E2E2DC", 0.8), cordao)
    cordao.scale.z = 0.45

    # wall clock on the bulkhead, facing the corridor (Beto watches it while Ana thinks); hands turn about y
    preto = clay("relogio_sala_aro", "#2B2B2E", boneco=False)
    tinta = simples("tinta_relogio", "#1B1B1F", 0.5)
    cilindro("relogio_sala_aro", (X0, -0.08, 2.58), 0.16, 0.04, preto, rot=(math.pi / 2, 0, 0))
    cilindro("relogio_sala", (X0, -0.1, 2.58), 0.14, 0.01, simples("relogio_sala", "#FAFAF7", 0.3), rot=(math.pi / 2, 0, 0))
    for i in range(12):
        a = i / 12 * math.tau
        caixa(f"marca_sala{i}", (X0 + 0.12 * math.sin(a), -0.106, 2.58 + 0.12 * math.cos(a)), (0.007, 0.004, 0.02), tinta, bev=0, rot=(0, a, 0))
    minuto = vazio("ponteiro_sala_min", (X0, -0.11, 2.58))
    caixa("pmin_sala", (X0, -0.11, 2.58 + 0.05), (0.01, 0.004, 0.1), tinta, minuto, bev=0.002)
    hora = vazio("ponteiro_sala_hora", (X0, -0.112, 2.58))
    caixa("phora_sala", (X0, -0.112, 2.58 + 0.032), (0.012, 0.004, 0.064), tinta, hora, bev=0.002)

    # whiteboard (scene 3 fills it), small table with a chair
    caixa("quadro_sala_moldura", (X0, 2.58, 1.5), (1.95, 0.04, 1.1), alu, bev=0.012)
    caixa("quadro_sala", (X0, 2.56, 1.5), (1.87, 0.025, 1.02), simples("quadro_sala", "#FBFBF9", 0.15), bev=0.006)
    caixa("bandeja_sala", (X0, 2.53, 0.96), (1.2, 0.08, 0.025), alu, bev=0.006)
    for i, cor in enumerate(("#B42318", "#1F4E8C", "#1B1B1F")):
        bastao(f"pincel_sala{i}", (X0 - 0.3 + i * 0.14, 2.51, 0.985), (X0 - 0.2 + i * 0.14, 2.51, 0.985), 0.014,
               clay(f"pincel_sala{i}", cor, boneco=False))
    mesa = clay("mesa_sala", "#C79A6B", rough=0.6, sulcos="madeira", cor2="#B98B5E", boneco=False, bump=0.3)
    cilindro("mesa_sala_tampo", (X0 - 1.0, 1.55, 0.74), 0.45, 0.04, mesa, bev=0.01)
    cilindro("mesa_sala_pe", (X0 - 1.0, 1.55, 0.37), 0.05, 0.72, simples("pe_mesa", "#2B2B2E", 0.4, metal=0.6))
    caixa("cadeira_sala", (X0 - 1.25, 2.05, 0.95), (0.5, 0.1, 0.62), clay("cadeira_sala", "#3A3F47", rough=0.8, boneco=False, bump=0.8),
          bev=0.05, rot=(0, 0, 0.4))

    lz = luz("key_sala", (X0 - 1.8, -2.3, 2.9), (X0, 0.5, 1.3), 600, 0.6, (1.0, 0.86, 0.72))
    bpy.data.objects["key_sala"].visible_glossy = False  # its hard square read badly reflected in the glass
    luz("fill_sala", (X0 + 2.6, -1.9, 1.6), (X0, 0.5, 1.2), 90, 3.0, (0.82, 0.9, 1.0))
    teto = luz("teto_sala", (X0, 1.3, 2.7), (X0, 1.3, 0), 220, 1.2, (1.0, 0.97, 0.92))
    teto.shape, teto.size_y = "RECTANGLE", 0.5
    return {"key": lz, "laminas": laminas, "trilho": trilho, "cordao": cordao, "minuto": minuto, "hora": hora,
            "porta": dobradica}


def baixar(sala, z):
    """Lowers the blind so its bottom rail sits at height z (slats below it are hidden)."""
    for i, lam in enumerate(sala["laminas"]):
        lam.hide_render = TOPO_PERSIANA - (i + 1) * PASSO_LAMINA < z - 0.01
    sala["trilho"].location.z = z - 0.012

