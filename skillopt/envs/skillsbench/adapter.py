"""SkillsBench adapter for ReflACT."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from skillopt.datasets.base import BatchSpec
from skillopt.envs.base import EnvAdapter
from skillopt.envs.skillsbench.dataloader import SkillsBenchDataLoader
from skillopt.envs.skillsbench.rollout import run_batch
from skillopt.gradient.reflect import run_minibatch_reflect


class SkillsBenchAdapter(EnvAdapter):
    """Run SkillsBench tasks while preserving SkillOpt's update loop."""

    def __init__(
        self,
        skillsbench_root: str = "/Users/liyulin/projects/skillsbench",
        tasks_dir: str = "",
        split_mode: str = "ratio",
        split_ratio: str = "2:1:7",
        split_seed: int = 42,
        stratify_by: str = "",
        split_dir: str = "",
        split_output_dir: str = "",
        seed: int = 42,
        limit: int = 0,
        skillsbench_agent: str = "claude-agent-acp",
        skillsbench_model: str = "claude-haiku-4-5-20251001",
        skillsbench_sandbox: str = "docker",
        sandbox_user: str = "agent",
        workers: int = 1,
        analyst_workers: int = 4,
        failure_only: bool = False,
        minibatch_size: int = 3,
        edit_budget: int = 4,
        include_task_skills: bool = False,
        agent_idle_timeout: int = 600,
        skillsbench_auth_mode: str = "api_key",
        skillsbench_agent_env: dict[str, str] | None = None,
    ) -> None:
        self.skillsbench_root = skillsbench_root
        self.skillsbench_agent = skillsbench_agent
        self.skillsbench_model = skillsbench_model or None
        self.skillsbench_sandbox = skillsbench_sandbox
        self.sandbox_user = sandbox_user or None
        self.workers = int(workers or 1)
        self.analyst_workers = int(analyst_workers or 1)
        self.failure_only = failure_only
        self.minibatch_size = int(minibatch_size or 1)
        self.edit_budget = int(edit_budget or 4)
        self.include_task_skills = bool(include_task_skills)
        self.agent_idle_timeout = int(agent_idle_timeout) if agent_idle_timeout is not None else None
        self.skillsbench_auth_mode = str(skillsbench_auth_mode or "api_key").strip()
        self.skillsbench_agent_env = self._resolve_agent_env(
            skillsbench_agent,
            dict(skillsbench_agent_env or {}),
            auth_mode=self.skillsbench_auth_mode,
        )
        self.dataloader = SkillsBenchDataLoader(
            skillsbench_root=skillsbench_root,
            tasks_dir=tasks_dir,
            split_mode=split_mode,
            split_ratio=split_ratio,
            split_seed=split_seed,
            stratify_by=stratify_by,
            split_dir=split_dir,
            split_output_dir=split_output_dir,
            seed=seed,
            limit=limit,
        )

    def setup(self, cfg: dict) -> None:
        super().setup(cfg)
        self._preflight_runtime_auth(cfg)
        self.dataloader.setup(cfg)

    def get_dataloader(self):
        return self.dataloader

    def build_env_from_batch(self, batch: BatchSpec, **kwargs):
        return list(batch.payload or [])

    def build_train_env(self, batch_size: int, seed: int, **kwargs):
        batch = self.dataloader.build_train_batch(batch_size=batch_size, seed=seed, **kwargs)
        return self.build_env_from_batch(batch, **kwargs)

    def build_eval_env(self, env_num: int, split: str, seed: int, **kwargs):
        batch = self.dataloader.build_eval_batch(env_num=env_num, split=split, seed=seed, **kwargs)
        return self.build_env_from_batch(batch, **kwargs)

    def rollout(
        self,
        env_manager,
        skill_content: str,
        out_dir: str,
        **kwargs,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = env_manager
        return run_batch(
            items=items,
            skill_content=skill_content,
            out_dir=out_dir,
            skillsbench_root=self.skillsbench_root,
            agent=self.skillsbench_agent,
            model=self.skillsbench_model,
            sandbox=self.skillsbench_sandbox,
            sandbox_user=self.sandbox_user,
            workers=self.workers,
            include_task_skills=self.include_task_skills,
            agent_idle_timeout=self.agent_idle_timeout,
            agent_env=self.skillsbench_agent_env,
        )

    def reflect(
        self,
        results: list[dict],
        skill_content: str,
        out_dir: str,
        **kwargs,
    ) -> list[dict | None]:
        prediction_dir = kwargs.get("prediction_dir", os.path.join(out_dir, "predictions"))
        patches_dir = kwargs.get("patches_dir", os.path.join(out_dir, "patches"))
        return run_minibatch_reflect(
            results=results,
            skill_content=skill_content,
            prediction_dir=prediction_dir,
            patches_dir=patches_dir,
            workers=self.analyst_workers,
            failure_only=self.failure_only,
            minibatch_size=self.minibatch_size,
            edit_budget=self.edit_budget,
            random_seed=kwargs.get("random_seed"),
            error_system=self.get_error_minibatch_prompt(),
            success_system=self.get_success_minibatch_prompt(),
            step_buffer_context=kwargs.get("step_buffer_context", ""),
            meta_skill_context=kwargs.get("meta_skill_context", ""),
            update_mode=getattr(self, "_cfg", {}).get("skill_update_mode", "patch"),
        )

    def get_task_types(self) -> list[str]:
        if getattr(self.dataloader, "categories", None):
            return list(self.dataloader.categories)
        return ["skillsbench"]

    @staticmethod
    def _resolve_agent_env(
        agent: str,
        explicit: dict[str, str],
        *,
        auth_mode: str = "api_key",
    ) -> dict[str, str]:
        """Pass Claude relay settings explicitly into BenchFlow agent env."""
        resolved = dict(explicit)
        if agent != "claude-agent-acp":
            return resolved
        auth_mode = str(auth_mode or "api_key").strip().lower()
        for key in (
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_AUTH_TOKEN",
            "CLAUDE_CODE_OAUTH_TOKEN",
            "ANTHROPIC_BASE_URL",
            "ANTHROPIC_MODEL",
        ):
            value = os.environ.get(key)
            if value:
                resolved.setdefault(key, value)
        if resolved.get("ANTHROPIC_BASE_URL"):
            resolved.setdefault("BENCHFLOW_PROVIDER_BASE_URL", resolved["ANTHROPIC_BASE_URL"])
        provider_key = resolved.get("ANTHROPIC_AUTH_TOKEN") or resolved.get("ANTHROPIC_API_KEY")
        if provider_key:
            resolved.setdefault("BENCHFLOW_PROVIDER_API_KEY", provider_key)
        if auth_mode == "api_key" and resolved.get("ANTHROPIC_API_KEY"):
            # Claude Code treats ANTHROPIC_AUTH_TOKEN as a bearer/OAuth path.
            # For Claude-compatible API-key relays, keep the key path explicit
            # and prevent BenchFlow env_mapping from reintroducing a token.
            resolved["ANTHROPIC_AUTH_TOKEN"] = ""
        elif auth_mode not in {"api_key", "auth_token"}:
            raise ValueError(
                "skillsbench_auth_mode must be 'api_key' or 'auth_token', "
                f"got {auth_mode!r}"
            )
        return resolved

    def _preflight_runtime_auth(self, cfg: dict) -> None:
        """Fail before producing invalid all-zero runs when credentials are absent."""
        if self.skillsbench_agent == "claude-agent-acp" and self.skillsbench_model:
            has_claude_env = any(
                os.environ.get(key)
                for key in (
                    "ANTHROPIC_API_KEY",
                    "ANTHROPIC_AUTH_TOKEN",
                    "CLAUDE_CODE_OAUTH_TOKEN",
                )
            )
            has_claude_login = (Path.home() / ".claude" / ".credentials.json").is_file()
            if not has_claude_env and not has_claude_login:
                raise RuntimeError(
                    "SkillsBench claude-agent-acp requires Anthropic auth. "
                    "Export ANTHROPIC_API_KEY/ANTHROPIC_AUTH_TOKEN or run `claude login` "
                    "so ~/.claude/.credentials.json exists."
                )

        optimizer_backend = str(cfg.get("optimizer_backend") or "").strip()
        if optimizer_backend in {"openai_chat", "azure_openai"}:
            endpoint = (
                cfg.get("optimizer_azure_openai_endpoint")
                or cfg.get("azure_openai_endpoint")
                or cfg.get("azure_endpoint")
                or os.environ.get("OPTIMIZER_AZURE_OPENAI_ENDPOINT")
                or os.environ.get("AZURE_OPENAI_ENDPOINT")
            )
            if not endpoint:
                raise RuntimeError(
                    "SkillOpt optimizer requires AZURE_OPENAI_ENDPOINT or "
                    "optimizer_azure_openai_endpoint before running SkillsBench training. "
                    "If using the repo .env shell fragment, source it in the launch shell first."
                )
