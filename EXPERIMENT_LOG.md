# EXPERIMENT_LOG.md

## SearchQA Training Experiments

| Date/Time | Experiment | Goal | Configuration | Command | Output | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-05-29 23:50:09 CST | SearchQA default full training | Run the default full SearchQA training loop and evaluate the learned skill. | `configs/searchqa/default.yaml`; optimizer/target default to `gpt-5.5`; train 400, batch 40, 4 epochs, full val/test. | `bash scripts/run_searchqa.sh` | `outputs/skillopt_searchqa_gpt-5.5_20260529_235037/` | Completed |

### Result Summary

The run completed all 40 training steps and final `valid_unseen` test
evaluation. The best selection checkpoint came from step 37.

| Evaluation | Skill | Hard | Soft | Notes |
| --- | --- | --- | --- | --- |
| Selection | Initial | 0.7550 | 0.8607 | Baseline before training. |
| Selection | Best learned | 0.8750 | - | Step 37, best checkpoint. |
| Test | Initial | 1111/1400 = 0.7936 | 0.8925 | `test_eval_baseline`. |
| Test | Best learned | 1211/1400 = 0.8650 | 0.9264 | Delta hard=+0.0714. |

Run summary: 40 steps, 7 accepts, 33 rejects, 0 skips; wall time 8790s;
total usage 44,115,918 tokens across 13,069 calls.

Key artifacts:
- [summary.json](outputs/skillopt_searchqa_gpt-5.5_20260529_235037/summary.json)
  records the full run config, epoch stats, metrics, wall time, and token
  accounting.
- [best_skill.md](outputs/skillopt_searchqa_gpt-5.5_20260529_235037/best_skill.md)
  contains the final learned SearchQA answering rules.
- [test_eval/summary.json](outputs/skillopt_searchqa_gpt-5.5_20260529_235037/test_eval/summary.json)
  and
  [test_eval_baseline/summary.json](outputs/skillopt_searchqa_gpt-5.5_20260529_235037/test_eval_baseline/summary.json)
  contain the final test metrics.
- `history.json`, `runtime_state.json`, `config.json`, per-step directories,
  `skills/skill_v*.md`, and prediction/result files are also in the output
  directory.

### Issue Resolution

The first sandboxed launch failed before training because `uv` could not access
`/Users/liyulin/.cache/uv`. No partial training result from that attempt was
used. The same command was relaunched outside the sandbox, after which the run
completed normally.

### Notes

- Preflight found `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, and `AZURE_OPENAI_AUTH_MODE` set.
- Dataset split sizes: train 400, val 200, test 1400.
- No prior formal `outputs/skillopt_searchqa_*` directory was present before launch.
- The first sandboxed launch failed before training because `uv` could not
  access `/Users/liyulin/.cache/uv`; the same command was relaunched outside
  the sandbox.
- Baseline selection completed with hard=0.7550 and soft=0.8607.
- Step 1 completed successfully and was accepted as the new best skill:
  selection hard=0.8250, current=0.8250, best=0.8250.
- Step 2 completed successfully and was accepted as the new best skill:
  selection hard=0.8350, current=0.8350, best=0.8350.
- Step 3 completed but was rejected: candidate selection hard=0.8300, current
  and best remain 0.8350.
- Step 4 completed successfully and was accepted as the new best skill:
  selection hard=0.8400, current=0.8400, best=0.8400.
- Step 5 completed but was rejected: candidate selection hard=0.8300, current
  and best remain 0.8400.
- Step 6 completed but was rejected: candidate selection hard=0.8200, current
  and best remain 0.8400.
- Step 7 completed but was rejected: candidate selection hard=0.8300, current
  and best remain 0.8400.
- Step 8 completed but was rejected: candidate selection hard=0.8250, current
  and best remain 0.8400.
- Step 9 completed successfully and was accepted as the new best skill:
  selection hard=0.8450, current=0.8450, best=0.8450.
- Step 10 completed but was rejected: candidate selection hard=0.8450 tied
  current, and the accept rule requires a strict improvement. Epoch 1 slow
  update injected an empty placeholder; meta skill was skipped for the first
  epoch.
- Step 11 completed but was rejected: candidate selection hard=0.8450 tied
  current; current and best remain 0.8450.
- Step 12 completed but was rejected: candidate selection hard=0.8350, current
  and best remain 0.8450. This step had a slower selection evaluation
  tail, with total evaluate time 140.2s.
- Step 13 completed but was rejected: candidate selection hard=0.8250, current
  and best remain 0.8450.
- Step 14 completed but was rejected: candidate selection hard=0.8450 tied
  current; current and best remain 0.8450. Selection evaluation again had a
  long tail, with total evaluate time 142.6s.
- Step 15 completed but was rejected: candidate selection hard=0.8250, current
  and best remain 0.8450.
- Step 16 completed but was rejected: candidate selection hard=0.8350, current
  and best remain 0.8450.
- Step 17 completed but was rejected: candidate selection hard=0.8350, current
  and best remain 0.8450. This step produced only one selected edit, entirely
  from the failure side.
- Step 18 completed but was rejected: candidate selection hard=0.8350, current
  and best remain 0.8450. Selection evaluation again had a long tail, with
  total evaluate time 139.1s.
- Step 19 completed but was rejected: candidate selection hard=0.8300, current
  and best remain 0.8450.
- Step 20 completed but was rejected: candidate selection hard=0.8400, current
  and best remain 0.8450. Epoch 2 ended without improving on the step 9 best;
  slow update started after the step.
- Epoch 2 slow update compared sampled train performance from epoch 1 vs epoch
  2: both hard=0.8500, with regressed=0, improved=0, persistent_fail=3, and
  stable_success=17. It force-injected a 1199-character update into current
  and best.
- Epoch 2 meta skill memory was written with 1098 characters and loaded at the
  start of epoch 3.
- Step 21 completed but was rejected: candidate selection hard=0.8300, current
  and best remain 0.8450. Selection evaluation had another long tail, with
  total evaluate time 144.3s.
- Step 22 completed but was rejected: candidate selection hard=0.8350, current
  and best remain 0.8450.
- Step 23 completed but was rejected: candidate selection hard=0.8300, current
  and best remain 0.8450. The candidate used two success-side edits; the
  failure side produced no edits.
- Step 24 completed but was rejected: candidate selection hard=0.8050, current
  and best remain 0.8450. This was the weakest candidate selection score so
  far in the run.
- Step 25 completed but was rejected: candidate selection hard=0.8350, current
  and best remain 0.8450. This was a slow step: total 380.4s, including
  aggregate 111.0s and evaluate 148.0s.
- Step 26 completed successfully and was accepted as the new best skill:
  selection hard=0.8550, current=0.8550, best=0.8550. The step merged 5 edits,
  then selected 3 under the current edit budget.
- Step 27 completed but was rejected: candidate selection hard=0.8350, current
  and best remain 0.8550.
- Step 28 completed but was rejected: candidate selection hard=0.8500, current
  and best remain 0.8550.
- Step 29 completed but was rejected: candidate selection hard=0.8450, current
  and best remain 0.8550. This candidate stayed near the acceptance threshold
  late in selection, then fell below it in the final items.
- Step 30 completed successfully and was accepted as the new best skill:
  selection hard=0.8650, current=0.8650, best=0.8650. This is the best
  selection score so far and closes epoch 3 before slow update.
- Epoch 3 slow update again found equal sampled train hard for the previous and
  current epochs (0.8500 vs 0.8500), with regressed=0, improved=0,
  persistent_fail=3, and stable_success=17. It force-injected a 1991-character
  update into current and best.
- Epoch 3 meta skill memory was written with 1151 characters and loaded at the
  start of epoch 4.
- Step 31 completed but was rejected: candidate selection hard=0.8550, current
  and best remain 0.8650. Selection evaluation had a long tail, with total
  evaluate time 153.7s.
- Step 32 completed but was rejected: candidate selection hard=0.8600, current
  and best remain 0.8650. This was another slow step: total 303.3s, including
  select 56.2s and evaluate 138.9s.
- Step 33 completed but was rejected: candidate selection hard=0.8550, current
  and best remain 0.8650. It was near the acceptance threshold late in
  selection but missed the final three validation items.
- Step 34 completed but was rejected: candidate selection hard=0.8600, current
  and best remain 0.8650.
- Step 35 completed but was rejected: candidate selection hard=0.8450, current
  and best remain 0.8650. Selection evaluation again had a long tail, with
  total evaluate time 131.6s.
- Step 36 completed but was rejected: candidate selection hard=0.8600, current
  and best remain 0.8650.
- Step 37 completed successfully and was accepted as the new best skill:
  selection hard=0.8750, current=0.8750, best=0.8750. The step merged 7 edits,
  selected 2, and produced the best selection score so far.
- Step 38 completed but was rejected: candidate selection hard=0.8550, current
  and best remain 0.8750.
- Step 39 completed but was rejected: candidate selection hard=0.8650, current
  and best remain 0.8750.
- Step 40 completed but was rejected: candidate selection hard=0.8500, current
  and best remain 0.8750. This completed the 40-step training loop; the best
  selection score remains Step 37's 0.8750 before final slow update/test
  evaluation.
- Epoch 4 slow update improved sampled train hard from 0.7500 to 0.8000, with
  regressed=0, improved=1, persistent_fail=4, and stable_success=15. It
  force-injected a 3111-character update into current and best; the final meta
  skill memory was written with 1703 characters.
- Final test completed on 1400 `valid_unseen` items: baseline hard=0.7936,
  best learned hard=0.8650, hard delta=+0.0714.

### SearchQA Training Analysis and Visualization

| Date/Time | Goal | Inputs | Command | Outputs | Status |
| --- | --- | --- | --- | --- | --- |
| 2026-06-07 CST | Analyze the completed SearchQA training run in more detail for group-meeting documentation. | `outputs/skillopt_searchqa_gpt-5.5_20260529_235037/summary.json`, `history.json`, `test_eval*/results.jsonl`, slow/meta logs. | `uv run python scripts/dev/analyze_searchqa_run.py` | [searchqa_experiment_flow.md](docs/searchqa_experiment_flow.md), [analysis_summary.json](docs/assets/searchqa_analysis/analysis_summary.json), SVG figures under `docs/assets/searchqa_analysis/`. | Completed |

The analysis added score dynamics, epoch acceptance, token usage, runtime,
completion-token effect, edit dynamics, and test-set migration visualizations to
[docs/searchqa_experiment_flow.md](docs/searchqa_experiment_flow.md). Key
findings: all 40 candidates beat the initial validation baseline, but only
7/40 were accepted against the current skill; train-batch hard and validation
hard had weak correlation (Pearson r=0.20); rollout/eval dominated cost
(90.5% tokens and 97.3% calls); per-step completion tokens had negative
correlation with candidate effect (Pearson r=-0.34); test migration was
117 fixes vs 17 regressions, for a net +100 exact-match answers. No new model
calls or training/evaluation runs were performed; the script only analyzed
saved logs and result files.

## SearchQA Baseline Evaluations

| Date/Time | Experiment | Goal | Configuration | Command | Output | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-06-06 16:02:29 CST | SearchQA no-skill baseline | Evaluate SearchQA with a truly empty skill prompt on `valid_unseen`. | `configs/searchqa/default.yaml`; eval-only; empty skill; target `gpt-5.5`; split `valid_unseen`; seed 42; `test_env_num=0`. | `bash scripts/run_searchqa_no_skill_baseline.sh` | `outputs/searchqa_no_skill_baseline_gpt-5.5_20260606_160335/` | Completed |

### No-Skill Baseline Result Summary

The no-skill eval completed all 1400 `valid_unseen` items. It underperformed
the prior initial-skill baseline by 10 exact-match answers, and underperformed
the best learned skill by 110 exact-match answers.

| Evaluation | Skill | Hard | Soft | Delta vs no-skill hard | Delta vs no-skill soft |
| --- | --- | --- | --- | --- | --- |
| Test | No skill | 1101/1400 = 0.7864 | 0.8896 | - | - |
| Test | Initial skill | 1111/1400 = 0.7936 | 0.8925 | +0.0071 | +0.0029 |
| Test | Best learned | 1211/1400 = 0.8650 | 0.9264 | +0.0786 | +0.0368 |

Key artifacts:
- [run_searchqa_no_skill_baseline.sh](scripts/run_searchqa_no_skill_baseline.sh)
  is the stored formal experiment runner.
- [eval_summary.json](outputs/searchqa_no_skill_baseline_gpt-5.5_20260606_160335/eval_summary.json)
  records the no-skill metrics.
- [results.jsonl](outputs/searchqa_no_skill_baseline_gpt-5.5_20260606_160335/results.jsonl)
  contains the 1400 per-example results.
- [empty_skill.md](outputs/searchqa_no_skill_baseline_gpt-5.5_20260606_160335/empty_skill.md)
  is the zero-byte skill file used for the completed 2026-06-06 run.

Issue resolution: the first launch failed before evaluation because the new
runner expanded an empty bash array under `set -u`; no evaluation result from
that failed timestamped output was used. The runner was fixed, checked with
`bash -n`, and the experiment was rerun successfully.

### No-Skill Baseline Notes

- The completed 2026-06-06 baseline used a zero-byte `empty_skill.md`, not
  `skillopt/envs/searchqa/skills/initial.md`.
- Current `scripts/run_searchqa_no_skill_baseline.sh` no longer creates that
  file. It calls `scripts/eval_only.py --no-skill`, which explicitly evaluates
  a blank skill.
- The purpose is to isolate the effect of removing skill instructions while
  keeping the SearchQA split and target model comparable to the previous full
  training run.
- The completed run used output directory
  `outputs/searchqa_no_skill_baseline_gpt-5.5_20260606_160335/`.

## SearchQA Claude Code Preflight Analysis

| Date/Time | Goal | Scope | Status |
| --- | --- | --- | --- |
| 2026-06-06 22:38:51 CST | Analyze whether a SearchQA run can be reproduced with `claude_code_exec` and how to avoid local Claude Code contamination. | Code/config inspection plus local CLI/import checks; no model inference run. | Analysis only |

Key findings:
- `configs/_base_/default.yaml` defines `claude_code_exec_use_sdk: auto`,
  `claude_code_exec_path: claude`, and `claude_code_exec_effort: medium`.
- `skillopt/model/common.py` maps `claude_code_exec` to default target model
  `claude-sonnet-4-6`.
- `scripts/train.py` can auto-switch an OpenAI sentinel target model to the
  Claude default for `claude_code_exec`, but only when no explicit
  `--target_model`/`model.target` override is present.
- `scripts/run_searchqa.sh` always passes `--target_model "${TARGET_MODEL}"`,
  whose default is `gpt-5.5`, so a direct wrapper launch with only
  `--backend claude_code_exec` would not load the Claude default model. Set
  `TARGET_MODEL=claude-sonnet-4-6` or pass
  `--target_model claude-sonnet-4-6`.
- The local Claude CLI is available at `/Users/liyulin/.local/bin/claude`,
  reports version `2.1.162 (Claude Code)`, and is logged in via
  `ANTHROPIC_API_KEY`. The project `.venv` currently does not import
  `claude_agent_sdk`, so `auto` mode would try SDK first and then fall back to
  CLI.

Isolation note: the current CLI path in `skillopt/model/codex_harness.py` sets
`cwd` to each prediction workspace and passes `--add-dir`, `--tools`,
`--allowedTools`, `--permission-mode`, `--model`, and reasoning flags, but it
does not pass `--bare`, `--no-session-persistence`, `--setting-sources`, or an
isolated settings file. Therefore local user-level Claude settings, plugins,
memory, and session persistence can influence or record the experiment unless
the harness is extended or a wrapper `claude` binary is used.

Suggested safe smoke configuration:

```bash
TARGET_MODEL=claude-sonnet-4-6 bash scripts/run_searchqa.sh \
  --backend claude_code_exec \
  --claude_code_exec_use_sdk cli \
  --claude_code_exec_max_thinking_tokens 0 \
  --num_epochs 1 \
  --train_size 1 \
  --batch_size 1 \
  --sel_env_num 1 \
  --test_env_num 1 \
  --workers 1 \
  --out_root outputs/smoke_searchqa_claude_code_sonnet46_$(date +%Y%m%d_%H%M%S)
```

## SearchQA Codex API Isolation Smoke

| Date/Time | Experiment | Goal | Output | Status |
| --- | --- | --- | --- | --- |
| 2026-06-06 23:57:56 CST | SearchQA Codex API isolated smoke | Verify SearchQA `codex_exec` can run through the API environment while isolating Codex live cwd, `HOME`, and `CODEX_HOME` outside the repo. | `outputs/searchqa_codex_api_gpt-5.5_20260606_235756/` | Completed |

Configuration:
- Runner: `bash scripts/run_searchqa_codex_api.sh`
- Target path: `target_backend=codex_exec`, `codex_exec_use_sdk=cli`,
  target model `gpt-5.5`.
- Optimizer path: `optimizer_backend=openai_chat`, optimizer model `gpt-5.5`.
- Smoke overrides: `num_epochs=1`, `train_size=1`, `batch_size=1`,
  `minibatch_size=1`, `merge_batch_size=1`, `sel_env_num=1`,
  `test_env_num=1`, `workers=1`, `analyst_workers=1`,
  `use_slow_update=false`, `use_meta_skill=false`, `lr_scheduler=constant`,
  `env.exec_timeout=240`.
- Runtime root: `../harness_state/skillopt`, resolved in manifests to
  `/Users/liyulin/projects/harness_state/skillopt`.

Result summary:

| Stage | Result | Notes |
| --- | --- | --- |
| Baseline selection | hard=1/1, soft=1.0000 | Initial skill on one `valid_seen` item. |
| Train rollout | hard=1/1, soft=1.0000 | Answered `Tom Clancy`; generated one success-side patch. |
| Candidate selection | hard=1/1, soft=1.0000 | Candidate tied current score, so strict-improvement rule rejected it. |
| Final test | baseline hard=1/1, best hard=1/1 | Delta hard=+0.0000 on one `valid_unseen` item. |
| Run totals | 1 step, 0 accepts, 1 reject, 0 skips | Wall time 60.2s; token summary 2,110 total tokens across 6 calls. |

Key artifacts:
- [summary.json](outputs/searchqa_codex_api_gpt-5.5_20260606_235756/summary.json)
  records the smoke config, metrics, wall time, and token accounting.
- [config.json](outputs/searchqa_codex_api_gpt-5.5_20260606_235756/config.json)
  confirms `azure_openai_endpoint` is empty in artifacts, while runtime uses
  environment variables.
- [runtime_state.json](outputs/searchqa_codex_api_gpt-5.5_20260606_235756/runtime_state.json)
  records `last_completed_step=1`, `best_step=0`, and `best_score=1.0`.
- [history.json](outputs/searchqa_codex_api_gpt-5.5_20260606_235756/history.json)
  records the rejected candidate step and generated edit counts.
- [codex_manifest.json](outputs/searchqa_codex_api_gpt-5.5_20260606_235756/test_eval/predictions/5093b6d997674d25be29a4c94fcd5185/codex_manifest.json)
  shows the repo-external live cwd and isolated `CODEX_HOME` for one target
  call.
- `codex_raw.txt` and `codex_trace_summary.txt` are present under each target
  prediction directory; five Codex target calls were recorded.
- Repo-external runtime state was preserved under
  `../harness_state/skillopt/searchqa_codex_api_gpt-5.5_20260606_235756/`.

Isolation checks:
- `codex_manifest.json` records `ignore_user_config=true`,
  `ignore_rules=true`, `ephemeral=true`, `minimal_subprocess_env=true`, and
  `repo_outside_live_cwd=true`.
- Live cwd and isolated homes are under
  `/Users/liyulin/projects/harness_state/skillopt/...`, not under the repo.
- No `codex_exec` live workspace was written under the repo output directory.
- Grep over final `codex_raw.txt`, `codex_manifest.json`, `config.json`, and
  `summary.json` found no actual endpoint string, no API-key-shaped secret, no
  `/Users/liyulin/.codex`, and no repo `AGENTS.md` / `.agents` path.

Issues resolved:
- The runner initially passed the API endpoint as a CLI config override, which
  made the actual endpoint appear in `config.json`/`summary.json`. The runner
  now relies on environment variables for the endpoint and only passes
  auth-mode overrides; the final smoke artifacts keep endpoint fields empty.
- An intermediate smoke exposed a timeout-path bug: `subprocess.TimeoutExpired`
  can carry bytes in `stdout`/`stderr`, and raw artifact writing expected
  strings. `skillopt/model/codex_harness.py` now coerces captured output to
  text before writing artifacts, and a function-level check verified bytes raw
  can be persisted.
- A direct `~/.codex` keyword grep is noisy because the active system Codex
  conversation itself records this plan. The final isolation check therefore
  relies on the experiment manifests, live cwd paths, subprocess env design,
  and raw artifact grep.

## SearchQA Codex API Default Run Attempt

| Date/Time | Experiment | Goal | Command | Output | Status |
| --- | --- | --- | --- | --- | --- |
| 2026-06-07 00:06 CST | SearchQA Codex API exact-default attempt | Run full SearchQA default training through isolated `codex_exec`. | `bash scripts/run_searchqa_codex_api.sh` | `outputs/searchqa_codex_api_gpt-5.5_20260607_000641/` | Aborted / invalid |

Configuration:
- Training configuration came from [configs/searchqa/default.yaml](configs/searchqa/default.yaml):
  4 epochs, train size 400, batch size 40, 10 steps per epoch, full
  selection/test splits, slow update enabled, and meta skill enabled.
- Runtime settings were also exact default: `env.workers=24` and
  `env.exec_timeout=120`.
- Codex target path used the isolated API runner:
  [scripts/run_searchqa_codex_api.sh](scripts/run_searchqa_codex_api.sh),
  `target_backend=codex_exec`, `codex_exec_use_sdk=cli`, target model
  `gpt-5.5`, optimizer backend `openai_chat`.

Outcome:
- Baseline selection completed on 200 `valid_seen` items with hard=0.5150 and
  soft=0.5891, but this is not a meaningful model-quality measurement.
- 59/200 baseline items had execution-level failures, mainly Codex CLI timeout
  at 120s or transient provider high-demand reconnect failures.
- The run had already entered step 1, where early train rollout items were also
  failing, so it was terminated to avoid producing invalid training signal and
  unnecessary API usage.

Issues and fixes:

| Issue | Evidence | Resolution |
| --- | --- | --- |
| Default runtime settings overloaded or outpaced the API path. | Baseline had 59 execution errors and step 1 began with execution failures. | Marked this run invalid; next meaningful run should keep default training hyperparameters but use operational reliability overrides such as lower concurrency and a longer timeout, or retry later under better service conditions. |
| Failure artifacts could include provider endpoint text via Python timeout exception strings. | Timeout `fail_reason` used the raw `TimeoutExpired` string, which includes argv. | Added centralized redaction in [codex_harness.py](skillopt/model/codex_harness.py) and applied it before writing Codex raw artifacts or SearchQA `fail_reason`; sanitized this aborted run's output/runtime files. |

Validation:
- `.venv/bin/python3 -m py_compile skillopt/model/codex_harness.py skillopt/envs/searchqa/rollout.py`
  passed after the redaction fix.
- A synthetic redaction check confirmed provider endpoint text and API-key
  shaped values are replaced with placeholders.
- Grep over the aborted output and repo-external runtime tree found no remaining
  provider-name or API-key-shaped strings after sanitization.

## SearchQA Codex API Reliability Relaunch Attempt

| Date/Time | Experiment | Goal | Command | Output | Status |
| --- | --- | --- | --- | --- | --- |
| 2026-06-07 00:29 CST | SearchQA Codex API default-scale relaunch | Keep default SearchQA training hyperparameters, but reduce API pressure with operational runtime overrides. | `bash scripts/run_searchqa_codex_api.sh --cfg-options env.exec_timeout=240 env.workers=8` | `outputs/searchqa_codex_api_gpt-5.5_20260607_002906/` | Aborted / blocked |

Configuration:
- Training scale remained the default from
  [configs/searchqa/default.yaml](configs/searchqa/default.yaml): 4 epochs,
  train size 400, batch size 40, 10 steps per epoch, full selection/test
  splits, slow update enabled, and meta skill enabled.
- Runtime reliability overrides were `env.exec_timeout=240` and
  `env.workers=8`.
- Target path remained `target_backend=codex_exec`, `codex_exec_use_sdk=cli`,
  target model `gpt-5.5`; optimizer remained `openai_chat` with `gpt-5.5`.

Outcome:
- Baseline selection completed cleanly: 130/200 exact-match answers,
  hard=0.6500, soft=0.7394, with 0 execution errors.
- Step 1 rollout also completed cleanly: 33/40 exact-match answers,
  hard=0.8250, with 0 execution errors.
- The optimizer generated 6 minibatch patch files, merged 2 edits, and produced
  [candidate_skill.md](outputs/searchqa_codex_api_gpt-5.5_20260607_002906/steps/step_0001/candidate_skill.md).
- Step 1 candidate selection was stopped after 24/200 items because all 24
  completed items were execution errors. Most were 403/forbidden responses, and
  the direct Codex probe confirmed quota exhaustion from the API account.

Issue notes:
- Lowering concurrency and increasing timeout fixed the earlier high-demand
  timeout pattern during baseline and train rollout.
- The run still cannot complete until the API account has usable quota again.
- Process inspection revealed Codex CLI was cloning OpenAI plugins into each
  isolated `CODEX_HOME`, even with `--ignore-user-config` and `--ephemeral`.
  This did not read user-local plugins, but it added remote plugin state that
  should not be part of the target workspace.
- Codex CLI command args also previously contained the provider base URL because
  provider config was passed with `-c model_providers...base_url=...`.

Fixes made after abort:
- [codex_harness.py](skillopt/model/codex_harness.py) now writes a temporary
  per-item `CODEX_HOME/config.toml` containing the neutral provider config,
  instead of passing provider base URL in argv.
- The generated config is removed after each Codex CLI call; if removal fails,
  it is overwritten with a redacted stub.
- Isolated target calls now disable `plugins`, `plugin_sharing`, and
  `shell_snapshot`, while keeping `--ignore-rules`, `--ephemeral`,
  `--skip-git-repo-check`, repo-external live cwd, isolated `HOME`, and
  isolated `CODEX_HOME`.
- `codex_manifest.json` now records `uses_isolated_generated_config=true`,
  `provider_config_in_argv=false`, and the plugin/snapshot disable flags.

Validation:
- `bash -n scripts/run_searchqa_codex_api.sh` passed.
- `.venv/bin/python3 -m compileall -q scripts skillopt` passed.
- `git diff --check` passed.
- A monkeypatch argv probe verified isolated Codex CLI calls no longer include
  provider base URL in argv, include the plugin/snapshot disable flags, set
  `HOME` and `CODEX_HOME` to the isolated home, and remove the generated
  `config.toml` after the call.
- Redaction grep passed over the aborted output, repo-external runtime tree,
  and temporary Codex probes after sanitization.
- Process check confirmed no remaining training, `codex exec`, plugin clone, or
  broad local search process.

Next action: restore API quota, then rerun the same default-scale command with
`env.exec_timeout=240 env.workers=8` and verify that no plugin clone processes
or provider endpoint strings appear in the resulting artifacts.

## SkillsBench Migration Pilot

| Date/Time | Experiment | Goal | Scope | Status |
| --- | --- | --- | --- | --- |
| 2026-06-14 13:17 CST | SkillsBench model recipe update | Configure the active SkillsBench pilot to use `gpt-5.5` for SkillOpt optimization and `claude-sonnet-4-6` for target task rollouts. | Config/runner update plus dummy-auth adapter setup only; no real Claude/BenchFlow rollout launched. | Config updated |
| 2026-06-14 12:24 CST | SkillsBench fixed split materialization | Store the full-benchmark SkillsBench train/validation/test split as a repo input so formal runs do not rebuild it. | Generated `data/skillsbench_split/` from the existing seed=42, 2:1:7, category-stratified logic; switched the pilot config to `split_mode=split_dir`; dummy-auth adapter setup only. | Split fixed |
| 2026-06-14 CST | SkillsBench single-category cleanup | Remove obsolete single-domain compatibility files and filtering logic after adopting full-benchmark training. | Deleted legacy config/runner/initial skill; simplified dataloader/adapter to always load all tasks. | Cleanup implemented |
| 2026-06-14 CST | SkillsBench full-benchmark SkillOpt pilot split migration | Evolve one shared SkillOpt skill over all SkillsBench tasks instead of per-category skills. | Config/code migration; dummy-auth adapter setup only; no real Claude/BenchFlow rollout launched. | Scaffold updated |
| 2026-06-14 04:53 CST | SkillsBench software-engineering Claude pilot run | Run the validation-gated SkillOpt pilot using SkillsBench tasks and `claude-agent-acp`. | Train=3, validation=2, test disabled; output `outputs/skillsbench_software_engineering_claude_pilot_20260614_045337`. | Invalid: missing auth/env |
| 2026-06-14 CST | SkillsBench software-engineering SkillOpt pilot scaffold | Use SkillsBench tasks/verifiers while evolving SkillOpt's own domain skill, without SkillsBench human-curated skills. | Code/config implementation plus no-Docker smoke checks; no real Claude/BenchFlow agent rollout launched. | Scaffold implemented |

Invalid launch result:
- Command:
  `uv run python scripts/train.py --config configs/skillsbench/software_engineering_claude_pilot.yaml --cfg-options env.out_root=outputs/skillsbench_software_engineering_claude_pilot_20260614_045337`.
- The run reached `Final Summary` but did not perform any meaningful target
  rollout or optimizer call.
- BenchFlow returned `ANTHROPIC_API_KEY required for model
  'claude-haiku-4-5-20251001' but not set` for target rollouts.
- SkillOpt reflection, slow update, and meta skill calls returned
  `Azure OpenAI endpoint is not configured for optimizer`.
- Baseline selection hard was 0.0, best step remained 0, and total token usage
  was 0. Treat the output directory as a failed preflight artifact, not as an
  experiment result.
- After the invalid launch, the SkillsBench adapter was updated to fail fast
  when Claude auth or the optimizer endpoint is missing.

Configuration decisions:
- Active pilot scope is the full SkillsBench task set.
- Evolve one shared skill for all categories. SkillsBench
  `[metadata].category` is used for fixed split provenance and reporting, not
  for separate skills.
- Formal runs now load the fixed repo split at
  [data/skillsbench_split](data/skillsbench_split). That split was generated
  once with `seed=42`, `train:validation:test=2:1:7`, and
  `stratify_by=category`, yielding train=18, validation=9, test=61 over
  88 tasks.
- Training split category counts are cybersecurity=1, finance-economics=2,
  industrial-physical-systems=3, mathematics-or-formal-reasoning=2,
  media-content-production=1, natural-science=3, office-white-collar=3,
  software-engineering=3.
- Validation split category counts are one task per category except
  software-engineering=2.
- Target rollout backend is BenchFlow `claude-agent-acp` with
  `skillsbench_model=claude-sonnet-4-6`; optimizer/reflection uses SkillOpt's
  `openai_chat` backend with `optimizer_model=gpt-5.5`.
- First full pilot uses `train_size=0` auto-derived from the split,
  `batch_size=18`, `num_epochs=4`, `slow_update_samples=18`, and
  `eval_test=false`.

Implemented artifacts:
- [adapter.py](skillopt/envs/skillsbench/adapter.py) wires the new env into
  SkillOpt's existing rollout/reflect contract and reports the discovered
  SkillsBench categories as task types after setup.
- [dataloader.py](skillopt/envs/skillsbench/dataloader.py) discovers
  the full SkillsBench task set, reads fixed task-ID split files, writes run
  split provenance manifests, and records per-split category counts.
- [data/skillsbench_split](data/skillsbench_split) stores the fixed
  SkillsBench task-ID split and provenance manifest used by the active pilot.
- [rollout.py](skillopt/envs/skillsbench/rollout.py) creates clean shadow
  tasks, removes curated `environment/skills`, generates the runtime
  `skillopt-target` skill pack, invokes BenchFlow `Rollout`, and converts
  ACP trajectories into SkillOpt `conversation.json`.
- [initial.md](skillopt/envs/skillsbench/skills/initial.md) is the initial
  full-benchmark skill. It uses SkillOpt's existing empty-rule initialization
  style rather than handwritten domain guidance.
- [full_claude_pilot.yaml](configs/skillsbench/full_claude_pilot.yaml) is the
  active pilot config.
- [run_skillsbench_claude_pilot.sh](scripts/run_skillsbench_claude_pilot.sh)
  is the formal launch runner.
- Obsolete single-category files were removed:
  `configs/skillsbench/software_engineering_claude_pilot.yaml`,
  `scripts/run_skillsbench_software_engineering_claude_pilot.sh`, and
  `skillopt/envs/skillsbench/skills/software_engineering_initial.md`.

Validation:
- `bash -n scripts/run_skillsbench_claude_pilot.sh` passed.
- `.venv/bin/python -m py_compile skillopt/envs/skillsbench/dataloader.py skillopt/envs/skillsbench/rollout.py skillopt/envs/skillsbench/adapter.py scripts/train.py`
  passed after removing the single-category compatibility path.
- `.venv/bin/python -m py_compile skillopt/envs/skillsbench/adapter.py` passed
  after adding credential preflight.
- Preflight smoke now stops before training with `SkillsBench claude-agent-acp
  requires Anthropic auth` when the launch shell lacks Claude credentials.
- Config/adapter smoke with dummy auth confirmed
  `configs/skillsbench/full_claude_pilot.yaml` resolves to
  no `domain` config key, `split_mode=split_dir`,
  `split_dir=data/skillsbench_split`, train=18, validation=9, test=61, and
  run-artifact provenance copied from the fixed source manifest.
- Config/adapter smoke with dummy auth confirmed the active model recipe:
  `optimizer_model=gpt-5.5`, `optimizer_backend=openai_chat`,
  `target_model=claude-sonnet-4-6`, `target_backend=claude_chat`, and
  `adapter.skillsbench_model=claude-sonnet-4-6`.
- Fixed split JSON parse passed for `train/items.json`, `val/items.json`,
  `test/items.json`, and `split_manifest.json`.
- Shadow-task smoke confirmed curated task skills are removed.
- Skill-pack smoke confirmed `skillopt-target/SKILL.md` frontmatter is
  generated.
- BenchFlow import smoke confirmed local SkillsBench `.venv` provides
  `benchflow.rollout.RolloutConfig`.
- `git diff --check` passed.

Next action:
- Launch the validation-gated pilot when Docker and Claude/BenchFlow auth are
  ready:
  `bash scripts/run_skillsbench_claude_pilot.sh`.
- After the pilot passes, enable held-out test with
  `--cfg-options evaluation.eval_test=true`.

## SearchQA Codex API Restart Probe

| Date/Time | Experiment | Goal | Scope | Status |
| --- | --- | --- | --- | --- |
| 2026-06-07 CST | SearchQA Codex API quota probe before restart | Check whether the API account can run Codex again before launching full default-scale training. | One isolated Codex target call under `/private/tmp/skillopt_codex_quota_probe`; no SearchQA full run launched. | Blocked |

Result:
- The isolated Codex target probe failed with 403/forbidden quota exhaustion.
- Because the blocker occurs before a single target answer can complete, the
  full SearchQA run was not launched.
- The current retry command remains:
  `bash scripts/run_searchqa_codex_api.sh --cfg-options env.exec_timeout=240 env.workers=8`.

Validation:
- Probe artifacts were redacted successfully; grep found no provider-name or
  API-key-shaped strings.
- The probe left no `plugins-clone`, `shell_snapshots`, or generated
  `config.toml` residue in the isolated home.
- Process check found no remaining training, `codex exec`, or plugin clone
  process after the probe.
