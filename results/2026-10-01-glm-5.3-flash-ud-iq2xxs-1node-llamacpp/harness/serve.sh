#!/usr/bin/env bash
# Weights: hf download unsloth/GLM-5.3-Flash-GGUF --include "UD-IQ2_XXS/*" --local-dir ~/glm53-gguf
# Image:   docker build -t glm53-llamacpp:unsloth-pr27754 -f Dockerfile .
docker run -d --name glm53-llama --restart unless-stopped --gpus all --network host --ipc host \
  -v $HOME/glm53-gguf:/models:ro glm53-llamacpp:unsloth-pr27754 \
  -m /models/UD-IQ2_XXS/GLM-5.3-Flash-UD-IQ2_XXS-00001-of-00004.gguf \
  --alias glm-5.3-flash --host 0.0.0.0 --port 8888 \
  -ngl 999 -c 262144 -np 1 -fa on -ctk q8_0 -ctv q8_0 -b 2048 -ub 1024 --jinja
