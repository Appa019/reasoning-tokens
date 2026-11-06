# reasoning-tokens

Código do vídeo de massinha sobre modelos de reasoning: a mesma pergunta com mais ou menos esforço de raciocínio, e o
que isso custa.

`compare.py` faz duas perguntas em vários níveis de `reasoning.effort` e confere cada resposta em código:

- `easy`: "What's 2 plus 3?". Qualquer esforço acerta; o que muda é quanto tempo e quantos tokens ele gasta.
- `hard`: fechar o orçamento de 2027 com 14 restrições (`reasoning/budget.py`). Só uma divisão satisfaz todas, e ela
  soma US$ 3,84 milhões, o valor do post-it da Ana. A resposta do modelo passa pelas 14 regras; ninguém confia na
  palavra dele.

Para cada esforço a tabela mostra acertos, tokens de raciocínio, tokens de saída e segundos. Os tokens de raciocínio
são cobrados como saída e você não vê o texto deles, só a contagem. Com `--summary` aparece o resumo que a API devolve,
que é um resumo escrito para você, não o raciocínio.

## Estrutura

```
compare.py             roda as perguntas e imprime a tabela
reasoning/budget.py    as 14 restrições, o schema da resposta e a checagem
reasoning/cli.py       argumentos e erros da API em uma linha
reasoning/config.py    .env e modelo
tests/                 provam que o orçamento tem solução única, sem chamar a API
stop_motion/           o filme: cenas em Blender por script e a montagem
```

## Rodar

```
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # coloque sua OPENAI_API_KEY
python compare.py easy
python compare.py hard --effort none,low,high --runs 3 --summary
python -m unittest        # sem API
```

O modelo padrão é `gpt-6-luna`; troque com `OPENAI_MODEL` no `.env`. Nem todo modelo aceita todos os esforços
(`none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`). A pergunta difícil em esforço alto é a parte cara.

## O filme (stop_motion/)

Stop motion de massinha feito no Blender 4.2 por script, sem animar à mão. Cada `blender/cenaN.py` monta o cenário,
posa os bonecos quadro a quadro a 12 fps e renderiza no Cycles. `montar.py` junta as sete cenas com vinheta, grão,
legenda e áudio.

- Bonecos: conceito em imagem gerada por IA, malha 3D por image-to-3D (`gerar.py`, fal.ai), rig automático e rostos
  trocáveis de stop motion (`rostos.py`, `expressoes.sh`, `mascaras.py`).
- Cara de massinha: material com subsurface, digitais e dedadas, textura que "ferve" a cada quadro, tremor de posição
  e de luz, profundidade de campo curta.
- `elenco.py`: IK de dois ossos, ciclo de passos, troca de boca e piscada, gravação de um quadro por pose.
- Vozes: `vozes.py` gera cada fala no [Kokoro-82M](https://github.com/thewh1teagle/kokoro-onnx), local e gratuito, e
  acelera só o necessário para caber antes da próxima fala. Ruído de sala, cliques, trinco e papel são ruído filtrado
  no próprio ffmpeg.

```
cd stop_motion/blender
blender -b -P cena1.py -- still 30    # um quadro de teste
blender -b -P cena1.py -- anim        # a cena inteira em ../saida/cena1/
cd ..
python vozes.py                       # Python com kokoro-onnx e os arquivos do modelo em ~/.local/opt/kokoro
python3 montar.py                     # saida/curta.mp4
```

Os bonecos (`saida/conceito/*.glb`) e os rostos (`saida/rostos/`) estão na release do repositório; extraia em
`stop_motion/saida/`. As fontes usadas são Archivo, Caveat e Inter.
