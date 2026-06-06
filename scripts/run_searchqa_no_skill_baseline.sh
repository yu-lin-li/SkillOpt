#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# SkillOpt — SearchQA no-skill baseline evaluation
#
# Usage:
#   bash scripts/run_searchqa_no_skill_baseline.sh
#   bash scripts/run_searchqa_no_skill_baseline.sh --split valid_seen
#   bash scripts/run_searchqa_no_skill_baseline.sh --out_root outputs/no_skill_eval
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

OPTIMIZER_MODEL="${OPTIMIZER_MODEL:-gpt-5.5}"
TARGET_MODEL="${TARGET_MODEL:-gpt-5.5}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEFAULT_OUT_ROOT="${PROJECT_ROOT}/outputs/searchqa_no_skill_baseline_${TARGET_MODEL}_${TIMESTAMP}"
OUT_ROOT="${DEFAULT_OUT_ROOT}"
SPLIT="valid_unseen"
PASSTHROUGH_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out_root)
            OUT_ROOT="$2"
            shift 2
            ;;
        --out_root=*)
            OUT_ROOT="${1#*=}"
            shift
            ;;
        --split)
            SPLIT="$2"
            shift 2
            ;;
        --split=*)
            SPLIT="${1#*=}"
            shift
            ;;
        *)
            PASSTHROUGH_ARGS+=("$1")
            shift
            ;;
    esac
done

cd "${PROJECT_ROOT}"

if [[ "${OUT_ROOT}" != /* ]]; then
    OUT_ROOT="${PROJECT_ROOT}/${OUT_ROOT}"
fi

if [[ -f ".env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source ".env"
    set +a
fi

# Check the key without passing it on the CLI, so output configs do not record it.
: "${AZURE_OPENAI_API_KEY:?AZURE_OPENAI_API_KEY is not set}"

mkdir -p "${OUT_ROOT}"
EMPTY_SKILL="${OUT_ROOT}/empty_skill.md"
: > "${EMPTY_SKILL}"

echo "============================================================"
echo "  SkillOpt — SearchQA No-Skill Baseline"
echo "============================================================"
echo "  Optimizer:  ${OPTIMIZER_MODEL}"
echo "  Target:     ${TARGET_MODEL}"
echo "  Split:      ${SPLIT}"
echo "  Empty skill:${EMPTY_SKILL}"
echo "  Out root:   ${OUT_ROOT}"
echo "============================================================"

uv run python scripts/eval_only.py \
    --config configs/searchqa/default.yaml \
    --skill "${EMPTY_SKILL}" \
    --split "${SPLIT}" \
    --azure_openai_endpoint "${AZURE_OPENAI_ENDPOINT:?AZURE_OPENAI_ENDPOINT is not set}" \
    --azure_openai_auth_mode "${AZURE_OPENAI_AUTH_MODE:?AZURE_OPENAI_AUTH_MODE is not set}" \
    --optimizer_azure_openai_auth_mode "${AZURE_OPENAI_AUTH_MODE}" \
    --target_azure_openai_auth_mode "${AZURE_OPENAI_AUTH_MODE}" \
    --optimizer_model "${OPTIMIZER_MODEL}" \
    --target_model "${TARGET_MODEL}" \
    --out_root "${OUT_ROOT}" \
    "${PASSTHROUGH_ARGS[@]+"${PASSTHROUGH_ARGS[@]}"}"

echo ""
echo "Output root: ${OUT_ROOT}"
