#!/usr/bin/env python3
"""Figure 7 — Reader-perceived quality per passage (n = 37).

Horizontal bar chart of composite quality ratings across all 8 survey passages,
ordered by quality (highest → lowest), colored by ground truth (human vs AI),
with machine-detector scores annotated to the right of each bar.

Visualizes the survey's central finding: the persona-engineered AI baseline
(Passage H) rates highest quality in the study, while three of four
cross-model outputs rate lowest — with machine detector scores inverted
relative to that ordering.

Output: fig7_reader_quality_per_passage.png
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "fig7_reader_quality_per_passage.png"
# Release layout: paper/figures_v09/ → data/ is ../../data/
RESULTS = HERE.parent.parent / "data" / "survey_results_n33.json"

# Human-readable source labels
SOURCE_LABELS = {
    "A": "Brandur / Stripe",
    "B": "Surgical v10.2",
    "C": "Cross-model v2",
    "D": "Brooker / AWS",
    "E": "Cross-model v2",
    "F": "Olah / colah",
    "G": "Cross-model v2",
    "H": "Persona (Dana)",
}

C_HUMAN = "#2b8a3e"
C_AI    = "#c92a2a"


def main():
    data = json.loads(RESULTS.read_text())
    rows = data["sections"]["J_quality_correlations"]["per_passage_table"]
    n_filtered = data["meta"]["n_kept"]

    # Sort by composite quality descending
    rows = sorted(rows, key=lambda r: r["composite_quality_mean"] or 0, reverse=True)

    passages = [r["passage"] for r in rows]
    truths = [r["truth"] for r in rows]
    sources = [SOURCE_LABELS[r["passage"]] for r in rows]
    quality = [r["composite_quality_mean"] for r in rows]
    colors = [C_HUMAN if t == "human" else C_AI for t in truths]

    # Detector score summary per row (best and worst)
    detector_lines = []
    for r in rows:
        scores = {
            "Pan": r.get("pangram_api"),
            "GPT": r.get("gptzero_api"),
            "CL":  r.get("copyleaks_api"),
            "Bin": r.get("binoculars"),
        }
        # Compact string: mean score, or flag if all high
        parts = []
        for name, v in scores.items():
            if v is None:
                continue
            parts.append(f"{name}={v:.2f}")
        detector_lines.append("  ".join(parts))

    # ---- Figure ----
    fig, ax = plt.subplots(figsize=(12.5, 7), dpi=140)

    y_pos = np.arange(len(rows))[::-1]   # highest quality at top
    bars = ax.barh(y_pos, quality, color=colors, edgecolor="black",
                   linewidth=1.0, height=0.65, zorder=3)

    # Reference line: human baseline mean (across 3 human passages)
    human_mean = np.mean([q for q, t in zip(quality, truths) if t == "human"])
    ai_mean    = np.mean([q for q, t in zip(quality, truths) if t == "ai"])
    ax.axvline(human_mean, color=C_HUMAN, linestyle="--", linewidth=1.5, alpha=0.7, zorder=2)
    ax.axvline(ai_mean,    color=C_AI,    linestyle="--", linewidth=1.5, alpha=0.7, zorder=2)

    # Annotate reference lines
    ax.text(human_mean, len(rows) + 0.05, f" Human mean\n {human_mean:.2f}",
            ha="center", va="bottom", fontsize=9, color=C_HUMAN, fontweight="bold")
    ax.text(ai_mean, -0.85, f" AI mean\n {ai_mean:.2f}",
            ha="center", va="top", fontsize=9, color=C_AI, fontweight="bold")

    # Left-aligned passage label + source inside or beside bar
    for i, (yp, r) in enumerate(zip(y_pos, rows)):
        passage_label = f"Passage {r['passage']}"
        source_label = SOURCE_LABELS[r["passage"]]
        qv = r["composite_quality_mean"]
        # Main label inside the bar (white on colored bar)
        ax.text(0.08, yp, f"{passage_label}  —  {source_label}",
                va="center", ha="left", fontsize=10.5, color="white",
                fontweight="bold")
        # Quality value at end of bar
        ax.text(qv + 0.03, yp, f"{qv:.2f}", va="center", ha="left",
                fontsize=10.5, fontweight="bold", color="black")
        # Detector scores further right
        ax.text(qv + 0.28, yp, detector_lines[i],
                va="center", ha="left", fontsize=9.0,
                color="#555", family="monospace")

    # Axes
    ax.set_yticks([])
    ax.set_xlim(0, 5.4)
    ax.set_xticks(np.arange(0, 5.1, 0.5))
    ax.set_xlabel("Composite perceived quality  "
                  "(mean of clarity, engagement, authority, overall quality; 1–5 scale)",
                  fontsize=11)
    ax.set_ylim(-1.1, len(rows) + 0.3)
    ax.grid(True, axis="x", alpha=0.2)
    ax.set_axisbelow(True)
    ax.set_facecolor("#fafafa")

    # Title
    fig.suptitle("Reader-perceived quality, by passage",
                 fontsize=15, fontweight="bold", y=0.99)
    ax.set_title(
        f"n = {n_filtered} (pre-registered exclusion applied); "
        "machine-detector scores shown at right  (Pan / GPT / CL / Bin, ai_score 0–1)",
        fontsize=10, pad=28, color="#333",
    )

    # Legend
    from matplotlib.patches import Patch
    handles = [
        Patch(facecolor=C_HUMAN, edgecolor="black", label="Human-written passage"),
        Patch(facecolor=C_AI, edgecolor="black", label="AI-generated passage"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=10,
              framealpha=0.95)

    plt.subplots_adjust(top=0.86, bottom=0.10, left=0.04, right=0.98)
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
