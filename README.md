# The Detector Paradox: Why Evading AI Detection Removes the Features Readers Value

Replication materials for the paper *The Detector Paradox* (Diamond, 2026).

**Paper version**: v0.9 (April 2026)
**Zenodo DOI**: [10.5281/zenodo.19767696](https://doi.org/10.5281/zenodo.19767696) (version-specific) · concept DOI [10.5281/zenodo.19767695](https://doi.org/10.5281/zenodo.19767695) (always-newest)
**Author**: Lance Diamond, independent researcher ([contact](mailto:lance.a.diamond@gmail.com))

## What this repository contains

Every data file, script, prompt, and figure required to reproduce the paper's findings from raw data:

```
detector-paradox/
├── paper/
│   ├── paper_v09.md              Paper source (markdown; render via pandoc)
│   ├── paper_v09.docx            Rendered paper with embedded figures
│   └── figures_v09/              Seven paper figures + Python scripts producing them
├── analysis/
│   ├── survey_analysis.py        Statistical analysis pipeline (§5.5, Appendix C)
│   ├── generate_paper_tables.py  Table generator + validator against source data
│   └── requirements.txt          Python package versions
├── data/
│   ├── humanization.db.gz        34 corpus documents × 22 linguistic + 6 info-theoretic features + 4 detector scores (gzipped to 63 MB; see Setup for one-time decompress step)
│   ├── survey_results_n33.json   Full statistical output, pre-registered n=33 cohort (PRIMARY)
│   ├── survey_results_n43.json   Full statistical output, unfiltered n=43 cohort (sensitivity check)
│   ├── survey_results_n37.json   Earlier under-applied filter (kept for reproducibility audit)
│   ├── responses_anonymized.json Raw survey responses, PIDs stripped
│   └── persona_dana_chen.txt     The 474-word Dana voice prompt
├── survey/                       Cloudflare Worker code administering the blind-evaluation study
│   ├── src/worker.js
│   ├── public/index.html
│   ├── anonymize_responses.py    Script that produced data/responses_anonymized.json
│   └── wrangler.toml.example     Config template (API keys redacted)
├── LICENSE                       MIT (applies to all code)
├── LICENSE-DATA                  CC-BY 4.0 (applies to humanization.db, JSONs, paper prose)
└── README.md                     This file
```

## Quick facts

| | |
|---|---|
| Corpus size | 34 documents × ~1,500 words each |
| Corpus conditions | 6 human + 7 persona-engineered (Dana) + 7 surgical v10.2 + 7 cross-model v1 + 7 cross-model v2 |
| AI detectors evaluated | 4 (Pangram, GPTZero, Copyleaks, Binoculars) |
| Survey participants (enrolled) | 43 (38 Prolific + 5 organic) |
| Survey participants (primary analysis) | 33 (pre-registered reading-rate exclusion, ≤ 500 WPM) |
| Survey passages | 8 (3 human + 1 persona + 1 surgical + 3 cross-model) |
| Primary analysis software | Python 3.11, scipy 1.17.1, numpy 2.4.4 |

## Reproducing the paper's findings

### Prerequisites

- Python 3.11 or later
- Ability to install from requirements.txt
- (Optional) `pandoc` for rendering the markdown paper to docx/pdf

### Setup

```bash
git clone https://github.com/lance-a-diamond/detector-paradox.git
cd detector-paradox
python3 -m venv .venv
source .venv/bin/activate
pip install -r analysis/requirements.txt

# One-time: decompress the corpus database (gzipped to fit GitHub's per-file limit)
gunzip -k data/humanization.db.gz
```

After this, `data/humanization.db` is the working SQLite file used by all analysis and figure scripts. The compressed `.gz` version remains in the repository as the canonical artifact; the decompressed `.db` is git-ignored.

### Reproduce the primary statistical analysis (n=33)

```bash
cd analysis
python3 survey_analysis.py --exclude 3,5,6,29,37,38,1,2,17,24 --out ../data/survey_results_n33.json
```

This is the pre-registered primary analysis. The exclude list corresponds to the ten participants whose mean page-based reading rates exceeded 500 WPM (see paper §5.5.1 for the Carver/Rayner pre-registration rationale).

### Reproduce the sensitivity-check analysis (n=43 unfiltered)

```bash
python3 survey_analysis.py --no-filter --out ../data/survey_results_n43.json
```

### Verify every table in the paper matches source data

```bash
python3 generate_paper_tables.py --validate
```

Expected output: `✓ All tables match source-of-truth data`. If any table differs from the authoritative source-of-truth (humanization.db + survey_results_n33.json), the validator will print a unified-diff-style mismatch report naming the specific rows and expected-vs-actual values.

### Reproduce any single table

```bash
python3 generate_paper_tables.py --table 8    # prints Table 8 markdown
```

Valid table IDs: `1, 2, 3, 4, 4a, 4b, 5, 6, 7, 8, 9`.

### Reproduce any single figure

```bash
cd ../paper/figures_v09
python3 fig1_hero_paradox.py             # Figure 1: The paradox, in one picture
python3 fig6_crowd_vs_detector.py        # Figure 6: Machine detectors vs crowd
python3 fig7_reader_quality_per_passage.py  # Figure 7: Reader quality per passage
python3 generate_v09_figures.py          # Figures 2-5 (radar, voice, density, detector bars)
```

All figures read from `../../data/survey_results_n33.json` and `../../data/humanization.db`.

## Data schemas

### `humanization.db`

SQLite database with the following tables:

| Table | Purpose |
|---|---|
| `samples` | 34 corpus documents: label, kind, category, word count, full text content |
| `linguistic_features` | 22 linguistic metrics per sample (FPS, FPP, contractions, burstiness, etc.) |
| `info_theoretic_features` | 6 metrics (density variance, redundancy, consecutive similarity, etc.) |
| `detector_runs` | Detector ai_scores per (sample × detector × run) |
| `iterations` | Pipeline-stage lineage (which sample → which output) |

Run `sqlite3 data/humanization.db '.schema'` for complete DDL.

### `survey_results_n33.json` (primary), `survey_results_n43.json`, `survey_results_n37.json`

Nested JSON with these top-level sections:

- `A_classification`: AI-detection rate, human-specificity, overall accuracy, SDT d′ and c with bootstrap CIs
- `B_likert`: per-dimension Likert deltas, Wilcoxon p-values, BH-FDR results
- `C_per_passage`: per-passage accuracy, condition-level comparisons, inter-rater reliability
- `D_best_quality`: "which passage was highest quality?" pick distribution
- `H_reasoning`: free-text reasoning feature analysis
- `I_machine_linkage`: Spearman ρ between each detector and crowd AI-call rate
- `J_quality_correlations`: Spearman ρ between linguistic metrics and reader-perceived quality

### `responses_anonymized.json`

Raw per-response survey data with Prolific identifiers stripped. Each record contains: random session UUID, timestamps (submission time), demographics (self-reported), passage order (randomized per participant), per-passage Likert ratings and origin classifications, free-text reasoning, and debrief responses. Country code (2-letter) is retained for aggregate-level description. No participant names, emails, IP addresses, or Prolific PIDs are present.

### `persona_dana_chen.txt`

The 474-word voice prompt used to generate the persona-engineered baseline (Passage H and the Dana group). Claude Opus at t = 1 was the generation model. See paper §4.1 for design rationale.

## Licensing

- **Code** (everything under `analysis/`, `paper/figures_v09/`, `survey/`): MIT License (see `LICENSE`).
- **Data and text artifacts** (`data/`, `paper/paper_v09.md`, `paper/paper_v09.docx`): Creative Commons Attribution 4.0 International (see `LICENSE-DATA`).
- **Third-party detector APIs** (Pangram, GPTZero, Copyleaks): not distributed; run under your own API credentials and respect vendor terms.

## Citation

If you use this data or code in your research, please cite:

```
Diamond, L. (2026). The Detector Paradox: Why Evading AI Detection Removes the
Features Readers Value. Zenodo. https://doi.org/10.5281/zenodo.19767696
```

## Contact

Questions, reproduction issues, or corrections: [lance.a.diamond@gmail.com](mailto:lance.a.diamond@gmail.com)

Issues and pull requests welcome at the repository's issue tracker.

## Ethics and participant protection

The survey was conducted with informed consent, anonymized responses, and compensation of $6.00 USD per participant (median task time 25 minutes; effective rate $14.40/hr, above Prolific platform minimum). Study was exempt from IRB review per independent-researcher / minimal-risk-anonymous-online-research criteria. See paper Declarations section for full documentation.

## Disclosure

This research emerged from engineering problems encountered during the author's development of Scribe, a commercial AI text generation product. The results reported — that the Dana persona baseline outperforms both humanization pipelines on reader-perceived quality — run contrary to the commercial interest that motivated the research. See paper Declarations section for the complete competing-interests disclosure.
