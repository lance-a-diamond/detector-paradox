#!/usr/bin/env python3
"""Figure 1 hero — The Detector Paradox in One Picture.

Shows three trajectories across the cumulative humanization pipeline
(Dana → v10.2 → 3-way v2):

    1. Detector evasion (1 − mean ai_score across 4 detectors)  — rises
    2. Linguistic convergence to human baselines                 — rises (or holds)
    3. Reader-perceived composite quality (survey, /5)           — falls

The visual story: two objective-metric lines go up (engineering succeeds),
one reader-perception line goes down (what we lose in the process).

Output: fig1_hero_paradox.png
Replaces: fig1_paradox.png (old "Linguistic Quality vs Detection Avoidance" scatter)
"""
import json
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "fig1_hero_paradox.png"
# Release layout: paper/figures_v09/ → repo root is two parents up
_REPO_ROOT = HERE.parent.parent
DB = _REPO_ROOT / "data" / "humanization.db"
SURVEY_RESULTS = _REPO_ROOT / "data" / "survey_results_n33.json"

# Pipeline stage → (label, DB label pattern, survey condition)
STAGES = [
    ("Dana\n(persona baseline)",   "%dana_baseline",                       "persona_dana"),
    ("v10.2\n(surgical)",           "%v10_2",                               "humanized_fnword"),
    ("3-way v2\n(cross-model)",     "%3way_v2",                             "crossmodel"),
]
# Dana pattern also needs: scribe_persona_opus_t1
# v10.2 pattern needs exclusion of v10_2_1

DETECTORS = ["pangram_api", "gptzero_api", "copyleaks_api", "binoculars"]

# Linguistic metrics we average convergence across. Chosen as the ones paper discusses.
LING_METRICS = [
    ("first_person_per_1k",        "linguistic_features"),
    ("fpp_per_1k",                 "linguistic_features"),
    ("contractions_per_1k",        "linguistic_features"),
    ("em_dashes_per_1k",           "linguistic_features"),
    ("hedging_per_1k",             "linguistic_features"),
    ("sent_mean_len",              "linguistic_features"),
    ("burstiness",                 "linguistic_features"),
    ("type_token_ratio",           "linguistic_features"),
    ("very_short_pct",             "linguistic_features"),
    ("very_long_pct",              "linguistic_features"),
    ("density_variance",           "info_theoretic_features"),
    ("redundancy_mean",            "info_theoretic_features"),
    ("consecutive_similarity_mean", "info_theoretic_features"),
]

HUMAN_LABELS = (
    "brandur_stripe_idempotency", "cockroach_parallel_commits",
    "brooker_backoff_jitter_2015", "hudson_go_gc_journey_2018",
    "srivastav_bloom_filters_2014", "olah_backprop_2015",
)


def group_where(stage_pattern: str) -> str:
    # Wrap every clause in parentheses so composition with AND r.detector = ?
    # doesn't trip SQL operator precedence (AND binds tighter than OR).
    if stage_pattern == "%dana_baseline":
        return "(s.label LIKE '%dana_baseline' OR s.label = 'scribe_persona_opus_t1')"
    if stage_pattern == "%v10_2":
        return "(s.label LIKE '%v10_2' AND s.label NOT LIKE '%v10_2_1')"
    if stage_pattern == "%3way_v2":
        return "(s.label LIKE '%3way_v2')"
    return "(0)"


def fetch_metric_mean(conn, where_clause: str, table: str, col: str) -> float | None:
    cur = conn.cursor()
    q = f"""
        SELECT AVG(t.{col})
        FROM samples s JOIN {table} t ON t.sample_id = s.id
        WHERE {where_clause}
    """
    cur.execute(q)
    row = cur.fetchone()
    return float(row[0]) if row and row[0] is not None else None


def fetch_detector_mean(conn, where_clause: str, detector: str) -> float | None:
    cur = conn.cursor()
    q = f"""
        SELECT AVG(r.ai_score)
        FROM samples s JOIN detector_runs r ON r.sample_id = s.id
        WHERE {where_clause} AND r.detector = ?
    """
    cur.execute(q, (detector,))
    row = cur.fetchone()
    return float(row[0]) if row and row[0] is not None else None


def fetch_human_mean(conn, table: str, col: str) -> float:
    cur = conn.cursor()
    placeholders = ",".join("?" * len(HUMAN_LABELS))
    q = f"""
        SELECT AVG(t.{col})
        FROM samples s JOIN {table} t ON t.sample_id = s.id
        WHERE s.label IN ({placeholders})
    """
    cur.execute(q, HUMAN_LABELS)
    return float(cur.fetchone()[0])


def compute_detector_evasion(conn, where_clause: str) -> float:
    """1 − mean ai_score across 4 detectors. Higher = better evasion."""
    scores = [fetch_detector_mean(conn, where_clause, d) for d in DETECTORS]
    scores = [s for s in scores if s is not None]
    return 1.0 - (sum(scores) / len(scores))


def compute_linguistic_convergence(conn, where_clause: str,
                                   dana_where: str,
                                   threshold: float = 0.30) -> float:
    """Fraction of linguistic metrics where the pipeline mean lies within
    ±threshold × |human| of the human baseline mean.

    Pipeline-agnostic (doesn't reference Dana starting point), stable against
    metrics where Dana is already at human. Interpretation: "X% of our
    tracked metrics are statistically close to the human baseline."
    """
    within = 0
    total = 0
    for col, table in LING_METRICS:
        p = fetch_metric_mean(conn, where_clause, table, col)
        h = fetch_human_mean(conn, table, col)
        if p is None or h is None:
            continue
        if abs(h) < 1e-9:
            # Metric with ~zero human mean (e.g. em-dashes) — accept absolute closeness
            total += 1
            if abs(p) < 1e-6 or abs(p - h) < 0.5:
                within += 1
            continue
        total += 1
        if abs(p - h) / abs(h) <= threshold:
            within += 1
    return within / total if total else 0.0


def compute_reader_quality(survey_data: dict, condition: str) -> float:
    rows = survey_data["sections"]["J_quality_correlations"]["per_passage_table"]
    vals = [r["composite_quality_mean"] for r in rows
            if r["condition"] == condition and r["composite_quality_mean"] is not None]
    if not vals:
        return float("nan")
    return (sum(vals) / len(vals)) / 5.0  # normalize to [0, 1]


def main():
    conn = sqlite3.connect(str(DB))
    try:
        survey = json.loads(SURVEY_RESULTS.read_text())
        dana_where = group_where("%dana_baseline")

        evasion = []
        convergence = []
        quality = []
        labels = []
        for label, patt, cond in STAGES:
            w = group_where(patt)
            evasion.append(compute_detector_evasion(conn, w))
            convergence.append(compute_linguistic_convergence(conn, w, dana_where))
            quality.append(compute_reader_quality(survey, cond))
            labels.append(label)

        # Human reference
        human_evasion = compute_detector_evasion(conn, f"s.label IN {HUMAN_LABELS}")
        human_quality = compute_reader_quality(survey, "human")
    finally:
        conn.close()

    # ---- Figure ----
    fig, ax = plt.subplots(figsize=(11, 7), dpi=140)

    x = np.arange(len(STAGES))

    # Colors
    C_DETECT = "#1c7ed6"    # blue — objective, good direction up
    C_LING   = "#7048e8"    # purple — objective, good direction up
    C_QUAL   = "#e03131"    # red — subjective, actual direction down

    # Plot lines
    ax.plot(x, evasion,     marker="o", markersize=12, linewidth=3,
            color=C_DETECT, label="Detector evasion  (1 − mean AI score)",
            zorder=3)
    ax.plot(x, convergence, marker="s", markersize=12, linewidth=3,
            color=C_LING,   label="Linguistic convergence  (frac. of metrics within ±30% of human)",
            zorder=3)
    ax.plot(x, quality,     marker="D", markersize=12, linewidth=3,
            color=C_QUAL,   label="Reader-perceived quality  (survey composite, /5)",
            zorder=3)

    # Annotate values
    for xi, y in zip(x, evasion):
        ax.annotate(f"{y:.2f}", (xi, y), xytext=(0, 14), textcoords="offset points",
                    ha="center", fontsize=10, color=C_DETECT, fontweight="bold")
    for xi, y in zip(x, convergence):
        ax.annotate(f"{y:.2f}", (xi, y), xytext=(0, 14), textcoords="offset points",
                    ha="center", fontsize=10, color=C_LING, fontweight="bold")
    for xi, y in zip(x, quality):
        ax.annotate(f"{y:.2f}", (xi, y), xytext=(0, -20), textcoords="offset points",
                    ha="center", fontsize=10, color=C_QUAL, fontweight="bold")

    # Human reference lines
    ax.axhline(human_quality, color=C_QUAL, linestyle=":", linewidth=1.5, alpha=0.6)
    ax.annotate(f"Human baseline reader-quality = {human_quality:.2f}",
                xy=(len(STAGES) - 1, human_quality), xytext=(-10, 8),
                textcoords="offset points", ha="right", fontsize=9, color=C_QUAL,
                style="italic", alpha=0.9)
    ax.axhline(human_evasion, color=C_DETECT, linestyle=":", linewidth=1.5, alpha=0.6)
    ax.annotate(f"Human baseline detector-evasion = {human_evasion:.2f}",
                xy=(len(STAGES) - 1, human_evasion), xytext=(-10, -14),
                textcoords="offset points", ha="right", fontsize=9, color=C_DETECT,
                style="italic", alpha=0.9)

    # Axes
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("Normalized score  (0 → 1)", fontsize=12)
    ax.set_ylim(-0.05, 1.15)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.grid(True, axis="y", alpha=0.25)
    ax.set_axisbelow(True)

    # Pipeline-direction arrow along the top
    ax.annotate("", xy=(len(STAGES) - 0.7, 1.12), xytext=(0.3, 1.12),
                arrowprops=dict(arrowstyle="->", color="#555", lw=1.5))
    ax.text((len(STAGES) - 1) / 2, 1.12, "  increasing detector-evasion engineering  ",
            ha="center", va="center", fontsize=10, color="#333",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.9), style="italic")

    # Title + subtitle
    fig.suptitle("The Detector Paradox, in one picture",
                 fontsize=15, fontweight="bold", y=0.99)
    ax.set_title(
        "Every objective target we optimized was largely achieved — "
        "reader-perceived quality declined at every stage anyway",
        fontsize=11, pad=14, color="#333",
    )

    # Legend — lower right; the 3-way-v2 column's lowest point is at y≈0.46,
    # so anchoring below that avoids overlapping any data.
    ax.legend(loc="lower right", fontsize=10, framealpha=0.95,
              bbox_to_anchor=(0.985, 0.03))

    plt.subplots_adjust(top=0.86, bottom=0.12, left=0.08, right=0.97)
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
