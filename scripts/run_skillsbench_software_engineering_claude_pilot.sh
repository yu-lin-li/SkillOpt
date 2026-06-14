#!/usr/bin/env bash
# Compatibility wrapper for the old single-domain pilot script name.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "This pilot now uses the full SkillsBench split. Forwarding to run_skillsbench_claude_pilot.sh." >&2
exec bash "${SCRIPT_DIR}/run_skillsbench_claude_pilot.sh" "$@"
