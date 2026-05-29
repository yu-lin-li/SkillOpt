# AGENTS.md

Repository-specific guidance for agents working in SkillOpt.

## Experiment Records

- When running, modifying, or analyzing an experiment in this repository,
  create or update the root `EXPERIMENT_LOG.md` automatically.
- Keep entries clear and concise. Each experiment entry should state what was
  done, why it was done, the exact configuration/overrides used, the result,
  and the conclusion or next action.
- Use Markdown tables for scanability. Include columns for date/time,
  experiment name, goal, motivation, configuration, command or script, outputs,
  results/metrics, issues encountered, fixes, and status.
- When problems occur during an experiment, record the symptom, root cause when
  known, the fix or workaround, and whether the issue is fully resolved.
- Link to concrete files where useful, such as configs, scripts, output
  directories, `summary.json`, `history.json`, or generated skill files.
- Do not invent results. If an experiment is interrupted, blocked, or only
  partially validated, record that state explicitly.

## Experiment Script Hygiene

- Keep formal experiment entrypoints minimal and readable. Scripts such as
  `scripts/run_*.sh` should mainly set essential defaults, load local
  environment when needed, call the real entrypoint, and pass through user
  arguments.
- Put helper content that is not part of the formal experiment workflow under
  `scripts/dev/`. This includes local data preparation scripts, smoke tests,
  dry-run helpers, schema checks, and one-off debugging utilities.
- Do not leave temporary smoke-test or debugging scaffolding in formal runners
  after validation is complete. If a check is only useful for development, move
  it to `scripts/dev/` or remove it.
- Keep code files focused on the final adopted logic. Once the data contract or
  execution path is settled, remove exploratory compatibility branches,
  stale switches, broad field guessing, and unused fallback paths.
- Add concise comments at the point where they clarify a non-obvious final
  decision, such as why raw data lives outside the repo or why a gateway auth
  override is required. Avoid comments that document temporary attempts.
