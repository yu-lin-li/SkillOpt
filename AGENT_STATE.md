# AGENT_STATE.md

## Current Goal

Run a strict no-skill SearchQA baseline evaluation on the full `valid_unseen`
split, using an empty skill file and `scripts/eval_only.py`.

## Current Status

- 2026-06-06 CST: Added formal runner
  `scripts/run_searchqa_no_skill_baseline.sh`. Preparing to launch the
  default no-skill baseline with target `gpt-5.5`, split `valid_unseen`, and
  config `configs/searchqa/default.yaml`.
- 2026-06-06 16:03 CST: First launch failed before eval due to a runner bug:
  empty `PASSTHROUGH_ARGS` expansion under `set -u`. Fixed the script and
  reran.
- 2026-06-06 16:05 CST: No-skill baseline completed at
  `outputs/searchqa_no_skill_baseline_gpt-5.5_20260606_160335/`.
  Result: hard=1101/1400=0.7864, soft=0.8896.

## Current Decisions

- Use a truly empty skill file, not `skillopt/envs/searchqa/skills/initial.md`.
- Use eval-only, not full training.
- Compare the result against the prior SearchQA test metrics:
  initial skill hard=0.7936 soft=0.8925; best learned hard=0.8650
  soft=0.9264.

## Current Next Steps

- No active continuation required.
- Optional follow-up: inspect no-skill failures against initial-skill failures
  to identify where `initial.md` adds value.

## Current Blockers

- None active.

## Current Validation

- `bash -n scripts/run_searchqa_no_skill_baseline.sh` passed.
- Confirmed `eval_summary.json` and 1400-line `results.jsonl` under
  `outputs/searchqa_no_skill_baseline_gpt-5.5_20260606_160335/`.

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
