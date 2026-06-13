"""Dataloader for SkillsBench task-domain splits."""
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - legacy interpreter fallback
    import tomli as tomllib  # type: ignore[no-redef]

from skillopt.datasets.base import BaseDataLoader, BatchSpec


def _compute_split_counts(total: int, ratio: tuple[int, int, int]) -> tuple[int, int, int]:
    weights = list(ratio)
    denom = sum(weights)
    raw = [total * weight / denom for weight in weights]
    counts = [int(value) for value in raw]
    remaining = total - sum(counts)
    order = sorted(
        range(len(raw)),
        key=lambda idx: (raw[idx] - counts[idx], weights[idx]),
        reverse=True,
    )
    for idx in order[:remaining]:
        counts[idx] += 1
    return counts[0], counts[1], counts[2]


def _parse_ratio(text: str) -> tuple[int, int, int]:
    parts = [part.strip() for part in str(text or "").split(":") if part.strip()]
    if len(parts) != 3:
        raise ValueError(f"split_ratio must be train:val:test, got {text!r}")
    ratio = tuple(int(part) for part in parts)
    if min(ratio) <= 0:
        raise ValueError(f"split_ratio parts must be positive, got {text!r}")
    return ratio  # type: ignore[return-value]


def _canonical_split(split: str) -> str:
    aliases = {
        "train": "train",
        "valid_seen": "val",
        "selection": "val",
        "val": "val",
        "valid_unseen": "test",
        "test": "test",
    }
    if split not in aliases:
        raise ValueError(f"Unknown split {split!r}")
    return aliases[split]


class SkillsBenchDataLoader(BaseDataLoader):
    """Build deterministic per-domain SkillsBench train/val/test splits."""

    def __init__(
        self,
        skillsbench_root: str,
        domain: str = "software-engineering",
        tasks_dir: str = "",
        split_mode: str = "ratio",
        split_ratio: str = "2:1:7",
        split_seed: int = 42,
        split_dir: str = "",
        split_output_dir: str = "",
        seed: int = 42,
        limit: int = 0,
    ) -> None:
        self.skillsbench_root = Path(skillsbench_root).expanduser()
        self.domain = domain
        self.tasks_dir = Path(tasks_dir).expanduser() if tasks_dir else self.skillsbench_root / "tasks"
        self.split_mode = split_mode
        self.split_ratio = split_ratio
        self.split_seed = int(split_seed)
        self.split_dir = Path(split_dir).expanduser() if split_dir else None
        self.split_output_dir = split_output_dir
        self.seed = int(seed)
        self.limit = int(limit or 0)
        self.train_items: list[dict[str, Any]] = []
        self.val_items: list[dict[str, Any]] = []
        self.test_items: list[dict[str, Any]] = []
        self._items_by_id: dict[str, dict[str, Any]] = {}
        self._out_root = ""

    def set_out_root(self, out_root: str) -> None:
        self._out_root = out_root

    def setup(self, cfg: dict) -> None:
        self._out_root = str(cfg.get("out_root") or self._out_root or "")
        if not self.tasks_dir.is_dir():
            raise FileNotFoundError(f"SkillsBench tasks dir not found: {self.tasks_dir}")
        items = self._load_domain_items()
        if self.limit > 0:
            items = items[: self.limit]
        if not items:
            raise ValueError(f"No SkillsBench tasks found for domain={self.domain!r}")
        self._items_by_id = {str(item["id"]): item for item in items}
        if self.split_mode == "ratio":
            self.train_items, self.val_items, self.test_items = self._build_ratio_split(items)
        elif self.split_mode == "split_dir":
            self.train_items = self._load_split_file("train")
            self.val_items = self._load_split_file("val")
            self.test_items = self._load_split_file("test")
        else:
            raise ValueError("split_mode must be 'ratio' or 'split_dir'")
        self._write_split_manifest()

    def get_train_size(self) -> int | None:
        return len(self.train_items)

    def state_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "split_seed": self.split_seed,
            "train": [item["id"] for item in self.train_items],
            "val": [item["id"] for item in self.val_items],
            "test": [item["id"] for item in self.test_items],
        }

    def build_train_batch(self, batch_size: int, seed: int, **kwargs) -> BatchSpec:
        items = self._sample(self.train_items, batch_size=batch_size, seed=seed)
        return BatchSpec(
            phase="train",
            split="train",
            seed=seed,
            batch_size=len(items),
            payload=items,
            metadata={"domain": self.domain},
        )

    def build_eval_batch(
        self,
        env_num: int,
        split: str,
        seed: int,
        **kwargs,
    ) -> BatchSpec:
        canonical = _canonical_split(split)
        pool = {
            "train": self.train_items,
            "val": self.val_items,
            "test": self.test_items,
        }[canonical]
        items = self._sample(pool, batch_size=env_num, seed=seed) if env_num > 0 else list(pool)
        return BatchSpec(
            phase="eval",
            split=split,
            seed=seed,
            batch_size=len(items),
            payload=items,
            metadata={"domain": self.domain, "canonical_split": canonical},
        )

    def _load_domain_items(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for task_toml in sorted(self.tasks_dir.glob("*/task.toml")):
            raw = tomllib.loads(task_toml.read_text(encoding="utf-8"))
            metadata = raw.get("metadata") or {}
            if metadata.get("category") != self.domain:
                continue
            task_dir = task_toml.parent
            instruction_path = task_dir / "instruction.md"
            instruction = instruction_path.read_text(encoding="utf-8") if instruction_path.exists() else ""
            item = {
                "id": task_dir.name,
                "task_id": task_dir.name,
                "task_path": str(task_dir),
                "instruction": instruction,
                "task_description": instruction[:2000],
                "category": metadata.get("category", ""),
                "difficulty": metadata.get("difficulty", ""),
                "subcategory": metadata.get("subcategory", ""),
                "tags": metadata.get("tags", []),
                "metadata": metadata,
            }
            items.append(item)
        return items

    def _build_ratio_split(
        self,
        items: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        ordered = sorted(items, key=lambda item: str(item["id"]))
        shuffled = list(ordered)
        random.Random(self.split_seed).shuffle(shuffled)
        n_train, n_val, _ = _compute_split_counts(len(shuffled), _parse_ratio(self.split_ratio))
        train = shuffled[:n_train]
        val = shuffled[n_train : n_train + n_val]
        test = shuffled[n_train + n_val :]
        return train, val, test

    def _load_split_file(self, name: str) -> list[dict[str, Any]]:
        if not self.split_dir:
            raise ValueError("split_dir is required when split_mode='split_dir'")
        path = self.split_dir / f"{name}.json"
        if not path.exists():
            path = self.split_dir / f"{name}.jsonl"
        if not path.exists():
            raise FileNotFoundError(f"Missing SkillsBench split file: {path}")
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return []
        if path.suffix == ".jsonl":
            ids = [json.loads(line)["id"] for line in text.splitlines() if line.strip()]
        else:
            data = json.loads(text)
            ids = data if isinstance(data, list) else data.get("ids", [])
        missing = [task_id for task_id in ids if str(task_id) not in self._items_by_id]
        if missing:
            raise ValueError(f"Split {name!r} references unknown task ids: {missing}")
        return [self._items_by_id[str(task_id)] for task_id in ids]

    @staticmethod
    def _sample(items: list[dict[str, Any]], batch_size: int, seed: int) -> list[dict[str, Any]]:
        if batch_size <= 0 or batch_size >= len(items):
            selected = list(items)
            random.Random(seed).shuffle(selected)
            return selected
        shuffled = list(items)
        random.Random(seed).shuffle(shuffled)
        return shuffled[:batch_size]

    def _write_split_manifest(self) -> None:
        output_dir = self.split_output_dir
        if not output_dir:
            if not self._out_root:
                return
            output_dir = os.path.join(self._out_root, "skillsbench_split")
        os.makedirs(output_dir, exist_ok=True)
        payload = {
            "domain": self.domain,
            "split_mode": self.split_mode,
            "split_ratio": self.split_ratio,
            "split_seed": self.split_seed,
            "counts": {
                "train": len(self.train_items),
                "val": len(self.val_items),
                "test": len(self.test_items),
            },
            "train": [item["id"] for item in self.train_items],
            "val": [item["id"] for item in self.val_items],
            "test": [item["id"] for item in self.test_items],
        }
        with open(os.path.join(output_dir, "split.json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

