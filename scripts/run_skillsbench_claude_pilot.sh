#!/usr/bin/env bash
# SkillOpt - full SkillsBench Claude pilot launch script.
#
# Usage:
#   bash scripts/run_skillsbench_claude_pilot.sh
#   bash scripts/run_skillsbench_claude_pilot.sh --cfg-options evaluation.eval_test=true
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEFAULT_OUT_ROOT="${PROJECT_ROOT}/outputs/skillsbench_claude_pilot_${TIMESTAMP}"

cd "${PROJECT_ROOT}"

if [[ -f ".env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source ".env"
    set +a
fi

if [[ -z "${ANTHROPIC_API_KEY:-}" \
      && -z "${ANTHROPIC_AUTH_TOKEN:-}" \
      && -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" \
      && ! -f "${HOME}/.claude/.credentials.json" ]]; then
    echo "Missing Claude auth: export ANTHROPIC_API_KEY/ANTHROPIC_AUTH_TOKEN or run 'claude login'." >&2
    exit 2
fi

: "${AZURE_OPENAI_ENDPOINT:?AZURE_OPENAI_ENDPOINT is not set}"
: "${AZURE_OPENAI_AUTH_MODE:?AZURE_OPENAI_AUTH_MODE is not set}"
if [[ "${AZURE_OPENAI_AUTH_MODE}" == "openai_compatible" || "${AZURE_OPENAI_AUTH_MODE}" == "api_key" ]]; then
    : "${AZURE_OPENAI_API_KEY:?AZURE_OPENAI_API_KEY is not set}"
fi

echo "============================================================"
echo "  SkillOpt - full SkillsBench Claude pilot"
echo "============================================================"
echo "  Config:     configs/skillsbench/full_claude_pilot.yaml"
echo "  Scope:      all SkillsBench tasks"
echo "  Split:      fixed split from data/skillsbench_split"
echo "  Agent:      claude-agent-acp"
echo "  Test split: disabled by default"
echo "  Output:     ${DEFAULT_OUT_ROOT}"
echo "============================================================"

uv run python scripts/train.py \
    --config configs/skillsbench/full_claude_pilot.yaml \
    --azure_openai_endpoint "${AZURE_OPENAI_ENDPOINT}" \
    --azure_openai_auth_mode "${AZURE_OPENAI_AUTH_MODE}" \
    --optimizer_azure_openai_auth_mode "${AZURE_OPENAI_AUTH_MODE}" \
    --target_azure_openai_auth_mode "${AZURE_OPENAI_AUTH_MODE}" \
    --out_root "${DEFAULT_OUT_ROOT}" \
    "$@"

echo ""
echo "Output root: ${DEFAULT_OUT_ROOT}"
