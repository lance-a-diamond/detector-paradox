#!/usr/bin/env python3
"""Regenerate all data-heavy tables in paper_v09.md from source-of-truth files.

Sources:
    - survey/survey_results.json  (n=37 primary analysis)
    - humanization.db             (group-level linguistic/info-theoretic data)

Output is the markdown for each table, printed in order. Copy into
paper_v09.md to replace stale values. Or diff the output against the paper
to catch drift.

Usage:
    python3 generate_paper_tables.py                  # print all tables
    python3 generate_paper_tables.py --table 8        # just Table 8
    python3 generate_paper_tables.py --validate       # compare to paper_v09.md,
                                                      # report any cells that
                                                      # don't match source data
"""
from __future__ import annotations
import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Release layout: analysis/, data/, paper/ are siblings under repo root.
_REPO_ROOT = HERE.parent
PAPER = _REPO_ROOT / "paper" / "paper_v09.md"
SURVEY_RESULTS = _REPO_ROOT / "data" / "survey_results_n37.json"
DB = _REPO_ROOT / "data" / "humanization.db"

# Passage letter → DB sample label
PASSAGE_LABELS = {
    "A": "brandur_stripe_idempotency",
    "B": "scribe_surgical_v10_2",
    "C": "scribe_idempotency_3way_v2",
    "D": "brooker_backoff_jitter_2015",
    "E": "scribe_backoff_3way_v2",
    "F": "olah_backprop_2015",
    "G": "scribe_bloom_filter_3way_v2",
    "H": "scribe_persona_opus_t1",
}

PASSAGE_SOURCE = {
    "A": "Human (Stripe)",
    "B": "Surgical v10.2",
    "C": "Cross-model v2",
    "D": "Human (AWS)",
    "E": "Cross-model v2",
    "F": "Human (colah)",
    "G": "Cross-model v2",
    "H": "Persona (Dana)",
}

PASSAGE_CONDITION_SHORT = {
    "A": "human", "B": "surgical v10.2", "C": "cross-model v2",
    "D": "human", "E": "cross-model v2", "F": "human",
    "G": "cross-model v2", "H": "persona (Dana)",
}

TRUTH = {"A":"human","B":"ai","C":"ai","D":"human","E":"ai","F":"human","G":"ai","H":"ai"}

# Group filter SQL fragments. These match statistical_analysis.py conventions.
GROUP_SQL = {
    "human":    "s.label IN ('brandur_stripe_idempotency','cockroach_parallel_commits',"
                "'brooker_backoff_jitter_2015','hudson_go_gc_journey_2018',"
                "'srivastav_bloom_filters_2014','olah_backprop_2015')",
    "dana":     "(s.label LIKE '%dana_baseline' OR s.label = 'scribe_persona_opus_t1')",
    "v10.2":    "(s.label LIKE '%v10_2' AND s.label NOT LIKE '%v10_2_1')",
    "3way_v1":  "(s.label LIKE '%_3way' AND s.label NOT LIKE '%_3way_v2')",
    "3way_v2":  "s.label LIKE '%3way_v2'",
}


def _um(x: float) -> str:
    """Format signed float with Unicode minus sign (U+2212) matching the paper's convention."""
    s = f"{x:+.3f}"
    return s.replace("-", "−")


def _unicode_minus(s: str) -> str:
    """Replace ASCII hyphens used as minus signs with Unicode minus (U+2212).
    Preserves table-separator rows ('|---|---|...') which use literal hyphens.
    Replaces '-' only when it appears to be a sign character in a data cell.
    """
    out = []
    for line in s.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and set(stripped.replace("|", "").replace(" ", "").replace("-", "")) == set():
            # table-separator row — keep ASCII hyphens
            out.append(line)
            continue
        # Replace "-" with "−" when preceded by " ", "|", "[", "(", or start of line
        # and followed by a digit (so it's clearly a sign)
        line = re.sub(r"(^|[\s|\[(*])-(?=\d)", r"\1−", line)
        out.append(line)
    return "\n".join(out)


def fmt_p(p: float | None) -> str:
    if p is None:
        return "n/a"
    if p < 0.001:
        return "<.001"
    return f"{p:.3f}"


def load_survey():
    return json.loads(SURVEY_RESULTS.read_text())


def db_query(sql: str, params: tuple = ()) -> list:
    conn = sqlite3.connect(str(DB))
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def fetch_per_passage_linguistic(column: str, table: str = "linguistic_features") -> dict:
    out = {}
    for passage, label in PASSAGE_LABELS.items():
        rows = db_query(
            f"SELECT f.{column} FROM samples s JOIN {table} f ON f.sample_id=s.id WHERE s.label=?",
            (label,),
        )
        out[passage] = rows[0][0] if rows and rows[0][0] is not None else None
    return out


def fetch_group_values(group: str, column: str, table: str = "linguistic_features") -> list[float]:
    """Pull per-sample values for a metric within a group."""
    where = GROUP_SQL[group]
    rows = db_query(
        f"SELECT f.{column} FROM samples s JOIN {table} f ON f.sample_id=s.id WHERE {where}"
    )
    return [r[0] for r in rows if r[0] is not None]


def fetch_group_detector(group: str, detector: str) -> list[float]:
    where = GROUP_SQL[group]
    rows = db_query(
        "SELECT r.ai_score FROM samples s JOIN detector_runs r ON r.sample_id=s.id "
        f"WHERE {where} AND r.detector=?",
        (detector,),
    )
    return [r[0] for r in rows if r[0] is not None]


def mann_whitney_p(a: list[float], b: list[float]) -> float:
    """Two-sided Mann-Whitney U p-value between two groups."""
    from scipy import stats as sstats
    if not a or not b:
        return float("nan")
    try:
        _, p = sstats.mannwhitneyu(a, b, alternative="two-sided")
        return float(p)
    except Exception:
        return float("nan")


def cohens_d(a: list[float], b: list[float]) -> float:
    """Cohen's d with pooled SD (matches statistical_analysis.py)."""
    import numpy as np
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pooled = np.sqrt(((len(a)-1)*np.var(a, ddof=1) + (len(b)-1)*np.var(b, ddof=1))
                     / (len(a)+len(b)-2))
    if pooled == 0:
        return 0.0
    return float((np.mean(a) - np.mean(b)) / pooled)


def _sig_marker(p: float) -> str:
    if p != p:  # NaN
        return ""
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


def fetch_per_passage_detector(detector: str) -> dict:
    out = {}
    for passage, label in PASSAGE_LABELS.items():
        rows = db_query(
            "SELECT r.ai_score FROM samples s JOIN detector_runs r ON r.sample_id=s.id "
            "WHERE s.label=? AND r.detector=? ORDER BY r.run_at DESC LIMIT 1",
            (label, detector),
        )
        out[passage] = rows[0][0] if rows and rows[0][0] is not None else None
    return out


# -----------------------------------------------------------------------------
# Table generators
# -----------------------------------------------------------------------------

def gen_table_1() -> str:
    """Linguistic metrics by group (group means with sig markers vs human)."""
    metrics = [
        ("first_person_per_1k", "First person singular /1k"),
        ("fpp_per_1k",          "First person plural /1k"),
        ("contractions_per_1k", "Contractions /1k"),
        ("sent_mean_len",       "Mean sentence length"),
        ("burstiness",          "Burstiness"),
    ]
    groups = ["human", "dana", "v10.2", "3way_v2"]
    group_labels = ["Human (n=6)", "Persona/Dana (n=7)", "v10.2 (n=7)", "3-way v2 (n=7)"]
    import numpy as np

    lines = [
        "**Table 1: Linguistic metrics by group (mean ± std)**",
        "",
        "| Metric | " + " | ".join(group_labels) + " |",
        "|---|" + "|".join(["---"] * len(groups)) + "|",
    ]
    for col, name in metrics:
        values = {g: fetch_group_values(g, col) for g in groups}
        human_vals = values["human"]
        row = [name]
        for g in groups:
            v = values[g]
            if not v:
                row.append("n/a")
                continue
            mean = np.mean(v)
            marker = ""
            if g != "human":
                p = mann_whitney_p(human_vals, v)
                marker = _sig_marker(p)
            row.append(f"{mean:.2f}{marker}")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("*p < 0.05, **p < 0.01 vs. human (Mann-Whitney U)")
    return "\n".join(lines)


def gen_table_2() -> str:
    """Information-theoretic metrics by group."""
    metrics = [
        ("density_variance",           "Density variance"),
        ("density_mean",               "Density mean"),
        ("redundancy_mean",            "Redundancy mean"),
        ("consecutive_similarity_mean","Consecutive sim. mean"),
        ("embedding_surprisal_variance","Embedding surprisal var."),
    ]
    groups = ["human", "dana", "v10.2", "3way_v2"]
    import numpy as np

    lines = [
        "**Table 2: Information-theoretic metrics by group**",
        "",
        "| Metric | Human | Persona/Dana | v10.2 | 3-way v2 |",
        "|---|---|---|---|---|",
    ]
    for col, name in metrics:
        values = {g: fetch_group_values(g, col, table="info_theoretic_features") for g in groups}
        human_vals = values["human"]
        row = [name]
        for g in groups:
            v = values[g]
            if not v:
                row.append("n/a")
                continue
            mean = np.mean(v)
            marker = ""
            if g != "human":
                p = mann_whitney_p(human_vals, v)
                marker = _sig_marker(p)
            fmt = f"{mean:.4f}" if col == "density_variance" else f"{mean:.3f}"
            row.append(f"{fmt}{marker}")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("*p < 0.05, **p < 0.01 vs. human (Mann-Whitney U)")
    return "\n".join(lines)


def gen_table_3() -> str:
    """Mean AI detection scores by group."""
    detectors = [("pangram_api","Pangram"),("gptzero_api","GPTZero"),
                 ("copyleaks_api","Copyleaks"),("binoculars","Binoculars")]
    groups = ["human", "dana", "v10.2", "3way_v2"]
    import numpy as np

    lines = [
        "**Table 3: Mean AI detection scores by group (higher = more likely AI)**",
        "",
        "| Detector | Human | Persona/Dana | v10.2 | 3-way v2 |",
        "|---|---|---|---|---|",
    ]
    for det, name in detectors:
        row = [name]
        for g in groups:
            v = fetch_group_detector(g, det)
            row.append(f"{np.mean(v):.3f}" if v else "n/a")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def gen_table_4() -> str:
    """The Detector Paradox (v10.2 vs 3-way v2)."""
    import numpy as np

    def _row(label: str, a_label: str, b_label: str,
             a_vals: list[float], b_vals: list[float], format_str="{:.3f}"):
        d = cohens_d(a_vals, b_vals)
        p = mann_whitney_p(a_vals, b_vals)
        a_mean = np.mean(a_vals)
        b_mean = np.mean(b_vals)
        return (f"| {label} | {format_str.format(a_mean)} ({a_label}) | "
                f"{format_str.format(b_mean)} ({b_label}) | {d:+.2f} | {p:.3f} |")

    v10_dv = fetch_group_values("v10.2", "density_variance", "info_theoretic_features")
    way_dv = fetch_group_values("3way_v2", "density_variance", "info_theoretic_features")
    lines = [
        "**Table 4: The Detector Paradox**",
        "",
        "| | v10.2 | 3-way v2 | Cohen's d | p-value |",
        "|---|---|---|---|---|",
    ]

    # density variance comparison (use framed labels for narrative clarity)
    d_dv = cohens_d(v10_dv, way_dv)
    p_dv = mann_whitney_p(v10_dv, way_dv)
    m_v10 = np.mean(v10_dv)
    m_way = np.mean(way_dv)
    lines.append(
        f"| Density variance | **{m_v10:.3f}** (≈ human) | "
        f"{m_way:.3f} ({m_way/max(m_v10, 1e-9):.0f}× worse) | "
        f"{d_dv:+.2f} | {p_dv:.3f} |"
    )

    # Detectors: "flagged" / "passes" based on >= 0.5 threshold
    for det, name in [("pangram_api","Pangram"),("gptzero_api","GPTZero"),
                      ("copyleaks_api","Copyleaks"),("binoculars","Binoculars")]:
        a = fetch_group_detector("v10.2", det)
        b = fetch_group_detector("3way_v2", det)
        d = cohens_d(a, b)
        p = mann_whitney_p(a, b)
        a_mean = np.mean(a); b_mean = np.mean(b)
        a_lbl = "flagged" if a_mean >= 0.5 else "passes"
        b_lbl = "flagged" if b_mean >= 0.5 else "passes"
        a_str = f"**{a_mean:.3f}** ({a_lbl})" if a_mean < 0.5 else f"{a_mean:.3f} ({a_lbl})"
        b_str = f"**{b_mean:.3f}** ({b_lbl})" if b_mean < 0.5 else f"{b_mean:.3f} ({b_lbl})"
        lines.append(f"| {name} AI score | {a_str} | {b_str} | {d:+.2f} | {p:.3f} |")
    return "\n".join(lines)


def gen_table_5(survey: dict) -> str:
    """Per-passage classification accuracy (n=37)."""
    c1 = survey["sections"]["C_per_passage"]["C1_per_passage"]
    lines = [
        f"**Table 5: Per-passage human classification accuracy (n = {survey['meta']['n_kept']})**",
        "",
        "| Passage | Source | Condition | Correct | Accuracy | 95% CI | p vs. chance |",
        "|---|---|---|---|---|---|---|",
    ]
    # Sort: humans (A, D, F) first then AI
    passages = ["A","D","F","B","C","E","G","H"]
    for k in passages:
        r = c1[k]
        # Source column: human author name for humans, "AI" for AI
        src = PASSAGE_SOURCE[k] if r["truth"] == "human" else "AI"
        cond = PASSAGE_CONDITION_SHORT[k] if r["truth"] == "ai" else "human"
        ci_lo = r["ci_95"][0] * 100
        ci_hi = r["ci_95"][1] * 100
        acc = r["accuracy"] * 100
        p = r["p_two_sided_vs_chance"]
        p_fmt = f"**{p:.3f}**" if p < 0.05 else f"{p:.3f}"
        # bold the accuracy if significant in either direction
        acc_str = f"**{acc:.1f}%**" if p < 0.05 else f"{acc:.1f}%"
        lines.append(
            f"| {k} | {src} | {cond} | {r['correct']}/{r['n']} | {acc_str} | "
            f"[{ci_lo:.1f}, {ci_hi:.1f}] | {p_fmt} |"
        )
    return "\n".join(lines)


def gen_table_6(survey: dict) -> str:
    """Likert ratings, AI vs human paired (n=37)."""
    b = survey["sections"]["B_likert"]
    dims_ordered = ["confidence", "naturalness", "authority", "engagement", "clarity", "quality"]
    dim_labels = {"confidence":"Confidence","naturalness":"Naturalness","authority":"Authority",
                  "engagement":"Engagement","clarity":"Clarity","quality":"Overall quality"}
    lines = [
        f"**Table 6: Mean Likert ratings — AI vs. human passages (n = {survey['meta']['n_kept']} paired differences)**",
        "",
        "| Dimension | AI mean | Human mean | Δ (AI − H) | Cohen's d | Wilcoxon p | BH-FDR sig. |",
        "|---|---|---|---|---|---|---|",
    ]
    for dim in dims_ordered:
        r = b[dim]
        sig = "**✓**" if r["bh_fdr_significant"] else "n.s."
        delta = r["delta"]
        d = r["cohens_d_paired"]
        p = r["wilcoxon_p"]
        # Bold delta/d/p only when the test is significant at α = 0.05 (uncorrected)
        delta_str = f"**{delta:+.2f}**" if p < 0.05 else f"{delta:+.2f}"
        d_str = f"**{d:+.2f}**" if p < 0.05 else f"{d:+.2f}"
        p_str = f"**{p:.3f}**" if p < 0.05 else f"{p:.3f}"
        lines.append(
            f"| {dim_labels[dim]} | {r['ai_mean']:.2f} | {r['human_mean']:.2f} | "
            f"{delta_str} | {d_str} | {p_str} | {sig} |"
        )
    return "\n".join(lines)


def gen_table_4a(survey: dict) -> str:
    """Spearman ρ — machine detector × crowd AI-call rate (n=37)."""
    sp_all = survey["sections"]["I_machine_linkage"]["spearman_all_passages"]
    sp_ai = survey["sections"]["I_machine_linkage"]["spearman_ai_only"]
    det_names = {
        "pangram_api":"Pangram","gptzero_api":"GPTZero",
        "copyleaks_api":"Copyleaks","binoculars":"Binoculars",
    }
    lines = [
        f"**Table 4a: Machine detector × human-crowd AI-call rate (Spearman ρ, n = {survey['meta']['n_kept']})**",
        "",
        "| Detector | All 8 passages | p | AI passages only (n = 5) | p |",
        "|---|---|---|---|---|",
    ]
    for det in ["pangram_api","gptzero_api","copyleaks_api","binoculars"]:
        a = sp_all[det]; i = sp_ai[det]
        a_rho = f"**{a['spearman_rho']:+.3f}**" if a['p_two_sided'] < 0.05 else f"{a['spearman_rho']:+.3f}"
        i_rho = f"**{i['spearman_rho']:+.3f}**" if i['p_two_sided'] < 0.10 else f"{i['spearman_rho']:+.3f}"
        a_p = f"**{a['p_two_sided']:.3f}**" if a['p_two_sided'] < 0.05 else f"{a['p_two_sided']:.3f}"
        i_p = f"**{i['p_two_sided']:.3f}**" if i['p_two_sided'] < 0.10 else f"{i['p_two_sided']:.3f}"
        lines.append(f"| {det_names[det]} | {a_rho} | {a_p} | {i_rho} | {i_p} |")
    return "\n".join(lines)


def gen_table_4b(survey: dict) -> str:
    """Per-passage crowd AI-call rate vs detector scores (AI passages only)."""
    rows = survey["sections"]["I_machine_linkage"]["per_passage"]
    # AI passages sorted by crowd AI-call rate ascending
    ai_rows = sorted((r for r in rows if r["truth"] == "ai"),
                     key=lambda r: r["human_ai_call_rate"])
    lines = [
        "**Table 4b: Per-passage detector scores vs. crowd AI-call rate (AI passages only)**",
        "",
        "| Passage | Condition | Crowd AI% | Pangram | GPTZero | Copyleaks | Binoculars |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in ai_rows:
        cond = {"raw_ai":"Persona (Dana)","persona_dana":"Persona (Dana)",
                "humanized_fnword":"Surgical v10.2","crossmodel":"Cross-model v2"}[r["condition"]]
        crowd = r["human_ai_call_rate"] * 100
        d = r["detectors"]
        def fmt(det):
            v = d.get(det, {}).get("ai_score")
            return f"{v:.2f}" if v is not None else "n/a"
        lines.append(
            f"| {r['passage']} | {cond} | {crowd:.1f}% | "
            f"{fmt('pangram_api')} | {fmt('gptzero_api')} | "
            f"{fmt('copyleaks_api')} | {fmt('binoculars')} |"
        )
    return "\n".join(lines)


def gen_table_7(survey: dict) -> str:
    """Reasoning-text feature mentions."""
    top = survey["sections"]["H_reasoning"]["top_10_by_mentions"]
    # Prettify the feature names
    pretty = {
        "personal_anecdote": "Personal anecdote / experience",
        "first_person_present": "First-person voice present",
        "technical_density": "Technical density",
        "typo_error": "Typos / grammar errors",
        "formal_stiff": "Formal / stiff / mechanical tone",
        "polish_flow": "Polished / overly smooth flow",
        "voice_tone": "Voice / tone (generic)",
        "generic_vague": "Generic / vague / bland",
        "ai_stereotype": "\"AI stereotype\" / cliché",
        "conversational": "Conversational / casual",
        "first_person_absent": "First-person voice absent",
        "punctuation": "Punctuation",
    }
    lines = [
        "**Table 7: Features cited in reasoning × classification accuracy**",
        "",
        "| Feature cited | Mentions | Accuracy when cited |",
        "|---|---|---|",
    ]
    for f in top:
        name = pretty.get(f["feature"], f["feature"])
        acc = f["accuracy_when_mentioned"]
        acc_str = f"{acc*100:.1f}%" if acc is not None else "n/a"
        # bold the most/least diagnostic
        if acc is not None and acc >= 0.60:
            acc_str = f"**{acc*100:.1f}%**"
        lines.append(f"| {name} | {f['mentions_total']} | {acc_str} |")
    return "\n".join(lines)


def gen_table_8(survey: dict) -> str:
    """Per-passage composite quality, key linguistic metrics, detectors."""
    rows = survey["sections"]["J_quality_correlations"]["per_passage_table"]
    # Also fetch contractions directly (not in J per_passage_table by default)
    contractions = fetch_per_passage_linguistic("contractions_per_1k")
    # Sort by composite quality descending
    rows = sorted(rows, key=lambda r: r["composite_quality_mean"] or 0, reverse=True)
    lines = [
        "**Table 8: Per-passage composite quality, linguistic metrics, detectors**",
        "",
        "| Passage | Condition | Composite quality | Density variance | FPS /1k | Contractions /1k | Copyleaks | GPTZero |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        k = r["passage"]
        cond = PASSAGE_SOURCE[k]
        cq = r["composite_quality_mean"]
        dv = r["density_variance"]
        fps = r["first_person_per_1k"]
        cn = contractions[k]
        cl = r["copyleaks_api"]
        gz = r["gptzero_api"]
        cq_str = f"**{cq:.2f}**" if k == "H" else f"{cq:.2f}"
        dv_str = f"**{dv:.3f}**" if k == "H" else f"{dv:.3f}"
        header_k = f"**{k}**" if k == "H" else k
        cond_str = f"**{cond}**" if k == "H" else cond
        lines.append(
            f"| {header_k} | {cond_str} | {cq_str} | {dv_str} | "
            f"{fps:.2f} | {cn:.2f} | {cl:.2f} | {gz:.2f} |"
        )
    return "\n".join(lines)


def gen_table_9(survey: dict) -> str:
    """Spearman ρ — composite quality × linguistic and detector metrics."""
    ling_all = survey["sections"]["J_quality_correlations"]["spearman"]["linguistic_all_passages"]["_composite"]
    ling_ai = survey["sections"]["J_quality_correlations"]["spearman"]["linguistic_ai_only"]["_composite"]
    det_all = survey["sections"]["J_quality_correlations"]["spearman"]["detector_all_passages"]["_composite"]
    det_ai = survey["sections"]["J_quality_correlations"]["spearman"]["detector_ai_only"]["_composite"]

    lbl = {
        "first_person_per_1k": "First-person singular /1k",
        "fpp_per_1k": "First-person plural /1k",
        "contractions_per_1k": "Contractions /1k",
        "em_dashes_per_1k": "Em-dashes /1k",
        "hedging_per_1k": "Hedging /1k",
        "sent_mean_len": "Mean sentence length",
        "burstiness": "Burstiness",
        "type_token_ratio": "Type-token ratio",
        "density_variance": "Information density variance",
        "consecutive_similarity_mean": "Consecutive similarity",
        "embedding_surprisal_variance": "Embedding surprisal variance",
        "redundancy_mean": "Redundancy (mean pairwise sim)",
        "pangram_api": "Pangram ai_score",
        "gptzero_api": "GPTZero ai_score",
        "copyleaks_api": "Copyleaks ai_score",
        "binoculars": "Binoculars ai_score",
    }

    ling_order = [
        "first_person_per_1k","contractions_per_1k","type_token_ratio",
        "burstiness","density_variance","consecutive_similarity_mean",
        "embedding_surprisal_variance",
    ]
    det_order = ["pangram_api","gptzero_api","copyleaks_api","binoculars"]

    lines = [
        "**Table 9: Spearman ρ — composite quality vs. linguistic and detector metrics**",
        "",
        "| Predictor | All 8 passages | p | AI only (n = 5) | p |",
        "|---|---|---|---|---|",
    ]
    for col in ling_order:
        a = ling_all.get(col, {}); i = ling_ai.get(col, {})
        if a.get("rho") is None: continue
        a_rho, a_p = a["rho"], a["p"]
        i_rho, i_p = i.get("rho"), i.get("p")
        a_rho_s = f"**{_um(a_rho)}**" if a_p < 0.05 else f"{_um(a_rho)}"
        a_p_s = f"**{a_p:.3f}**" if a_p < 0.05 else f"{a_p:.3f}"
        i_rho_s = f"{_um(i_rho)}" if i_rho is not None else "n/a"
        i_p_s = f"**{i_p:.3f}**" if i_p is not None and i_p < 0.05 else (f"{i_p:.3f}" if i_p is not None else "n/a")
        lines.append(f"| {lbl[col]} | {a_rho_s} | {a_p_s} | {i_rho_s} | {i_p_s} |")
    for det in det_order:
        a = det_all.get(det, {}); i = det_ai.get(det, {})
        if a.get("rho") is None: continue
        a_rho, a_p = a["rho"], a["p"]
        i_rho, i_p = i.get("rho"), i.get("p")
        a_rho_s = f"**{_um(a_rho)}**" if a_p < 0.05 else f"{_um(a_rho)}"
        a_p_s = f"**{a_p:.3f}**" if a_p < 0.05 else f"{a_p:.3f}"
        i_rho_s = f"**{_um(i_rho)}**" if i_p is not None and i_p < 0.05 else (f"{_um(i_rho)}" if i_rho is not None else "n/a")
        i_p_s = f"**{i_p:.3f}**" if i_p is not None and i_p < 0.05 else (f"{i_p:.3f}" if i_p is not None else "n/a")
        lines.append(f"| {lbl[det]} | {a_rho_s} | {a_p_s} | {i_rho_s} | {i_p_s} |")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

def extract_table_from_paper(table_id: str) -> str | None:
    """Pull the markdown text of a specific table by its ID (e.g. '5', '4a', '4b')."""
    if not PAPER.exists():
        return None
    text = PAPER.read_text()
    # Find the table header `**Table N...`
    pattern = rf"\*\*Table {re.escape(table_id)}[:.]"
    m = re.search(pattern, text)
    if not m:
        return None
    start = m.start()
    # The table ends at the next blank line following the last table row
    # Tables end after a run of `|` lines. Find the first `\n\n` after the last `|...|` line.
    rest = text[start:]
    # Match the header line + the table rows (any lines starting with | or blank/non-table lines)
    lines = rest.split("\n")
    collected = []
    in_table = False
    for line in lines:
        if line.startswith("**Table "):
            collected.append(line)
            continue
        if line.startswith("|"):
            collected.append(line)
            in_table = True
            continue
        if in_table and line.strip() == "":
            break
        collected.append(line)
    return "\n".join(collected).strip()


def validate():
    survey = load_survey()
    generators = {
        "1":  lambda _s: gen_table_1(),
        "2":  lambda _s: gen_table_2(),
        "3":  lambda _s: gen_table_3(),
        "4":  lambda _s: gen_table_4(),
        "4a": gen_table_4a,
        "4b": gen_table_4b,
        "5": gen_table_5,
        "6": gen_table_6,
        "7": gen_table_7,
        "8": gen_table_8,
        "9": gen_table_9,
    }
    mismatches = []
    for tid, gen in generators.items():
        expected = _unicode_minus(gen(survey)).strip()
        actual = extract_table_from_paper(tid)
        if actual is None:
            mismatches.append(f"Table {tid}: NOT FOUND in paper")
            continue
        # Normalize: strip whitespace on each line, drop blank lines,
        # and drop the sig-marker footnote (static explanatory text).
        def _norm(text):
            return [l.rstrip() for l in text.splitlines()
                    if l.strip() and not l.strip().startswith("*p <")]
        exp_lines = _norm(expected)
        act_lines = _norm(actual)
        if exp_lines != act_lines:
            mismatches.append(f"Table {tid}: MISMATCH")
            # Show first differing line
            for i, (e, a) in enumerate(zip(exp_lines, act_lines)):
                if e != a:
                    mismatches.append(f"    line {i}:")
                    mismatches.append(f"      paper:    {a[:100]}")
                    mismatches.append(f"      expected: {e[:100]}")
                    break
            if len(exp_lines) != len(act_lines):
                mismatches.append(f"    length mismatch: paper {len(act_lines)} vs expected {len(exp_lines)}")
    if not mismatches:
        print("✓ All tables match source-of-truth data")
        return 0
    for m in mismatches:
        print(m)
    return 1


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--table", help="Generate one specific table (e.g. '8' or '4a')")
    p.add_argument("--validate", action="store_true", help="Compare paper against source; report mismatches")
    args = p.parse_args()

    if args.validate:
        return validate()

    survey = load_survey()
    generators = {
        "1":  lambda _s: gen_table_1(),
        "2":  lambda _s: gen_table_2(),
        "3":  lambda _s: gen_table_3(),
        "4":  lambda _s: gen_table_4(),
        "4a": gen_table_4a,
        "4b": gen_table_4b,
        "5": gen_table_5,
        "6": gen_table_6,
        "7": gen_table_7,
        "8": gen_table_8,
        "9": gen_table_9,
    }

    if args.table:
        gen = generators.get(args.table)
        if gen is None:
            print(f"Unknown table: {args.table}", file=sys.stderr)
            return 1
        print(_unicode_minus(gen(survey)))
        return 0

    for tid, gen in generators.items():
        print(f"\n=== Table {tid} ===\n")
        print(_unicode_minus(gen(survey)))


if __name__ == "__main__":
    sys.exit(main() or 0)
