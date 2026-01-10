#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

uv run api_server.py \
    --port "${API_PORT:-8000}" \
    --host "${API_HOST:-0.0.0.0}" \
    --model-path "${MODEL_PATH:-./models/Qwen3-VL-Embedding-2B}"
