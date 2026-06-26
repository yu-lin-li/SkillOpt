#!/usr/bin/env python3
"""Smoke-test SkillsBench core Docker sandboxes on the local Docker host.

The script intentionally checks only Docker sandbox setup: compose build,
compose up --wait, and compose down. It does not run agents, oracles, or
verifiers.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


DEFAULT_SKILLSBENCH_ROOT = Path("/Users/liyulin/projects/skillsbench")
DEFAULT_VERSION = "1.2"
UP_TIMEOUT_SEC = 180
DOWN_TIMEOUT_SEC = 120
TAIL_BYTES = 96 * 1024

SANDBOX_PATHS = {
    "ENV_VERIFIER_LOGS_PATH": "/logs/verifier",
    "ENV_AGENT_LOGS_PATH": "/logs/agent",
    "ENV_ARTIFACTS_PATH": "/logs/artifacts",
}

TRANSIENT_PATTERNS = (
    "connection reset",
    "econnreset",
    "timeout awaiting headers",
    "tls handshake timeout",
    "i/o timeout",
    "temporary failure",
    "could not resolve",
    "no route to host",
    "network is unreachable",
    "unexpected eof",
    "too many requests",
    "rate limit",
    "http 429",
    "status 429",
    "429 too many",
    "503 service unavailable",
    "failed to fetch",
)


@dataclass(frozen=True)
class CommandOutcome:
    return_code: int | None
    timed_out: bool
    duration_sec: float


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    task_dir: Path
    category: str
    network_mode: str
    build_timeout_sec: int
    cpus: int
    memory_mb: int
    static_arch_flags: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Docker build+up smoke tests for SkillsBench core tasks."
    )
    parser.add_argument(
        "--skillsbench-root",
        type=Path,
        default=DEFAULT_SKILLSBENCH_ROOT,
        help="Path to the local SkillsBench checkout.",
    )
    parser.add_argument(
        "--registry-version",
        default=DEFAULT_VERSION,
        help="SkillsBench registry version to smoke-test.",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=None,
        help="Output directory. Defaults to outputs/dev/skillsbench_core_build_up_smoke_<timestamp>.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List selected tasks and write the manifest without running Docker.",
    )
    parser.add_argument(
        "--tasks",
        nargs="+",
        default=None,
        help="Optional task IDs to run, in the given order.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit after task filtering; 0 means no limit.",
    )
    parser.add_argument(
        "--no-retry-transient",
        action="store_true",
        help="Disable the default one retry for recognizable transient failures.",
    )
    parser.add_argument(
        "--up-timeout-sec",
        type=int,
        default=UP_TIMEOUT_SEC,
        help="Timeout for docker compose up --detach --wait.",
    )
    parser.add_argument(
        "--down-timeout-sec",
        type=int,
        default=DOWN_TIMEOUT_SEC,
        help="Timeout for docker compose down cleanup.",
    )
    return parser.parse_args()


def sanitize_compose_project_name(name: str) -> str:
    name = name.lower()
    if not re.match(r"^[a-z0-9]", name):
        name = "0" + name
    return re.sub(r"[^a-z0-9_-]", "-", name)


def sanitize_image_name(name: str) -> str:
    name = name.lower()
    if not re.match(r"^[a-z0-9]", name):
        name = "0" + name
    return re.sub(r"[^a-z0-9._-]", "-", name)


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def read_task_frontmatter(task_md: Path) -> dict[str, Any]:
    text = task_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{task_md} does not start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{task_md} has no closing YAML frontmatter marker")
    data = yaml.safe_load(text[4:end]) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{task_md} frontmatter is not a mapping")
    return data


def resolve_compose_files(skillsbench_root: Path) -> dict[str, Path]:
    candidates = sorted(
        (skillsbench_root / ".venv").glob(
            "lib/python*/site-packages/benchflow/sandbox/_compose_files"
        )
    )
    if not candidates:
        raise FileNotFoundError(
            "Could not find BenchFlow compose files under "
            f"{skillsbench_root / '.venv'}"
        )
    compose_dir = candidates[-1]
    files = {
        "base": compose_dir / "docker-compose-base.yaml",
        "build": compose_dir / "docker-compose-build.yaml",
        "no_network": compose_dir / "docker-compose-no-network.yaml",
    }
    missing = [str(path) for path in files.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing BenchFlow compose files: {missing}")
    return files


def load_registry_tasks(skillsbench_root: Path, version: str) -> list[str]:
    registry = read_json(skillsbench_root / "registry.json")
    for entry in registry:
        if entry.get("name") == "skillsbench" and str(entry.get("version")) == version:
            tasks = entry.get("tasks", [])
            return [str(task["name"]) for task in tasks]
    raise ValueError(f"registry version {version!r} not found in registry.json")


def assert_core_roster(skillsbench_root: Path, registry_task_ids: list[str]) -> None:
    tasks_dir = skillsbench_root / "tasks"
    local_task_ids = sorted(path.name for path in tasks_dir.iterdir() if path.is_dir())
    registry_sorted = sorted(registry_task_ids)
    if registry_sorted != local_task_ids:
        missing_local = sorted(set(registry_sorted) - set(local_task_ids))
        extra_local = sorted(set(local_task_ids) - set(registry_sorted))
        raise RuntimeError(
            "Registry/tasks roster mismatch: "
            f"missing_local={missing_local}, extra_local={extra_local}"
        )
    if "taxonomy-tree-merge" in registry_sorted:
        raise RuntimeError("taxonomy-tree-merge is not a core task and must not be included")


def find_static_arch_flags(environment_dir: Path) -> list[str]:
    flags: list[str] = []
    for rel in ("Dockerfile", "Dockerfile.api"):
        path = environment_dir / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if "--platform=linux/amd64" in text:
            flags.append(f"{rel}:forced_linux_amd64")
        if "cs-x86_64" in text:
            flags.append(f"{rel}:hardcoded_cs_x86_64")
        if "openjdk-amd64" in text or "java-17-openjdk-amd64" in text:
            flags.append(f"{rel}:hardcoded_openjdk_amd64")
        if re.search(r"\bamd64\b", text):
            flags.append(f"{rel}:mentions_amd64")
        if re.search(r"\bx86_64\b", text):
            flags.append(f"{rel}:mentions_x86_64")
    return sorted(set(flags))


def make_task_spec(skillsbench_root: Path, task_id: str) -> TaskSpec:
    task_dir = skillsbench_root / "tasks" / task_id
    frontmatter = read_task_frontmatter(task_dir / "task.md")
    metadata = frontmatter.get("metadata") or {}
    environment = frontmatter.get("environment") or {}
    if not isinstance(metadata, dict) or not isinstance(environment, dict):
        raise ValueError(f"Invalid metadata/environment in {task_dir / 'task.md'}")
    build_timeout = int(float(environment.get("build_timeout_sec", 600)))
    memory_mb = int(environment.get("memory_mb", 1024))
    cpus = int(environment.get("cpus", 1))
    return TaskSpec(
        task_id=task_id,
        task_dir=task_dir,
        category=str(metadata.get("category", "")),
        network_mode=str(environment.get("network_mode", "public")),
        build_timeout_sec=build_timeout,
        cpus=cpus,
        memory_mb=memory_mb,
        static_arch_flags=find_static_arch_flags(task_dir / "environment"),
    )


def tail_text(path: Path, limit: int = TAIL_BYTES) -> str:
    if not path.exists():
        return ""
    size = path.stat().st_size
    with path.open("rb") as f:
        if size > limit:
            f.seek(-limit, os.SEEK_END)
        return f.read().decode(errors="replace")


def is_transient_log(text: str) -> bool:
    lower = text.lower()
    return any(pattern in lower for pattern in TRANSIENT_PATTERNS)


def is_retryable_failure(root_cause: str, text: str) -> bool:
    lower = text.lower()
    if root_cause == "network_download_failure":
        return True
    if root_cause == "resource_or_daemon_failure":
        return any(
            pattern in lower
            for pattern in (
                "cannot connect to the docker daemon",
                "context canceled",
                "grpc",
                "deadline exceeded",
            )
        )
    return False


def classify_root_cause(text: str, static_arch_flags: list[str]) -> str:
    lower = text.lower()
    if any(
        pattern in lower
        for pattern in (
            "rosetta error",
            "exec format error",
            "/lib64/ld-linux-x86-64.so.2",
            "trace/breakpoint trap",
        )
    ):
        return "arch_binary_mismatch"
    if static_arch_flags and any(
        pattern in lower for pattern in ("platform", "amd64", "x86_64", "rosetta")
    ):
        return "forced_amd64_or_rosetta"
    if any(
        pattern in lower
        for pattern in (
            "unable to locate package",
            "has no installation candidate",
            "could not find a version that satisfies the requirement",
            "no matching distribution found",
            "e: package",
            "apt-get",
            "apk add",
            "yum install",
            "dnf install",
        )
    ):
        return "package_or_apt_failure"
    if is_transient_log(text):
        return "network_download_failure"
    if any(
        pattern in lower
        for pattern in (
            "no space left on device",
            "cannot connect to the docker daemon",
            "permission denied while trying to connect to the docker api",
            "out of memory",
            "oom",
            "killed",
            "context canceled",
        )
    ):
        return "resource_or_daemon_failure"
    if any(
        pattern in lower
        for pattern in (
            "yaml",
            "services.",
            "invalid compose",
            "invalid interpolation format",
            "service \"",
            "variable is not set",
        )
    ):
        return "compose_config_failure"
    return "unknown"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_command(
    command: list[str],
    log_path: Path,
    env: dict[str, str],
    timeout_sec: int,
) -> CommandOutcome:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"$ {' '.join(command)}\n")
        f.write(f"# started_at={datetime.now().isoformat(timespec='seconds')}\n\n")
        f.flush()
        try:
            completed = subprocess.run(
                command,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout_sec,
                check=False,
            )
            duration = time.monotonic() - start
            f.write(f"\n# finished_at={datetime.now().isoformat(timespec='seconds')}\n")
            f.write(f"# return_code={completed.returncode}\n")
            f.write(f"# duration_sec={duration:.3f}\n")
            return CommandOutcome(completed.returncode, False, duration)
        except subprocess.TimeoutExpired:
            duration = time.monotonic() - start
            f.write(f"\n# timed_out_after_sec={timeout_sec}\n")
            f.write(f"# duration_sec={duration:.3f}\n")
            return CommandOutcome(None, True, duration)


def build_compose_command(
    *,
    project_name: str,
    environment_dir: Path,
    compose_paths: list[Path],
    subcommand: list[str],
) -> list[str]:
    command = [
        "docker",
        "compose",
        "--project-name",
        project_name,
        "--project-directory",
        str(environment_dir.resolve()),
    ]
    for path in compose_paths:
        command.extend(["-f", str(path.resolve())])
    command.extend(subcommand)
    return command


def docker_info() -> dict[str, str]:
    result = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Arch}} {{.Server.Os}}"],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    parts = result.stdout.strip().split()
    return {
        "server_arch": parts[0] if parts else "",
        "server_os": parts[1] if len(parts) > 1 else "",
    }


def git_rev_parse(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    return result.stdout.strip()


def compose_env(spec: TaskSpec, out_root: Path) -> dict[str, str]:
    task_logs = out_root / "logs" / spec.task_id
    verifier_mount = task_logs / "verifier_mount"
    agent_mount = task_logs / "agent_mount"
    artifacts_mount = task_logs / "artifacts_mount"
    for path in (verifier_mount, agent_mount, artifacts_mount):
        path.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(
        {
            "MAIN_IMAGE_NAME": sanitize_image_name(f"bf__{spec.task_id}"),
            "CONTEXT_DIR": str((spec.task_dir / "environment").resolve()),
            "HOST_VERIFIER_LOGS_PATH": str(verifier_mount.resolve()),
            "HOST_AGENT_LOGS_PATH": str(agent_mount.resolve()),
            "HOST_ARTIFACTS_PATH": str(artifacts_mount.resolve()),
            "CPUS": str(spec.cpus),
            "MEMORY": f"{spec.memory_mb}M",
            "NETWORK_MODE": "none" if spec.network_mode == "no-network" else "bridge",
            **SANDBOX_PATHS,
        }
    )
    return env


def compose_paths_for_task(spec: TaskSpec, benchflow_compose: dict[str, Path]) -> list[Path]:
    paths = [benchflow_compose["base"], benchflow_compose["build"]]
    task_compose = spec.task_dir / "environment" / "docker-compose.yaml"
    if task_compose.exists():
        paths.append(task_compose)
    if spec.network_mode == "no-network":
        paths.append(benchflow_compose["no_network"])
    return paths


def run_down(
    *,
    spec: TaskSpec,
    project_name: str,
    compose_paths: list[Path],
    env: dict[str, str],
    out_root: Path,
    down_timeout_sec: int,
) -> CommandOutcome:
    command = build_compose_command(
        project_name=project_name,
        environment_dir=spec.task_dir / "environment",
        compose_paths=compose_paths,
        subcommand=["down", "--volumes", "--remove-orphans"],
    )
    return run_command(
        command,
        out_root / "logs" / spec.task_id / "down.log",
        env,
        down_timeout_sec,
    )


def run_one_attempt(
    *,
    spec: TaskSpec,
    attempt: int,
    compose_paths: list[Path],
    out_root: Path,
    up_timeout_sec: int,
    down_timeout_sec: int,
) -> tuple[dict[str, Any], bool]:
    project_name = sanitize_compose_project_name(f"sb-smoke-{spec.task_id}-a{attempt}")
    env = compose_env(spec, out_root)
    task_log_dir = out_root / "logs" / spec.task_id
    task_log_dir.mkdir(parents=True, exist_ok=True)

    build_command = build_compose_command(
        project_name=project_name,
        environment_dir=spec.task_dir / "environment",
        compose_paths=compose_paths,
        subcommand=["build"],
    )
    build = run_command(
        build_command,
        task_log_dir / f"build_attempt_{attempt}.log",
        env,
        spec.build_timeout_sec,
    )
    if build.timed_out or build.return_code != 0:
        down = run_down(
            spec=spec,
            project_name=project_name,
            compose_paths=compose_paths,
            env=env,
            out_root=out_root,
            down_timeout_sec=down_timeout_sec,
        )
        log = tail_text(task_log_dir / f"build_attempt_{attempt}.log")
        root_cause = "unknown" if build.timed_out else classify_root_cause(log, spec.static_arch_flags)
        retryable = False if build.timed_out else is_retryable_failure(root_cause, log)
        row = {
            "status": "timeout" if build.timed_out else "build_failed",
            "stage": "build",
            "root_cause": root_cause,
            "transient": retryable,
            "return_code": build.return_code,
            "timed_out": build.timed_out,
            "build_duration_sec": round(build.duration_sec, 3),
            "up_duration_sec": None,
            "down_return_code": down.return_code,
            "down_timed_out": down.timed_out,
            "log_path": str(task_log_dir / f"build_attempt_{attempt}.log"),
        }
        return row, False

    up_command = build_compose_command(
        project_name=project_name,
        environment_dir=spec.task_dir / "environment",
        compose_paths=compose_paths,
        subcommand=["up", "--detach", "--wait"],
    )
    up = run_command(
        up_command,
        task_log_dir / f"up_attempt_{attempt}.log",
        env,
        up_timeout_sec,
    )
    down = run_down(
        spec=spec,
        project_name=project_name,
        compose_paths=compose_paths,
        env=env,
        out_root=out_root,
        down_timeout_sec=down_timeout_sec,
    )
    if up.timed_out or up.return_code != 0:
        log = tail_text(task_log_dir / f"up_attempt_{attempt}.log")
        root_cause = "unknown" if up.timed_out else classify_root_cause(log, spec.static_arch_flags)
        retryable = False if up.timed_out else is_retryable_failure(root_cause, log)
        row = {
            "status": "timeout" if up.timed_out else "up_failed",
            "stage": "up",
            "root_cause": root_cause,
            "transient": retryable,
            "return_code": up.return_code,
            "timed_out": up.timed_out,
            "build_duration_sec": round(build.duration_sec, 3),
            "up_duration_sec": round(up.duration_sec, 3),
            "down_return_code": down.return_code,
            "down_timed_out": down.timed_out,
            "log_path": str(task_log_dir / f"up_attempt_{attempt}.log"),
        }
        return row, False

    row = {
        "status": "pass",
        "stage": "complete",
        "root_cause": "",
        "transient": False,
        "return_code": 0,
        "timed_out": False,
        "build_duration_sec": round(build.duration_sec, 3),
        "up_duration_sec": round(up.duration_sec, 3),
        "down_return_code": down.return_code,
        "down_timed_out": down.timed_out,
        "log_path": str(task_log_dir),
    }
    return row, True


def run_task(
    *,
    spec: TaskSpec,
    compose_files: dict[str, Path],
    out_root: Path,
    retry_transient: bool,
    up_timeout_sec: int,
    down_timeout_sec: int,
) -> dict[str, Any]:
    compose_paths = compose_paths_for_task(spec, compose_files)
    max_attempts = 2 if retry_transient else 1
    start = time.monotonic()
    attempt_rows: list[dict[str, Any]] = []
    for attempt in range(1, max_attempts + 1):
        row, success = run_one_attempt(
            spec=spec,
            attempt=attempt,
            compose_paths=compose_paths,
            out_root=out_root,
            up_timeout_sec=up_timeout_sec,
            down_timeout_sec=down_timeout_sec,
        )
        attempt_rows.append(row)
        if success:
            if attempt > 1:
                row["root_cause"] = "network_download_failure"
                row["transient_recovered"] = True
            break
        if not retry_transient or not row.get("transient") or attempt == max_attempts:
            break
        time.sleep(3)

    final = dict(attempt_rows[-1])
    if final["status"] != "pass" and final.get("transient") and len(attempt_rows) == max_attempts:
        final["status"] = "transient_retry_exhausted"
    final.update(
        {
            "task_id": spec.task_id,
            "category": spec.category,
            "network_mode": spec.network_mode,
            "build_timeout_sec": spec.build_timeout_sec,
            "cpus": spec.cpus,
            "memory_mb": spec.memory_mb,
            "static_arch_flags": spec.static_arch_flags,
            "attempts": len(attempt_rows),
            "attempt_history": attempt_rows,
            "total_duration_sec": round(time.monotonic() - start, 3),
        }
    )
    return final


def render_summary(out_root: Path, specs: list[TaskSpec], rows: list[dict[str, Any]]) -> None:
    by_status = Counter(row["status"] for row in rows)
    by_root = Counter(row["root_cause"] or "none" for row in rows)
    by_category_status: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_category_status[row["category"]][row["status"]] += 1

    lines: list[str] = []
    lines.append("# SkillsBench Core Docker Build+Up Smoke")
    lines.append("")
    lines.append(f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`")
    lines.append(f"- Tasks selected: `{len(specs)}`")
    lines.append(f"- Results file: `{out_root / 'results.jsonl'}`")
    lines.append("")
    lines.append("## Status Counts")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("| --- | ---: |")
    for status, count in sorted(by_status.items()):
        lines.append(f"| `{status}` | {count} |")
    lines.append("")
    lines.append("## Root Cause Counts")
    lines.append("")
    lines.append("| Root cause | Count |")
    lines.append("| --- | ---: |")
    for root_cause, count in sorted(by_root.items()):
        lines.append(f"| `{root_cause}` | {count} |")
    lines.append("")
    lines.append("## Category Status")
    lines.append("")
    lines.append("| Category | pass | build_failed | up_failed | timeout | transient_retry_exhausted | unknown |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for category in sorted(by_category_status):
        counter = by_category_status[category]
        lines.append(
            f"| `{category}` | {counter['pass']} | {counter['build_failed']} | "
            f"{counter['up_failed']} | {counter['timeout']} | "
            f"{counter['transient_retry_exhausted']} | {counter['unknown']} |"
        )
    failures = [row for row in rows if row["status"] != "pass"]
    lines.append("")
    lines.append("## Failures")
    lines.append("")
    if not failures:
        lines.append("No failures.")
    else:
        lines.append("| Task | Status | Stage | Root cause | Attempts | Log |")
        lines.append("| --- | --- | --- | --- | ---: | --- |")
        for row in failures:
            lines.append(
                f"| `{row['task_id']}` | `{row['status']}` | `{row['stage']}` | "
                f"`{row['root_cause']}` | {row['attempts']} | `{row['log_path']}` |"
            )
    lines.append("")
    lines.append("## Static Architecture Flags")
    lines.append("")
    flagged = [spec for spec in specs if spec.static_arch_flags]
    if not flagged:
        lines.append("No static architecture flags found in Dockerfiles.")
    else:
        lines.append("| Task | Flags |")
        lines.append("| --- | --- |")
        for spec in flagged:
            flags = ", ".join(f"`{flag}`" for flag in spec.static_arch_flags)
            lines.append(f"| `{spec.task_id}` | {flags} |")
    lines.append("")
    (out_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    skillsbench_root = args.skillsbench_root.expanduser().resolve()
    if not skillsbench_root.exists():
        raise FileNotFoundError(skillsbench_root)
    if args.out_root is None:
        out_root = Path("outputs/dev") / f"skillsbench_core_build_up_smoke_{timestamp()}"
    else:
        out_root = args.out_root
    out_root = out_root.resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    registry_task_ids = load_registry_tasks(skillsbench_root, args.registry_version)
    assert_core_roster(skillsbench_root, registry_task_ids)
    selected_ids = registry_task_ids
    if args.tasks:
        unknown = sorted(set(args.tasks) - set(registry_task_ids))
        if unknown:
            raise ValueError(f"Tasks are not in registry {args.registry_version}: {unknown}")
        selected_ids = list(args.tasks)
    if args.limit:
        selected_ids = selected_ids[: args.limit]
    specs = [make_task_spec(skillsbench_root, task_id) for task_id in selected_ids]
    compose_files = resolve_compose_files(skillsbench_root)

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "skillsbench_root": str(skillsbench_root),
        "skillsbench_commit": git_rev_parse(skillsbench_root),
        "registry_version": args.registry_version,
        "registry_task_count": len(registry_task_ids),
        "selected_task_count": len(specs),
        "selected_task_ids": [spec.task_id for spec in specs],
        "excluded_task_ids": ["taxonomy-tree-merge"],
        "docker": docker_info() if not args.dry_run else {},
        "benchflow_compose_files": {key: str(path) for key, path in compose_files.items()},
        "mode": "dry-run" if args.dry_run else "build+up",
        "parallelism": 1,
        "retry_transient_once": not args.no_retry_transient,
        "up_timeout_sec": args.up_timeout_sec,
        "down_timeout_sec": args.down_timeout_sec,
    }
    write_json(out_root / "manifest.json", manifest)

    print(f"Output root: {out_root}")
    print(f"Selected {len(specs)} tasks from SkillsBench registry {args.registry_version}")
    for spec in specs:
        print(
            f"- {spec.task_id} "
            f"(category={spec.category}, build_timeout={spec.build_timeout_sec}s, "
            f"network={spec.network_mode})"
        )
    if args.dry_run:
        render_summary(out_root, specs, [])
        return 0

    results_path = out_root / "results.jsonl"
    if results_path.exists():
        results_path.unlink()
    rows: list[dict[str, Any]] = []
    retry_transient = not args.no_retry_transient
    for index, spec in enumerate(specs, start=1):
        print(f"[{index}/{len(specs)}] {spec.task_id}: build+up smoke start", flush=True)
        row = run_task(
            spec=spec,
            compose_files=compose_files,
            out_root=out_root,
            retry_transient=retry_transient,
            up_timeout_sec=args.up_timeout_sec,
            down_timeout_sec=args.down_timeout_sec,
        )
        rows.append(row)
        append_jsonl(results_path, row)
        render_summary(out_root, specs, rows)
        print(
            f"[{index}/{len(specs)}] {spec.task_id}: {row['status']} "
            f"stage={row['stage']} root={row['root_cause'] or 'none'} "
            f"attempts={row['attempts']} duration={row['total_duration_sec']}s",
            flush=True,
        )
    render_summary(out_root, specs, rows)
    print(f"Summary: {out_root / 'summary.md'}")
    return 0 if all(row["status"] == "pass" for row in rows) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
