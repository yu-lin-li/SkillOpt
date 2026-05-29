#!/usr/bin/env python3
"""Prepare SearchQA data for local SkillOpt experiments.

The full upstream SearchQA dataset is stored outside the repo as flat JSONL
files. The repo-local split contains only the items selected by
data/searchqa_id_split.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


HF_DATASET = "lucadiliello/searchqa"
UPSTREAM_SPLITS = ("train", "validation")
DEFAULT_RAW_DATA_DIR = Path("/Users/liyulin/datasets/SearchQA")
DEFAULT_ID_SPLIT = Path("data/searchqa_id_split")
DEFAULT_OUT_SPLIT = Path("data/searchqa_split")
ID_SPLIT_FILES = {
    "train": Path("train/train.json"),
    "val": Path("val/sel.json"),
    "test": Path("test/test.json"),
}


def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False))
            f.write("\n")


def _load_id_items(split_path: Path) -> list[dict[str, Any]]:
    data = _read_json(split_path)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array in {split_path}, got {type(data).__name__}")
    for idx, item in enumerate(data):
        if not isinstance(item, dict) or not str(item.get("id") or "").strip():
            raise ValueError(f"{split_path} item {idx} must be an object with non-empty id")
    return data


def _validate_source_row(row: dict[str, Any]) -> dict[str, Any]:
    key = str(row.get("key") or "").strip()
    question = str(row.get("question") or "").strip()
    context = str(row.get("context") or "").strip()
    answers = row.get("answers")

    if not key:
        raise ValueError("SearchQA source row is missing key")
    if not question:
        raise ValueError(f"SearchQA source row {key!r} is missing question")
    if not context:
        raise ValueError(f"SearchQA source row {key!r} is missing context")
    if not isinstance(answers, list) or not all(isinstance(a, str) and a for a in answers):
        raise ValueError(f"SearchQA source row {key!r} must have non-empty string answers")

    return row


def _as_skillopt_item(source: dict[str, Any], requested_id: str) -> dict[str, Any]:
    return {
        "id": requested_id,
        "question": source["question"],
        "context": source["context"],
        "answers": source["answers"],
    }


def _load_upstream_rows() -> dict[str, list[dict[str, Any]]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: datasets. Run with:\n"
            "  uv run --with datasets python scripts/dev/prepare_searchqa.py"
        ) from exc

    dataset = load_dataset(HF_DATASET)
    missing = [name for name in UPSTREAM_SPLITS if name not in dataset]
    if missing:
        raise ValueError(f"{HF_DATASET} is missing expected split(s): {missing}")

    rows_by_split: dict[str, list[dict[str, Any]]] = {}
    for split_name in UPSTREAM_SPLITS:
        rows_by_split[split_name] = [
            _validate_source_row(dict(row)) for row in dataset[split_name]
        ]
    return rows_by_split


def _write_raw_dataset(
    rows_by_split: dict[str, list[dict[str, Any]]],
    raw_data_dir: Path,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for split_name, rows in rows_by_split.items():
        _write_jsonl(raw_data_dir / f"{split_name}.jsonl", rows)
        counts[split_name] = len(rows)
    return counts


def _build_index(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for split in rows_by_split.values():
        for row in split:
            key = row["key"]
            if key in index:
                raise ValueError(f"Duplicate SearchQA source key/id: {key}")
            index[key] = row
    return index


def _resolve_id_split_files(id_split_dir: Path) -> dict[str, Path]:
    candidates = {
        split: id_split_dir / rel_path
        for split, rel_path in ID_SPLIT_FILES.items()
    }
    missing = [str(path) for path in candidates.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing SearchQA id split file(s): " + ", ".join(missing))
    return candidates


def _write_skillopt_split(
    *,
    id_split_dir: Path,
    out_split_dir: Path,
    index: dict[str, dict[str, Any]],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    id_files = _resolve_id_split_files(id_split_dir)
    missing_ids: dict[str, list[str]] = {}

    for split_name, id_file in id_files.items():
        items = []
        split_missing = []
        for id_item in _load_id_items(id_file):
            requested_id = str(id_item["id"]).strip()
            source = index.get(requested_id)
            if source is None:
                split_missing.append(requested_id)
                continue
            items.append(_as_skillopt_item(source, requested_id))

        if split_missing:
            missing_ids[split_name] = split_missing[:20]
            continue

        counts[split_name] = len(items)
        _write_json(out_split_dir / split_name / "items.json", items)

    if missing_ids:
        details = "; ".join(
            f"{split}: {len(ids)} missing, first={ids[:3]}"
            for split, ids in missing_ids.items()
        )
        raise ValueError(f"ID split contains ids not found in raw SearchQA dataset: {details}")

    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare SearchQA raw data and SkillOpt split")
    parser.add_argument("--raw-data-dir", type=Path, default=DEFAULT_RAW_DATA_DIR)
    parser.add_argument("--id-split-dir", type=Path, default=DEFAULT_ID_SPLIT)
    parser.add_argument("--out-split-dir", type=Path, default=DEFAULT_OUT_SPLIT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_data_dir = args.raw_data_dir.expanduser().resolve()
    id_split_dir = args.id_split_dir.resolve()
    out_split_dir = args.out_split_dir.resolve()

    rows_by_split = _load_upstream_rows()
    raw_counts = _write_raw_dataset(rows_by_split, raw_data_dir)
    index = _build_index(rows_by_split)
    split_counts = _write_skillopt_split(
        id_split_dir=id_split_dir,
        out_split_dir=out_split_dir,
        index=index,
    )

    print("SearchQA prepared")
    print(f"  raw_data_dir:  {raw_data_dir}")
    print(f"  raw_counts:    {raw_counts}")
    print(f"  id_split_dir:  {id_split_dir}")
    print(f"  out_split_dir: {out_split_dir}")
    print(f"  split_counts:  {split_counts}")


if __name__ == "__main__":
    main()
