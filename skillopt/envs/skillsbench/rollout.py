"""Run SkillsBench tasks through BenchFlow and adapt results to SkillOpt."""
from __future__ import annotations

import asyncio
import glob
import json
import os
import re
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from skillopt.model.codex_harness import render_skill_md
from skillopt.utils import skill_hash


_PROMPT_PREFIX = (
    "Use the workspace files to solve the task. Before starting, use the "
    "`skillopt-target` skill installed for this run. The only intended "
    "experiment skill is `skillopt-target`; follow the task instruction exactly."
)


def ensure_benchflow_importable(skillsbench_root: str | Path) -> None:
    """Make the user's local SkillsBench/BenchFlow install importable."""
    try:
        import benchflow  # noqa: F401
        _patch_benchflow_agent_installers()
        return
    except ModuleNotFoundError:
        pass

    root = Path(skillsbench_root).expanduser()
    candidates = sorted(glob.glob(str(root / ".venv" / "lib" / "python*" / "site-packages")))
    for candidate in candidates:
        if (Path(candidate) / "benchflow").is_dir() and candidate not in sys.path:
            sys.path.append(candidate)
            break

    try:
        import benchflow  # noqa: F401
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Could not import benchflow. Set env.skillsbench_root to a local "
            "SkillsBench checkout with `.venv` already synced."
        ) from exc
    _patch_benchflow_agent_installers()


def _patch_benchflow_agent_installers() -> None:
    """Make transient npm fetch failures less likely during agent install."""
    try:
        from benchflow.agents.registry import AGENT_INSTALLERS
    except Exception:  # noqa: BLE001
        return
    cmd = AGENT_INSTALLERS.get("claude-agent-acp")
    if not cmd or "--fetch-retries=5" in cmd:
        return
    AGENT_INSTALLERS["claude-agent-acp"] = cmd.replace(
        "npm install -g --prefix",
        (
            "npm install -g "
            "--fetch-retries=5 "
            "--fetch-retry-mintimeout=20000 "
            "--fetch-retry-maxtimeout=120000 "
            "--prefix"
        ),
    )


def run_batch(
    *,
    items: list[dict[str, Any]],
    skill_content: str,
    out_dir: str,
    skillsbench_root: str,
    agent: str,
    model: str | None,
    sandbox: str,
    sandbox_user: str | None,
    workers: int,
    include_task_skills: bool,
    agent_idle_timeout: int | None,
    agent_env: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Run a batch of SkillsBench tasks and return SkillOpt rollout rows."""
    ensure_benchflow_importable(skillsbench_root)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    prediction_dir = out / "predictions"
    prediction_dir.mkdir(exist_ok=True)
    results_path = out / "results.jsonl"

    existing = _load_existing(results_path)
    missing = [item for item in items if str(item["id"]) not in existing]
    if missing:
        skills_dir = _write_skill_pack(out, skill_content)
        max_workers = max(1, int(workers or 1))
        if max_workers == 1:
            for item in missing:
                row = _run_one(
                    item=item,
                    out_dir=out,
                    prediction_dir=prediction_dir,
                    skills_dir=skills_dir,
                    agent=agent,
                    model=model,
                    sandbox=sandbox,
                    sandbox_user=sandbox_user,
                    include_task_skills=include_task_skills,
                    agent_idle_timeout=agent_idle_timeout,
                    agent_env=agent_env or {},
                )
                existing[str(item["id"])] = row
                _write_results(results_path, items, existing)
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {
                    ex.submit(
                        _run_one,
                        item=item,
                        out_dir=out,
                        prediction_dir=prediction_dir,
                        skills_dir=skills_dir,
                        agent=agent,
                        model=model,
                        sandbox=sandbox,
                        sandbox_user=sandbox_user,
                        include_task_skills=include_task_skills,
                        agent_idle_timeout=agent_idle_timeout,
                        agent_env=agent_env or {},
                    ): item
                    for item in missing
                }
                for fut in as_completed(futures):
                    item = futures[fut]
                    existing[str(item["id"])] = fut.result()
                    _write_results(results_path, items, existing)

    return [existing[str(item["id"])] for item in items if str(item["id"]) in existing]


def _load_existing(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows[str(row["id"])] = row
    return rows


def _write_results(
    path: Path,
    items: list[dict[str, Any]],
    rows: dict[str, dict[str, Any]],
) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            row = rows.get(str(item["id"]))
            if row:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_skill_pack(out_dir: Path, skill_content: str) -> Path:
    skill_dir = out_dir / "skill_pack" / "skillopt-target"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = render_skill_md(
        skill_content,
        name="skillopt-target",
        description="Use this skill for SkillsBench tasks.",
        preamble=(
            "Use this skill before solving the current SkillsBench task. "
            "It contains the evolving SkillOpt guidance for the benchmark."
        ),
    )
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    return skill_dir.parent


def _run_one(
    *,
    item: dict[str, Any],
    out_dir: Path,
    prediction_dir: Path,
    skills_dir: Path,
    agent: str,
    model: str | None,
    sandbox: str,
    sandbox_user: str | None,
    include_task_skills: bool,
    agent_idle_timeout: int | None,
    agent_env: dict[str, str],
) -> dict[str, Any]:
    ensure_benchflow_importable(Path(item["task_path"]).parents[1])
    from benchflow.rollout import Rollout, RolloutConfig

    task_id = str(item["id"])
    pred_dir = prediction_dir / _safe_id(task_id)
    pred_dir.mkdir(parents=True, exist_ok=True)
    shadow_task = _prepare_shadow_task(Path(item["task_path"]), out_dir / "shadow_tasks" / task_id)
    prompt = _build_prompt(item)
    job_name = "benchflow"
    rollout_name = _safe_id(task_id)
    jobs_dir = out_dir / "benchflow_jobs"

    config = RolloutConfig(
        task_path=shadow_task,
        agent=agent,
        model=model,
        prompts=[prompt],
        environment=sandbox,
        jobs_dir=jobs_dir,
        job_name=job_name,
        rollout_name=rollout_name,
        skills_dir=skills_dir,
        sandbox_user=sandbox_user,
        include_task_skills=include_task_skills,
        agent_idle_timeout=agent_idle_timeout,
        agent_env=agent_env,
    )
    result = _run_coro(Rollout(config).run())
    rollout_dir = jobs_dir / job_name / rollout_name
    row = _to_skillopt_result(item, result, prompt, rollout_dir)
    _write_prediction_artifacts(pred_dir, row, result, prompt, rollout_dir)
    return row


def _prepare_shadow_task(src: Path, dst: Path) -> Path:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    curated = dst / "environment" / "skills"
    if curated.exists():
        shutil.rmtree(curated)
    return dst


def _build_prompt(item: dict[str, Any]) -> str:
    instruction = str(item.get("instruction") or "").strip()
    return f"{_PROMPT_PREFIX}\n\n{instruction}".strip()


def _run_coro(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    box: dict[str, Any] = {}

    def _target() -> None:
        try:
            box["result"] = asyncio.run(coro)
        except BaseException as exc:  # noqa: BLE001
            box["exception"] = exc

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    thread.join()
    if "exception" in box:
        raise box["exception"]
    return box.get("result")


def _to_skillopt_result(
    item: dict[str, Any],
    result: Any,
    prompt: str,
    rollout_dir: Path,
) -> dict[str, Any]:
    rewards = getattr(result, "rewards", None) or {}
    reward = _extract_reward(rewards)
    error = getattr(result, "error", None)
    verifier_error = getattr(result, "verifier_error", None)
    soft = float(reward) if reward is not None else 0.0
    hard = 1 if reward is not None and soft >= 1.0 and not error and not verifier_error else 0
    fail_reason = _fail_reason(error, verifier_error, reward)
    task_type = str(item.get("category") or item.get("subcategory") or item.get("difficulty") or "unknown")
    return {
        "id": str(item["id"]),
        "hard": hard,
        "soft": soft,
        "n_turns": len(getattr(result, "trajectory", []) or []),
        "fail_reason": fail_reason,
        "task_type": task_type,
        "task_description": str(item.get("task_description") or item.get("instruction") or "")[:2000],
        "target_user_prompt": prompt,
        "skillsbench_task_path": str(item.get("task_path", "")),
        "benchflow_rollout_dir": str(rollout_dir),
        "benchflow_rewards": rewards,
        "benchflow_error": error or "",
        "benchflow_verifier_error": verifier_error or "",
        "benchflow_agent": getattr(result, "agent", ""),
        "benchflow_model": getattr(result, "model", ""),
        "benchflow_n_tool_calls": getattr(result, "n_tool_calls", 0),
        "benchflow_trajectory_source": getattr(result, "trajectory_source", "") or "",
        "skill_hash": skill_hash(prompt),
    }


def _extract_reward(rewards: dict[str, Any]) -> float | None:
    if not isinstance(rewards, dict):
        return None
    if "reward" in rewards:
        return float(rewards["reward"])
    numeric = [float(v) for v in rewards.values() if isinstance(v, int | float)]
    if not numeric:
        return None
    return max(numeric)


def _fail_reason(error: str | None, verifier_error: str | None, reward: float | None) -> str:
    if error:
        return f"agent_error: {error}"
    if verifier_error:
        return f"verifier_error: {verifier_error}"
    if reward is None:
        return "missing_reward"
    if float(reward) < 1.0:
        return f"reward={float(reward):.4f}"
    return ""


def _write_prediction_artifacts(
    pred_dir: Path,
    row: dict[str, Any],
    result: Any,
    prompt: str,
    rollout_dir: Path,
) -> None:
    (pred_dir / "target_user_prompt.txt").write_text(prompt, encoding="utf-8")
    (pred_dir / "result.json").write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    bench_result = rollout_dir / "result.json"
    if bench_result.exists():
        shutil.copy2(bench_result, pred_dir / "benchflow_result.json")
    conversation = _format_conversation(row, getattr(result, "trajectory", []) or [])
    (pred_dir / "conversation.json").write_text(
        json.dumps(conversation, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _format_conversation(row: dict[str, Any], trajectory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conversation: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "BenchFlow rollout summary\n"
                f"task={row['id']}\n"
                f"hard={row['hard']} soft={row['soft']:.4f}\n"
                f"failure={row.get('fail_reason', '')}\n"
                f"reward={json.dumps(row.get('benchflow_rewards', {}), ensure_ascii=False)}\n"
                f"agent_error={row.get('benchflow_error', '')}\n"
                f"verifier_error={row.get('benchflow_verifier_error', '')}\n"
                f"tool_calls={row.get('benchflow_n_tool_calls', 0)}"
            ),
        },
        {"role": "user", "content": row.get("target_user_prompt", "")},
    ]
    for event in trajectory[:200]:
        conversation.append(_event_to_message(event))
    if len(trajectory) > 200:
        conversation.append(
            {
                "role": "system",
                "content": f"Trajectory truncated: kept 200 of {len(trajectory)} events.",
            }
        )
    return conversation


def _event_to_message(event: dict[str, Any]) -> dict[str, Any]:
    event_type = str(event.get("type") or event.get("event") or "").lower()
    if "tool" in event_type:
        return {
            "type": "tool_call",
            "cmd": _clip(_pick(event, ("cmd", "command", "name", "tool_name")) or event_type),
            "obs": _clip(_pick(event, ("output", "result", "content", "text", "stdout", "stderr")) or event),
        }
    role = str(event.get("role") or event.get("source") or event_type or "agent")
    content = _pick(event, ("content", "text", "message", "delta"))
    if content is None:
        content = event
    return {"role": role, "content": _clip(content)}


def _pick(event: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in event and event[key] not in (None, ""):
            return event[key]
    return None


def _clip(value: Any, max_chars: int = 4000) -> str:
    if not isinstance(value, str):
        text = json.dumps(value, ensure_ascii=False, default=str)
    else:
        text = value
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "task"
