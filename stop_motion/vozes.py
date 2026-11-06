"""Voices of video 02 with Kokoro-82M (local, Apache 2.0): one wav per line in saida/vozes/, sped up only as much as
the gap before the next line requires.

Run with the Python that has kokoro-onnx (model files next to it):
  ~/.local/opt/kokoro/.venv/bin/python vozes.py
"""

import os
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro

from montar import FALAS, S, voz_wav

KOKORO = Path(os.environ.get("KOKORO_DIR", Path.home() / ".local/opt/kokoro"))
VOZES = {"ger": "am_michael", "beto": "am_puck", "ana": "af_heart", "carla": "bf_emma"}
VELOCIDADE_MAX = 1.45  # faster than this stops sounding like a person


def main():
    k = Kokoro(str(KOKORO / "kokoro-v1.0.onnx"), str(KOKORO / "voices-v1.0.bin"))
    (S / "vozes").mkdir(exist_ok=True)
    for cena, quadro, quem, texto, maximo in FALAS:
        lang = "en-gb" if VOZES[quem].startswith("b") else "en-us"
        amostras, sr = k.create(texto, voice=VOZES[quem], lang=lang)
        velocidade = min(VELOCIDADE_MAX, max(1.0, len(amostras) / sr / maximo))
        if velocidade > 1.0:
            amostras, sr = k.create(texto, voice=VOZES[quem], lang=lang, speed=velocidade)
        sf.write(voz_wav(cena, quadro), amostras * (0.9 / abs(amostras).max()), sr)  # same peak for every line
        print(f"cena {cena} f{quadro} {quem:<5} {len(amostras) / sr:4.2f}s (max {maximo}s, x{velocidade:.2f})  {texto}")


if __name__ == "__main__":
    main()
