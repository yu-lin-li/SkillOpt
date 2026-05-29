#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# SkillOpt — SearchQA training launch script
#
# Usage:
#   bash scripts/run_searchqa.sh
#   bash scripts/run_searchqa.sh --num_epochs 2 --edit_budget 6
#   bash scripts/run_searchqa.sh --split_dir /path/to/searchqa_split
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

OPTIMIZER_MODEL="${OPTIMIZER_MODEL:-gpt-5.5}"
TARGET_MODEL="${TARGET_MODEL:-gpt-5.5}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEFAULT_OUT_ROOT="${PROJECT_ROOT}/outputs/skillopt_searchqa_${TARGET_MODEL}_${TIMESTAMP}"

cd "${PROJECT_ROOT}"

if [[ -f ".env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source ".env"
    set +a
fi

# Check the key without passing it on the CLI, so output configs do not record it.
: "${AZURE_OPENAI_API_KEY:?AZURE_OPENAI_API_KEY is not set}"

echo "============================================================"
echo "  SkillOpt — SearchQA Training"
echo "============================================================"
echo "  Optimizer:  ${OPTIMIZER_MODEL}"
echo "  Target:     ${TARGET_MODEL}"
echo "============================================================"

uv run python scripts/train.py \
    --config configs/searchqa/default.yaml \
    --azure_openai_endpoint "${AZURE_OPENAI_ENDPOINT:?AZURE_OPENAI_ENDPOINT is not set}" \
    --azure_openai_auth_mode "${AZURE_OPENAI_AUTH_MODE:?AZURE_OPENAI_AUTH_MODE is not set}" \
    --optimizer_azure_openai_auth_mode "${AZURE_OPENAI_AUTH_MODE}" \
    --target_azure_openai_auth_mode "${AZURE_OPENAI_AUTH_MODE}" \
    --optimizer_model "${OPTIMIZER_MODEL}" \
    --target_model "${TARGET_MODEL}" \
    --out_root "${DEFAULT_OUT_ROOT}" \
    "$@"

echo ""
echo "Output root: ${DEFAULT_OUT_ROOT}"
