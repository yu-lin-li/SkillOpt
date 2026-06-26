# AGENT_STATE.md

## Latest Completed Work

- 2026-06-18 CST: Checked the copied SkillOpt repo on this Linux machine.
  The copied `.venv` was unusable because it pointed to a macOS arm64 CPython
  path under `/Users/liyulin/...`. Rebuilt it with `uv sync --dev` and
  `uv sync --extra dev`, then verified Linux CPython 3.12.13, core imports,
  CLI help, `pytest tests -q` (`97 passed, 2 skipped`), and the no-key
  `skillopt_sleep` deterministic proof.
- 2026-06-14 CST: Updated the SearchQA no-skill baseline runner to use the
  explicit `scripts/eval_only.py --no-skill` flag instead of creating an
  `empty_skill.md` artifact or relying on a deliberately missing path.
- 2026-06-14 CST: Updated the SkillsBench pilot model recipe so SkillOpt
  optimizer/reflection uses `gpt-5.5`, while BenchFlow target rollouts use
  `claude-sonnet-4-6` through `env.skillsbench_model`.
- 2026-06-14 CST: Materialized the full SkillsBench pilot split into
  `data/skillsbench_split/` and switched
  `configs/skillsbench/full_claude_pilot.yaml` to `split_mode: split_dir`.
  Formal runs now load the fixed 18/9/61 task-ID split instead of rebuilding a
  seed=42 ratio split at setup time.
- 2026-06-14 CST: Removed the obsolete single-category SkillsBench entry
  points and filtering path. The `skillsbench` dataloader now always loads the
  full benchmark, uses deterministic `stratify_by=category` splits, writes
  per-split category manifests, and reports category-level task types while
  keeping one evolving skill. The active config is
  `configs/skillsbench/full_claude_pilot.yaml`, the initial skill is
  `skillopt/envs/skillsbench/skills/initial.md`, and the formal runner is
  `scripts/run_skillsbench_claude_pilot.sh`.
- 2026-06-14 CST: Implemented the first SkillsBench migration scaffold for
  SkillOpt: clean shadow task copies that remove SkillsBench curated
  `environment/skills`, runtime `skillopt-target` skill-pack generation,
  BenchFlow Python `Rollout` integration, and fail-fast auth preflight. No
  valid Claude/BenchFlow agent rollout has completed yet.
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

Audit the current SkillsBench v1.2 core Docker sandboxes on the local arm64
Docker host with a build+up smoke test, without running agents, oracles, or
verifiers.

## Current Status

- 2026-06-16 CST: Started implementing a dev-only SkillsBench Docker
  build+up smoke helper for the current `/Users/liyulin/projects/skillsbench`
  `skillsbench@1.2` roster. Scope is the 87 core `tasks/` entries from
  `registry.json`; `tasks-extra/taxonomy-tree-merge` is intentionally excluded.
  The smoke will run sequentially with Docker compose build, up `--wait`, and
  down cleanup, keeping images/build cache for later inspection.
- 2026-06-16 CST: Completed the full 87-task SkillsBench core Docker build+up
  smoke at `outputs/dev/skillsbench_core_build_up_smoke_20260616_full`.
  Docker host was `arm64 linux` and SkillsBench commit was
  `87df9cbd82fcf07fcb0cab960a1f8435d0c415ee`. Results: 84 pass, 2 build
  failures, 1 up timeout. Failures were `python-scala-translation`
  (`arch_binary_mismatch`, hardcoded `cs-x86_64-pc-linux.gz` fails under
  Rosetta), `multilingual-video-dubbing` (`package_or_apt_failure`, no
  matching `torchaudio==2.6.0+cpu` distribution on aarch64), and
  `latex-formula-extraction` (`timeout` during `docker compose up --wait` after
  a long build; root cause remains unresolved from this smoke alone). Several
  static amd64-risk tasks still passed build+up on this host, including
  `fix-build-google-auto`, `fix-druid-loophole-cve`, `flink-query`, and
  `glm-lake-mendota`.
- 2026-06-14 CST: The active pilot config is now
  `configs/skillsbench/full_claude_pilot.yaml`. It loads all 88 tasks from
  `/Users/liyulin/projects/skillsbench/tasks` and reads the fixed
  `data/skillsbench_split/` split: train=18, validation=9, test=61. The
  split provenance remains recorded in
  `data/skillsbench_split/split_manifest.json` as seed=42, `2:1:7`,
  `stratify_by=category`.
- 2026-06-14 04:53 CST: The first launch completed but is invalid. No Claude
  task execution or optimizer reflection actually ran: BenchFlow returned
  `ANTHROPIC_API_KEY required...`, and SkillOpt reflection/slow/meta updates
  returned `Azure OpenAI endpoint is not configured...`. The invalid artifacts
  are kept at
  `outputs/skillsbench_software_engineering_claude_pilot_20260614_045337`.
- 2026-06-14 CST: Added a SkillsBench adapter preflight so missing Claude auth
  or missing SkillOpt optimizer endpoint now raises before training starts,
  preventing future all-zero invalid runs.
- 2026-06-14 13:39 CST: Local `.env` now maps the user's existing
  `BASE_URL`/`API_KEY` relay variables to `ANTHROPIC_AUTH_TOKEN`,
  `ANTHROPIC_API_KEY`, and `ANTHROPIC_BASE_URL`. The SkillsBench adapter now
  explicitly forwards these Claude relay variables into BenchFlow
  `agent_env`, including `BENCHFLOW_PROVIDER_BASE_URL` and
  `BENCHFLOW_PROVIDER_API_KEY`, so `claude-agent-acp` can use the relay inside
  the sandbox.
- 2026-06-14 13:39 CST: Preflight passed without real rollouts: fixed split
  resolved to train=18, validation=9, test=61; Claude relay env keys are
  present in adapter `agent_env`; Docker daemon is ready when checked outside
  the Codex sandbox.
- 2026-06-14 13:44 CST: User clarified that this SkillsBench experiment must
  run held-out test. `configs/skillsbench/full_claude_pilot.yaml` now sets
  `evaluation.eval_test=true`, so `test_env_num=0` means the full 61-task test
  split will run.
- 2026-06-14 13:44 CST: The interrupted launch at
  `outputs/skillsbench_claude_pilot_20260614_134046` is invalid: it used the
  old test-disabled default and was manually interrupted during baseline
  selection. Its first completed item failed before agent execution because
  container-side `npm install @zed-industries/claude-agent-acp@latest` hit
  `ECONNRESET`.
- 2026-06-14 13:44 CST: Added a SkillsBench rollout-side patch that appends
  npm fetch retry options to the BenchFlow `claude-agent-acp` installer. This
  does not change the experiment logic; it only hardens transient agent
  installation fetches.
- 2026-06-14 14:09 CST: The relaunched full pilot at
  `outputs/skillsbench_claude_pilot_20260614_135343` is invalid/diagnostic.
  It had held-out test enabled and the npm install step succeeded, but the
  first baseline task `civ6-adjacency-optimizer` produced no result or agent
  log for about 15 minutes and was manually interrupted before any valid
  Selection metric existed.
- 2026-06-14 14:13 CST: A minimal SkillsBench/BenchFlow/Claude smoke on the
  `hello-world` sanity task completed successfully at
  `outputs/dev/skillsbench_claude_hello_smoke_20260614_1410`: hard=1,
  soft=1.0, `benchflow_trajectory_source=acp`, and verifier passed 2/2 tests.
  This confirms the local relay mapping, `claude-agent-acp`, skill injection,
  and verifier path can work end-to-end.
- 2026-06-14 14:33 CST: The formal held-out-test-enabled pilot was stopped
  after monitoring showed model API failures. It launched detached with PID
  `84395`. Log:
  `outputs/run_logs/skillsbench_claude_pilot_20260614_141531.log`. Output root:
  `outputs/skillsbench_claude_pilot_20260614_141531`. The resolved config
  confirms `eval_test=True`, `test_env_num=0`, `sel_env_num=0`, `train_size=18`,
  `batch_size=18`, `num_epochs=4`, and `skillsbench_model=claude-sonnet-4-6`.
  It completed two Selection baseline items, both invalid due to agent/model
  API errors: `civ6-adjacency-optimizer` failed with a relay channel 403, and
  `suricata-custom-exfil` failed with insufficient quota 402. The run was
  terminated before continuing through the remaining validation/test tasks.
- 2026-06-14 CST: Since the user does not have relay backend permissions,
  added a client-side workaround for SkillsBench Claude rollouts:
  `skillsbench_auth_mode=api_key`. This forces `ANTHROPIC_AUTH_TOKEN=""` while
  preserving `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL`, preventing
  BenchFlow's provider mapping from switching `claude-agent-acp` into the
  bearer/auth-token path. The active config now sets this mode explicitly, and
  local `.env` no longer exports `ANTHROPIC_AUTH_TOKEN`.
- 2026-06-14 15:00 CST: Real-task api-key smoke completed at
  `outputs/dev/skillsbench_claude_api_key_smoke_20260614_145446` on
  `suricata-custom-exfil`. It avoided the previous immediate 402/403 API
  failures, produced ACP trajectory and verifier artifacts, and reached normal
  benchmark scoring. The task scored hard=0/reward=0 because one negative test
  case false-positived, not because of model access failure.
- 2026-06-14 15:01 CST: Relaunched the formal full SkillsBench pilot with the
  api-key workaround. PID `9573`, log
  `outputs/run_logs/skillsbench_claude_pilot_20260614_150129.log`, output root
  `outputs/skillsbench_claude_pilot_20260614_150129`. Resolved config confirms
  `skillsbench_auth_mode=api_key`, `eval_test=True`, `test_env_num=0`,
  `sel_env_num=0`, train=18, validation=9, and test=61. At last check it was
  running the first Selection baseline task, `civ6-adjacency-optimizer`.
- 2026-06-14 15:46 CST: Monitoring update for the active api-key run: PID
  `9573` is still running. Selection baseline has completed 2/9 items:
  `civ6-adjacency-optimizer` failed by BenchFlow per-task wall-clock timeout
  after 1800s, and `suricata-custom-exfil` reached verifier normally but
  scored reward=0. No 402/403 model API errors have appeared in this run.
  The third task, `fix-build-agentops`, has an active Docker container.
- 2026-06-14 16:37 CST: The same run has completed all 9 Selection baseline
  items with hard=1/9 (`current_score=0.1111`) and wrote
  `runtime_state.json` with `last_completed_step=0`. It then entered
  `steps/step_0001/rollout` and prepared the first train task `edit-pdf`, but
  no step-1 rollout result has been written yet. The baseline included normal
  verifier outcomes, Docker build/runtime incompatibility on
  `python-scala-translation`, and multiple Claude/model access failures:
  quota 402, model access, and self-signed certificate errors.
- 2026-06-14 17:11 CST: PID `9573` and child `uv`/Python training processes
  are still alive. Step 1 rollout has written 2/18 train-task results:
  `edit-pdf` failed with a self-signed certificate API error, and
  `earthquake-phase-association` succeeded. A Docker container
  `shock-analysis-demand-main-1` is currently up, and the Python process is
  inside `claude-agent-acp` for that third train task. No `history.json` or
  `summary.json` exists yet; `runtime_state.json` still has
  `last_completed_step=0`.
- 2026-06-14 20:43 CST: The active run was stopped on request because it was
  not producing a valid experiment trajectory. It had been running for about
  5h41m, Selection baseline was 9/9 with hard=1/9, and step 1 rollout had only
  10/18 train-task results with hard=3/10. The run had repeated external
  failures: Claude quota 402, model access errors, self-signed certificate API
  errors, per-task wall-clock timeouts, and a Docker/Rosetta build failure.
  No training step completed (`last_completed_step=0`), and no `history.json`
  or `summary.json` exists. Processes `9573`/`9579`/`9580` and the active
  `jpg-ocr-stat` Docker container were stopped.

## Current Decisions

- Use SkillsBench tasks and verifiers, but not SkillsBench human-curated
  skills.
- Evolve one shared skill for the whole SkillsBench benchmark, not one skill
  per category or task.
- Use SkillsBench `[metadata].category` for the fixed split provenance and
  category-level reporting, not for separate skills.
- Use the fixed repo split at `data/skillsbench_split/` for SkillsBench
  experiments. It was generated from all SkillsBench tasks with `seed=42`,
  `train:validation:test=2:1:7`, and `stratify_by=category`, giving `18/9/61`
  over 88 tasks.
- Use `claude-agent-acp` for target rollouts through BenchFlow Python API.
- Use `claude-sonnet-4-6` for target rollouts through BenchFlow
  `claude-agent-acp`.
- Use `gpt-5.5` on SkillOpt's `openai_chat` backend for optimizer/reflection.
- Initialize the benchmark skill with SkillOpt's existing empty-rule style:
  `(No learned rules yet. Rules will be added through the reflection process.)`.
- Generate a runtime `skillopt-target/SKILL.md` skill pack using the existing
  `render_skill_md` style; do not add frontmatter protection.
- Convert BenchFlow/ACP trajectories into SkillOpt's existing
  `conversation.json` format for reflection.
- First full pilot uses `train_size=0` auto-derived from the split,
  `batch_size=18`, `num_epochs=4`, `slow_update_samples=18`, and
  `eval_test=true`.

## Current Next Steps

- Before relaunching SkillsBench SkillOpt experiments, decide whether to skip
  or patch the three failing Docker smoke tasks. The highest-confidence code
  fix is `python-scala-translation`; `multilingual-video-dubbing` needs a
  compatible torchaudio pin/index for aarch64; `latex-formula-extraction`
  needs a deeper compose/up investigation or a longer up timeout.

## Current Blockers

- The current blocker is upstream model access: the test-enabled formal run
  produced a relay channel 403 followed by an insufficient-quota 402 from the
  Claude-compatible relay. Docker and local ACP execution are otherwise usable.
- After stopping the invalid run, minimal direct probes through both
  `x-api-key` and `Authorization: Bearer` succeeded for
  `claude-sonnet-4-6`, so the local `.env` mapping is not the immediate
  blocker. The remaining issue is relay-side capacity/routing/quota under real
  benchmark workloads.

## Current Validation

- The invalid run produced `baseline_selection_hard=0.0`, `total_steps=4`,
  and no token usage; it must not be used as an experiment result.
- `selection_eval_baseline/results.jsonl` shows both validation failures were
  agent setup errors from missing Anthropic auth.
- `.venv/bin/python -m py_compile skillopt/envs/skillsbench/adapter.py` passed
  after adding fail-fast preflight.
- Preflight smoke now raises `SkillsBench claude-agent-acp requires Anthropic
  auth` before training when the shell lacks credentials.
- `.venv/bin/python -m py_compile skillopt/envs/skillsbench/dataloader.py skillopt/envs/skillsbench/rollout.py skillopt/envs/skillsbench/adapter.py scripts/train.py`
  passed after removing the single-category compatibility path.
- `bash -n scripts/run_skillsbench_claude_pilot.sh` passed.
- Config/adapter smoke with dummy auth passed for
  `configs/skillsbench/full_claude_pilot.yaml`, confirming it now uses
  `split_mode=split_dir`, `split_dir=data/skillsbench_split`, train=18,
  val=9, test=61, and records the source split manifest in the run artifact.
- Config/adapter smoke with dummy auth also confirmed
  `optimizer_model=gpt-5.5`, `target_model=claude-sonnet-4-6`, and
  `adapter.skillsbench_model=claude-sonnet-4-6`.
- Config/adapter smoke with real local relay env passed after sourcing `.env`;
  it confirmed `ANTHROPIC_BASE_URL`, `BENCHFLOW_PROVIDER_BASE_URL`, and the
  fixed 18/9/61 split are present before any BenchFlow rollout is launched.
- Config parse check confirms `eval_test=True`, `test_env_num=0`, and
  `sel_env_num=0` for `configs/skillsbench/full_claude_pilot.yaml`.
- Installer patch smoke confirms the BenchFlow `claude-agent-acp` install
  command now contains `--fetch-retries=5`.
- `docker info` succeeds outside the Codex sandbox after starting Docker
  Desktop.
- The real API probe after sourcing `.env` succeeded against
  `ANTHROPIC_BASE_URL/v1/messages` with model `claude-sonnet-4-6`.
- The development smoke
  `outputs/dev/skillsbench_claude_hello_smoke_20260614_1410` completed through
  SkillOpt `run_batch`, wrote `hello.txt`, produced ACP trajectory artifacts,
  and passed the SkillsBench verifier.
- Fixed split JSON parse passed for
  `data/skillsbench_split/train/items.json`, `val/items.json`,
  `test/items.json`, and `split_manifest.json`.
- Shadow-task smoke on `dialogue-parser` confirmed `environment/skills` is
  removed.
- Skill-pack smoke confirmed `skillopt-target/SKILL.md` is generated with
  YAML frontmatter.
- BenchFlow import smoke confirmed `RolloutConfig` imports from the local
  SkillsBench `.venv`.
- `git diff --check` passed.

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
