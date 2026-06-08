#!/usr/bin/env python3
"""Generate SearchQA run analysis figures from saved SkillOpt outputs.

This script intentionally uses only the Python standard library so it can run
inside the repo environment without adding plotting dependencies.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_OUT_ROOT = Path("outputs/skillopt_searchqa_gpt-5.5_20260529_235037")
DEFAULT_FIGURE_DIR = Path("docs/assets/searchqa_analysis")

COLORS = {
    "bg": "#f8fafc",
    "panel": "#ffffff",
    "grid": "#e2e8f0",
    "text": "#0f172a",
    "muted": "#64748b",
    "blue": "#2563eb",
    "green": "#16a34a",
    "red": "#dc2626",
    "orange": "#f97316",
    "purple": "#7c3aed",
    "teal": "#0f766e",
    "amber": "#d97706",
    "slate": "#334155",
}


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_svg(path: Path, width: int, height: int, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
  <style>
    text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: {COLORS['text']}; }}
    .title {{ font-size: 26px; font-weight: 700; }}
    .subtitle {{ font-size: 15px; fill: {COLORS['muted']}; }}
    .axis {{ font-size: 13px; fill: {COLORS['muted']}; }}
    .label {{ font-size: 14px; fill: {COLORS['text']}; }}
    .small {{ font-size: 12px; fill: {COLORS['muted']}; }}
    .legend {{ font-size: 13px; fill: {COLORS['text']}; }}
  </style>
  <rect width="100%" height="100%" fill="{COLORS['bg']}"/>
{body}
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def fmt_pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def polyline(points: list[tuple[float, float]], color: str, width: float = 3.0, dash: str = "") -> str:
    coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"{dash_attr}/>'


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mx = statistics.mean(xs)
    my = statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = sum((x - mx) ** 2 for x in xs)
    den_y = sum((y - my) ** 2 for y in ys)
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / math.sqrt(den_x * den_y)


def chart_score_timeline(path: Path, history: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    width, height = 1180, 650
    left, right, top, bottom = 90, 40, 105, 92
    chart_w = width - left - right
    chart_h = height - top - bottom
    steps = [int(row["step"]) for row in history]
    y_values = [summary["baseline_selection_hard"]]
    for row in history:
        y_values += [row["selection_hard"], row["current_score"], row["best_score"]]
    y_min = math.floor((min(y_values) - 0.01) * 100) / 100
    y_max = math.ceil((max(y_values) + 0.005) * 1000) / 1000
    y_min = min(y_min, 0.75)
    y_max = max(y_max, 0.88)

    def x_scale(step: float) -> float:
        return left + (step - 1) / (max(steps) - 1) * chart_w

    def y_scale(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * chart_h

    parts: list[str] = []
    parts.append(f'<text x="{left}" y="44" class="title">Selection score over training</text>')
    parts.append(
        f'<text x="{left}" y="70" class="subtitle">Accepted steps move the current/best skill; rejected candidates can still be far above the initial baseline.</text>'
    )
    parts.append(f'<rect x="{left}" y="{top}" width="{chart_w}" height="{chart_h}" rx="10" fill="{COLORS["panel"]}" stroke="{COLORS["grid"]}"/>')

    epoch_w = chart_w / 4
    for idx in range(4):
        if idx % 2 == 1:
            x = left + idx * epoch_w
            parts.append(f'<rect x="{x:.1f}" y="{top}" width="{epoch_w:.1f}" height="{chart_h}" fill="#eef6ff" opacity="0.65"/>')
        parts.append(
            f'<text x="{left + idx * epoch_w + epoch_w / 2:.1f}" y="{height - 35}" text-anchor="middle" class="small">Epoch {idx + 1}</text>'
        )

    tick_values = [0.75, 0.80, 0.825, 0.85, 0.875]
    for tick in tick_values:
        if tick < y_min or tick > y_max:
            continue
        y = y_scale(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_w}" y2="{y:.1f}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
        parts.append(f'<text x="{left - 14}" y="{y + 4:.1f}" text-anchor="end" class="axis">{tick:.3f}</text>')

    for step in range(1, 41, 5):
        x = x_scale(step)
        parts.append(f'<line x1="{x:.1f}" y1="{top + chart_h}" x2="{x:.1f}" y2="{top + chart_h + 5}" stroke="{COLORS["grid"]}"/>')
        parts.append(f'<text x="{x:.1f}" y="{top + chart_h + 24}" text-anchor="middle" class="axis">{step}</text>')

    baseline_y = y_scale(summary["baseline_selection_hard"])
    parts.append(
        f'<line x1="{left}" y1="{baseline_y:.1f}" x2="{left + chart_w}" y2="{baseline_y:.1f}" stroke="{COLORS["slate"]}" stroke-width="2" stroke-dasharray="7 7"/>'
    )
    parts.append(
        f'<text x="{left + chart_w - 8}" y="{baseline_y - 8:.1f}" text-anchor="end" class="small">baseline {summary["baseline_selection_hard"]:.3f}</text>'
    )

    selection_points = [(x_scale(row["step"]), y_scale(row["selection_hard"])) for row in history]
    current_points = [(x_scale(row["step"]), y_scale(row["current_score"])) for row in history]
    best_points = [(x_scale(row["step"]), y_scale(row["best_score"])) for row in history]
    parts.append(polyline(selection_points, COLORS["orange"], 2.4))
    parts.append(polyline(current_points, COLORS["blue"], 3.0))
    parts.append(polyline(best_points, COLORS["green"], 3.0))

    for row in history:
        x = x_scale(row["step"])
        y = y_scale(row["selection_hard"])
        accepted = str(row["action"]).startswith("accept")
        if accepted:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{COLORS["green"]}" stroke="#ffffff" stroke-width="2"/>')
            parts.append(f'<text x="{x:.1f}" y="{y - 12:.1f}" text-anchor="middle" class="small">{row["step"]}</text>')
        else:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#ffffff" stroke="{COLORS["red"]}" stroke-width="1.7"/>')

    legend_y = height - 60
    legend = [
        ("candidate", COLORS["orange"]),
        ("current", COLORS["blue"]),
        ("best", COLORS["green"]),
        ("initial baseline", COLORS["slate"]),
    ]
    x0 = left + 235
    for idx, (label, color) in enumerate(legend):
        x = x0 + idx * 175
        dash = ' stroke-dasharray="7 7"' if label == "initial baseline" else ""
        parts.append(f'<line x1="{x}" y1="{legend_y}" x2="{x + 28}" y2="{legend_y}" stroke="{color}" stroke-width="3"{dash}/>')
        parts.append(f'<text x="{x + 36}" y="{legend_y + 5}" class="legend">{label}</text>')

    write_svg(path, width, height, "\n".join(parts))


def chart_epoch_acceptance(path: Path, summary: dict[str, Any]) -> None:
    width, height = 980, 560
    left, right, top, bottom = 90, 60, 95, 85
    chart_w = width - left - right
    chart_h = height - top - bottom
    stats = summary["epoch_stats"]
    max_total = max(s["accepts"] + s["rejects"] + s["skips"] for s in stats)

    parts = [
        f'<text x="{left}" y="42" class="title">Validation gate acceptance by epoch</text>',
        f'<text x="{left}" y="68" class="subtitle">Only 7 of 40 candidates were accepted; the gate became more selective as the best score rose.</text>',
        f'<rect x="{left}" y="{top}" width="{chart_w}" height="{chart_h}" rx="10" fill="{COLORS["panel"]}" stroke="{COLORS["grid"]}"/>',
    ]

    def y_count(v: float) -> float:
        return top + chart_h - v / max_total * (chart_h - 30)

    for tick in range(0, max_total + 1, 2):
        y = y_count(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_w}" y2="{y:.1f}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
        parts.append(f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{tick}</text>')

    bar_w = 86
    gap = chart_w / len(stats)
    best_min = min(s["best_score_at_epoch_end"] for s in stats)
    best_max = max(s["best_score_at_epoch_end"] for s in stats)
    if best_max == best_min:
        best_max += 0.01

    line_points: list[tuple[float, float]] = []
    for idx, stat in enumerate(stats):
        cx = left + gap * idx + gap / 2
        x = cx - bar_w / 2
        acc_h = stat["accepts"] / max_total * (chart_h - 30)
        rej_h = stat["rejects"] / max_total * (chart_h - 30)
        base_y = top + chart_h
        parts.append(f'<rect x="{x:.1f}" y="{base_y - acc_h:.1f}" width="{bar_w}" height="{acc_h:.1f}" rx="5" fill="{COLORS["green"]}"/>')
        parts.append(f'<rect x="{x:.1f}" y="{base_y - acc_h - rej_h:.1f}" width="{bar_w}" height="{rej_h:.1f}" rx="5" fill="{COLORS["red"]}" opacity="0.83"/>')
        parts.append(f'<text x="{cx:.1f}" y="{base_y - acc_h / 2 + 5:.1f}" text-anchor="middle" class="label" style="fill:#ffffff">{stat["accepts"]}</text>')
        parts.append(f'<text x="{cx:.1f}" y="{base_y - acc_h - rej_h / 2 + 5:.1f}" text-anchor="middle" class="label" style="fill:#ffffff">{stat["rejects"]}</text>')
        parts.append(f'<text x="{cx:.1f}" y="{height - 40}" text-anchor="middle" class="axis">Epoch {stat["epoch"]}</text>')
        best_y = top + 20 + (best_max - stat["best_score_at_epoch_end"]) / (best_max - best_min) * (chart_h - 70)
        line_points.append((cx, best_y))
        parts.append(f'<text x="{cx:.1f}" y="{best_y - 14:.1f}" text-anchor="middle" class="small">{stat["best_score_at_epoch_end"]:.3f}</text>')

    parts.append(polyline(line_points, COLORS["blue"], 3.2))
    for x, y in line_points:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{COLORS["blue"]}" stroke="#ffffff" stroke-width="2"/>')

    parts.append(f'<rect x="{left + 540}" y="{height - 68}" width="16" height="16" rx="3" fill="{COLORS["green"]}"/>')
    parts.append(f'<text x="{left + 562}" y="{height - 55}" class="legend">accepted</text>')
    parts.append(f'<rect x="{left + 650}" y="{height - 68}" width="16" height="16" rx="3" fill="{COLORS["red"]}" opacity="0.83"/>')
    parts.append(f'<text x="{left + 672}" y="{height - 55}" class="legend">rejected</text>')
    parts.append(f'<line x1="{left + 755}" y1="{height - 60}" x2="{left + 785}" y2="{height - 60}" stroke="{COLORS["blue"]}" stroke-width="3"/>')
    parts.append(f'<text x="{left + 795}" y="{height - 55}" class="legend">epoch-end best</text>')
    write_svg(path, width, height, "\n".join(parts))


def chart_token_usage(path: Path, summary: dict[str, Any]) -> None:
    width, height = 1100, 610
    left, top = 250, 110
    bar_w, bar_h = 730, 34
    rows = [
        (name, value)
        for name, value in summary["token_summary"].items()
        if name != "_total"
    ]
    rows.sort(key=lambda item: item[1]["total_tokens"], reverse=True)
    total = summary["token_summary"]["_total"]["total_tokens"]
    total_calls = summary["token_summary"]["_total"]["calls"]
    parts = [
        f'<text x="70" y="42" class="title">Token usage by pipeline stage</text>',
        f'<text x="70" y="68" class="subtitle">Total {total:,} tokens across {total_calls:,} calls. Rollout dominates both tokens and calls.</text>',
        f'<rect x="60" y="92" width="{width - 120}" height="{height - 145}" rx="12" fill="{COLORS["panel"]}" stroke="{COLORS["grid"]}"/>',
    ]
    max_pct = max(value["total_tokens"] / total for _, value in rows)
    for idx, (name, value) in enumerate(rows):
        y = top + idx * 66
        pct = value["total_tokens"] / total
        calls_pct = value["calls"] / total_calls
        w = max(8, pct / max_pct * bar_w)
        color = [COLORS["blue"], COLORS["orange"], COLORS["purple"], COLORS["teal"], COLORS["amber"], COLORS["green"]][idx % 6]
        parts.append(f'<text x="{left - 18}" y="{y + 24}" text-anchor="end" class="label">{html.escape(name)}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bar_w}" height="{bar_h}" rx="8" fill="#e5e7eb"/>')
        parts.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="8" fill="{color}"/>')
        label_x = left + min(w + 12, bar_w - 120)
        parts.append(
            f'<text x="{label_x:.1f}" y="{y + 23}" class="label">{fmt_pct(pct)} tokens, {fmt_pct(calls_pct)} calls</text>'
        )
        parts.append(f'<text x="{left}" y="{y + 52}" class="small">{value["total_tokens"]:,} tokens; {value["calls"]:,} calls</text>')
    write_svg(path, width, height, "\n".join(parts))


def chart_test_migration(path: Path, migration: dict[str, Any]) -> None:
    width, height = 920, 620
    left, top = 205, 145
    cell = 210
    counts = migration["counts"]
    total = migration["total"]
    cells = [
        ("baseline correct", "best correct", counts["both_correct"], COLORS["green"]),
        ("baseline correct", "best wrong", counts["regressed"], COLORS["red"]),
        ("baseline wrong", "best correct", counts["improved"], COLORS["blue"]),
        ("baseline wrong", "best wrong", counts["both_wrong"], COLORS["slate"]),
    ]
    lookup = {
        (0, 0): cells[0],
        (1, 0): cells[1],
        (0, 1): cells[2],
        (1, 1): cells[3],
    }
    net = counts["improved"] - counts["regressed"]
    parts = [
        f'<text x="70" y="42" class="title">Test-set answer migration</text>',
        f'<text x="70" y="68" class="subtitle">Best skill fixes {counts["improved"]} baseline errors and introduces {counts["regressed"]} new errors, net +{net} exact answers.</text>',
        f'<rect x="62" y="96" width="{width - 124}" height="{height - 150}" rx="12" fill="{COLORS["panel"]}" stroke="{COLORS["grid"]}"/>',
        f'<text x="{left + cell}" y="{top - 70}" text-anchor="middle" class="label">Best skill result</text>',
        f'<text x="{left + cell / 2}" y="{top - 30}" text-anchor="middle" class="axis">correct</text>',
        f'<text x="{left + 1.5 * cell}" y="{top - 30}" text-anchor="middle" class="axis">wrong</text>',
        f'<text x="{left - 95}" y="{top + cell}" transform="rotate(-90 {left - 95},{top + cell})" text-anchor="middle" class="label">Initial skill result</text>',
        f'<text x="{left - 28}" y="{top + cell / 2 + 5}" text-anchor="end" class="axis">correct</text>',
        f'<text x="{left - 28}" y="{top + 1.5 * cell + 5}" text-anchor="end" class="axis">wrong</text>',
    ]
    for row in range(2):
        for col in range(2):
            _, _, count, color = lookup[(col, row)]
            x = left + col * cell
            y = top + row * cell
            opacity = 0.88 if count else 0.2
            parts.append(f'<rect x="{x}" y="{y}" width="{cell - 12}" height="{cell - 12}" rx="14" fill="{color}" opacity="{opacity}"/>')
            parts.append(f'<text x="{x + (cell - 12) / 2}" y="{y + 82}" text-anchor="middle" font-size="36" font-weight="700" style="fill:#ffffff">{count}</text>')
            parts.append(f'<text x="{x + (cell - 12) / 2}" y="{y + 118}" text-anchor="middle" font-size="18" style="fill:#ffffff">{count / total * 100:.1f}%</text>')
    parts.append(f'<text x="{left}" y="{height - 52}" class="small">Aligned by 1,400 shared SearchQA ids from baseline and best-skill test outputs.</text>')
    write_svg(path, width, height, "\n".join(parts))


def chart_rollout_vs_selection(path: Path, history: list[dict[str, Any]]) -> None:
    width, height = 900, 650
    left, right, top, bottom = 92, 50, 100, 88
    chart_w = width - left - right
    chart_h = height - top - bottom
    xs = [row["rollout_hard"] for row in history]
    ys = [row["selection_hard"] for row in history]
    r = pearson(xs, ys)
    x_min, x_max = 0.80, 0.95
    y_min, y_max = 0.80, 0.88

    def sx(x: float) -> float:
        return left + (x - x_min) / (x_max - x_min) * chart_w

    def sy(y: float) -> float:
        return top + (y_max - y) / (y_max - y_min) * chart_h

    parts = [
        f'<text x="{left}" y="42" class="title">Train-batch score vs validation score</text>',
        f'<text x="{left}" y="68" class="subtitle">Pearson r = {r:.2f}: batch rollout accuracy is only a weak predictor of validation gain.</text>',
        f'<rect x="{left}" y="{top}" width="{chart_w}" height="{chart_h}" rx="10" fill="{COLORS["panel"]}" stroke="{COLORS["grid"]}"/>',
    ]
    for xt in [0.80, 0.85, 0.90, 0.95]:
        x = sx(xt)
        parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + chart_h}" stroke="{COLORS["grid"]}"/>')
        parts.append(f'<text x="{x:.1f}" y="{top + chart_h + 26}" text-anchor="middle" class="axis">{xt:.2f}</text>')
    for yt in [0.80, 0.82, 0.84, 0.86, 0.88]:
        y = sy(yt)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_w}" y2="{y:.1f}" stroke="{COLORS["grid"]}"/>')
        parts.append(f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{yt:.2f}</text>')
    parts.append(f'<text x="{left + chart_w / 2}" y="{height - 30}" text-anchor="middle" class="label">train batch hard</text>')
    parts.append(f'<text x="28" y="{top + chart_h / 2}" transform="rotate(-90 28,{top + chart_h / 2})" text-anchor="middle" class="label">validation hard</text>')
    for row in history:
        accepted = str(row["action"]).startswith("accept")
        color = COLORS["green"] if accepted else COLORS["red"]
        radius = 8 if accepted else 6
        opacity = 0.9 if accepted else 0.55
        x, y = sx(row["rollout_hard"]), sy(row["selection_hard"])
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{color}" opacity="{opacity}" stroke="#ffffff" stroke-width="1.5"/>')
        if accepted:
            parts.append(f'<text x="{x:.1f}" y="{y - 13:.1f}" text-anchor="middle" class="small">{row["step"]}</text>')
    parts.append(f'<circle cx="{left + 540}" cy="{height - 56}" r="6" fill="{COLORS["green"]}" opacity="0.9"/>')
    parts.append(f'<text x="{left + 554}" y="{height - 51}" class="legend">accepted</text>')
    parts.append(f'<circle cx="{left + 645}" cy="{height - 56}" r="6" fill="{COLORS["red"]}" opacity="0.55"/>')
    parts.append(f'<text x="{left + 659}" y="{height - 51}" class="legend">rejected</text>')
    write_svg(path, width, height, "\n".join(parts))


def chart_runtime(path: Path, history: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    width, height = 1180, 650
    left, right, top, bottom = 85, 45, 105, 85
    chart_w = width - left - right
    chart_h = height - top - bottom
    max_wall = max(row["wall_time_s"] for row in history)
    parts = [
        f'<text x="{left}" y="42" class="title">Wall time per training step</text>',
        f'<text x="{left}" y="68" class="subtitle">Total run wall time {summary["total_wall_time_s"] / 60:.1f} minutes; slow steps are usually evaluation or aggregation tails.</text>',
        f'<rect x="{left}" y="{top}" width="{chart_w}" height="{chart_h}" rx="10" fill="{COLORS["panel"]}" stroke="{COLORS["grid"]}"/>',
    ]

    def sx(step: float) -> float:
        return left + (step - 1) / 39 * chart_w

    def sy(seconds: float) -> float:
        return top + (max_wall - seconds) / max_wall * (chart_h - 28)

    for tick in [0, 100, 200, 300, 400]:
        if tick > max_wall + 20:
            continue
        y = sy(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_w}" y2="{y:.1f}" stroke="{COLORS["grid"]}"/>')
        parts.append(f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{tick}s</text>')
    for step in range(1, 41, 5):
        x = sx(step)
        parts.append(f'<text x="{x:.1f}" y="{top + chart_h + 25}" text-anchor="middle" class="axis">{step}</text>')

    bar_w = chart_w / 44
    for row in history:
        x = sx(row["step"]) - bar_w / 2
        y = sy(row["wall_time_s"])
        h = top + chart_h - y
        accepted = str(row["action"]).startswith("accept")
        color = COLORS["green"] if accepted else COLORS["blue"]
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="3" fill="{color}" opacity="0.82"/>')
        if row["wall_time_s"] >= 300 or accepted and row["step"] in {1, 37}:
            parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" class="small">{row["step"]}</text>')

    phase_totals: Counter[str] = Counter()
    for row in history:
        for name, value in row.get("timing", {}).items():
            phase_totals[name] += float(value)
    phase_rows = phase_totals.most_common()
    box_x, box_y = left + 735, top + 26
    parts.append(f'<rect x="{box_x}" y="{box_y}" width="300" height="205" rx="10" fill="#f8fafc" stroke="{COLORS["grid"]}"/>')
    parts.append(f'<text x="{box_x + 18}" y="{box_y + 28}" class="label">Step-loop timing totals</text>')
    max_phase = max(v for _, v in phase_rows)
    for idx, (name, seconds) in enumerate(phase_rows[:6]):
        y = box_y + 52 + idx * 24
        w = seconds / max_phase * 150
        parts.append(f'<text x="{box_x + 18}" y="{y + 10}" class="small">{name.replace("_s", "")}</text>')
        parts.append(f'<rect x="{box_x + 118}" y="{y}" width="{w:.1f}" height="13" rx="3" fill="{COLORS["orange"]}" opacity="0.80"/>')
        parts.append(f'<text x="{box_x + 276}" y="{y + 10}" text-anchor="end" class="small">{seconds / 60:.1f}m</text>')
    write_svg(path, width, height, "\n".join(parts))


def _step_completion_effect_rows(
    history: list[dict[str, Any]],
    summary: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    prev_current = float(summary["baseline_selection_hard"])
    for row in history:
        completion_tokens = sum(
            int(values.get("completion_tokens", 0))
            for values in row.get("tokens", {}).values()
        )
        prompt_tokens = sum(
            int(values.get("prompt_tokens", 0))
            for values in row.get("tokens", {}).values()
        )
        selection_hard = float(row["selection_hard"])
        effect = selection_hard - prev_current
        accepted = str(row["action"]).startswith("accept")
        rows.append(
            {
                "step": int(row["step"]),
                "completion_tokens": completion_tokens,
                "prompt_tokens": prompt_tokens,
                "selection_hard": selection_hard,
                "prev_current_hard": prev_current,
                "effect": effect,
                "accepted": accepted,
                "action": row["action"],
            }
        )
        if accepted:
            prev_current = selection_hard
    return rows


def chart_completion_tokens_vs_effect(
    path: Path,
    history: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    rows = _step_completion_effect_rows(history, summary)
    xs = [row["completion_tokens"] for row in rows]
    ys = [row["effect"] for row in rows]
    r = pearson(xs, ys)
    accepted_rows = [row for row in rows if row["accepted"]]
    rejected_rows = [row for row in rows if not row["accepted"]]
    accepted_mean = statistics.mean(row["completion_tokens"] for row in accepted_rows)
    rejected_mean = statistics.mean(row["completion_tokens"] for row in rejected_rows)

    width, height = 1050, 680
    left, right, top, bottom = 110, 58, 105, 100
    chart_w = width - left - right
    chart_h = height - top - bottom
    x_min = math.floor((min(xs) - 600) / 1000) * 1000
    x_max = math.ceil((max(xs) + 600) / 1000) * 1000
    y_min = -0.03
    y_max = 0.075

    def sx(value: float) -> float:
        return left + (value - x_min) / (x_max - x_min) * chart_w

    def sy(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * chart_h

    parts = [
        f'<text x="{left}" y="42" class="title">Output tokens vs skill effect</text>',
        f'<text x="{left}" y="68" class="subtitle">Only completion/output tokens are counted. More generated text did not translate into better candidate skills.</text>',
        f'<rect x="{left}" y="{top}" width="{chart_w}" height="{chart_h}" rx="10" fill="{COLORS["panel"]}" stroke="{COLORS["grid"]}"/>',
    ]

    for tick in range(x_min, x_max + 1, 3000):
        x = sx(tick)
        parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + chart_h}" stroke="{COLORS["grid"]}"/>')
        parts.append(f'<text x="{x:.1f}" y="{top + chart_h + 26}" text-anchor="middle" class="axis">{tick // 1000}k</text>')

    for tick in [-0.025, 0.0, 0.025, 0.05, 0.075]:
        y = sy(tick)
        stroke = COLORS["slate"] if abs(tick) < 1e-12 else COLORS["grid"]
        width_attr = 2 if abs(tick) < 1e-12 else 1
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_w}" y2="{y:.1f}" stroke="{stroke}" stroke-width="{width_attr}"/>')
        label = f"{tick * 100:+.1f} pp"
        parts.append(f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{label}</text>')

    for row in rows:
        x = sx(row["completion_tokens"])
        y = sy(row["effect"])
        color = COLORS["green"] if row["accepted"] else COLORS["red"]
        radius = 8 if row["accepted"] else 6
        opacity = 0.92 if row["accepted"] else 0.58
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{color}" opacity="{opacity}" stroke="#ffffff" stroke-width="1.6"/>')
        if row["accepted"] or row["step"] in {6, 10, 39, 40}:
            label_y = y - 12 if row["effect"] >= 0 else y + 22
            parts.append(f'<text x="{x:.1f}" y="{label_y:.1f}" text-anchor="middle" class="small">{row["step"]}</text>')

    mean_y = top + 30
    parts.append(f'<line x1="{sx(accepted_mean):.1f}" y1="{top}" x2="{sx(accepted_mean):.1f}" y2="{top + chart_h}" stroke="{COLORS["green"]}" stroke-width="2" stroke-dasharray="6 6"/>')
    parts.append(f'<line x1="{sx(rejected_mean):.1f}" y1="{top}" x2="{sx(rejected_mean):.1f}" y2="{top + chart_h}" stroke="{COLORS["red"]}" stroke-width="2" stroke-dasharray="6 6"/>')
    parts.append(f'<text x="{sx(accepted_mean):.1f}" y="{mean_y}" text-anchor="middle" class="small">accept mean {accepted_mean / 1000:.1f}k</text>')
    parts.append(f'<text x="{sx(rejected_mean):.1f}" y="{mean_y + 20}" text-anchor="middle" class="small">reject mean {rejected_mean / 1000:.1f}k</text>')

    box_x, box_y = left + chart_w - 300, top + chart_h - 132
    parts.append(f'<rect x="{box_x}" y="{box_y}" width="270" height="96" rx="10" fill="#f8fafc" stroke="{COLORS["grid"]}"/>')
    parts.append(f'<text x="{box_x + 16}" y="{box_y + 26}" class="label">Correlation r = {r:.2f}</text>')
    parts.append(f'<text x="{box_x + 16}" y="{box_y + 50}" class="small">x: output tokens only</text>')
    parts.append(f'<text x="{box_x + 16}" y="{box_y + 72}" class="small">y: candidate hard minus prior current</text>')

    parts.append(f'<text x="{left + chart_w / 2}" y="{height - 36}" text-anchor="middle" class="label">completion tokens per step (prompt/input tokens excluded)</text>')
    parts.append(f'<text x="30" y="{top + chart_h / 2}" transform="rotate(-90 30,{top + chart_h / 2})" text-anchor="middle" class="label">candidate effect on validation hard</text>')
    parts.append(f'<circle cx="{left + 660}" cy="{height - 66}" r="6" fill="{COLORS["green"]}" opacity="0.92"/>')
    parts.append(f'<text x="{left + 674}" y="{height - 61}" class="legend">accepted</text>')
    parts.append(f'<circle cx="{left + 760}" cy="{height - 66}" r="6" fill="{COLORS["red"]}" opacity="0.58"/>')
    parts.append(f'<text x="{left + 774}" y="{height - 61}" class="legend">rejected</text>')
    write_svg(path, width, height, "\n".join(parts))


def chart_edit_dynamics(path: Path, history: list[dict[str, Any]]) -> None:
    width, height = 1080, 620
    left, right, top, bottom = 85, 60, 95, 85
    chart_w = width - left - right
    chart_h = height - top - bottom
    max_len = max(row["skill_len"] for row in history)
    max_edits = max(row["n_edits_ranked"] for row in history)

    def sx(step: float) -> float:
        return left + (step - 1) / 39 * chart_w

    def sy_len(value: float) -> float:
        return top + (max_len - value) / max_len * (chart_h - 20)

    parts = [
        f'<text x="{left}" y="42" class="title">Skill growth and edit budget</text>',
        f'<text x="{left}" y="68" class="subtitle">The skill grows early, then late accepts come from fewer selected edits under a smaller budget.</text>',
        f'<rect x="{left}" y="{top}" width="{chart_w}" height="{chart_h}" rx="10" fill="{COLORS["panel"]}" stroke="{COLORS["grid"]}"/>',
    ]
    for tick in [0, 4000, 8000, 12000, 16000]:
        if tick > max_len + 3000:
            continue
        y = sy_len(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_w}" y2="{y:.1f}" stroke="{COLORS["grid"]}"/>')
        parts.append(f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{tick // 1000}k</text>')
    for step in range(1, 41, 5):
        x = sx(step)
        parts.append(f'<text x="{x:.1f}" y="{top + chart_h + 25}" text-anchor="middle" class="axis">{step}</text>')

    len_points = [(sx(row["step"]), sy_len(row["skill_len"])) for row in history]
    parts.append(polyline(len_points, COLORS["blue"], 3.2))
    for row in history:
        x = sx(row["step"])
        y0 = top + chart_h
        h = row["n_edits_ranked"] / max_edits * 82
        color = COLORS["green"] if str(row["action"]).startswith("accept") else COLORS["orange"]
        parts.append(f'<rect x="{x - 5:.1f}" y="{y0 - h:.1f}" width="10" height="{h:.1f}" rx="3" fill="{color}" opacity="0.72"/>')
        if str(row["action"]).startswith("accept"):
            parts.append(f'<circle cx="{x:.1f}" cy="{sy_len(row["skill_len"]):.1f}" r="5.5" fill="{COLORS["green"]}" stroke="#ffffff" stroke-width="2"/>')
    for row in history:
        if row["step"] in {1, 10, 20, 30, 40}:
            parts.append(f'<text x="{sx(row["step"]):.1f}" y="{sy_len(row["skill_len"]) - 10:.1f}" text-anchor="middle" class="small">{row["skill_len"]:,}</text>')
    parts.append(f'<text x="{left + 620}" y="{height - 50}" class="legend">blue line: accepted/current skill length; bars: selected edits per candidate</text>')
    write_svg(path, width, height, "\n".join(parts))


def build_analysis(out_root: Path) -> dict[str, Any]:
    history = read_json(out_root / "history.json")
    summary = read_json(out_root / "summary.json")
    baseline_rows = read_jsonl(out_root / "test_eval_baseline" / "results.jsonl")
    best_rows = read_jsonl(out_root / "test_eval" / "results.jsonl")
    baseline_by_id = {row["id"]: row for row in baseline_rows}
    best_by_id = {row["id"]: row for row in best_rows}
    shared_ids = sorted(set(baseline_by_id) & set(best_by_id))
    if len(shared_ids) != len(baseline_rows) or len(shared_ids) != len(best_rows):
        raise ValueError("Baseline and best test result ids do not align one-to-one")

    transition_counter: Counter[tuple[bool, bool]] = Counter()
    for item_id in shared_ids:
        transition_counter[(bool(baseline_by_id[item_id]["hard"]), bool(best_by_id[item_id]["hard"]))] += 1

    improved = [
        (item_id, baseline_by_id[item_id], best_by_id[item_id])
        for item_id in shared_ids
        if not baseline_by_id[item_id]["hard"] and best_by_id[item_id]["hard"]
    ]
    regressed = [
        (item_id, baseline_by_id[item_id], best_by_id[item_id])
        for item_id in shared_ids
        if baseline_by_id[item_id]["hard"] and not best_by_id[item_id]["hard"]
    ]
    improved.sort(key=lambda row: (len(row[1].get("question", "")), row[0]))
    regressed.sort(key=lambda row: (len(row[1].get("question", "")), row[0]))

    accepted_steps = [row["step"] for row in history if str(row["action"]).startswith("accept")]
    rejected_steps = [row["step"] for row in history if row["action"] == "reject"]
    tie_reject_steps = [
        row["step"]
        for row in history
        if row["action"] == "reject" and abs(row["selection_hard"] - row["current_score"]) < 1e-12
    ]
    rollout_hard = [row["rollout_hard"] for row in history]
    selection_hard = [row["selection_hard"] for row in history]
    total_tokens = summary["token_summary"]["_total"]["total_tokens"]
    total_calls = summary["token_summary"]["_total"]["calls"]
    token_percent = {
        name: values["total_tokens"] / total_tokens
        for name, values in summary["token_summary"].items()
        if name != "_total"
    }
    call_percent = {
        name: values["calls"] / total_calls
        for name, values in summary["token_summary"].items()
        if name != "_total"
    }
    f1_delta = [best_by_id[item_id]["f1"] - baseline_by_id[item_id]["f1"] for item_id in shared_ids]
    token_effect_rows = _step_completion_effect_rows(history, summary)
    accepted_token_effect_rows = [row for row in token_effect_rows if row["accepted"]]
    rejected_token_effect_rows = [row for row in token_effect_rows if not row["accepted"]]

    return {
        "out_root": str(out_root),
        "summary": {
            "baseline_selection_hard": summary["baseline_selection_hard"],
            "best_selection_hard": summary["best_selection_hard"],
            "baseline_test_hard": summary["baseline_test_hard"],
            "test_hard": summary["test_hard"],
            "baseline_test_soft": summary["baseline_test_soft"],
            "test_soft": summary["test_soft"],
            "test_delta_hard": summary["test_delta_hard"],
            "best_step": summary["best_step"],
            "total_steps": summary["total_steps"],
            "total_accepts": summary["total_accepts"],
            "total_rejects": summary["total_rejects"],
            "total_wall_time_s": summary["total_wall_time_s"],
            "total_tokens": total_tokens,
            "total_calls": total_calls,
        },
        "step_analysis": {
            "accepted_steps": accepted_steps,
            "rejected_steps": rejected_steps,
            "tie_reject_steps": tie_reject_steps,
            "accept_rate": len(accepted_steps) / len(history),
            "selection_hard_min": min(selection_hard),
            "selection_hard_max": max(selection_hard),
            "selection_hard_mean": statistics.mean(selection_hard),
            "rollout_selection_pearson": pearson(rollout_hard, selection_hard),
            "accepted_selection_mean": statistics.mean(row["selection_hard"] for row in history if str(row["action"]).startswith("accept")),
            "rejected_selection_mean": statistics.mean(row["selection_hard"] for row in history if row["action"] == "reject"),
            "candidate_above_initial_baseline_count": sum(
                row["selection_hard"] > summary["baseline_selection_hard"] for row in history
            ),
        },
        "token_analysis": {
            "token_percent": token_percent,
            "call_percent": call_percent,
            "completion_effect": {
                "completion_tokens_vs_effect_pearson": pearson(
                    [row["completion_tokens"] for row in token_effect_rows],
                    [row["effect"] for row in token_effect_rows],
                ),
                "completion_tokens_vs_selection_hard_pearson": pearson(
                    [row["completion_tokens"] for row in token_effect_rows],
                    [row["selection_hard"] for row in token_effect_rows],
                ),
                "accepted_completion_tokens_mean": statistics.mean(
                    row["completion_tokens"] for row in accepted_token_effect_rows
                ),
                "rejected_completion_tokens_mean": statistics.mean(
                    row["completion_tokens"] for row in rejected_token_effect_rows
                ),
                "positive_effect_steps": sum(row["effect"] > 0 for row in token_effect_rows),
                "zero_effect_steps": sum(abs(row["effect"]) < 1e-12 for row in token_effect_rows),
                "negative_effect_steps": sum(row["effect"] < 0 for row in token_effect_rows),
                "top_completion_token_steps": sorted(
                    token_effect_rows,
                    key=lambda row: row["completion_tokens"],
                    reverse=True,
                )[:8],
                "accepted_steps": [
                    {
                        "step": row["step"],
                        "completion_tokens": row["completion_tokens"],
                        "effect": row["effect"],
                    }
                    for row in accepted_token_effect_rows
                ],
            },
        },
        "migration": {
            "total": len(shared_ids),
            "counts": {
                "both_correct": transition_counter[(True, True)],
                "regressed": transition_counter[(True, False)],
                "improved": transition_counter[(False, True)],
                "both_wrong": transition_counter[(False, False)],
            },
            "soft_mean_delta": statistics.mean(f1_delta),
            "soft_improved_count": sum(delta > 0 for delta in f1_delta),
            "soft_regressed_count": sum(delta < 0 for delta in f1_delta),
            "soft_unchanged_count": sum(delta == 0 for delta in f1_delta),
            "improved_examples": [example_to_json(row) for row in improved[:8]],
            "regressed_examples": [example_to_json(row) for row in regressed[:8]],
        },
    }


def example_to_json(row: tuple[str, dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
    item_id, baseline, best = row
    return {
        "id": item_id,
        "question": baseline["question"],
        "gold_answers": best["gold_answers"],
        "baseline_prediction": baseline["predicted_answer"],
        "best_prediction": best["predicted_answer"],
        "baseline_f1": baseline["f1"],
        "best_f1": best["f1"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    args = parser.parse_args()

    out_root = args.out_root.resolve()
    figure_dir = args.figure_dir.resolve()
    history = read_json(out_root / "history.json")
    summary = read_json(out_root / "summary.json")
    analysis = build_analysis(out_root)

    chart_score_timeline(figure_dir / "score_timeline.svg", history, summary)
    chart_epoch_acceptance(figure_dir / "epoch_acceptance.svg", summary)
    chart_token_usage(figure_dir / "token_usage.svg", summary)
    chart_test_migration(figure_dir / "test_migration.svg", analysis["migration"])
    chart_rollout_vs_selection(figure_dir / "rollout_vs_selection.svg", history)
    chart_runtime(figure_dir / "runtime_by_step.svg", history, summary)
    chart_completion_tokens_vs_effect(figure_dir / "completion_tokens_vs_effect.svg", history, summary)
    chart_edit_dynamics(figure_dir / "edit_dynamics.svg", history)

    summary_path = figure_dir / "analysis_summary.json"
    summary_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote figures and analysis summary to {figure_dir}")


if __name__ == "__main__":
    main()
