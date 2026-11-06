"""Cut of video 02: turns each scene's 12 fps frames (blender/cenaN.py -- anim) into 24 fps with vignette and film
grain, burns the English subtitles and joins the seven scenes.

Run: python3 montar.py  ->  saida/curta.mp4 (crf 18) and saida/curta_leve.mp4 (small copy to share)
"""

import subprocess
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
S = AQUI / "saida"
FONTE = Path.home() / ".fonts" / "Inter-SemiBold.ttf"
CENAS = 7

# scene -> [(t0, t1, text)] in seconds from the scene's first frame (frame f starts at (f - 1) / 12)
LEGENDAS = {
    1: [(0.3, 2.1, "What's 2 plus 3?"), (2.2, 3.3, "5."), (3.4, 6.0, "Just a minute.")],
    5: [(2.2, 5.0, "Close the 2027 budget with these 14 constraints."), (5.2, 6.3, "Three million."),
        (6.6, 8.0, "It doesn't balance.")],
    6: [(9.2, 10.6, "It balances.")],
}


def filtro(cena, tmp):
    """vignette + grain, then one drawtext per subtitle (textfile: apostrophes break inline text=)."""
    partes = ["vignette=PI/5", "noise=alls=7:allf=t"]
    estilo = f"fontfile={FONTE}:fontsize=40:fontcolor=white:borderw=3:bordercolor=black@0.85:x=(w-tw)/2:y=h-170"
    for i, (t0, t1, texto) in enumerate(LEGENDAS.get(cena, [])):
        arq = Path(tmp) / f"c{cena}_{i}.txt"
        arq.write_text(texto)
        partes.append(f"drawtext={estilo}:textfile={arq}:enable='between(t,{t0},{t1})'")
    return ",".join(partes)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def main():
    faltam = [n for n in range(1, CENAS + 1) if not (S / f"cena{n}" / "f_0001.png").exists()]
    if faltam:
        raise SystemExit(f"no frames for scene(s) {faltam}: run blender/cenaN.py -- anim first")
    with tempfile.TemporaryDirectory() as tmp:
        clipes = []
        for n in range(1, CENAS + 1):
            saida = Path(tmp) / f"cena{n}.mp4"
            ffmpeg("-framerate", "12", "-i", str(S / f"cena{n}" / "f_%04d.png"), "-vf", filtro(n, tmp),
                   "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "24", str(saida))
            clipes.append(saida)
        entradas = [a for c in clipes for a in ("-i", str(c))]
        ffmpeg(*entradas, "-filter_complex", f"concat=n={len(clipes)}:v=1[v]", "-map", "[v]",
               "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(S / "curta.mp4"))
    ffmpeg("-i", str(S / "curta.mp4"), "-c:v", "libx264", "-crf", "25", "-preset", "slow", "-pix_fmt", "yuv420p",
           str(S / "curta_leve.mp4"))
    print(S / "curta.mp4")


if __name__ == "__main__":
    main()
