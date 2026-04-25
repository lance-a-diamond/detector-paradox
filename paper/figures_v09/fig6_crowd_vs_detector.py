#!/usr/bin/env python3
"""Figure 6 for paper v0.9 — Crowd AI-call rate vs machine-detector scores.

Reads the 8 survey passages' machine-detector scores and crowd AI-call rate
from survey_results_n33.json (Section I per_passage table) and plots a 2×2 grid
of scatter plots, one per detector, with Spearman ρ in each panel.

Output: fig6_crowd_vs_detector.png
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
OUT = HERE / "fig6_crowd_vs_detector.png"
# Release layout: paper/figures_v09/ → data/ is ../../data/
RESULTS = HERE.parent.parent / "data" / "survey_results_n33.json"

DETECTORS = [
    ("pangram_api",   "Pangram"),
    ("gptzero_api",   "GPTZero"),
    ("copyleaks_api", "Copyleaks"),
    ("binoculars",    "Binoculars"),
]

COLOR_HUMAN = "#2b8a3e"   # green
COLOR_AI    = "#c92a2a"   # red


def main():
    data = json.loads(RESULTS.read_text())
    rows = data["sections"]["I_machine_linkage"]["per_passage"]

    # Sort by passage letter for consistent ordering
    rows.sort(key=lambda r: r["passage"])

    fig, axes = plt.subplots(2, 2, figsize=(11, 10), dpi=140)
    axes = axes.flatten()

    for ax, (det_key, det_label) in zip(axes, DETECTORS):
        xs, ys, labels, colors = [], [], [], []
        for r in rows:
            det = r["detectors"].get(det_key, {})
            x = det.get("ai_score")
            y = r["human_ai_call_rate"]
            if x is None or y is None:
                continue
            xs.append(x)
            ys.append(y)
            labels.append(r["passage"])
            colors.append(COLOR_HUMAN if r["truth"] == "human" else COLOR_AI)
        xs, ys = np.array(xs), np.array(ys)

        # Spearman ρ across all shown points
        rho, p = stats.spearmanr(xs, ys)

        ax.scatter(xs, ys, c=colors, s=160, edgecolor="black", linewidth=1.2, zorder=3)
        for x, y, lab in zip(xs, ys, labels):
            ax.annotate(lab, (x, y), xytext=(6, 6), textcoords="offset points",
                        fontsize=10, fontweight="bold")

        # Reference lines
        ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.7, alpha=0.6)
        ax.axvline(0.5, color="gray", linestyle="--", linewidth=0.7, alpha=0.6)

        # Trend line (OLS on rank — matches direction of Spearman)
        if len(xs) >= 2:
            slope, intercept = np.polyfit(xs, ys, 1)
            xline = np.linspace(0, 1, 50)
            ax.plot(xline, slope * xline + intercept, color="#555",
                    linestyle=":", linewidth=1.2, alpha=0.8)

        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlabel(f"{det_label} ai_score", fontsize=11)
        ax.set_ylabel("Crowd AI-call rate (n=33)", fontsize=11)
        ax.set_title(f"{det_label}  —  Spearman ρ = {rho:+.2f}  (p = {p:.3f})",
                     fontsize=12, fontweight="bold")
        ax.grid(True, alpha=0.2)

    # Legend via proxy artists
    from matplotlib.lines import Line2D
    legend_handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLOR_HUMAN,
               markeredgecolor="black", markersize=11, label="Human passage"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLOR_AI,
               markeredgecolor="black", markersize=11, label="AI passage"),
        Line2D([0], [0], linestyle="--", color="gray", label="Decision threshold (0.5)"),
    ]
    fig.suptitle(
        "Machine detectors vs. human crowd — per-passage\n"
        "(each point = one of the 8 survey passages, labeled A–H)",
        fontsize=13, fontweight="bold", y=0.98,
    )
    fig.legend(handles=legend_handles, loc="lower center", ncol=3,
               bbox_to_anchor=(0.5, 0.01), frameon=False, fontsize=11)
    plt.subplots_adjust(top=0.90, bottom=0.09, left=0.08, right=0.97, hspace=0.30, wspace=0.25)

    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
