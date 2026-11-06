#!/usr/bin/env bash
# Replacement-face set for one puppet: AI edits of saida/rostos/<nome>/neutro.png (render it with rostos.py first).
# Usage: blender/expressoes.sh <nome>   (run from stop_motion/)
set -euo pipefail
D=saida/rostos/$1
python3 -I -c "
from PIL import Image
im=Image.open('$D/neutro.png').convert('RGBA'); bg=Image.new('RGBA',im.size,(128,128,128,255)); bg.alpha_composite(im); bg.convert('RGB').save('$D/neutro_rgb.png')"
P="Edit this image of a stop-motion puppet face. Keep everything else identical: exact same framing, size and position of every feature, same face, hair, glasses, colours, flat even lighting, same grey background. Do not move the head, do not add shading. Only change: "
while IFS='|' read -r n t; do
  [ -f "$D/$n.png" ] && continue
  ASPECTO=auto TETO_USD=${TETO_USD:-13} python3 gerar.py imagem "$D/$n.png" "$P$t" "$D/neutro_rgb.png"
done <<'LISTA'
olhos_fechados|the eyelids are gently closed, a blink: skin-coloured upper lids cover the eyes completely, the lash line curves down. The mouth stays exactly as it is.
olhos_meio|the eyes are half closed mid-blink: the upper lids come down to cover the top half of each iris. The mouth stays exactly as it is.
boca_a|the puppet is talking, mouth open saying 'ah': lips parted about one centimetre at puppet scale, upper teeth visible, dark mouth interior with a hint of tongue. Eyes stay exactly as they are.
boca_o|the puppet is talking, mouth in a rounded 'oh' shape: lips rounded and slightly pushed forward around a small dark oval opening. Eyes stay exactly as they are.
boca_e|the puppet is talking, mouth open saying 'eh': lips parted wide and relaxed, upper and lower teeth visible, dark interior. Eyes stay exactly as they are.
LISTA
