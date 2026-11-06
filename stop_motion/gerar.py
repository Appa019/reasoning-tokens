"""Image and video generation for the LinkedIn videos through fal.ai, with a hard spending cap.

Usage:
  python3 gerar.py imagem <out.png> "<prompt>" [ref.png ...]      # Nano Banana 2 (edit mode when refs are given)
  python3 gerar.py video  <out.mp4> <segundos> <start.png> "<prompt>" [mudo]   # Kling v3 image-to-video
  python3 gerar.py modelo3d <out.glb> <frente.png>                # Hunyuan3D v3 image-to-3D, textured ("Normal")
  python3 gerar.py gasto

Each call's cost (fal list price x units) is appended to custos.jsonl next to this file.
A call is refused if the spent total plus its cost would pass TETO_USD.
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TETO_USD = float(os.environ.get("TETO_USD", "10"))
LEDGER = AQUI / "custos.jsonl"

IMAGEM, IMAGEM_EDIT = "fal-ai/nano-banana-2", "fal-ai/nano-banana-2/edit"
VIDEO = "fal-ai/kling-video/v3/pro/image-to-video"
MODELO3D = "fal-ai/hunyuan3d-v3/image-to-3d"
# fal bills this endpoint in $0.015 units; a textured "Normal" generation is $0.375 (model page, 2026-11-06).
PRECO_MODELO3D = 0.375
# fal's usage API billed native audio as 1.2x the listed per-second price (checked 2026-11-05).
FATOR_AUDIO = 1.2


def chave():
    for linha in (AQUI / ".env").read_text().splitlines():
        if linha.startswith("FAL_KEY="):
            return linha.split("=", 1)[1].strip()
    sys.exit("FAL_KEY missing in .env")


def http(url, corpo=None, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode() if corpo is not None else None,
                                 headers={"Authorization": f"Key {chave()}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:800]}")


def preco(endpoint):
    r = http(f"https://api.fal.ai/v1/models/pricing?endpoint_id={endpoint}")
    return r["prices"][0]["unit_price"]


def gasto_total():
    if not LEDGER.exists():
        return 0.0
    return sum(json.loads(l)["usd"] for l in LEDGER.read_text().splitlines() if l.strip())


def checar_teto(usd):
    total = gasto_total()
    if total + usd > TETO_USD:
        sys.exit(f"cap reached: spent ${total:.2f}, this call costs ${usd:.2f}, cap ${TETO_USD:.2f}")


def registrar(endpoint, out, usd, entrada):
    with LEDGER.open("a") as f:
        f.write(json.dumps({"quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "modelo": endpoint, "saida": str(out),
                            "usd": round(usd, 4), "entrada": entrada}) + "\n")
    print(f"${usd:.2f} · total ${gasto_total():.2f} of ${TETO_USD:.2f}")


def data_uri(p):
    mime = "image/png" if str(p).lower().endswith(".png") else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(Path(p).read_bytes()).decode()}"


def rodar(endpoint, entrada):
    """Submit to fal's queue and wait for the result."""
    fila = http(f"https://queue.fal.run/{endpoint}", entrada)
    print("request", fila.get("request_id"), flush=True)  # lets a stuck job be checked or fetched later
    while True:
        st = http(fila["status_url"])
        if st.get("status") == "COMPLETED":
            return http(fila["response_url"], timeout=300)
        if st.get("status") not in ("IN_QUEUE", "IN_PROGRESS"):
            sys.exit(f"fal failed: {json.dumps(st)[:800]}")
        time.sleep(4)


def baixar(url, out):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r:
        Path(out).write_bytes(r.read())
    print(out)


def imagem(out, prompt, refs):
    endpoint = IMAGEM_EDIT if refs else IMAGEM
    usd = preco(endpoint)
    checar_teto(usd)
    aspecto = os.environ.get("ASPECTO", "9:16")  # "auto" keeps the reference framing (face replacement edits)
    entrada = {"prompt": prompt, "aspect_ratio": aspecto, "resolution": "1K", "num_images": 1, "output_format": "png"}
    if refs:
        entrada["image_urls"] = [data_uri(r) for r in refs]
    r = rodar(endpoint, entrada)
    registrar(endpoint, out, usd, {"prompt": prompt, "refs": refs})
    baixar(r["images"][0]["url"], out)


def video(out, segundos, inicio, prompt, audio=True):
    usd = preco(VIDEO) * int(segundos) * (FATOR_AUDIO if audio else 1)
    checar_teto(usd)
    entrada = {"prompt": prompt, "start_image_url": data_uri(inicio), "duration": str(segundos),
               "generate_audio": audio, "negative_prompt": "music, subtitles, captions, on-screen text, beauty filter"}
    r = rodar(VIDEO, entrada)
    registrar(VIDEO, out, usd, {"prompt": prompt, "inicio": inicio, "segundos": segundos})
    baixar(r["video"]["url"], out)


def modelo3d(out, frente):
    checar_teto(PRECO_MODELO3D)
    r = rodar(MODELO3D, {"input_image_url": data_uri(frente), "generate_type": "Normal", "enable_pbr": False})
    registrar(MODELO3D, out, PRECO_MODELO3D, {"frente": frente})
    baixar(r["model_glb"]["url"], out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["gasto"]:
        print(f"spent ${gasto_total():.2f} of ${TETO_USD:.2f}")
    elif a[:1] == ["imagem"] and len(a) >= 3:
        imagem(a[1], a[2], a[3:])
    elif a[:1] == ["video"] and len(a) in (5, 6):
        video(a[1], a[2], a[3], a[4], audio=a[5:] != ["mudo"])
    elif a[:1] == ["modelo3d"] and len(a) == 3:
        modelo3d(a[1], a[2])
    else:
        sys.exit(__doc__)
