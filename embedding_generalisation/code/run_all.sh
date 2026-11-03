#!/bin/bash
# embeds with every model, one after the other (CPU); skips models that are already done
cd "$(dirname "$0")"
for m in codebert graphcodebert unixcoder codet5 roberta qwen_coder; do
  [ -f ../embeddings/$m.npz ] || /home/souhardya/miniforge3/bin/python e1_embed.py $m > ../embeddings/$m.log 2>&1
done
echo ALLDONE > ../embeddings/ALLDONE
