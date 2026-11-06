"""Cut of video 02: turns each scene's 12 fps frames (blender/cenaN.py -- anim) into 24 fps with vignette and film
grain, burns the English subtitles, joins the seven scenes and lays the voices (vozes.py) over room tone and a few
synthesized sounds.

Run: python3 montar.py  ->  saida/curta.mp4 (crf 18) and saida/curta_leve.mp4 (small copy to share)
"""

import subprocess
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
S = AQUI / "saida"
FONTE = Path.home() / ".fonts" / "Inter-SemiBold.ttf"
CENAS = 7
FPS = 12

# (scene, first mouth frame, character, spoken text, seconds until the next line or the scene's end)
FALAS = [
    (1, 5, "ger", "What's two plus three?", 1.7),
    (1, 27, "beto", "Five.", 1.1),
    (1, 41, "ana", "Just a minute.", 2.4),
    (5, 25, "ger", "Close the twenty twenty-seven budget with these fourteen constraints.", 3.1),
    (5, 63, "beto", "Three million.", 1.3),
    (5, 80, "carla", "It doesn't balance.", 1.3),
    (6, 112, "carla", "It balances.", 1.6),
]
# (scene, frame, sound): dial clicks, door latch, the invoice unrolling to the floor
EFEITOS = [(5, f, "clique") for f in (6, 8, 10, 12, 14, 16)] + [
    (4, 3, "trinco"), (6, 26, "trinco"), (6, 41, "trinco"), (6, 48, "trinco"), (7, 33, "papel")]
SONS = {  # lavfi sources: short filtered noise is enough for clicks, a latch and paper
    "clique": "anoisesrc=color=white:a=0.12:d=0.035,highpass=f=2500,afade=t=out:d=0.035",
    "trinco": "anoisesrc=color=pink:a=0.35:d=0.09,bandpass=f=900:t=h:w=600,afade=t=out:d=0.09",
    "papel": "anoisesrc=color=pink:a=0.6:d=3.2,bandpass=f=3500:t=h:w=3000,tremolo=f=11:d=0.7,"
             "afade=t=in:d=0.15,afade=t=out:st=1.6:d=1.6",
}

# scene -> [(t0, t1, text)] in seconds from the scene's first frame (frame f starts at (f - 1) / 12)
LEGENDAS = {
    1: [(0.3, 2.1, "What's 2 plus 3?"), (2.2, 3.3, "5."), (3.4, 6.0, "Just a minute.")],
    5: [(2.2, 5.0, "Close the 2027 budget with these 14 constraints."), (5.2, 6.3, "Three million."),
        (6.6, 8.0, "It doesn't balance.")],
    6: [(9.2, 10.6, "It balances.")],
}


def voz_wav(cena, quadro):
    return S / "vozes" / f"c{cena}_f{quadro:03d}.wav"


def inicio_cenas():
    """Start time (s) of each scene in the joined cut, from its frame count."""
    t, inicio = 0.0, {}
    for n in range(1, CENAS + 1):
        inicio[n] = t
        t += len(list((S / f"cena{n}").glob("f_*.png"))) / FPS
    return inicio, t


def trilha(destino):
    """Voices + room tone + effects, each placed at (scene start + (frame - 1) / 12)."""
    inicio, total = inicio_cenas()
    faltam = [str(voz_wav(c, q)) for c, q, *_ in FALAS if not voz_wav(c, q).exists()]
    if faltam:
        raise SystemExit("missing voices, run vozes.py first:\n" + "\n".join(faltam))
    entradas, cadeias, rotulos = [], [], []

    def por(entrada, cena, quadro, efeito):
        i = len(rotulos)
        entradas.extend(entrada)
        ms = round((inicio[cena] + (quadro - 1) / FPS) * 1000)
        cadeias.append(f"[{i}:a]aresample=48000,{efeito}adelay={ms}:all=1[s{i}]")
        rotulos.append(f"[s{i}]")

    for c, q, *_ in FALAS:
        por(["-i", str(voz_wav(c, q))], c, q, "highpass=f=90,aecho=0.8:0.5:35:0.12,")
    for c, q, som in EFEITOS:
        por(["-f", "lavfi", "-i", SONS[som]], c, q, "")
    entradas += ["-f", "lavfi", "-i", f"anoisesrc=color=brown:a=0.02:d={total:.2f},lowpass=f=500"]
    rotulos.append(f"[{len(rotulos)}:a]")
    mistura = ";".join(cadeias) + ";" + "".join(rotulos) + \
        f"amix=inputs={len(rotulos)}:normalize=0:duration=longest,atrim=0:{total:.3f},volume=6dB,alimiter=limit=0.85[a]"
    ffmpeg(*entradas, "-filter_complex", mistura, "-map", "[a]", "-ar", "48000", "-ac", "2", str(destino))


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
        audio = Path(tmp) / "trilha.wav"
        trilha(audio)
        entradas = [a for c in clipes for a in ("-i", str(c))] + ["-i", str(audio)]
        ffmpeg(*entradas, "-filter_complex", f"concat=n={len(clipes)}:v=1[v]", "-map", "[v]", "-map",
               f"{len(clipes)}:a", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac",
               "-b:a", "192k", "-shortest", str(S / "curta.mp4"))
    ffmpeg("-i", str(S / "curta.mp4"), "-c:v", "libx264", "-crf", "25", "-preset", "slow", "-pix_fmt", "yuv420p",
           "-c:a", "copy", str(S / "curta_leve.mp4"))
    print(S / "curta.mp4")


if __name__ == "__main__":
    main()
