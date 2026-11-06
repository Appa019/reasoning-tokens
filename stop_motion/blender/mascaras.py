"""Replacement-face decals: each AI-edited face keeps only the pixels that changed versus the neutral face
(eyes for blinks, mouth for mouth shapes), feathered, as the PNG alpha (troca_<expr>.png).
Usage: python3 -I mascaras.py <rostos/nome dir>"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

d = Path(sys.argv[1])
neutro = Image.open(d / "neutro_rgb.png").convert("RGB")


def mudou(nome):
    diff = ImageChops.difference(Image.open(d / f"{nome}.png").convert("RGB").resize(neutro.size), neutro)
    diff = diff.convert("L").filter(ImageFilter.GaussianBlur(4))
    return diff.point(lambda v: 255 if v > 30 else 0)


# rows of the closed-eye change split the face: eye edits stay above, mouth edits below
olhos = mudou("olhos_fechados")
caixa = olhos.crop((0, 0, olhos.width, olhos.height * 2 // 3)).getbbox()
corte = caixa[3] + 20 if caixa else olhos.height // 2
print("eye zone bottom row", corte)
# one mask per zone, the union of everything that changes there, so the edit also replaces the neutral
# feature it covers (e.g. the corners of a smile around an "oh" mouth)
grupos = {}
for f in sorted(d.glob("*.png")):
    if f.stem.startswith(("olhos_", "boca_")):
        grupos.setdefault(f.stem.split("_")[0], []).append(f)
for zona_nome, arquivos in grupos.items():
    zona = Image.new("L", neutro.size, 0)
    zona.paste(255, (0, 0, zona.width, corte) if zona_nome == "olhos" else (0, corte, zona.width, zona.height))
    uniao = Image.new("L", neutro.size, 0)
    for f in arquivos:
        uniao = ImageChops.lighter(uniao, ImageChops.multiply(mudou(f.stem), zona))
    m = uniao.filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.GaussianBlur(16))
    print(zona_nome, m.getbbox())
    for f in arquivos:
        im = Image.open(f).convert("RGB").resize(neutro.size)
        im.putalpha(m)
        im.save(d / f"troca_{f.stem}.png")
