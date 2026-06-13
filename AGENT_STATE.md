# AGENT_STATE.md

## Latest Completed Work

- 2026-06-07 CST: Completed post-hoc analysis of
  `outputs/skillopt_searchqa_gpt-5.5_20260529_235037/` for group-meeting
  documentation. Added a reproducible stdlib-only analysis script at
  `scripts/dev/analyze_searchqa_run.py`, generated SVG figures plus
  `docs/assets/searchqa_analysis/analysis_summary.json`, appended the analysis
  to `docs/searchqa_experiment_flow.md`, including the later completion-token
  effect analysis requested by the user, and recorded the work in
  `EXPERIMENT_LOG.md`.
- Validation: ran `uv run python scripts/dev/analyze_searchqa_run.py` outside
  the sandbox because `uv` needed access to `/Users/liyulin/.cache/uv`; ran
  `python -m py_compile scripts/dev/analyze_searchqa_run.py`; parsed all
  generated SVG files as XML; checked that all 8 Markdown image links resolve.
- No new training or model evaluation was launched; the analysis only read
  saved SearchQA outputs and generated local documentation artifacts.

## Current Goal

Run the full default SearchQA training experiment through the isolated
`codex_exec` API path and record the result.

## Current Status

- 2026-06-07 CST: User requested another restart. A minimal isolated Codex API
  probe was run before launching full default-scale training; it still returned
  403/forbidden with quota exhaustion, so no full run was launched.
- 2026-06-07 CST: User confirmed relaunch. Relaunch will keep default SearchQA
  training hyperparameters and only override runtime reliability settings:
  `env.exec_timeout=240` and `env.workers=8`.
- 2026-06-07 00:29 CST: Relaunched at
  `outputs/searchqa_codex_api_gpt-5.5_20260607_002906/`; baseline selection is
  running.
- 2026-06-07 CST: Relaunch baseline selection completed with hard=0.6500 and
  soft=0.7394 on 200 `valid_seen` items, with 0 execution errors. Step 1 is
  running.
- 2026-06-07 CST: Step 1 rollout completed with hard=33/40=0.8250 and
  0 execution errors; optimizer patch generation is running.
- 2026-06-07 CST: The relaunched run was stopped during step 1 selection
  evaluation. Baseline and rollout were clean, but selection eval had 24/24
  execution errors, mostly 403/forbidden responses with quota exhaustion.
- 2026-06-07 CST: Found and fixed an additional isolation issue: Codex CLI was
  cloning OpenAI plugins into each isolated `CODEX_HOME`. The harness now uses
  a temporary generated config in the isolated home, disables
  `plugins`, `plugin_sharing`, and `shell_snapshot`, and no longer places the
  provider base URL in process argv.
- 2026-06-07 CST: Preflight complete for a default-configuration SearchQA
  Codex run. Planned launch command is `bash scripts/run_searchqa_codex_api.sh`
  with no scale-reducing overrides.
- 2026-06-07 00:06 CST: Default SearchQA Codex run launched at
  `outputs/searchqa_codex_api_gpt-5.5_20260607_000641/`; baseline selection is
  running.
- 2026-06-07 00:14 CST: The exact-default launch was stopped during step 1.
  Baseline selection finished with hard=0.5150, but 59/200 baseline items were
  execution errors from Codex CLI timeout or transient provider high-demand
  failures, so the run is invalid for training conclusions.
- 2026-06-07 CST: Added redaction for Codex CLI failure artifacts and sanitized
  the aborted run output/runtime files.
- 2026-06-06 CST: Implemented the isolated Codex API path:
  added a neutral SearchQA runner, `model.codex_exec_runtime_root`, Codex CLI
  isolation flags, minimal subprocess environment, repo-external work/home
  directories, and per-item `codex_manifest.json`.
- 2026-06-06 23:57 CST: Final one-item SearchQA Codex API smoke completed at
  `outputs/searchqa_codex_api_gpt-5.5_20260606_235756/`. Result: 1 step,
  0 accepts, 1 reject, 0 skips; final test hard=1.0000, soft=1.0000.

## Current Decisions

- Use the default SearchQA hyperparameters from `configs/searchqa/default.yaml`:
  4 epochs, train size 400, batch size 40, full selection/test splits, slow
  update enabled, and meta skill enabled.
- Use neutral names only: `scripts/run_searchqa_codex_api.sh`,
  `searchqa_codex_api_*`, and provider id `skillopt-experiment`.
- Resolve default `model.codex_exec_runtime_root` relative to the project root:
  `../harness_state/skillopt` -> `/Users/liyulin/projects/harness_state/skillopt`.
- Keep durable experiment artifacts under the normal `out_root`; keep Codex
  live cwd and `CODEX_HOME` under the repo-external runtime tree.
- In isolated Codex runs, use a generated per-item `CODEX_HOME/config.toml`
  instead of provider `-c ...base_url=...` argv overrides; remove that config
  after the CLI call.
- Disable Codex `plugins`, `plugin_sharing`, and `shell_snapshot` for target
  subprocesses so the live cwd/home contain only explicit experiment inputs and
  required runtime state.
- Force the SearchQA runner to use `target_backend=codex_exec`,
  `optimizer_backend=openai_chat`, and `codex_exec_use_sdk=cli`.

## Current Next Steps

- Wait until the API account has usable quota again.
- After quota is restored, relaunch with default training hyperparameters plus
  the operational reliability overrides:
  `bash scripts/run_searchqa_codex_api.sh --cfg-options env.exec_timeout=240 env.workers=8`.
- On relaunch, verify no plugin clone processes appear and no provider endpoint
  or API-key-shaped strings remain in durable artifacts after sanitization.

## Current Blockers

- Current API calls return 403/forbidden with quota exhaustion. A meaningful
  full run cannot continue until quota is restored.
- Exact-default runtime settings (`env.workers=24`, `env.exec_timeout=120`)
  produced many transient Codex execution failures through the configured API
  service; future full attempts should keep the training defaults but use
  `env.exec_timeout=240` and `env.workers=8` unless a stronger rate limit is
  needed.

## Current Validation

- 2026-06-07 restart probe used the current isolated Codex harness under
  `/private/tmp/skillopt_codex_quota_probe`; it failed before full launch with
  403/forbidden quota exhaustion.
- Probe redaction check passed, and probe cleanup checks found no
  `plugins-clone`, `shell_snapshots`, or generated `config.toml` residue.
- Process check confirmed no remaining training, `codex exec`, or plugin clone
  process after the probe.
- Preflight confirmed the runner exists and default SearchQA config keeps the
  full-scale settings requested for this run.
- Aborted exact-default output:
  `outputs/searchqa_codex_api_gpt-5.5_20260607_000641/`.
- Aborted reliability-relaunch output:
  `outputs/searchqa_codex_api_gpt-5.5_20260607_002906/`.
- Relaunch baseline selection: 130/200 hard=0.6500, soft=0.7394, 0 execution
  errors.
- Relaunch step 1 rollout: 33/40 hard=0.8250, 0 execution errors.
- Relaunch step 1 selection eval: stopped after 24/200, with 24 execution
  errors dominated by 403/forbidden/quota responses.
- Redaction check passed for the aborted output and repo-external runtime tree.
- Redaction check passed for the second aborted output, repo-external runtime
  tree, and temporary Codex probes.
- Process check confirmed no remaining run, `codex exec`, plugin clone, or
  wide local search process.
- Syntax checks after redaction changes passed:
  `.venv/bin/python3 -m py_compile skillopt/model/codex_harness.py skillopt/envs/searchqa/rollout.py`.
- `bash -n scripts/run_searchqa_codex_api.sh` passed.
- `.venv/bin/python3 -m compileall -q scripts skillopt` passed.
- `git diff --check` passed.
- Monkeypatch argv probe passed: isolated Codex CLI calls no longer include the
  provider base URL in argv, do include plugin/snapshot disable flags, and
  remove generated `config.toml` after the call.
- `uv run python -c ... scripts.train.load_config(...)` confirmed
  `target_backend=codex_exec`, `optimizer_backend=openai_chat`,
  `codex_exec_use_sdk=cli`, `codex_exec_runtime_root=../harness_state/skillopt`,
  and target model `gpt-5.5`.
- Function-level artifact check verified bytes raw output is coerced to text
  before writing `codex_raw.txt`.
- Final smoke completed at
  `outputs/searchqa_codex_api_gpt-5.5_20260606_235756/`; repo-external runtime
  state was created at
  `../harness_state/skillopt/searchqa_codex_api_gpt-5.5_20260606_235756/`.
- Final artifact grep found no actual endpoint string, no API-key-shaped
  secret, no `/Users/liyulin/.codex`, and no repo `AGENTS.md` / `.agents` path
  in `codex_raw.txt`, `codex_manifest.json`, `config.json`, or `summary.json`.

## Previous Goal

## Goal

Run the default full SearchQA training experiment and record the result.

## Status

- 2026-05-29 23:50:09 CST: Preflight complete; about to start `bash scripts/run_searchqa.sh`.
- 2026-05-29 23:50 CST: Initial sandboxed launch failed because `uv` could not
  access `/Users/liyulin/.cache/uv`; relaunched outside the sandbox.
- 2026-05-29 23:51 CST: Training is running at
  `outputs/skillopt_searchqa_gpt-5.5_20260529_235037/`. Baseline selection
  completed with hard=0.7550 and soft=0.8607; step 1 rollout completed and
  reflect is running.
- 2026-05-29 23:54 CST: Step 1 completed and was accepted as the new best
  skill: selection hard=0.8250, current=0.8250, best=0.8250.
- 2026-05-29 23:56 CST: Step 2 completed and was accepted as the new best
  skill: selection hard=0.8350, current=0.8350, best=0.8350.
- 2026-05-30 00:00 CST: Step 3 completed and was rejected: candidate
  selection hard=0.8300, current remains 0.8350, best remains 0.8350.
- 2026-05-30 00:04 CST: Step 4 completed and was accepted as the new best
  skill: selection hard=0.8400, current=0.8400, best=0.8400.
- 2026-05-30 00:08 CST: Step 5 completed and was rejected: candidate
  selection hard=0.8300, current remains 0.8400, best remains 0.8400.
- 2026-05-30 00:11 CST: Step 6 completed and was rejected: candidate
  selection hard=0.8200, current remains 0.8400, best remains 0.8400.
- 2026-05-30 00:14 CST: Step 7 completed and was rejected: candidate
  selection hard=0.8300, current remains 0.8400, best remains 0.8400.
- 2026-05-30 00:17 CST: Step 8 completed and was rejected: candidate
  selection hard=0.8250, current remains 0.8400, best remains 0.8400.
- 2026-05-30 00:21 CST: Step 9 completed and was accepted as the new best
  skill: selection hard=0.8450, current=0.8450, best=0.8450.
- 2026-05-30 00:24 CST: Step 10 completed and was rejected: candidate
  selection hard=0.8450 tied current, so current and best remain 0.8450.
  Epoch 1 slow update injected an empty placeholder; meta skill was skipped for
  the first epoch.
- 2026-05-30 00:27 CST: Step 11 completed and was rejected: candidate
  selection hard=0.8450 tied current, so current and best remain 0.8450.
- 2026-05-30 00:31 CST: Step 12 completed and was rejected: candidate
  selection hard=0.8350, current remains 0.8450, best remains 0.8450.
- 2026-05-30 00:33 CST: Step 13 completed and was rejected: candidate
  selection hard=0.8250, current remains 0.8450, best remains 0.8450.
- 2026-05-30 00:37 CST: Step 14 completed and was rejected: candidate
  selection hard=0.8450 tied current, so current and best remain 0.8450.
- 2026-05-30 00:41 CST: Step 15 completed and was rejected: candidate
  selection hard=0.8250, current remains 0.8450, best remains 0.8450.
- 2026-05-30 00:43 CST: Step 16 completed and was rejected: candidate
  selection hard=0.8350, current remains 0.8450, best remains 0.8450.
- 2026-05-30 00:46 CST: Step 17 completed and was rejected: candidate
  selection hard=0.8350, current remains 0.8450, best remains 0.8450.
- 2026-05-30 00:50 CST: Step 18 completed and was rejected: candidate
  selection hard=0.8350, current remains 0.8450, best remains 0.8450.
- 2026-05-30 00:53 CST: Step 19 completed and was rejected: candidate
  selection hard=0.8300, current remains 0.8450, best remains 0.8450.
- 2026-05-30 00:55 CST: Step 20 completed and was rejected: candidate
  selection hard=0.8400, current remains 0.8450, best remains 0.8450. Epoch
  2 slow update is running.
- 2026-05-30 00:58 CST: Epoch 2 slow update completed: previous and current
  epoch hard both 0.8500 on the sampled train comparison, with regressed=0,
  improved=0, persistent_fail=3, stable_success=17; it force-injected a
  1199-character update into current and best.
- 2026-05-30 00:59 CST: Epoch 2 meta skill memory written with 1098
  characters; epoch 3 started with that memory loaded.
- 2026-05-30 01:03 CST: Step 21 completed and was rejected: candidate
  selection hard=0.8300, current remains 0.8450, best remains 0.8450.
- 2026-05-30 01:06 CST: Step 22 completed and was rejected: candidate
  selection hard=0.8350, current remains 0.8450, best remains 0.8450.
- 2026-05-30 01:09 CST: Step 23 completed and was rejected: candidate
  selection hard=0.8300, current remains 0.8450, best remains 0.8450.
- 2026-05-30 01:13 CST: Step 24 completed and was rejected: candidate
  selection hard=0.8050, current remains 0.8450, best remains 0.8450.
- 2026-05-30 01:19 CST: Step 25 completed and was rejected: candidate
  selection hard=0.8350, current remains 0.8450, best remains 0.8450.
- 2026-05-30 01:18 CST: Step 26 completed and was accepted as the new best
  skill: selection hard=0.8550, current=0.8550, best=0.8550. Candidate
  merged 5 edits after selection reduced the edit set from 5 to 3.
- 2026-05-30 01:20 CST: Step 27 completed and was rejected: candidate
  selection hard=0.8350, current remains 0.8550, best remains 0.8550.
- 2026-05-30 01:23 CST: Step 28 completed and was rejected: candidate
  selection hard=0.8500, current remains 0.8550, best remains 0.8550.
- 2026-05-30 01:26 CST: Step 29 completed and was rejected: candidate
  selection hard=0.8450, current remains 0.8550, best remains 0.8550.
- 2026-05-30 01:29 CST: Step 30 completed and was accepted as the new best
  skill: selection hard=0.8650, current=0.8650, best=0.8650. Epoch 3 slow
  update is running.
- 2026-05-30 01:30 CST: Epoch 3 slow update completed: previous and current
  epoch hard both 0.8500 on the sampled train comparison, with regressed=0,
  improved=0, persistent_fail=3, stable_success=17; it force-injected a
  1991-character update into current and best.
- 2026-05-30 01:30 CST: Epoch 3 meta skill memory written with 1151
  characters; epoch 4 started with that memory loaded.
- 2026-05-30 01:35 CST: Step 31 completed and was rejected: candidate
  selection hard=0.8550, current remains 0.8650, best remains 0.8650.
- 2026-05-30 01:40 CST: Step 32 completed and was rejected: candidate
  selection hard=0.8600, current remains 0.8650, best remains 0.8650.
- 2026-05-30 01:43 CST: Step 33 completed and was rejected: candidate
  selection hard=0.8550, current remains 0.8650, best remains 0.8650.
- 2026-05-30 01:44 CST: Step 34 completed and was rejected: candidate
  selection hard=0.8600, current remains 0.8650, best remains 0.8650.
- 2026-05-30 01:49 CST: Step 35 completed and was rejected: candidate
  selection hard=0.8450, current remains 0.8650, best remains 0.8650.
- 2026-05-30 01:53 CST: Step 36 completed and was rejected: candidate
  selection hard=0.8600, current remains 0.8650, best remains 0.8650.
- 2026-05-30 01:56 CST: Step 37 completed and was accepted as the new best
  skill: selection hard=0.8750, current=0.8750, best=0.8750.
- 2026-05-30 02:00 CST: Step 38 completed and was rejected: candidate
  selection hard=0.8550, current remains 0.8750, best remains 0.8750.
- 2026-05-30 02:04 CST: Step 39 completed and was rejected: candidate
  selection hard=0.8650, current remains 0.8750, best remains 0.8750.
- 2026-05-30 02:07 CST: Step 40 completed and was rejected: candidate
  selection hard=0.8500, current remains 0.8750, best remains 0.8750. Epoch
  4 slow update is running.
- 2026-05-30 02:09 CST: Epoch 4 slow update completed: sampled train hard
  improved from 0.7500 to 0.8000, with regressed=0, improved=1,
  persistent_fail=4, stable_success=15; it force-injected a 3111-character
  update into current and best. Epoch 4 meta skill memory written with 1703
  characters. Final baseline test evaluation is running on 1400 valid_unseen
  items.
- 2026-05-30 02:20 CST: Experiment completed successfully. Final baseline
  test hard=1111/1400=0.7936, best skill test hard=1211/1400=0.8650 and
  soft=0.9264, for hard delta=+0.0714. Best selection score was 0.8750 at
  step 37. Summary and artifacts are under
  `outputs/skillopt_searchqa_gpt-5.5_20260529_235037/`.

## Decisions

- Use the default SearchQA configuration.
- Run in the foreground for live monitoring.
- Let `scripts/run_searchqa.sh` create the timestamped output directory.

## Next Steps

- No required continuation for this run.
- Optional follow-up: inspect failed `test_eval` examples against the learned
  rules in `best_skill.md` before designing a next SearchQA experiment.

## Blockers

- None active. Initial sandbox cache access issue was resolved by relaunching
  the same command outside the sandbox.

## Validation

- Completed. Confirmed `summary.json`, `best_skill.md`,
  `test_eval/summary.json`, and `test_eval_baseline/summary.json` under
  `outputs/skillopt_searchqa_gpt-5.5_20260529_235037/`.
