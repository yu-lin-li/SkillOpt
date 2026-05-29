#!/usr/bin/env bash
# Run a tiny real SearchQA training smoke test.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${PROJECT_ROOT}"

SMOKE_MODEL="${SMOKE_MODEL:-gpt-5.5}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUT_ROOT="${OUT_ROOT:-${PROJECT_ROOT}/outputs/searchqa_smoke_${TIMESTAMP}}"

OPTIMIZER_MODEL="${SMOKE_MODEL}" \
TARGET_MODEL="${SMOKE_MODEL}" \
bash scripts/run_searchqa.sh \
    --num_epochs 1 \
    --train_size 1 \
    --batch_size 1 \
    --accumulation 1 \
    --minibatch_size 1 \
    --merge_batch_size 1 \
    --analyst_workers 1 \
    --max_analyst_rounds 1 \
    --sel_env_num 1 \
    --test_env_num 1 \
    --limit 1 \
    --eval_test true \
    --use_slow_update false \
    --use_meta_skill false \
    --lr_scheduler constant \
    --out_root "${OUT_ROOT}" \
    "$@"

echo ""
echo "Smoke test output: ${OUT_ROOT}"
