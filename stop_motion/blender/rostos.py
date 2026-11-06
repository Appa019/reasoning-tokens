# Flat albedo render of a puppet's face through an orthographic "projector" camera. AI edits of this image become
# replacement faces (blink, mouth shapes) projected back onto the head.
# ~/.local/opt/blender-4.2.23-linux-x64/blender -b -P rostos.py -- <nome> [altura]   (reads saida/conceito/<nome>.glb)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import boneco3d as A  # noqa: E402
import massinha as M  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
NOME = ARGS[0] if ARGS else "ana_a"
ALTURA = float(ARGS[1]) if len(ARGS) > 1 else 1.9
SAIDA = os.path.normpath(os.path.join(AQUI, "..", "saida", "rostos", NOME))

o = A.importar(os.path.normpath(os.path.join(AQUI, "..", "saida", "conceito", f"{NOME}.glb")), ALTURA)
for m in o.data.materials:  # unlit: output the painted texture colour as is
    nt = m.node_tree
    img = next(n for n in nt.nodes if n.type == "TEX_IMAGE")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(img.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
M.sc.camera = A.projetor(o) if NOME != "ana_a" else A.projetor(o, 1.62, 0.42)
r = M.configurar_render(16, 1024, 1024)
M.sc.cycles.use_denoising = False
M.sc.view_settings.view_transform, M.sc.view_settings.look, M.sc.view_settings.exposure = "Standard", "None", 0.0
w = bpy.data.worlds.new("cinza")  # flat mid-grey behind the head, the background the AI edits expect
M.sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.2158, 0.2158, 0.2158, 1)
os.makedirs(SAIDA, exist_ok=True)
r.filepath = os.path.join(SAIDA, "neutro.png")
bpy.ops.render.render(write_still=True)
print("OK", r.filepath)
