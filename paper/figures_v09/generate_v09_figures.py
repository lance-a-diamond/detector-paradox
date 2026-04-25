#!/usr/bin/env python3
"""Generate all 5 figures for paper v0.9 — The Detector Paradox.

Figure 1: The Paradox (quality vs detection scatter)
Figure 2: Detector Disagreement (grouped bars, 4 detectors × 4 groups)
Figure 3: Information Density Variance (box plots)
Figure 4: Convergence Profile (radar chart)
Figure 5: Voice Degradation Under Cross-Model Mixing (ratio-to-human bars)
"""
import json
import sqlite3
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

import os as _os
from pathlib import Path as _Path
# Release layout: paper/figures_v09/ → data/ is ../../data/
_HERE = _Path(__file__).resolve().parent
DB = str(_HERE.parent.parent / "data" / "humanization.db")
OUT = str(_HERE)

GROUPS = {
    'human': """label IN ('brandur_stripe_idempotency','cockroach_parallel_commits',
        'brooker_backoff_jitter_2015','hudson_go_gc_journey_2018',
        'srivastav_bloom_filters_2014','olah_backprop_2015')""",
    'dana': """label LIKE '%dana_baseline' OR label = 'scribe_persona_opus_t1'""",
    'v10.2': """label LIKE '%v10_2' AND label NOT LIKE '%v10_2_1'""",
    '3way_v1': """label LIKE '%_3way' AND label NOT LIKE '%_3way_v2'""",
    '3way_v2': """label LIKE '%3way_v2'""",
}

# Colors
C_HUMAN = '#2ecc71'
C_DANA = '#e74c3c'
C_V10 = '#9b59b6'
C_3V1 = '#00bcd4'
C_3V2 = '#3498db'
C_BG = '#fafafa'

DETECTORS = ['pangram_api', 'gptzero_api', 'copyleaks_api', 'binoculars']
DET_LABELS = ['Pangram', 'GPTZero', 'Copyleaks', 'Binoculars']
DET_COLORS = ['#e91e63', '#607d8b', '#cddc39', '#ff9800']


def get_vals(conn, group_where, table, col, join_col='sample_id'):
    if table == 'detector_runs':
        # col is detector name
        rows = conn.execute(f'''
            SELECT d.ai_score FROM detector_runs d
            JOIN samples s ON s.id = d.sample_id
            WHERE ({group_where}) AND d.detector = ? AND d.ai_score IS NOT NULL
        ''', (col,)).fetchall()
    else:
        rows = conn.execute(f'''
            SELECT t.{col} FROM {table} t
            JOIN samples s ON s.id = t.sample_id
            WHERE ({group_where}) AND t.{col} IS NOT NULL
        ''').fetchall()
    return [r[0] for r in rows]


def compute_convergence_recovery(baseline_vals, pipeline_vals, human_vals):
    """Mean convergence recovery across matched metrics."""
    hm = np.mean(human_vals) if human_vals else 0
    bm = np.mean(baseline_vals) if baseline_vals else 0
    pm = np.mean(pipeline_vals) if pipeline_vals else 0
    if abs(bm - hm) < 1e-9:
        return 1.0
    return 1.0 - abs(pm - hm) / abs(bm - hm)


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    conn = sqlite3.connect(DB)

    # Pre-fetch all data
    data = {}
    ling_cols = ['fpp_per_1k', 'first_person_per_1k', 'contractions_per_1k',
                 'sent_mean_len', 'burstiness', 'hedging_per_1k', 'type_token_ratio']
    info_cols = ['density_variance', 'density_mean', 'redundancy_mean',
                 'consecutive_similarity_mean', 'embedding_surprisal_mean',
                 'embedding_surprisal_variance']

    for gname, where in GROUPS.items():
        data[gname] = {}
        for col in ling_cols:
            data[gname][col] = get_vals(conn, where, 'linguistic_features', col)
        for col in info_cols:
            data[gname][col] = get_vals(conn, where, 'info_theoretic_features', col)
        for det in DETECTORS:
            data[gname][det] = get_vals(conn, where, 'detector_runs', det)

    # =========================================================
    # FIGURE 1: THE PARADOX — Quality vs Detection Scatter
    # =========================================================
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_facecolor(C_BG)
    fig.patch.set_facecolor('white')

    # Compute composite scores for each group
    recovery_metrics = ['fpp_per_1k', 'contractions_per_1k', 'sent_mean_len',
                        'burstiness', 'density_variance', 'consecutive_similarity_mean']

    points = {}
    for gname in ['dana', 'v10.2', '3way_v1', '3way_v2']:
        recoveries = []
        for col in recovery_metrics:
            r = compute_convergence_recovery(data['dana'][col], data[gname][col], data['human'][col])
            recoveries.append(max(0, min(1, r)))
        quality = np.mean(recoveries)

        det_scores = []
        for det in DETECTORS:
            vals = data[gname][det]
            if vals:
                det_scores.append(1.0 - np.mean(vals))  # invert: higher = more evasion
        detection = np.mean(det_scores) if det_scores else 0

        points[gname] = (quality, detection)

    # Optimal region
    ax.fill([0.5, 1.1, 1.1, 0.5], [0.5, 0.5, 1.05, 1.05],
            color=C_HUMAN, alpha=0.08, zorder=0)
    ax.text(0.82, 0.95, 'Optimal region:\nhigh quality +\nhigh evasion',
            fontsize=9, color='#27ae60', alpha=0.6, ha='center', style='italic')

    # Quadrant labels
    ax.text(0.15, 0.95, 'Low quality\nEvades detection', fontsize=8, color='#aaa',
            ha='center', va='top', style='italic')
    ax.text(0.85, 0.08, 'High quality\nDetected', fontsize=8, color='#aaa',
            ha='center', style='italic')
    ax.text(0.15, 0.08, 'Low quality\nDetected', fontsize=8, color='#aaa',
            ha='center', style='italic')

    # Plot points
    configs = {
        'dana': (C_DANA, 'Dana\nbaseline', 180, 'o'),
        'v10.2': (C_V10, 'v10.2\n(calibrated)', 200, 's'),
        '3way_v1': (C_3V1, '3-way v1\n(uncalib.)', 160, 'D'),
        '3way_v2': (C_3V2, '3-way v2\n(calib.)', 200, 'D'),
    }

    # Draw trajectory
    trajectory = ['dana', 'v10.2', '3way_v2']
    for i in range(len(trajectory) - 1):
        x1, y1 = points[trajectory[i]]
        x2, y2 = points[trajectory[i + 1]]
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='#bbb', lw=1.5,
                                    connectionstyle='arc3,rad=0.1'))

    # Also show the quality-only path: dana → v10.2
    # and the fork: v10.2 → 3way_v2 (up and left)

    for gname, (color, label, size, marker) in configs.items():
        x, y = points[gname]
        ax.scatter(x, y, c=color, s=size, marker=marker, zorder=5,
                   edgecolors='white', linewidth=1.5)
        offset = {'dana': (-0.06, -0.06), 'v10.2': (0.07, -0.05),
                  '3way_v1': (-0.08, 0.04), '3way_v2': (0.08, 0.04)}
        ox, oy = offset[gname]
        ax.annotate(label, (x, y), (x + ox, y + oy), fontsize=9,
                    fontweight='bold', color=color, ha='center')

    # Human point
    ax.scatter(1.0, 1.0, c=C_HUMAN, s=300, marker='D', zorder=5,
               edgecolors='white', linewidth=2)
    ax.annotate('Human\nbaseline', (1.0, 1.0), (0.92, 0.88), fontsize=10,
                fontweight='bold', color=C_HUMAN, ha='center')

    ax.set_xlabel('Linguistic Quality  (convergence recovery to human baseline)',
                  fontsize=12, fontweight='bold')
    ax.set_ylabel('Detection Avoidance  (1 = evades all 4 detectors)',
                  fontsize=12, fontweight='bold')
    ax.set_xlim(-0.05, 1.1)
    ax.set_ylim(-0.05, 1.05)
    ax.axhline(y=0.5, color='#ddd', linestyle=':', linewidth=1, zorder=0)
    ax.axvline(x=0.5, color='#ddd', linestyle=':', linewidth=1, zorder=0)
    ax.set_title('Figure 1 — The Detector Paradox\nLinguistic Quality vs. Detection Avoidance',
                 fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.15)
    plt.tight_layout()
    # NOTE: fig1_paradox.png is now the new hero (fig1_hero_paradox.py).
    # This legacy scatter is kept for reference but lives under a different filename
    # to avoid clobbering the canonical hero.
    plt.savefig(f'{OUT}/fig1_paradox_scatter_legacy.png', dpi=200, bbox_inches='tight')
    plt.close()
    print('  Fig 1: The Paradox ✓')

    # =========================================================
    # FIGURE 2: DETECTOR DISAGREEMENT — Grouped bar chart
    # =========================================================
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_facecolor(C_BG)
    fig.patch.set_facecolor('white')

    display_groups = ['human', 'dana', 'v10.2', '3way_v2']
    display_labels = ['Human', 'Persona\n(Dana)', 'v10.2\n(calibrated)', '3-way v2\n(detector-opt.)']
    n_groups = len(display_groups)
    n_det = len(DETECTORS)
    bar_width = 0.18
    x = np.arange(n_groups)

    for i, (det, det_label, det_color) in enumerate(zip(DETECTORS, DET_LABELS, DET_COLORS)):
        vals = [np.mean(data[g][det]) if data[g][det] else 0 for g in display_groups]
        bars = ax.bar(x + i * bar_width, vals, bar_width, label=det_label,
                      color=det_color, alpha=0.85, edgecolor='white', linewidth=0.5)
        for bar, val in zip(bars, vals):
            if val > 0.01:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                        f'{val:.2f}', ha='center', va='bottom', fontsize=7.5, fontweight='bold')

    ax.axhline(y=0.5, color='#e74c3c', linestyle=':', linewidth=1, alpha=0.5, label='AI threshold')
    ax.set_xticks(x + bar_width * 1.5)
    ax.set_xticklabels(display_labels, fontsize=11)
    ax.set_ylabel('Mean AI Probability (lower = more human)', fontsize=12, fontweight='bold')
    ax.set_ylim(0, 1.15)
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax.set_title('Figure 5 — Four-Detector Scores Across Pipeline Stages',
                 fontsize=14, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.15)
    plt.tight_layout()
    plt.savefig(f'{OUT}/fig2_detectors.png', dpi=200, bbox_inches='tight')
    plt.close()
    print('  Fig 2: Detector Disagreement ✓')

    # =========================================================
    # FIGURE 3: INFORMATION DENSITY VARIANCE — Box plots
    # =========================================================
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.set_facecolor(C_BG)
    fig.patch.set_facecolor('white')

    box_groups = ['human', 'dana', 'v10.2', '3way_v1', '3way_v2']
    box_labels = ['Human', 'Persona\n(Dana)', 'v10.2\n(calibrated)', '3-way v1\n(uncalib.)', '3-way v2\n(calib.)']
    box_colors = [C_HUMAN, C_DANA, C_V10, C_3V1, C_3V2]

    box_data = [data[g]['density_variance'] for g in box_groups]

    bp = ax.boxplot(box_data, patch_artist=True, widths=0.5,
                    medianprops=dict(color='black', linewidth=2),
                    whiskerprops=dict(color='#666'),
                    capprops=dict(color='#666'))

    for patch, color in zip(bp['boxes'], box_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
        patch.set_edgecolor('white')
        patch.set_linewidth(1.5)

    # Add individual points
    for i, (vals, color) in enumerate(zip(box_data, box_colors)):
        x_jitter = np.random.normal(i + 1, 0.08, len(vals))
        ax.scatter(x_jitter, vals, c=color, s=40, alpha=0.6, edgecolors='white',
                   linewidth=0.5, zorder=5)

    # Annotate means
    for i, vals in enumerate(box_data):
        m = np.mean(vals)
        ax.text(i + 1, max(vals) + 0.008, f'μ = {m:.4f}', ha='center',
                fontsize=9, fontweight='bold', color=box_colors[i])

    # Highlight the match
    ax.annotate('', xy=(1, np.mean(box_data[0])), xytext=(3, np.mean(box_data[2])),
                arrowprops=dict(arrowstyle='<->', color=C_V10, lw=2, ls='--'))
    ax.text(2, np.mean(box_data[0]) - 0.008, 'Near-identical\n(d = −0.002)',
            ha='center', fontsize=8, color=C_V10, style='italic')

    # Highlight the divergence
    ax.annotate('', xy=(3, np.mean(box_data[2])), xytext=(5, np.mean(box_data[4])),
                arrowprops=dict(arrowstyle='<->', color='#e74c3c', lw=2))
    mid_y = (np.mean(box_data[2]) + np.mean(box_data[4])) / 2
    ax.text(4.3, mid_y + 0.01, '5× divergence\n(d = −3.15, p = 0.001)',
            ha='center', fontsize=8, color='#e74c3c', fontweight='bold')

    ax.set_xticklabels(box_labels, fontsize=10)
    ax.set_ylabel('Information Density Variance', fontsize=12, fontweight='bold')
    ax.set_title('Figure 4 — Information Density Variance by Pipeline Stage\n'
                 'The core paradox metric: v10.2 matches human, 3-way diverges',
                 fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.15)
    plt.tight_layout()
    plt.savefig(f'{OUT}/fig3_density_variance.png', dpi=200, bbox_inches='tight')
    plt.close()
    print('  Fig 3: Density Variance ✓')

    # =========================================================
    # FIGURE 4: CONVERGENCE PROFILE — Radar chart
    # =========================================================
    radar_metrics = ['fpp_per_1k', 'contractions_per_1k', 'sent_mean_len',
                     'burstiness', 'type_token_ratio', 'density_variance',
                     'consecutive_similarity_mean', 'redundancy_mean']
    radar_labels = ['FPP /1k', 'Contractions /1k', 'Sent. length',
                    'Burstiness', 'Type-token ratio', 'Density var.',
                    'Consec. similarity', 'Redundancy']

    # Compute ratio-to-human for each metric
    n_metrics = len(radar_metrics)
    angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('white')

    for gname, color, label, ls in [
        ('human', C_HUMAN, 'Human (target)', '-'),
        ('v10.2', C_V10, 'v10.2 (calibrated)', '-'),
        ('3way_v2', C_3V2, '3-way v2 (detector-opt.)', '--'),
        ('dana', C_DANA, 'Persona baseline (Dana)', ':'),
    ]:
        ratios = []
        for col in radar_metrics:
            hm = np.mean(data['human'][col]) if data['human'][col] else 1
            gm = np.mean(data[gname][col]) if data[gname][col] else 0
            if hm == 0:
                ratios.append(1.0)
            else:
                ratios.append(min(gm / hm, 2.0))  # cap at 2x
        ratios += ratios[:1]
        ax.plot(angles, ratios, color=color, linewidth=2.5 if gname == 'human' else 2,
                label=label, linestyle=ls, alpha=0.9)
        if gname in ('human', 'v10.2', '3way_v2'):
            ax.fill(angles, ratios, color=color, alpha=0.05)

    # Human = 1.0 reference ring
    ax.plot(angles, [1.0] * (n_metrics + 1), color=C_HUMAN, linewidth=1,
            linestyle='-', alpha=0.3)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(radar_labels, fontsize=10)
    ax.set_ylim(0, 2.0)
    ax.set_yticks([0.5, 1.0, 1.5, 2.0])
    ax.set_yticklabels(['0.5×', '1.0×\n(human)', '1.5×', '2.0×'], fontsize=8)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10, framealpha=0.9)
    ax.set_title('Figure 2 — Metric Convergence Profiles\n(ratio to human baseline, 1.0 = match)',
                 fontsize=13, fontweight='bold', pad=25)
    plt.tight_layout()
    plt.savefig(f'{OUT}/fig4_radar.png', dpi=200, bbox_inches='tight')
    plt.close()
    print('  Fig 4: Convergence Radar ✓')

    # =========================================================
    # FIGURE 5: VOICE DEGRADATION — Ratio-to-human bars
    # =========================================================
    voice_metrics = ['contractions_per_1k', 'burstiness', 'sent_mean_len',
                     'fpp_per_1k', 'type_token_ratio']
    voice_labels = ['Contractions\n/1k', 'Burstiness', 'Sent. mean\nlength',
                    'FPP /1k', 'Type-token\nratio']

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_facecolor(C_BG)
    fig.patch.set_facecolor('white')

    display_pipelines = ['v10.2', '3way_v1', '3way_v2']
    pipe_labels_short = ['v10.2', '3-way v1', '3-way v2']
    pipe_colors = [C_V10, C_3V1, C_3V2]
    n_metrics = len(voice_metrics)
    n_pipes = len(display_pipelines)
    bar_width = 0.22
    x = np.arange(n_metrics)

    for i, (gname, plabel, pcolor) in enumerate(zip(display_pipelines, pipe_labels_short, pipe_colors)):
        ratios = []
        for col in voice_metrics:
            hm = np.mean(data['human'][col]) if data['human'][col] else 1
            gm = np.mean(data[gname][col]) if data[gname][col] else 0
            ratios.append(gm / hm if hm != 0 else 1.0)

        bars = ax.bar(x + i * bar_width, ratios, bar_width, label=plabel,
                      color=pcolor, alpha=0.8, edgecolor='white', linewidth=0.5)
        for bar, val in zip(bars, ratios):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.03,
                    f'{val:.2f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Human = 1.0 reference line
    ax.axhline(y=1.0, color=C_HUMAN, linewidth=2.5, linestyle='-', alpha=0.7, label='Human = 1.0')
    ax.fill_between([-0.5, n_metrics + 0.5], 0.9, 1.1, color=C_HUMAN, alpha=0.08)

    ax.set_xticks(x + bar_width)
    ax.set_xticklabels(voice_labels, fontsize=10)
    ax.set_ylabel('Ratio to Human Baseline  (1.0 = match)', fontsize=12, fontweight='bold')
    ax.set_ylim(0, max(2.0, ax.get_ylim()[1] * 1.1))
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
    ax.set_title('Figure 3 — Voice Metric Convergence to Human Baseline\n'
                 'Cross-model mixing inflates first-person plural while calibration preserves voice',
                 fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.15)
    plt.tight_layout()
    plt.savefig(f'{OUT}/fig5_voice.png', dpi=200, bbox_inches='tight')
    plt.close()
    print('  Fig 5: Voice Degradation ✓')

    conn.close()
    print(f'\nAll figures saved to {OUT}/')


if __name__ == '__main__':
    main()
