# Scene 1 of video 02 (dialogue in English): the manager asks "What's two plus three?", Beto shoots his hand up with
# "Five!", Ana raises a hand: "Just a minute." AI-sculpted puppets (boneco3d.py) in the clay office set (escritorio.py).
# ~/.local/opt/blender-4.2.23-linux-x64/blender -b -P cena1.py -- still N | anim | poses
# Output: ../saida/cena1/ (f_0001.png ... f_0072.png at 12 fps)
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import boneco3d as A  # noqa: E402
import escritorio  # noqa: E402
import massinha as M  # noqa: E402
from elenco import em_repouso, girar, gravar, mira, misturar, osso, renderizar, rosto, sentar  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAIDA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "saida", "cena1"))
N_QUADROS = 72

KEY = escritorio.montar()
ana, beto, ger = (A.montar_boneco(n) for n in ("ana_a", "beto", "gerente"))

sentar(ana, -0.6, 0.42)
sentar(beto, 0.2, 0.42)
REP = {"ana": em_repouso(ana), "beto": em_repouso(beto)}
# Ana's "one minute" hand and Beto's hand shot straight up
mira(ana, "braco.R", (-0.2, -0.4, -1))
ANA_MAO = {"braco.R": osso(ana, "braco.R").rotation_quaternion.copy(),
           "antebraco.R": mira(ana, "antebraco.R", (-0.1, -0.5, 1)), "mao.R": mira(ana, "mao.R", (0, -0.15, 1), 90)}
BETO_MAO = {"braco.L": mira(beto, "braco.L", (0.15, -0.1, 1)), "antebraco.L": mira(beto, "antebraco.L", (0.05, -0.05, 1)),
            "mao.L": mira(beto, "mao.L", (0, 0, 1), -90)}
# manager: standing at the right of the desk, turned towards the two, explaining with his right hand
ger["rig"].location = (0.95, -0.45, 0)
ger["rig"].rotation_euler.z = math.radians(-60)
bpy.context.view_layer.update()
GER_REP = {f"braco.{l}": mira(ger, f"braco.{l}", (s * 0.1, 0.02, -1)) for l, s in (("L", 1), ("R", -1))}
GER_MAO = {"braco.R": mira(ger, "braco.R", (-0.45, -0.5, -1)), "antebraco.R": mira(ger, "antebraco.R", (-0.2, -1, 0.6)),
           "mao.R": mira(ger, "mao.R", (0.3, -1, 0.2), 0)}

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
M.sc.collection.objects.link(cam)
M.sc.camera = cam
cam.location = (0.15, -3.3, 1.5)
M.mirar(cam, (0.15, 0.3, 1.3))
cam.data.lens = 42
cam.data.dof.use_dof, cam.data.dof.focus_distance, cam.data.dof.aperture_fstop = True, 3.85, 1.4

# ------------------------------------------------------------------ animation (12 fps, every frame hand-posed)
FALA = {"ger": (5, "oaaxooxeexiiiex"),      # "What's two plus three?"
        "beto": (27, "aaaiixx"),            # "Five!"
        "ana": (41, "eaaxaxxiieex")}        # "Just a minute."
PISCA = {"ger": (14, 60), "beto": (20, 58), "ana": (31, 66)}
ELENCO = {"ana": ana, "beto": beto, "ger": ger}


def pose(f):
    for k, c in ELENCO.items():
        rosto(c, f, FALA[k], PISCA[k])
    # manager: talks with small nods and a hand gesture, then turns his head to Ana
    falando = 5 <= f < 23
    k = {7: 0.4, 8: 0.8}.get(f, 1.0 if 8 < f < 20 else ({20: 0.6, 21: 0.3}.get(f, 0.0)))
    misturar(ger, GER_REP, GER_MAO, k)
    girar(ger, "cabeca", (0.05 if falando and f % 4 < 2 else -0.01, 0, 0.25 if f >= 56 else 0.0))
    # Beto: snaps his arm up with "Cinco!", holds it, smug, puts it down
    b = 1.0 if 26 <= f < 50 else 0.0
    b = {25: 0.5, 50: 0.5}.get(f, b)
    misturar(beto, REP["beto"], BETO_MAO, b)
    girar(beto, "cabeca", (-0.08 if 26 <= f < 34 else 0.0, 0.0, 0.3 if f >= 56 else -0.2))
    # Ana: lifts her hand, looks up while she "thinks", says "Só um minuto."
    a = {36: 0.35, 37: 0.7}.get(f, 1.0 if f >= 38 else 0.0)
    misturar(ana, REP["ana"], ANA_MAO, a)
    pensando = f >= 39
    girar(ana, "cabeca", (0.06 if pensando else 0.0, 0.0, 0.1 if pensando else -0.25))
    for c in ELENCO.values():
        girar(c, "peito", (0.012 * math.sin(f / 4 + len(c["obj"].name)), 0.0, 0.0))  # breathing


gravar(list(ELENCO.values()), N_QUADROS, pose, {KEY: 650})
renderizar(ARGS, SAIDA)
