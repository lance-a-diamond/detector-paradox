#!/usr/bin/env python3
"""Statistical analysis of the human-eval survey (Scribe paper v0.9).

Runs Tier 1 + Tier 2 analyses on quality-filtered responses:

    A. Origin classification      — binomial tests, SDT (d', c)
    B. Likert ratings              — paired Wilcoxon + Cohen's d + BH-FDR
    C. Per-passage accuracy        — binomial + condition comparison + Fleiss' κ
    D. "Best quality" pick         — base-rate test
    H. Reasoning-text themes       — keyword scan, feature × correctness
    I. Machine-vs-human detectors  — per-passage score join + Spearman correlation
    J. Quality × metrics            — quality rating × linguistic + detector correlations

Outputs:
    survey_results.json    (machine-readable)
    stdout                 (human-readable tables)

Usage:
    python3 survey_analysis.py                      # top 30 from responses_latest.json
    python3 survey_analysis.py --keep 30
    python3 survey_analysis.py --no-filter          # use all responses
    python3 survey_analysis.py --path other.json
"""
from __future__ import annotations
import argparse
import json
import re
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import stats

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
# Release layout: analysis/ and data/ are siblings under the repo root.
_REPO_ROOT = SCRIPT_DIR.parent
_DATA = _REPO_ROOT / "data"
DEFAULT_PATH = _DATA / "responses_anonymized.json"
OUT_PATH = _DATA / "survey_results.json"
HUMANIZATION_DB = _DATA / "humanization.db"

# Survey passage letter → humanization.db sample label
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

# Machine detectors to pull (column names in detector_runs)
MACHINE_DETECTORS = ["pangram_api", "gptzero_api", "copyleaks_api", "binoculars"]

# Linguistic & info-theoretic metrics to correlate with quality ratings.
# Chosen as the ones highlighted in the paper (§§5.1, 5.2).
LINGUISTIC_METRICS = [
    ("density_variance",             "Information density variance"),
    ("consecutive_similarity_mean",  "Consecutive sentence similarity"),
    ("embedding_surprisal_variance", "Embedding surprisal variance"),
    ("redundancy_mean",              "Redundancy (mean pairwise sim)"),
    ("burstiness",                   "Burstiness (sent-length var)"),
    ("sent_mean_len",                "Mean sentence length"),
    ("type_token_ratio",             "Type-token ratio"),
    ("first_person_per_1k",          "First-person singular /1k"),
    ("fpp_per_1k",                   "First-person plural /1k"),
    ("contractions_per_1k",          "Contractions /1k"),
    ("em_dashes_per_1k",             "Em-dashes /1k"),
    ("hedging_per_1k",               "Hedging /1k"),
]

# Which table each metric lives in (linguistic_features vs info_theoretic_features)
LING_TABLE = {
    "density_variance": "info_theoretic_features",
    "consecutive_similarity_mean": "info_theoretic_features",
    "embedding_surprisal_variance": "info_theoretic_features",
    "redundancy_mean": "info_theoretic_features",
    "burstiness": "linguistic_features",
    "sent_mean_len": "linguistic_features",
    "type_token_ratio": "linguistic_features",
    "first_person_per_1k": "linguistic_features",
    "fpp_per_1k": "linguistic_features",
    "contractions_per_1k": "linguistic_features",
    "em_dashes_per_1k": "linguistic_features",
    "hedging_per_1k": "linguistic_features",
}

TRUTH = {
    "A": "human", "B": "ai", "C": "ai", "D": "human",
    "E": "ai",    "F": "human", "G": "ai", "H": "ai",
}
HUMAN_PASSAGES = [k for k, v in TRUTH.items() if v == "human"]
AI_PASSAGES = [k for k, v in TRUTH.items() if v == "ai"]

# Passage conditions (manipulation)
CONDITIONS = {
    "H": "persona_dana",
    "B": "humanized_fnword",
    "C": "crossmodel",
    "E": "crossmodel",
    "G": "crossmodel",
    "A": "human",
    "D": "human",
    "F": "human",
}

LIKERT_DIMS = ["confidence", "naturalness", "clarity", "engagement", "authority", "quality"]

# Reasoning-text feature keywords (for thematic coding)
REASONING_FEATURES = {
    "first_person_absent":   r"\black.*first.?person|no first.?person|missing.*first.?person|lacks.*first.?person|\bno personal|lack.*personal|missing.*personal|doesn.?t.*personal|no first person",
    "first_person_present":  r"\bfirst.?person|\bwe\b|\bour\b",
    "personal_anecdote":     r"\banecdot|\bstory|\bexperience|\bpersonal",
    "formal_stiff":          r"\bformal|\bstiff|\bdry\b|\bstilted|\bmechanical|\bcold\b|\brobotic",
    "polish_flow":           r"\bpolish|\bflow\b|\bsmooth|too perfect|\bclean\b",
    "em_dash":               r"em[\- ]?dash|—",
    "bullets_lists":         r"\bbullet|\blist\b|\benumerat",
    "rhetorical":            r"\brhetor",
    "typo_error":            r"\btypo|\berror|\bmistake|\bgrammar|\bmissing.*period|lowercase|abrupt|incomplete",
    "discontinuity":         r"pieces.*different|out of place|different text|no cohes|no coher|abrupt|splice|disjoint|choppy",
    "generic_vague":         r"\bgeneric|\bvague|\bbland|\bboring",
    "technical_density":     r"\btechnic|\bcomplex|\bjargon|detailed.*coding",
    "conversational":        r"\bconversational|\bcasual|\bchatty",
    "opinion_stance":        r"\bopinion|\bstance|\bargument|extreme",
    "ai_stereotype":         r"\bstereotyp|typical.*ai|\bcliche",
    "punctuation":           r"\bpunctuat|exclamation|\bcomma|question mark",
    "sentence_structure":    r"\bsentence.?length|short sentence|long sentence|fragment|sentence.?level",
    "voice_tone":            r"\btone\b|\bvoice\b",
}

# -----------------------------------------------------------------------------
# Quality score (same logic as quality_check.py)
# -----------------------------------------------------------------------------

def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def quality_score(r: dict) -> float:
    """Composite quality score; higher = better. Used to rank responses for filtering."""
    try:
        dur_min = (_parse_iso(r["completedAt"]) - _parse_iso(r["startedAt"])).total_seconds() / 60
    except Exception:
        dur_min = 0
    passages = r.get("passages", {})
    times = [p.get("timeOnPage", 0) or 0 for p in passages.values()]
    short = sum(1 for t in times if t < 60)
    reasoning = sum(
        1 for p in passages.values()
        if len((p.get("reasoning") or "").strip()) >= 10
    )
    stds = []
    for p in passages.values():
        vs = [p.get(d) for d in LIKERT_DIMS if isinstance(p.get(d), (int, float))]
        if len(vs) >= 2:
            stds.append(statistics.stdev(vs))
    mean_std = statistics.mean(stds) if stds else 0
    origins = [p.get("origin") for p in passages.values() if p.get("origin")]
    uniform = 1 if (len(set(origins)) < 2 and len(origins) == 8) else 0
    return min(dur_min, 60) + reasoning * 5 + mean_std * 20 - short * 5 - uniform * 30


# -----------------------------------------------------------------------------
# Stat helpers
# -----------------------------------------------------------------------------

def binom_two_sided(k: int, n: int, p: float = 0.5) -> float:
    """Two-sided binomial test p-value."""
    if n == 0:
        return float("nan")
    return stats.binomtest(k, n, p, alternative="two-sided").pvalue


def binom_less(k: int, n: int, p: float = 0.5) -> float:
    return stats.binomtest(k, n, p, alternative="less").pvalue


def binom_greater(k: int, n: int, p: float = 0.5) -> float:
    return stats.binomtest(k, n, p, alternative="greater").pvalue


def binom_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Clopper–Pearson exact binomial CI."""
    if n == 0:
        return (float("nan"), float("nan"))
    lo = stats.beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
    hi = stats.beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
    return float(lo), float(hi)


def cohens_d_paired(differences: list[float]) -> float:
    """Cohen's d for paired design: mean(diff) / sd(diff)."""
    if len(differences) < 2:
        return float("nan")
    sd = np.std(differences, ddof=1)
    if sd == 0:
        return 0.0
    return float(np.mean(differences) / sd)


def bh_fdr(pvals: list[float], alpha: float = 0.05) -> list[bool]:
    """Benjamini–Hochberg FDR; returns list of booleans (True = reject H0)."""
    p = np.array(pvals)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    thresh = alpha * (np.arange(1, n + 1) / n)
    passing = ranked <= thresh
    # Monotonic: find largest rank that passes
    if passing.any():
        cutoff = np.max(np.where(passing)[0])
        reject_sorted = np.arange(n) <= cutoff
    else:
        reject_sorted = np.zeros(n, dtype=bool)
    reject = np.empty(n, dtype=bool)
    reject[order] = reject_sorted
    return reject.tolist()


def fleiss_kappa(ratings: np.ndarray) -> float:
    """Fleiss' κ.

    ratings: 2-D array, shape (n_subjects, n_categories), each row is the count
    of raters assigning subject to each category. All row sums equal.
    """
    n_subj, n_cat = ratings.shape
    n_raters = ratings.sum(axis=1)
    if not np.all(n_raters == n_raters[0]):
        return float("nan")
    N = n_raters[0]
    if N < 2 or n_subj < 1:
        return float("nan")
    # Per-subject agreement
    P_i = (np.sum(ratings * (ratings - 1), axis=1)) / (N * (N - 1))
    P_bar = P_i.mean()
    # Per-category proportion
    p_j = ratings.sum(axis=0) / (n_subj * N)
    P_e = np.sum(p_j ** 2)
    if P_e == 1.0:
        return float("nan")
    return float((P_bar - P_e) / (1 - P_e))


def sdt_d_c(hits: int, hit_n: int, fa: int, fa_n: int) -> tuple[float, float]:
    """Signal detection: d' and criterion c. Applies log-linear correction for extreme rates."""
    # Apply 0.5-trial correction if at floor/ceiling
    hit_rate = (hits + 0.5) / (hit_n + 1) if hits in (0, hit_n) else hits / hit_n
    fa_rate = (fa + 0.5) / (fa_n + 1) if fa in (0, fa_n) else fa / fa_n
    z_h = stats.norm.ppf(hit_rate)
    z_fa = stats.norm.ppf(fa_rate)
    d = float(z_h - z_fa)
    c = float(-0.5 * (z_h + z_fa))
    return d, c


def bootstrap_sdt(rows: list[tuple[str, str]], n_boot: int = 10000, seed: int = 42) -> dict:
    """Bootstrap d' and c, 95% CI.

    rows: list of (truth, guess) tuples across all judgments.
    """
    rng = np.random.default_rng(seed)
    rows_arr = np.array(rows)
    n = len(rows_arr)
    ds = np.empty(n_boot)
    cs = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        sample = rows_arr[idx]
        # Compute d', c
        hits = np.sum((sample[:, 0] == "ai") & (sample[:, 1] == "ai"))
        hit_n = np.sum(sample[:, 0] == "ai")
        fa = np.sum((sample[:, 0] == "human") & (sample[:, 1] == "ai"))
        fa_n = np.sum(sample[:, 0] == "human")
        if hit_n == 0 or fa_n == 0:
            ds[b] = np.nan
            cs[b] = np.nan
            continue
        d, c = sdt_d_c(hits, hit_n, fa, fa_n)
        ds[b] = d
        cs[b] = c
    d_lo, d_hi = np.nanpercentile(ds, [2.5, 97.5])
    c_lo, c_hi = np.nanpercentile(cs, [2.5, 97.5])
    return {
        "d_mean": float(np.nanmean(ds)),
        "d_ci": [float(d_lo), float(d_hi)],
        "c_mean": float(np.nanmean(cs)),
        "c_ci": [float(c_lo), float(c_hi)],
    }


# -----------------------------------------------------------------------------
# Analysis sections
# -----------------------------------------------------------------------------

def section_a_classification(responses: list[dict]) -> dict:
    """A. Origin classification: A1–A4."""
    rows = []  # (truth, guess)
    for r in responses:
        for k, p in r["passages"].items():
            truth = TRUTH[k]
            guess = p.get("origin")
            if guess:
                rows.append((truth, guess))

    correct = sum(1 for t, g in rows if t == g)
    total = len(rows)

    ai_rows = [(t, g) for t, g in rows if t == "ai"]
    ai_correct = sum(1 for t, g in ai_rows if g == "ai")
    h_rows = [(t, g) for t, g in rows if t == "human"]
    h_correct = sum(1 for t, g in h_rows if g == "human")

    # A1: AI below chance
    a1_p = binom_less(ai_correct, len(ai_rows), 0.5)
    a1_ci = binom_ci(ai_correct, len(ai_rows))

    # A2: Human above chance
    a2_p = binom_greater(h_correct, len(h_rows), 0.5)
    a2_ci = binom_ci(h_correct, len(h_rows))

    # A3: Overall ≠ chance
    a3_p = binom_two_sided(correct, total, 0.5)
    a3_ci = binom_ci(correct, total)

    # A4: SDT — point estimate + bootstrap
    d_point, c_point = sdt_d_c(ai_correct, len(ai_rows),
                               len(h_rows) - h_correct, len(h_rows))
    sdt_boot = bootstrap_sdt(rows)

    return {
        "n_judgments": total,
        "A1_ai_detection": {
            "hit": ai_correct, "n": len(ai_rows),
            "rate": ai_correct / len(ai_rows),
            "ci_95": a1_ci, "p_below_chance_one_sided": a1_p,
        },
        "A2_human_specificity": {
            "hit": h_correct, "n": len(h_rows),
            "rate": h_correct / len(h_rows),
            "ci_95": a2_ci, "p_above_chance_one_sided": a2_p,
        },
        "A3_overall_accuracy": {
            "hit": correct, "n": total,
            "rate": correct / total,
            "ci_95": a3_ci, "p_two_sided": a3_p,
        },
        "A4_sdt": {
            "d_prime_point": d_point,
            "d_prime_bootstrap_ci": sdt_boot["d_ci"],
            "d_prime_bootstrap_mean": sdt_boot["d_mean"],
            "criterion_c_point": c_point,
            "criterion_c_bootstrap_ci": sdt_boot["c_ci"],
            "criterion_c_bootstrap_mean": sdt_boot["c_mean"],
        },
    }


def section_b_likert(responses: list[dict]) -> dict:
    """B. Likert ratings per dimension — paired Wilcoxon + Cohen's d + FDR."""
    # For each participant, compute mean(AI passages) and mean(human passages) per dim
    per_participant = []  # list of dict: {dim: (ai_mean, h_mean)}
    for r in responses:
        row = {}
        for dim in LIKERT_DIMS:
            ai_vals = [r["passages"][k].get(dim) for k in AI_PASSAGES
                       if isinstance(r["passages"].get(k, {}).get(dim), (int, float))]
            h_vals = [r["passages"][k].get(dim) for k in HUMAN_PASSAGES
                      if isinstance(r["passages"].get(k, {}).get(dim), (int, float))]
            if ai_vals and h_vals:
                row[dim] = (np.mean(ai_vals), np.mean(h_vals))
        per_participant.append(row)

    out = {}
    raw_p = []
    for dim in LIKERT_DIMS:
        pairs = [(p[dim]) for p in per_participant if dim in p]
        ai_means = np.array([x[0] for x in pairs])
        h_means = np.array([x[1] for x in pairs])
        diffs = ai_means - h_means
        # Paired Wilcoxon (signed-rank)
        if len(diffs) >= 5 and np.any(diffs != 0):
            w, p = stats.wilcoxon(ai_means, h_means, zero_method="wilcox", alternative="two-sided")
            p = float(p)
        else:
            w, p = float("nan"), float("nan")
        # Paired t (for completeness)
        if len(diffs) >= 2:
            t_stat, t_p = stats.ttest_rel(ai_means, h_means)
            t_p = float(t_p)
        else:
            t_stat, t_p = float("nan"), float("nan")
        d = cohens_d_paired(diffs.tolist())
        out[dim] = {
            "n_pairs": len(diffs),
            "ai_mean": float(ai_means.mean()) if len(ai_means) else None,
            "human_mean": float(h_means.mean()) if len(h_means) else None,
            "delta": float(diffs.mean()) if len(diffs) else None,
            "cohens_d_paired": d,
            "wilcoxon_W": float(w) if not np.isnan(w) else None,
            "wilcoxon_p": p,
            "ttest_t": float(t_stat) if not np.isnan(t_stat) else None,
            "ttest_p": t_p,
        }
        raw_p.append(p if not np.isnan(p) else 1.0)

    # FDR correction across dimensions
    rejects = bh_fdr(raw_p, alpha=0.05)
    for dim, rej in zip(LIKERT_DIMS, rejects):
        out[dim]["bh_fdr_significant"] = bool(rej)

    return out


def section_c_per_passage(responses: list[dict]) -> dict:
    """C. Per-passage analysis: accuracy, condition comparison, Fleiss' κ."""
    per_passage = {k: {"correct": 0, "total": 0, "guesses": []} for k in TRUTH}
    for r in responses:
        for k, p in r["passages"].items():
            g = p.get("origin")
            if not g:
                continue
            per_passage[k]["total"] += 1
            per_passage[k]["guesses"].append(g)
            if g == TRUTH[k]:
                per_passage[k]["correct"] += 1

    # C1: per-passage binomial
    c1 = {}
    for k, v in per_passage.items():
        c = v["correct"]
        n = v["total"]
        if n > 0:
            p_two = binom_two_sided(c, n, 0.5)
            ci = binom_ci(c, n)
        else:
            p_two, ci = float("nan"), (float("nan"), float("nan"))
        c1[k] = {
            "truth": TRUTH[k], "condition": CONDITIONS[k],
            "correct": c, "n": n, "accuracy": c / n if n else None,
            "ci_95": ci, "p_two_sided_vs_chance": p_two,
        }

    # C2: condition comparison — AI-detection rate by condition
    #   (fraction of raters who called it AI, for each AI passage, grouped by condition)
    cond_data = defaultdict(lambda: {"called_ai": 0, "n": 0})
    for k in AI_PASSAGES:
        cond = CONDITIONS[k]
        cond_data[cond]["called_ai"] += sum(1 for g in per_passage[k]["guesses"] if g == "ai")
        cond_data[cond]["n"] += per_passage[k]["total"]

    # Chi-square: calls × condition (for AI passages only)
    # Rows: conditions; Cols: [called_ai, called_human]
    cond_labels = list(cond_data.keys())
    table = np.array([
        [cond_data[c]["called_ai"], cond_data[c]["n"] - cond_data[c]["called_ai"]]
        for c in cond_labels
    ])
    if table.shape[0] >= 2 and table.min() > 0:
        chi2, chi_p, dof, _ = stats.chi2_contingency(table)
    else:
        chi2, chi_p, dof = float("nan"), float("nan"), 0

    # Pairwise: persona (Dana) vs humanized pipelines (v10.2 + cross-model) pooled
    persona_called = cond_data.get("persona_dana", {}).get("called_ai", 0)
    persona_n = cond_data.get("persona_dana", {}).get("n", 0)
    hum_called = sum(v["called_ai"] for k, v in cond_data.items() if k in ("humanized_fnword", "crossmodel"))
    hum_n = sum(v["n"] for k, v in cond_data.items() if k in ("humanized_fnword", "crossmodel"))
    if persona_n > 0 and hum_n > 0:
        # 2×2 Fisher's exact
        table_2x2 = np.array([
            [persona_called, persona_n - persona_called],
            [hum_called, hum_n - hum_called],
        ])
        fisher_res = stats.fisher_exact(table_2x2, alternative="two-sided")
        fisher_p = float(fisher_res.pvalue)
        fisher_or = float(fisher_res.statistic)
    else:
        fisher_p, fisher_or = float("nan"), float("nan")

    c2 = {
        "by_condition": {
            c: {
                "called_ai": v["called_ai"], "n": v["n"],
                "detection_rate": v["called_ai"] / v["n"] if v["n"] else None,
            }
            for c, v in cond_data.items()
        },
        "chi2_condition_x_call": {"chi2": float(chi2), "dof": int(dof), "p": float(chi_p)},
        "persona_vs_humanized": {
            "persona_detection_rate": persona_called / persona_n if persona_n else None,
            "humanized_detection_rate": hum_called / hum_n if hum_n else None,
            "fisher_odds_ratio": fisher_or,
            "fisher_p_two_sided": fisher_p,
        },
    }

    # C3: Fleiss' κ per passage
    # Each passage = 1 subject; raters = participants; categories = {ai, human}
    kappa_per_passage = {}
    for k in TRUTH:
        guesses = per_passage[k]["guesses"]
        if not guesses:
            continue
        # Ratings: single-row matrix, each "subject" is one passage here,
        # so we treat this as one passage × 2 categories.
        # For Fleiss' proper use we'd have multiple subjects; single-passage
        # inter-rater reliability reduces to agreement proportion, so we report both.
        n_ai = sum(1 for g in guesses if g == "ai")
        n_h = sum(1 for g in guesses if g == "human")
        N = n_ai + n_h
        p_i = (n_ai * (n_ai - 1) + n_h * (n_h - 1)) / (N * (N - 1)) if N >= 2 else float("nan")
        kappa_per_passage[k] = {
            "n_raters": N,
            "majority": "ai" if n_ai > n_h else "human",
            "majority_share": max(n_ai, n_h) / N if N else None,
            "agreement_P_i": p_i,  # within-passage agreement proportion
        }

    # Cross-passage Fleiss κ: each passage is a "subject", categories {ai, human}
    ratings_matrix = []
    for k in TRUTH:
        guesses = per_passage[k]["guesses"]
        n_ai = sum(1 for g in guesses if g == "ai")
        n_h = sum(1 for g in guesses if g == "human")
        ratings_matrix.append([n_ai, n_h])
    ratings_matrix = np.array(ratings_matrix)
    # Trim to passages with identical N (the full cohort answered all)
    min_N = ratings_matrix.sum(axis=1).min()
    max_N = ratings_matrix.sum(axis=1).max()
    if min_N == max_N and min_N > 1:
        kappa_overall = fleiss_kappa(ratings_matrix)
    else:
        kappa_overall = float("nan")

    c3 = {
        "per_passage": kappa_per_passage,
        "fleiss_kappa_across_passages": kappa_overall,
    }

    return {"C1_per_passage": c1, "C2_condition": c2, "C3_reliability": c3}


def section_d_best_quality(responses: list[dict]) -> dict:
    """D. 'Best quality' pick."""
    picks = [r.get("debrief", {}).get("bestAi") for r in responses
             if r.get("debrief", {}).get("bestAi")]
    picks = [p for p in picks if p in TRUTH]
    n = len(picks)
    ai_picks = sum(1 for p in picks if TRUTH[p] == "ai")

    # Base rate: 5/8 = 0.625 (5 AI passages out of 8)
    base_rate = len(AI_PASSAGES) / len(TRUTH)
    p_two = binom_two_sided(ai_picks, n, base_rate) if n > 0 else float("nan")
    ci = binom_ci(ai_picks, n)

    # Distribution across all 8 passages
    dist = Counter(picks)
    return {
        "n_responses_with_pick": n,
        "ai_pick_count": ai_picks,
        "ai_pick_rate": ai_picks / n if n > 0 else None,
        "ai_base_rate": base_rate,
        "ci_95": ci,
        "p_vs_base_rate_two_sided": p_two,
        "distribution": {k: dist.get(k, 0) for k in sorted(TRUTH)},
    }


def section_i_machine_linkage(responses: list[dict], db_path: Path = HUMANIZATION_DB) -> dict:
    """I. Join per-passage machine-detector scores with human detection rates.

    For each of the 8 passages, pull the latest detector score from humanization.db
    and compare to the crowd's AI-call rate. Headline: Spearman correlation between
    each detector's score and the human detection rate.
    """
    # 1. Compute human detection rate per passage (P(crowd calls 'ai'))
    crowd = {k: {"called_ai": 0, "n": 0} for k in TRUTH}
    for r in responses:
        for k, p in r["passages"].items():
            g = p.get("origin")
            if not g:
                continue
            crowd[k]["n"] += 1
            if g == "ai":
                crowd[k]["called_ai"] += 1

    human_call_ai_rate = {
        k: (v["called_ai"] / v["n"]) if v["n"] else None
        for k, v in crowd.items()
    }

    # 2. Pull latest detector scores from the DB
    scores: dict[str, dict[str, float]] = {k: {} for k in TRUTH}
    missing: list[str] = []
    if not db_path.exists():
        return {
            "error": f"humanization.db not found at {db_path}",
            "human_call_ai_rate": human_call_ai_rate,
        }
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        for passage, label in PASSAGE_LABELS.items():
            for det in MACHINE_DETECTORS:
                cur.execute(
                    """
                    SELECT r.ai_score, r.prediction
                    FROM samples s
                    JOIN detector_runs r ON r.sample_id = s.id
                    WHERE s.label = ? AND r.detector = ?
                    ORDER BY r.run_at DESC
                    LIMIT 1
                    """,
                    (label, det),
                )
                row = cur.fetchone()
                if row is None:
                    missing.append(f"{passage}/{det}")
                else:
                    scores[passage][det] = {
                        "ai_score": float(row[0]) if row[0] is not None else None,
                        "prediction": row[1],
                    }
    finally:
        conn.close()

    # 3. Per-passage row (join crowd + detectors)
    rows = []
    for k in sorted(TRUTH):
        row = {
            "passage": k,
            "truth": TRUTH[k],
            "condition": CONDITIONS[k],
            "db_label": PASSAGE_LABELS[k],
            "human_ai_call_rate": human_call_ai_rate[k],
            "human_n": crowd[k]["n"],
            "detectors": scores[k],
        }
        rows.append(row)

    # 4. Spearman correlation per detector × human AI-call rate (across 8 passages)
    #    Test H0: ρ = 0. Report for all 8; also report for AI-only (5 passages) since
    #    that's where the paradox lives.
    corr_all = {}
    corr_ai_only = {}
    ai_only_idx = [i for i, r in enumerate(rows) if r["truth"] == "ai"]
    human_rate_all = np.array([r["human_ai_call_rate"] for r in rows], dtype=float)
    human_rate_ai = human_rate_all[ai_only_idx]

    for det in MACHINE_DETECTORS:
        scores_all = np.array(
            [rows[i]["detectors"].get(det, {}).get("ai_score") for i in range(len(rows))],
            dtype=float,
        )
        # All-8 correlation
        mask = ~np.isnan(scores_all) & ~np.isnan(human_rate_all)
        if mask.sum() >= 3:
            rho, p = stats.spearmanr(scores_all[mask], human_rate_all[mask])
            corr_all[det] = {"spearman_rho": float(rho), "p_two_sided": float(p), "n": int(mask.sum())}
        else:
            corr_all[det] = {"spearman_rho": None, "p_two_sided": None, "n": int(mask.sum())}

        # AI-only correlation (5 passages)
        scores_ai = scores_all[ai_only_idx]
        mask_ai = ~np.isnan(scores_ai) & ~np.isnan(human_rate_ai)
        if mask_ai.sum() >= 3:
            rho_ai, p_ai = stats.spearmanr(scores_ai[mask_ai], human_rate_ai[mask_ai])
            corr_ai_only[det] = {"spearman_rho": float(rho_ai), "p_two_sided": float(p_ai), "n": int(mask_ai.sum())}
        else:
            corr_ai_only[det] = {"spearman_rho": None, "p_two_sided": None, "n": int(mask_ai.sum())}

    # 5. Crowd-vs-detector agreement on binary classification (Cohen's κ).
    #    Detector label: ai_score ≥ 0.5 → "ai", else "human".
    #    Crowd label:   majority rule (called_ai / n ≥ 0.5 → "ai", else "human").
    crowd_labels = {k: ("ai" if (crowd[k]["called_ai"] / crowd[k]["n"]) >= 0.5 else "human")
                    for k in TRUTH if crowd[k]["n"] > 0}
    detector_kappa = {}
    for det in MACHINE_DETECTORS:
        crowd_seq, det_seq = [], []
        for k in sorted(TRUTH):
            sc = rows[ord(k) - ord("A")]["detectors"].get(det, {}).get("ai_score")
            if sc is None:
                continue
            det_lab = "ai" if sc >= 0.5 else "human"
            crowd_seq.append(crowd_labels[k])
            det_seq.append(det_lab)
        # Cohen's κ
        if len(crowd_seq) >= 2:
            # Build confusion matrix
            cats = ["ai", "human"]
            mat = np.zeros((2, 2), dtype=int)
            for c, d in zip(crowd_seq, det_seq):
                mat[cats.index(c)][cats.index(d)] += 1
            po = np.trace(mat) / mat.sum()
            pe_sum = 0
            for i in range(2):
                pe_sum += (mat[i, :].sum() / mat.sum()) * (mat[:, i].sum() / mat.sum())
            kappa = (po - pe_sum) / (1 - pe_sum) if pe_sum < 1 else float("nan")
            detector_kappa[det] = {
                "cohens_kappa_crowd_vs_detector": float(kappa),
                "n_passages": len(crowd_seq),
                "agreement_rate": float(po),
                "crowd_labels": crowd_seq,
                "detector_labels": det_seq,
            }

    # 6. Ground-truth accuracy of detectors (for reference)
    detector_accuracy = {}
    for det in MACHINE_DETECTORS:
        correct = 0
        n = 0
        for k in TRUTH:
            sc = rows[ord(k) - ord("A")]["detectors"].get(det, {}).get("ai_score")
            if sc is None:
                continue
            pred = "ai" if sc >= 0.5 else "human"
            truth = TRUTH[k]
            n += 1
            if pred == truth:
                correct += 1
        detector_accuracy[det] = {"correct": correct, "n": n, "accuracy": correct / n if n else None}

    return {
        "per_passage": rows,
        "missing_scores": missing,
        "spearman_all_passages": corr_all,
        "spearman_ai_only": corr_ai_only,
        "crowd_vs_detector_kappa": detector_kappa,
        "detector_accuracy_vs_truth": detector_accuracy,
        "human_crowd_accuracy_vs_truth": {
            "overall": sum(1 for k in TRUTH
                           if ((crowd[k]["called_ai"] / crowd[k]["n"]) >= 0.5) == (TRUTH[k] == "ai")
                           ) / len(TRUTH),
        },
    }


def section_j_quality_correlations(responses: list[dict], db_path: Path = HUMANIZATION_DB) -> dict:
    """J. Correlate human Likert quality ratings with linguistic metrics and detector scores.

    For each of the 8 passages:
      - compute the mean quality rating across the 30 raters
      - fetch the passage's linguistic and info-theoretic features from humanization.db
      - fetch its detector scores
      - Spearman rank correlation across the 8 passages between quality and each metric
    """
    # 1. Mean quality (and also mean of all 6 Likert dims) per passage
    per_passage_quality: dict[str, dict[str, float]] = {k: {} for k in TRUTH}
    for k in TRUTH:
        dim_values = {dim: [] for dim in LIKERT_DIMS}
        for r in responses:
            p = r["passages"].get(k, {})
            for dim in LIKERT_DIMS:
                v = p.get(dim)
                if isinstance(v, (int, float)):
                    dim_values[dim].append(v)
        for dim, vs in dim_values.items():
            per_passage_quality[k][dim] = float(np.mean(vs)) if vs else None
        # composite "perceived quality" = mean of clarity + engagement + authority + quality
        # (drops "confidence" and "naturalness", which can mean different things)
        comp = [per_passage_quality[k][d] for d in ("clarity", "engagement", "authority", "quality")
                if per_passage_quality[k][d] is not None]
        per_passage_quality[k]["_composite"] = float(np.mean(comp)) if comp else None

    # 2. Fetch linguistic + info-theoretic features for each passage
    linguistic: dict[str, dict[str, float]] = {k: {} for k in TRUTH}
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.cursor()
            for passage, label in PASSAGE_LABELS.items():
                # Resolve sample_id
                cur.execute("SELECT id FROM samples WHERE label = ?", (label,))
                row = cur.fetchone()
                if row is None:
                    continue
                sample_id = row[0]
                # Per-metric fetch from the right table
                for col, _ in LINGUISTIC_METRICS:
                    table = LING_TABLE[col]
                    cur.execute(f"SELECT {col} FROM {table} WHERE sample_id = ?", (sample_id,))
                    rr = cur.fetchone()
                    if rr and rr[0] is not None:
                        linguistic[passage][col] = float(rr[0])
        finally:
            conn.close()

    # 3. Fetch detector scores (same as Section I)
    detector_scores: dict[str, dict[str, float]] = {k: {} for k in TRUTH}
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.cursor()
            for passage, label in PASSAGE_LABELS.items():
                for det in MACHINE_DETECTORS:
                    cur.execute(
                        """
                        SELECT r.ai_score FROM samples s
                        JOIN detector_runs r ON r.sample_id = s.id
                        WHERE s.label = ? AND r.detector = ?
                        ORDER BY r.run_at DESC LIMIT 1
                        """,
                        (label, det),
                    )
                    rr = cur.fetchone()
                    if rr and rr[0] is not None:
                        detector_scores[passage][det] = float(rr[0])
        finally:
            conn.close()

    # 4. Spearman correlations
    passages = sorted(TRUTH)
    ai_only = [k for k in passages if TRUTH[k] == "ai"]

    def corr(x: list[float], y: list[float]) -> dict:
        xa, ya = np.array(x, dtype=float), np.array(y, dtype=float)
        mask = ~np.isnan(xa) & ~np.isnan(ya)
        if mask.sum() < 3:
            return {"rho": None, "p": None, "n": int(mask.sum())}
        rho, p = stats.spearmanr(xa[mask], ya[mask])
        return {"rho": float(rho), "p": float(p), "n": int(mask.sum())}

    # Quality dimensions to correlate: composite + overall_quality + naturalness
    quality_axes = ("_composite", "quality", "naturalness", "clarity")

    corr_linguistic_all = {ax: {} for ax in quality_axes}
    corr_linguistic_ai  = {ax: {} for ax in quality_axes}
    corr_detector_all   = {ax: {} for ax in quality_axes}
    corr_detector_ai    = {ax: {} for ax in quality_axes}

    for ax in quality_axes:
        qa_all = [per_passage_quality[k].get(ax) for k in passages]
        qa_ai  = [per_passage_quality[k].get(ax) for k in ai_only]

        for col, _ in LINGUISTIC_METRICS:
            x_all = [linguistic[k].get(col) for k in passages]
            x_ai  = [linguistic[k].get(col) for k in ai_only]
            corr_linguistic_all[ax][col] = corr(x_all, qa_all)
            corr_linguistic_ai[ax][col]  = corr(x_ai,  qa_ai)

        for det in MACHINE_DETECTORS:
            x_all = [detector_scores[k].get(det) for k in passages]
            x_ai  = [detector_scores[k].get(det) for k in ai_only]
            corr_detector_all[ax][det] = corr(x_all, qa_all)
            corr_detector_ai[ax][det]  = corr(x_ai,  qa_ai)

    # 5. Per-passage table for the paper
    per_passage_table = []
    for k in passages:
        row = {
            "passage": k,
            "truth": TRUTH[k],
            "condition": CONDITIONS[k],
            "quality_mean": per_passage_quality[k].get("quality"),
            "composite_quality_mean": per_passage_quality[k].get("_composite"),
            "naturalness_mean": per_passage_quality[k].get("naturalness"),
            "clarity_mean": per_passage_quality[k].get("clarity"),
            "density_variance": linguistic[k].get("density_variance"),
            "burstiness": linguistic[k].get("burstiness"),
            "first_person_per_1k": linguistic[k].get("first_person_per_1k"),
            "pangram_api": detector_scores[k].get("pangram_api"),
            "gptzero_api": detector_scores[k].get("gptzero_api"),
            "copyleaks_api": detector_scores[k].get("copyleaks_api"),
            "binoculars": detector_scores[k].get("binoculars"),
        }
        per_passage_table.append(row)

    return {
        "per_passage_table": per_passage_table,
        "spearman": {
            "linguistic_all_passages": corr_linguistic_all,
            "linguistic_ai_only":      corr_linguistic_ai,
            "detector_all_passages":   corr_detector_all,
            "detector_ai_only":        corr_detector_ai,
        },
    }


def section_h_reasoning(responses: list[dict]) -> dict:
    """H. Reasoning-text feature mentions × passage condition × correctness."""
    # For each (passage, guess, truth) with non-empty reasoning, which features are mentioned
    feature_counts = defaultdict(lambda: defaultdict(int))  # feature → condition → count
    feature_correct = defaultdict(lambda: {"correct": 0, "incorrect": 0})
    total_by_cond = defaultdict(int)

    for r in responses:
        for k, p in r["passages"].items():
            txt = (p.get("reasoning") or "").strip()
            if not txt:
                continue
            low = txt.lower()
            cond = CONDITIONS[k]
            guess = p.get("origin")
            correct = (guess == TRUTH[k])
            total_by_cond[cond] += 1
            for feat, pattern in REASONING_FEATURES.items():
                if re.search(pattern, low):
                    feature_counts[feat][cond] += 1
                    if correct:
                        feature_correct[feat]["correct"] += 1
                    else:
                        feature_correct[feat]["incorrect"] += 1

    # Organize output
    h1 = {}
    for feat, cond_counts in feature_counts.items():
        fc = feature_correct[feat]
        n_mentions = fc["correct"] + fc["incorrect"]
        accuracy_given_mention = fc["correct"] / n_mentions if n_mentions else None
        h1[feat] = {
            "mentions_total": n_mentions,
            "mentions_by_condition": dict(cond_counts),
            "accuracy_when_mentioned": accuracy_given_mention,
        }

    # Top features
    top = sorted(h1.items(), key=lambda kv: kv[1]["mentions_total"], reverse=True)[:10]
    top_summary = [
        {"feature": f, **v} for f, v in top
    ]

    return {
        "n_reasoning_entries_by_condition": dict(total_by_cond),
        "features_full": h1,
        "top_10_by_mentions": top_summary,
    }


# -----------------------------------------------------------------------------
# Printing helpers
# -----------------------------------------------------------------------------

def fmt_p(p: float) -> str:
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "  n/a"
    if p < 0.001:
        return "<.001"
    return f"{p:.3f}"


def fmt_ci(lo: float, hi: float) -> str:
    if np.isnan(lo) or np.isnan(hi):
        return "n/a"
    return f"[{lo:.3f}, {hi:.3f}]"


def print_results(results: dict) -> None:
    a = results["sections"]["A_classification"]
    b = results["sections"]["B_likert"]
    c = results["sections"]["C_per_passage"]
    d = results["sections"]["D_best_quality"]
    h = results["sections"]["H_reasoning"]
    i_sec = results["sections"]["I_machine_linkage"]
    j_sec = results["sections"]["J_quality_correlations"]

    print("\n" + "=" * 78)
    print(f"  SURVEY ANALYSIS — n={results['meta']['n_responses']} "
          f"(filter={results['meta']['filter']}, kept={results['meta']['n_kept']})")
    print("=" * 78)

    # ---- A ----
    print("\n[A] Origin classification")
    print("-" * 78)
    print(f"  A1 — AI-detection rate:   "
          f"{a['A1_ai_detection']['hit']}/{a['A1_ai_detection']['n']} "
          f"= {a['A1_ai_detection']['rate']:.1%}  "
          f"95% CI {fmt_ci(*a['A1_ai_detection']['ci_95'])}  "
          f"p(below chance)={fmt_p(a['A1_ai_detection']['p_below_chance_one_sided'])}")
    print(f"  A2 — Human-specificity:   "
          f"{a['A2_human_specificity']['hit']}/{a['A2_human_specificity']['n']} "
          f"= {a['A2_human_specificity']['rate']:.1%}  "
          f"95% CI {fmt_ci(*a['A2_human_specificity']['ci_95'])}  "
          f"p(above chance)={fmt_p(a['A2_human_specificity']['p_above_chance_one_sided'])}")
    print(f"  A3 — Overall accuracy:    "
          f"{a['A3_overall_accuracy']['hit']}/{a['A3_overall_accuracy']['n']} "
          f"= {a['A3_overall_accuracy']['rate']:.1%}  "
          f"95% CI {fmt_ci(*a['A3_overall_accuracy']['ci_95'])}  "
          f"p(≠chance)={fmt_p(a['A3_overall_accuracy']['p_two_sided'])}")
    print(f"  A4 — SDT:  d' = {a['A4_sdt']['d_prime_point']:.3f}  "
          f"95% CI {fmt_ci(*a['A4_sdt']['d_prime_bootstrap_ci'])}   "
          f"c = {a['A4_sdt']['criterion_c_point']:.3f}  "
          f"95% CI {fmt_ci(*a['A4_sdt']['criterion_c_bootstrap_ci'])}")
    print("     (d' ≈ 0 → no discrimination; c > 0 → bias toward 'human' response)")

    # ---- B ----
    print("\n[B] Likert ratings — AI vs Human (paired, per participant)")
    print("-" * 78)
    print(f"  {'dim':<14} {'AI':>6} {'Human':>6} {'Δ':>7} {'d':>6} {'Wilcoxon p':>12} {'FDR-sig':>8}")
    for dim in LIKERT_DIMS:
        row = b[dim]
        sig = "✓" if row["bh_fdr_significant"] else ""
        print(f"  {dim:<14} "
              f"{row['ai_mean']:>6.2f} {row['human_mean']:>6.2f} "
              f"{row['delta']:>+7.2f} {row['cohens_d_paired']:>+6.2f} "
              f"{fmt_p(row['wilcoxon_p']):>12} {sig:>8}")

    # ---- C1 ----
    print("\n[C1] Per-passage accuracy")
    print("-" * 78)
    print(f"  {'pass':<6} {'truth':<6} {'condition':<20} {'correct':>8} {'acc':>6} "
          f"{'95% CI':>18} {'p (vs .5)':>10}")
    for k in sorted(TRUTH):
        row = c["C1_per_passage"][k]
        print(f"  {k:<6} {row['truth']:<6} {row['condition']:<20} "
              f"{row['correct']:>4}/{row['n']:<3} {row['accuracy']:>6.1%} "
              f"{fmt_ci(*row['ci_95']):>18} {fmt_p(row['p_two_sided_vs_chance']):>10}")

    # ---- C2 ----
    print("\n[C2] AI-detection rate by condition")
    print("-" * 78)
    for cond, v in c["C2_condition"]["by_condition"].items():
        if v["n"]:
            print(f"  {cond:<22} {v['called_ai']}/{v['n']} = {v['detection_rate']:.1%}")
    chi = c["C2_condition"]["chi2_condition_x_call"]
    rh = c["C2_condition"]["persona_vs_humanized"]
    print(f"  χ²(condition × call) = {chi['chi2']:.2f}, dof={chi['dof']}, p={fmt_p(chi['p'])}")
    if rh["persona_detection_rate"] is not None:
        print(f"  Persona (Dana) vs humanized pooled: {rh['persona_detection_rate']:.1%} vs "
              f"{rh['humanized_detection_rate']:.1%}  "
              f"OR={rh['fisher_odds_ratio']:.3f}, Fisher p={fmt_p(rh['fisher_p_two_sided'])}")

    # ---- C3 ----
    print("\n[C3] Inter-rater reliability (Fleiss' κ across passages)")
    print("-" * 78)
    k_overall = c["C3_reliability"]["fleiss_kappa_across_passages"]
    if not np.isnan(k_overall):
        interp = ("poor" if k_overall < 0.2 else
                  "fair" if k_overall < 0.4 else
                  "moderate" if k_overall < 0.6 else "substantial")
        print(f"  Fleiss' κ = {k_overall:.3f} ({interp} agreement)")
    else:
        print(f"  Fleiss' κ = n/a (uneven rater counts across passages)")
    print(f"  Per-passage majority share:")
    for k in sorted(TRUTH):
        rel = c["C3_reliability"]["per_passage"][k]
        truth = TRUTH[k]
        print(f"    {k} ({truth:5}): majority={rel['majority']:5}  "
              f"share={rel['majority_share']:.1%}  "
              f"agreement P_i={rel['agreement_P_i']:.3f}")

    # ---- D ----
    print("\n[D] 'Best quality' pick — AI base rate 5/8 = 62.5%")
    print("-" * 78)
    print(f"  AI passage picked as best: {d['ai_pick_count']}/{d['n_responses_with_pick']} = "
          f"{d['ai_pick_rate']:.1%}  "
          f"95% CI {fmt_ci(*d['ci_95'])}  "
          f"p(vs .625)={fmt_p(d['p_vs_base_rate_two_sided'])}")
    print(f"  Distribution: " +
          "  ".join(f"{k}({TRUTH[k][0]}):{d['distribution'][k]}" for k in sorted(TRUTH)))

    # ---- H ----
    print("\n[H] Reasoning-text feature mentions (top 10)")
    print("-" * 78)
    print(f"  {'feature':<22} {'mentions':>9} {'acc when cited':>16}")
    for f in h["top_10_by_mentions"]:
        acc = f["accuracy_when_mentioned"]
        acc_str = f"{acc:.1%}" if acc is not None else "n/a"
        print(f"  {f['feature']:<22} {f['mentions_total']:>9} {acc_str:>16}")

    # ---- I ----
    print("\n[I] Machine detectors vs human crowd")
    print("-" * 78)
    print(f"  {'pass':<5} {'truth':<6} {'condition':<18} {'crowd AI%':>10} {'Pangram':>8} "
          f"{'GPTZero':>8} {'Copyleaks':>10} {'Binoc':>7}")
    for row in i_sec["per_passage"]:
        dets = row["detectors"]
        def fmt(det):
            v = dets.get(det, {}).get("ai_score")
            return f"{v:.2f}" if v is not None else "  n/a"
        crowd_pct = f"{row['human_ai_call_rate']:.1%}" if row["human_ai_call_rate"] is not None else "n/a"
        print(f"  {row['passage']:<5} {row['truth']:<6} {row['condition']:<18} "
              f"{crowd_pct:>10} {fmt('pangram_api'):>8} {fmt('gptzero_api'):>8} "
              f"{fmt('copyleaks_api'):>10} {fmt('binoculars'):>7}")

    print(f"\n  Spearman ρ (detector score × crowd AI-call rate) across 8 passages:")
    for det, v in i_sec["spearman_all_passages"].items():
        rho = v["spearman_rho"]
        p = v["p_two_sided"]
        rho_s = f"{rho:+.3f}" if rho is not None else "  n/a"
        print(f"    {det:<15} ρ={rho_s}  p={fmt_p(p):<6}  (n={v['n']})")

    print(f"\n  Spearman ρ (AI passages only, n=5):")
    for det, v in i_sec["spearman_ai_only"].items():
        rho = v["spearman_rho"]
        p = v["p_two_sided"]
        rho_s = f"{rho:+.3f}" if rho is not None else "  n/a"
        print(f"    {det:<15} ρ={rho_s}  p={fmt_p(p):<6}  (n={v['n']})")

    print(f"\n  Binary-label agreement (crowd majority vs detector threshold ≥ .5):")
    print(f"    {'detector':<15} {'κ (crowd×det)':>14} {'raw agree':>11} {'det acc vs truth':>18}")
    for det in MACHINE_DETECTORS:
        kap = i_sec["crowd_vs_detector_kappa"].get(det, {})
        det_acc = i_sec["detector_accuracy_vs_truth"].get(det, {})
        k_val = kap.get("cohens_kappa_crowd_vs_detector")
        k_str = f"{k_val:+.3f}" if k_val is not None and not np.isnan(k_val) else "  n/a"
        agree = kap.get("agreement_rate")
        agree_s = f"{agree:.1%}" if agree is not None else "n/a"
        acc = det_acc.get("accuracy")
        acc_s = f"{acc:.1%} ({det_acc.get('correct',0)}/{det_acc.get('n',0)})" if acc is not None else "n/a"
        print(f"    {det:<15} {k_str:>14} {agree_s:>11} {acc_s:>18}")

    crowd_overall = i_sec["human_crowd_accuracy_vs_truth"]["overall"]
    print(f"\n  Crowd-majority accuracy (8 passages): {crowd_overall:.1%}  "
          f"vs best machine detector")

    # ---- J ----
    print("\n[J] Quality rating × metrics (Spearman ρ across 8 passages)")
    print("-" * 78)
    print("  Composite quality = mean(clarity, engagement, authority, quality)\n")
    print(f"  Linguistic metrics × composite quality:")
    print(f"    {'metric':<34} {'ρ (all 8)':>11} {'p':>7}   {'ρ (AI 5)':>10} {'p':>7}")
    for col, lbl in LINGUISTIC_METRICS:
        a = j_sec["spearman"]["linguistic_all_passages"]["_composite"].get(col, {})
        i5 = j_sec["spearman"]["linguistic_ai_only"]["_composite"].get(col, {})
        def _fmt(x):
            v = x.get("rho")
            return f"{v:+.3f}" if v is not None else "  n/a"
        pa = a.get("p"); pi = i5.get("p")
        print(f"    {lbl:<34} {_fmt(a):>11} {fmt_p(pa):>7}   {_fmt(i5):>10} {fmt_p(pi):>7}")

    print(f"\n  Detector scores × composite quality:")
    print(f"    {'detector':<34} {'ρ (all 8)':>11} {'p':>7}   {'ρ (AI 5)':>10} {'p':>7}")
    for det in MACHINE_DETECTORS:
        a = j_sec["spearman"]["detector_all_passages"]["_composite"].get(det, {})
        i5 = j_sec["spearman"]["detector_ai_only"]["_composite"].get(det, {})
        def _fmt(x):
            v = x.get("rho")
            return f"{v:+.3f}" if v is not None else "  n/a"
        pa = a.get("p"); pi = i5.get("p")
        print(f"    {det:<34} {_fmt(a):>11} {fmt_p(pa):>7}   {_fmt(i5):>10} {fmt_p(pi):>7}")

    print("\n" + "=" * 78)
    print(f"  Written: {results['meta']['output_path']}")
    print("=" * 78 + "\n")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--path", default=str(DEFAULT_PATH), help="input responses JSON")
    p.add_argument("--keep", type=int, default=30, help="top-N by quality score to analyze (default 30)")
    p.add_argument("--no-filter", action="store_true", help="use all responses (ignore --keep)")
    p.add_argument("--exclude", default="", help="comma-separated response numbers to drop explicitly (overrides --keep)")
    p.add_argument("--out", default=str(OUT_PATH), help="output JSON path")
    args = p.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"error: {path} does not exist", file=sys.stderr)
        return 1

    data = json.loads(path.read_text())
    all_resps = data.get("responses", [])
    total_n = len(all_resps)

    if args.exclude.strip():
        drop_set = {int(x.strip()) for x in args.exclude.split(",") if x.strip()}
        kept = [r for r in all_resps if r.get("_meta", {}).get("responseNumber") not in drop_set]
        filt_label = f"explicit-exclude-{sorted(drop_set)}"
    elif args.no_filter:
        kept = all_resps
        filt_label = "none"
    else:
        ranked = sorted(all_resps, key=quality_score, reverse=True)
        kept = ranked[:args.keep]
        filt_label = f"top-{args.keep}-by-quality-score"

    results = {
        "meta": {
            "input_path": str(path),
            "n_responses": total_n,
            "n_kept": len(kept),
            "filter": filt_label,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "output_path": args.out,
            "truth_map": TRUTH,
            "conditions": CONDITIONS,
        },
        "sections": {
            "A_classification": section_a_classification(kept),
            "B_likert":         section_b_likert(kept),
            "C_per_passage":    section_c_per_passage(kept),
            "D_best_quality":   section_d_best_quality(kept),
            "H_reasoning":      section_h_reasoning(kept),
            "I_machine_linkage": section_i_machine_linkage(kept),
            "J_quality_correlations": section_j_quality_correlations(kept),
        },
    }

    Path(args.out).write_text(json.dumps(results, indent=2, default=str))
    print_results(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
