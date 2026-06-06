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
  is the zero-byte skill file used for this run.

Issue resolution: the first launch failed before evaluation because the new
runner expanded an empty bash array under `set -u`; no evaluation result from
that failed timestamped output was used. The runner was fixed, checked with
`bash -n`, and the experiment was rerun successfully.

### No-Skill Baseline Notes

- This baseline uses a zero-byte `empty_skill.md`, not
  `skillopt/envs/searchqa/skills/initial.md`.
- The purpose is to isolate the effect of removing skill instructions while
  keeping the SearchQA split and target model comparable to the previous full
  training run.
- The completed run used output directory
  `outputs/searchqa_no_skill_baseline_gpt-5.5_20260606_160335/`.
