---
title: "The Detector Paradox: Why Evading AI Detection Removes the Features Readers Value"
author: "Lance Diamond"
date: "2026"
abstract: |
  AI text detectors are increasingly used as content-quality gates, with text a detector passes assumed better than text it flags. We present empirical evidence that this assumption is inverted. Beginning with a voice-engineered AI baseline — Claude Opus 4 at temperature 1 driven by a 474-word persona prompt — that produced supra-human warmth densities (first-person singular ≈ 4× the human corpus mean; contractions 2.4× the human corpus mean), we apply two successive detector-evasion techniques: surgical linguistic calibration that converges on human population statistical means, and cross-model sentence mixing (Qwen 2.5 14B + Mistral Nemo 12B) that disrupts single-model distributional fingerprints. Detector group-mean scores fall monotonically along the pipeline (Pangram 0.94 → 0.30 → 0.06; Copyleaks 0.98 → 0.77 → 0.05), and reader-perceived composite quality falls alongside them (4.21 → 3.54 → 3.26 on a 5-point scale), as judged by 33 blind technology-professional raters (pre-registered n = 33 of 43 enrolled; reading-rate exclusion applied). Readers cannot distinguish the persona baseline from human technical writing at above-chance rates (AI-detection rate 40.6%, p = 0.010 *below* chance; signal-detection d′ = 0.138, 95% CI [−0.18, +0.47]); their aggregate AI-guesses anti-correlate with every detector tested (Copyleaks ρ = −0.71 on AI passages); and the warmth features that predict reader quality (first-person density ρ = +0.90, contractions ρ = +0.91) are exactly what the calibration pipeline suppresses. Readers prefer *supra-human* warmth densities, not the human statistical means the humanization literature adopts as its convergence target. The mechanism is one pipeline effect: every detector we tested reads a mix of linguistic-distribution and token-level signals, and every engineering lever that lowers any detector's score routes through features readers value. This is Goodhart's Law applied to AI text detection as a writing-quality proxy: the industry's "pass AI detection" gate rewards exactly the engineering that degrades the quality it purports to protect.
---

# Plain-language summary

AI text detectors are increasingly used as quality gates: if a detector flags a piece of writing as AI-generated, the text is rejected or rewritten. We tested whether this practice actually tracks writing quality. We applied two engineering techniques specifically designed to fool AI detectors to a voice-engineered AI baseline that 33 working technology professionals (reading blind) rated the highest-quality passage in our 8-passage study — above every human-written comparison. Both techniques lowered detector scores, and three of four detectors no longer flagged the final output as AI. But at each engineering step, readers rated the text as *lower* quality, not higher. The features that made detectors confident the text was AI — dense first-person narration, contractions, personal war stories at rates that exceeded human norms — were exactly the features readers valued. Engineering away the detector fingerprint engineered away the signal readers responded to. On our data, policies that gate content on AI detection reject the AI writing readers rate highest.

# 1. Introduction

A growing ecosystem of commercial AI text detectors — including GPTZero, Copyleaks, Pangram, and academic tools like Binoculars — has emerged to address institutional concerns about undisclosed AI-generated content. These tools are now embedded in publishing workflows, academic integrity processes, and content procurement pipelines, where their classifications function as de facto quality gates: text that "passes" detection is accepted; text that is "flagged" is rejected or revised.

This practice rests on an implicit assumption: that detector classification is a reliable proxy for writing quality. Text a detector labels as "human" is presumed to possess the qualities of human writing — natural voice, varied information density, authentic expertise. Text labeled "AI-generated" is presumed to lack these qualities.

We test this assumption directly. Beginning from a **persona-engineered baseline** — a 474-word voice prompt ("Dana") designed to produce reader-perceptibly warm technical writing — we apply two successive detector-evasion techniques and measure what each does to the text:

1. **Surgical linguistic calibration (v10.2)** — a 13-step chain that normalizes voice markers toward human population statistical means, designed to defeat feature-engineered detectors by matching human surface statistics.
2. **Cross-model sentence mixing (3-way v2)** — stochastic rewrite of ~33% of sentences through Qwen 2.5 14B and Mistral Nemo 12B, designed to defeat perplexity-based detectors by breaking single-model distributional fingerprints.

We evaluate the resulting corpus against six human-authored technical blog posts using (a) the 22-metric linguistic battery, (b) information-theoretic analysis of content density and redundancy, (c) four AI detectors representing distinct detection architectures, and (d) blind human evaluation by 33 technology professionals (retained from 43 enrolled under a pre-registered reading-rate exclusion criterion; see §5.5.1).

Our central finding is that detector-evasion engineering and reader-perceived quality **move together in the wrong direction**. As we progress through the engineering chain (Dana → v10.2 → 3-way v2), detector scores fall monotonically (e.g., Copyleaks group mean 0.98 → 0.77 → 0.05) and reader-perceived composite quality falls alongside them (4.21 → 3.54 → 3.26 on a 5-point scale). The Dana persona baseline — flagged unanimously by every detector — is rated the highest-quality passage in the study, exceeding every human baseline. The 3-way v2 output — passing three of four detectors — is the lowest-quality.

This is Goodhart's Law in practice: "When a measure becomes a target, it ceases to be a good measure" (Strathern, 1997). The AI detectors we tested read two things about a text — its distance from the human linguistic distribution, and the token-level fingerprint of single-model large language model (LLM) generation. Claude Opus 4 at t = 1 produced the Dana baseline at supra-human warmth densities (first-person singular ≈ 4× the human group mean; contractions 2.4× the human group mean) that place Dana maximally outside the human linguistic distribution, which all four detectors flag — most sharply for Pangram. Those same densities are what readers recognize as high-quality technical writing. Engineering against either signal — calibrating toward human means to pass distribution-weighted detectors, or cross-model sentence mixing to pass fingerprint-weighted detectors — routes through features readers care about. §6 develops how each detection architecture contributes to this effect.

![**Figure 1**. The detector paradox, in one picture. Across the cumulative humanization pipeline (Dana persona baseline → surgical v10.2 → cross-model 3-way v2), detector-evasion effort rises (blue) and linguistic convergence to human population means is partially preserved (purple), while reader-perceived quality declines monotonically (red). Human-baseline reference lines shown dotted.](figures_v09/fig1_hero_paradox.png){ width=6in fig-alt="Three-line chart with pipeline stage on the x-axis (Dana persona, surgical v10.2, cross-model 3-way v2) and normalized outcome on the y-axis. The blue line (detector evasion) rises across the three stages. The red line (reader-perceived quality) declines monotonically across the three stages. The purple line (linguistic convergence to human) stays roughly flat. Horizontal dotted lines mark the human baseline for each metric." }

We contribute:

- A **measurement framework** of 22 linguistic metrics and 6 information-theoretic metrics that serves as a mechanistic diagnostic of what each text-engineering pipeline does to its output. We explicitly disclaim the framework as a quality proxy; our reader data shows it is not.
- **Empirical evidence** of the detector paradox across four detection architectures (feature-engineered, distributional, perplexity-ratio, and commercial hybrid) on a single corpus axis: detector scores and reader-perceived quality move together *away* from the engineering target as detector-evasion effort increases.
- A **detector taxonomy** explaining why different architectures respond to different text properties, why they disagree with each other, and why no single detector captures the signal readers attend to.
- **Human evaluation data** from 33 technology professionals (retained from 43 enrolled under a pre-registered reading-rate exclusion criterion) demonstrating that readers cannot distinguish calibrated AI from human technical writing at above-chance rates (signal-detection d′ = 0.138, 95% CI [−0.18, +0.47]), and that crowd judgments systematically anti-correlate with every machine detector we tested (Copyleaks ρ = −0.71 on AI passages). The reader-cited cues that readers *believe* distinguish AI from human writing (personal anecdote, first-person voice, absence of typos) are shown to be anti-diagnostic.

# 2. Related Work

## 2.1 AI Text Detection Reliability

The reliability of AI text detectors has been extensively studied. Weber-Wulff et al. (2023) tested 14 detection tools and concluded they were "neither accurate nor reliable" enough for institutional use. Pudasaini et al. (2025) benchmarked leading detectors across diverse domains and evasion strategies, finding "considerable unreliability in real-world scenarios." Liang et al. (2023) documented systematic bias in GPT detectors against non-native English writers, with TOEFL essays misclassified as AI-generated at rates up to 98%.

Hans et al. (2024) introduced Binoculars, an academic detector based on the perplexity ratio between a base language model and its instruction-tuned variant, reporting 90% detection at 0.01% false positive rate across a wide range of document types in their evaluation. Our evaluation on technical blog posts reveals substantially higher false positive rates (50%, 3 of 6 human samples misclassified: Cockroach Labs *Parallel Commits* 2017, Brooker/AWS *Exponential Backoff & Jitter* 2015, Olah/colah *Backpropagation* 2015), suggesting domain-dependent performance not captured by the original evaluation.

These studies establish that detectors are unreliable. Our contribution extends this finding: we show that unreliability is not merely a classification problem but a quality-measurement problem, since the properties detectors measure are orthogonal to writing quality.

## 2.2 Linguistic Comparison of AI and Human Text

Comparative studies of AI-generated and human-written text have accelerated since 2023. Culda et al. (2025) proposed a framework analyzing linguistic features, stylistic differences, and sentiment consistency across three open generative models (GPT-Neo 1.3B, Qwen2.5-1.5B-Instruct, BloomZ-560M). Georgiou (2025) systematically compared phonological, morphological, syntactic, and lexical features across AI-generated and human-written texts, finding significant differences in pronoun usage, adjective frequency, and word difficulty. Consistent with the broader literature, Kujur (2025) reports that AI text exhibits lower perplexity, more uniform sentence structures, and higher lexical repetitiveness than human writing.

These studies compare raw AI output to human writing as a static snapshot. Our work differs in two ways. First, we track a **calibrated convergence path** — a multi-stage pipeline where each intervention is measured against human baselines, showing progressive reduction in the AI-human gap. Second, we introduce **information-theoretic metrics** (density variance, embedding surprisal variance) that capture structural properties of writing quality not addressed by standard NLP features.

## 2.3 Adversarial Detection Evasion

Adversarial attacks on AI text detectors are an active research area. Early work introduced watermarking and paraphrasing as opposing primitives: Kirchenbauer et al. (2023) proposed embedding detectable green-list signals into LLM outputs, while Krishna et al. (2023) showed that DIPPER-paraphrased text evades watermarking and multiple zero-shot detectors, dropping DetectGPT accuracy from 70.3% to 4.6%. Zhou et al. (2024) reported that current detection models "can be compromised in as little as 10 seconds" through adversarial perturbations. Cheng et al. (2025) introduce a training-free "adversarial paraphrasing" framework that uses an instruction-following LLM to rewrite AI text under detector guidance, achieving broad transferability across detection systems. Meng et al. (2025) present GradEscape, a gradient-based evader that succeeds against real commercial detectors in the black-box setting.

All existing evasion research measures success by detector bypass rate. **None measure whether the evaded text is linguistically closer to or further from human writing, and none measure what blind human readers think of it.** This gap is precisely our contribution. We construct a cumulative humanization pipeline whose individual stages are designed to converge linguistically toward human population means *and* defeat AI detectors (§4.1, Table 1). We show that the pipeline largely succeeds at both explicit objectives — surface linguistic metrics remain close to human baselines through the final cross-model stage, and three of four commercial detectors are defeated — yet reader-perceived quality decreases monotonically at every stage of the pipeline, from the persona baseline (4.21/5.00) through surgical calibration (3.54) to cross-model mixing (3.26). **Successful evasion on the metrics we designed for does not preserve the signal readers respond to.** The narrower structural finding reported in prior framings of this work — that cross-model mixing specifically degrades information density variance while preserving surface metrics — is a linguistic-level manifestation of the same dynamic.

## 2.4 Goodhart's Law and Proxy Metrics

Goodhart's Law — that optimizing for a proxy metric causes it to diverge from the true objective — has been formalized in machine learning contexts. Gao et al. (2023) documented measurement of Goodhart's effects in reward model overoptimization under RLHF. Thomas and Uminsky (2022) catalog the harms of metric overreliance in AI systems and propose a mitigation framework built on using a slate of metrics, qualitative data, domain-expert audits, and stakeholder input. In AI evaluation, Goodhart effects have been observed in benchmark gaming, BLEU score optimization for machine translation, and leaderboard manipulation.

To our knowledge, we present the **first empirical demonstration** of Goodhart's Law applied to AI text detection as a writing quality proxy.

# 3. Measurement Framework

We propose a two-part measurement framework for assessing AI-to-human writing convergence: a 22-metric linguistic battery and a 6-metric information-theoretic analysis. Both are computed automatically and provide ground-truth assessment independent of detector classification.

## 3.1 Linguistic Battery

The linguistic battery measures surface-level and stylistic properties across five categories:

**Voice and person** (4 metrics): first-person singular (FPS) frequency (per 1,000 words), first-person plural (FPP) frequency, second-person frequency, and contraction density. These capture the authenticity of narrative voice — a dimension where AI text systematically diverges from human writing through either avoidance or overuse of personal pronouns.

**Readability and structure** (5 metrics): Flesch reading ease, mean sentence length, sentence length standard deviation (burstiness), very short sentence percentage (<8 words), and very long sentence percentage (>35 words). Human technical writing exhibits higher burstiness — greater variation between short punchy sentences and long complex ones — while AI text tends toward uniform sentence lengths.

**Lexical diversity** (3 metrics): type-token ratio, average word length, and hapax legomena ratio. AI text typically shows slightly higher lexical diversity than human text in the same domain, as language models draw from a broader vocabulary distribution.

**Discourse markers** (5 metrics): hedging density ("perhaps," "somewhat," "arguably"), comparative density, em-dash usage, semicolon usage, and quotation frequency. These markers signal rhetorical sophistication and personal style.

**Quality signals** (5 metrics): total AI-tell count (formulaic constructions like "It is important to note" plus structural tells — copula-avoidance, negative-parallelism, present-participle endings — via the surface scanner described in Appendix A.1); weighted tell severity (composite score weighting different tell categories); Pangram-phrase density per 1,000 words (broken out separately — Pangram over-used phrases are the strongest single phrase-level discriminator in the literature); bold/emphasis density; and tricolon count.

## 3.2 Information-Theoretic Analysis

The information-theoretic layer captures deeper structural properties using sentence embeddings from all-mpnet-base-v2 (Reimers and Gurevych, 2019):

**Redundancy** (2 metrics): mean and maximum pairwise cosine similarity across all sentence pairs. Higher redundancy indicates repetitive content — a known AI tendency.

**Consecutive similarity** (2 metrics): mean and standard deviation of cosine similarity between adjacent sentences. This measures information flow smoothness. Human writing exhibits moderate consecutive similarity with high variance (topic shifts, asides, examples), while AI text shows lower variance (uniform information delivery).

**Information density variance** (1 metric): variance of per-paragraph content diversity, measured as the mean pairwise distance between sentence embeddings within each paragraph, computed across paragraphs. Human writing packs information unevenly — dense technical paragraphs alternate with lighter narrative ones. AI text distributes information more uniformly. This metric proves to be the strongest discriminator in our analysis.

**Embedding surprisal variance** (1 metric): variance of the semantic distance between consecutive sentences. High variance indicates a mixture of predictable transitions and surprising topic shifts — characteristic of human writing.

## 3.3 Convergence Recovery Metric

To quantify pipeline effectiveness, we define a convergence recovery score for each metric:

$$R_m = 1 - \frac{|x_{pipeline} - x_{human}|}{|x_{baseline} - x_{human}|}$$

where $x_{pipeline}$ is the pipeline output value, $x_{human}$ is the human baseline mean, and $x_{baseline}$ is the persona baseline value (the starting-point text a pipeline attempts to modify; see §4.1 for the persona's design). A score of 1.0 indicates perfect convergence to the human population mean; 0.0 indicates no movement from baseline; negative values indicate movement away from human. Note that convergence to human statistical means is not the same as reader-perceived quality (§5.5.7); $R_m$ measures the former only.

# 4. Experimental Setup

## 4.1 Corpus

We evaluate across seven technical topics: idempotency keys, Linux virtual memory, attention mechanisms, exponential backoff with jitter, garbage collection, Bloom filters, and backpropagation. For each topic, we collect human reference text and then generate AI text through a **cumulative humanization pipeline**: each successive stage operates on the output of the stage before it, layering a new intervention on top of the previous one. Table 1 summarizes the chain; the conditions are described below.

**Table 1: The cumulative humanization pipeline (per topic)**

| Stage | Sample prefix | Input | Intervention | Evasion strategy |
|---|---|---|---|---|
| 0 | human baseline | — | (published human essay) | — |
| 1 | Dana persona | prompt | voice-engineered persona prompt (Claude Opus 4, t = 1) | — (reader-warmth target) |
| 2 | v9 full | Dana output | v1–v9 surgical chain | feature-level cleanup |
| 3 | **v10.2** | v9 output | function-word reduction + density targets | **linguistic mimicry → defeat Pangram** |
| 4 | 3-way v1 | v10.2 output | stochastic cross-model sentence rewrite (Qwen/Mistral) | distributional disruption |
| 5 | **3-way v2** | v10.2 output | calibrated cross-model rewrite (voice-preserving prompt) | **distributional disruption + voice preservation** |

Each stage's sample in the corpus database carries a note identifying the parent stage (e.g., `scribe_idempotency_3way_v2` is recorded as "3-way calibrated cross-model mix v2" applied to `scribe_surgical_v10_2`, which in turn was produced from `scribe_*_v9_full`). This is important for interpreting results: observations about v10.2 are observations about what *surgical calibration* does on top of the Dana baseline; observations about 3-way v2 are observations about what *cross-model mixing* does on top of v10.2. We do not have parallel conditions where each intervention is applied to the raw persona independently.

**Human baselines** (6 samples): Published technical blog posts by recognized practitioners — Brandur Leach (Stripe, 2017), Marc Brooker (AWS, 2015), Chris Olah (colah.github.io, 2015), and others. Selected for established authority and natural voice.

**Persona-engineered baseline — Dana** (7 samples, Stage 1): Claude Opus 4 at t = 1 generation using a 474-word voice prompt we refer to as the *Dana persona*. The prompt defines a technical-blogger voice ("Dana Chen, staff software engineer, ten years of payments infrastructure at three startups") and specifies ten explicit style rules: open with a specific incident rather than an encyclopedic topic sentence; write in first person throughout; include at least three war stories with concrete details (year, company type, dollar amount); include at least one deliberate digression; use sentence case for every heading; do not use markdown bold for source attributions; use contractions throughout; allow single-sentence paragraphs; target ≈ 1,500 words; cite background facts in the persona's own voice. A descriptive prologue additionally instructs the model to never write "plays a crucial role"-class phrasing. The persona was selected as the best-performing voice prompt in a Copyscape classification screen (mean AI-probability 0.499 across topics). Crucially, this baseline is **not an uncalibrated raw-model generation** — it is voice-engineered to produce reader-perceptible human-like writing, and its linguistic statistics systematically *overshoot* human population means on warmth markers (first-person singular 16.68/1k vs. human 4.26/1k; contractions 27.14/1k vs. human 11.48/1k).

**Surgical pipeline v10.2** (7 samples, Stage 3, applied to Dana → v9 output): A 13-step surgical chain applying voice injection, function-word density correction (programmatic regex + LLM polish with per-word targets), and structural variety interventions. Each step is measured against human baselines and tuned to minimize divergence. The intended purpose is detector evasion via *linguistic mimicry* — text that statistically matches human surface features should not be flagged by feature-engineered detectors. At this stage we observe Pangram partial evasion (group mean from 0.94 on Dana to 0.30 on v10.2) while GPTZero, Copyleaks, and Binoculars remain flagged.

**Cross-model mix v1** (7 samples, Stage 4, applied to v10.2 output): Approximately 33% of sentences randomly rewritten by Qwen 2.5 14B and Mistral Nemo 12B via local inference, using an uncalibrated rewrite prompt. The intended purpose is detector evasion via *distributional disruption* — breaking the single-model fingerprint that perplexity-based detectors rely on, while relying on the surgical v10.2 input to preserve linguistic convergence.

**Cross-model mix v2** (7 samples, Stage 5, applied to v10.2 output): Same architecture as v1 but with a calibrated rewrite prompt that constrains the local models to preserve voice characteristics (contractions, readability, function-word ratios). This is the "check all the boxes" endpoint of the pipeline — both detector evasion (passes Pangram, Copyleaks, and Binoculars; GPTZero still partially flags) and statistical convergence to human linguistic means (preserved on most metrics, as reported in §5.1–5.2).

Total corpus: 34 documents, approximately 50,000 words.

For the blind human evaluation (§5.5), eight passages were drawn from this corpus, spanning the full condition range: three human baselines (Brandur Leach/Stripe, Marc Brooker/AWS, Chris Olah/colah.github.io); one persona-engineered baseline (Dana, Claude Opus 4 at t = 1, idempotency topic); one surgical v10.2 calibration output; and three cross-model v2 outputs (idempotency, exponential backoff, Bloom filters). Passage order was randomized per participant, and the human/AI ratio was not disclosed.

## 4.2 Detection Architecture Taxonomy

We evaluate four detectors representing distinct detection approaches:

**Pangram** (feature-engineered): Analyzes per-window stylistic features including word choice patterns, sentence structure regularity, and lexical predictability. Returns per-window AI confidence scores aggregated into a document-level classification.

**GPTZero** (distributional): Measures statistical properties of the token distribution, including perplexity and burstiness at the document level. Detects deviations from expected human text distributions.

**Copyleaks** (commercial hybrid): Proprietary classifier combining multiple detection signals. Returns human and AI probability scores.

**Binoculars** (perplexity-ratio, academic): Computes the ratio of text perplexity under a base language model (Falcon-7B) to cross-perplexity with its instruction-tuned observer (Falcon-7B-Instruct), normalizing an observed-perplexity signal by the expected perplexity of machine-generated text to counter the "capybara problem" — the confound in which prompt conditioning inflates the perplexity of an LLM's own output (Hans et al., 2024).

## 4.3 Statistical Methods

Given small sample sizes (n = 6–7 per group), we employ non-parametric methods. Group comparisons use the Mann-Whitney U test (two-sided). Effect sizes are reported as Cohen's d with pooled standard deviation. Confidence intervals for mean differences are computed via bootstrap resampling (10,000 iterations, 95% CI). We report exact p-values and flag significance at α = 0.05.

# 5. Results

## 5.1 Linguistic Convergence

The calibrated pipeline (v10.2) achieves substantial convergence toward human baselines across multiple linguistic dimensions. Table 2 reports key metrics.

**Table 2: Linguistic metrics by group (mean ± std)**

| Metric | Human (n = 6) | Persona/Dana (n = 7) | v10.2 (n = 7) | 3-way v2 (n = 7) |
|---|---|---|---|---|
| First person singular /1k | 4.26 | 16.68** | 0.39** | 0.41** |
| First person plural /1k | 16.70 | 11.04 | 10.05 | 21.85 |
| Contractions /1k | 11.48 | 27.14** | 12.37 | 10.07 |
| Mean sentence length | 19.43 | 16.53 | 20.13 | 18.72 |
| Burstiness | 0.51 | 0.70* | 0.54 | 0.53 |

*p < 0.05, **p < 0.01 vs. human (Mann-Whitney U)

The Dana persona baseline **overshoots** human population means on the markers the prompt explicitly instructs (first-person singular 16.68/1k vs. human 4.26/1k, p = 0.001; contractions 27.14/1k vs. 11.48/1k, p = 0.001). This overshoot is prompt-driven and intentional at the persona level, though the *magnitude* (roughly 4× human first-person density, 2.4× contractions) is an emergent property of Claude Opus 4 at t = 1 rather than a target we set. The v10.2 calibrated pipeline then corrects these features *toward* human population means, bringing contractions to near-human levels (12.37/1k) and reducing burstiness divergence; in doing so, however, it under-shoots the human first-person baseline (0.39/1k against human 4.26/1k).

The cross-model mix (3-way v2) introduces a new divergence: first-person plural inflation (21.85/1k vs. human 16.70/1k). The difference does not reach statistical significance at the corpus level (Mann-Whitney U, p = 0.234) because of wide within-group variance (human FPP ranges 7.8–25.2; 3-way v2 ranges 13.5–32.8), but the cross-model rewrite process reliably shifts the *central tendency* by approximately 5 per 1k — consistent with Qwen and Mistral systematically introducing "we/our" constructions not present in the original v10.2 text.

![**Figure 2**. Metric convergence profiles. Ratio to human baseline (1.0 = match) across eight linguistic dimensions for the persona (Dana) baseline, surgical v10.2 output, and cross-model 3-way v2 output. The calibration pipeline brings most metrics toward human means; cross-model mixing inflates first-person plural density while preserving other surface markers.](figures_v09/fig4_radar.png){ width=5in fig-alt="Radar chart with eight axes corresponding to eight linguistic metrics (first-person plural per 1k, contractions per 1k, mean sentence length, burstiness, type-token ratio, density variance, consecutive similarity, redundancy). Each axis is scaled so that 1.0 equals the human population mean (green target polygon). Three polygons are overlaid: Dana persona (dotted red), surgical v10.2 (solid purple), and cross-model 3-way v2 (dashed blue). Dana's polygon extends outside the unit circle on contractions. The v10.2 polygon sits close to the unit circle on most axes. The 3-way v2 polygon tracks v10.2 closely except for first-person plural (extending outside the unit circle) and density variance (also extended)." }

![**Figure 3**. Voice metric convergence detail. Ratio-to-human bars on five representative voice markers. Cross-model v1 (uncalibrated rewrite) produces the dramatic FPP inflation (3.20× human) that v2's calibrated rewrite prompt reduces to 1.31×. v10.2 and 3-way v2 hold within ±30% of human on contractions, burstiness, sentence length, and type-token ratio.](figures_v09/fig5_voice.png){ width=6in fig-alt="Grouped bar chart. Five voice metrics on the x-axis (first-person plural, contractions, burstiness, mean sentence length, type-token ratio). Four bar groups per metric corresponding to Dana, surgical v10.2, cross-model 3-way v1, and cross-model 3-way v2. The y-axis is ratio-to-human, with a horizontal reference line at 1.0. The tallest bar in the chart is 3-way v1 first-person plural at approximately 3.2. All v10.2 and 3-way v2 bars fall within roughly 0.7 to 1.3 of the reference line except 3-way v2 first-person plural at 1.31." }

## 5.2 Information-Theoretic Analysis

Table 3 reports information-theoretic metrics. Information density variance emerges as the strongest discriminator.

**Table 3: Information-theoretic metrics by group**

| Metric | Human | Persona/Dana | v10.2 | 3-way v2 |
|---|---|---|---|---|
| Density variance | 0.0157 | 0.0383* | 0.0158* | 0.0771* |
| Density mean | 0.706 | 0.661 | 0.654 | 0.583* |
| Redundancy mean | 0.247 | 0.215 | 0.249 | 0.239 |
| Consecutive sim. mean | 0.387 | 0.307* | 0.335 | 0.319 |
| Embedding surprisal var. | 0.037 | 0.025** | 0.030 | 0.029 |

*p < 0.05, **p < 0.01 vs. human (Mann-Whitney U)

The v10.2 pipeline achieves mean-level convergence on information density variance (0.0158 vs. human 0.0157, Cohen's d = −0.002, indicating essentially zero effect size). The Mann–Whitney U test in Table 3 marks this at the boundary of significance (p = 0.047) — a rank-based artifact driven by the distribution shape: five of six human samples have density_variance = 0 (uniformly paragraphed prose) while all seven v10.2 values lie between 0.005 and 0.035, creating rank separation despite near-identical group means. The substantive claim — that the calibrated text distributes information across paragraphs with the same unevenness as human writing on average — rests on the near-zero Cohen's d and the matching group means, not on the rank test.

**The cross-model v2 stage preserves linguistic convergence on most surface metrics and breaks it on density variance specifically.** Because cross-model mixing is applied on top of the already-converged v10.2 output (§4.1, Table 1), most of v10.2's statistical match to human baselines survives the rewrite: sentence length, burstiness, type-token ratio, em-dash density, redundancy, and consecutive similarity all remain close to human. Of the thirteen linguistic and information-theoretic metrics we track, 3-way v2 holds convergence on eight, drifts slightly on three, and outright breaks on two — first-person plural density (21.85/1k against human 16.70/1k, introduced by "we/our" constructions during the cross-model rewrite) and **information density variance, which rises from 0.0158 to 0.0771** — a ≈5× divergence from human baselines (0.0771 ÷ 0.0157).

The density-variance break is mechanistically explicable. The cross-model rewrite process randomly substitutes ~33% of sentences with rephrasings from different model families; some paragraphs receive multiple substitutions (becoming informationally fragmented), while others remain unchanged (retaining the original model's uniform density). The result is artificial paragraph-to-paragraph density variation that does not match the organic variation found in human writing. The calibrated rewrite prompt used in v2 preserves surface voice features (contractions, function-word ratios) but cannot preserve a paragraph-level structural property that no individual sentence reveals.

This is the linguistic half of the core paradox: the pipeline that successfully hits its surface linguistic targets and defeats three of four detectors breaks the one structural property — density variance — that is the strongest linguistic discriminator of AI from human writing in our corpus. We flag "the strongest discriminator" with care: as §5.5.7 shows, density variance is a marker of statistical distance from human writing, not of reader-perceived quality, and the distinction matters for interpreting the paradox.

![**Figure 4**. Information density variance by pipeline stage. The v10.2 surgical output (μ = 0.0158) is statistically indistinguishable from human (μ = 0.0157). Cross-model mixing (3-way v1 and v2) breaks this convergence, rising to μ ≈ 0.08 — a 5× divergence from v10.2 (Cohen's d = −3.15, p = 0.001). Box plots show sample distributions; overlay points are individual documents.](figures_v09/fig3_density_variance.png){ width=5.5in fig-alt="Box-plot chart. Five groups on the x-axis (human, Dana, surgical v10.2, cross-model 3-way v1, cross-model 3-way v2) and information density variance on the y-axis from zero to approximately 0.12. The human and v10.2 boxes cluster around 0.016. The Dana box sits slightly below the human box. The 3-way v1 and 3-way v2 boxes sit much higher at roughly 0.07 to 0.08, with individual documents plotted as overlay points scattered inside each box." }

## 5.3 Detector Analysis

Table 4 reports mean AI detection scores across all four detectors.

**Table 4: Mean AI detection scores by group (higher = more likely AI)**

| Detector | Human | Persona/Dana | v10.2 | 3-way v2 |
|---|---|---|---|---|
| Pangram | 0.000 | 0.938 | 0.299 | 0.056 |
| GPTZero | 0.009 | 0.934 | 0.824 | 0.394 |
| Copyleaks | 0.000 | 0.983 | 0.774 | 0.053 |
| Binoculars | 0.467 | 0.723 | 0.531 | 0.160 |

Several findings warrant discussion.

**Detector disagreement is substantial.** On v10.2 text, Pangram scores 0.299 (mostly passes), GPTZero scores 0.824 (caught), and Copyleaks scores 0.774 (caught). Three detectors, three different verdicts on the same text. This inconsistency undermines the use of any single detector as a quality gate.

**Binoculars exhibits high false-positive rates on human text.** Three of six human-authored blog posts (50%) are classified as AI-generated by Binoculars: Cockroach Labs *Parallel Commits* (2017) at 0.885, Brooker/AWS *Exponential Backoff & Jitter* (2015) at 0.874, and Olah/colah *Backpropagation* (2015) at 0.851 — all above Binoculars' own prediction threshold. The three correctly-classified human samples are Brandur/Stripe (2017), Hudson *Go GC Journey* (2018), and Srivastav *Bloom Filters* (2014), with scores 0.03 to 0.08. The original Binoculars paper reports 0.01% false positive rates, but this was evaluated on news articles and Wikipedia — domains with different distributional properties than technical blog posts. Our finding suggests that Binoculars' published performance metrics do not generalize to technical writing. The human-evaluation sample of §5.4.1 concurs: of the three human baselines drawn into the survey, Binoculars scores 0.87 on Brooker/AWS (Passage D, 2015) and 0.85 on Olah/colah (Passage F, 2015), while correctly passing Brandur/Stripe (Passage A) at 0.03. The crowd correctly identified all three as human (A 57.6%, D 72.7%, F 63.6% accuracy).

**The 3-way v2 pipeline passes all four detectors.** Mean scores drop to 0.056 (Pangram), 0.394 (GPTZero), 0.053 (Copyleaks), and 0.160 (Binoculars). Cross-model sentence mixing disrupts the single-model distributional fingerprint that all four architectures rely on, regardless of their specific detection methodology.

**Detection architecture determines vulnerability.** Feature-engineered detectors (Pangram) are vulnerable to surface-level calibration — the v10.2 pipeline already reduces Pangram scores from 0.938 to 0.299 by adjusting function words and sentence patterns. Distributional detectors (GPTZero, Copyleaks) are robust to surface edits but vulnerable to model mixing. Binoculars' perplexity-ratio approach is partially resilient but suffers from high baseline false positives.

## 5.4 The Detector Paradox

The paradox is formalized in Table 5, which juxtaposes detector scores against information density variance — the strongest linguistic discriminator between AI and human writing in our corpus (§5.2). We note up front that "strongest linguistic discriminator" means strongest marker of statistical distance from human writing, not strongest predictor of reader-perceived quality: §5.5.7 establishes that reader quality does not track this metric.

**Table 5: The Detector Paradox**

| | v10.2 | 3-way v2 | Cohen's d | p-value |
|---|---|---|---|---|
| Density variance | **0.016** (≈ human) | 0.077 (5× worse) | −3.15 | 0.001 |
| Pangram AI score | **0.299** (passes) | **0.056** (passes) | +1.30 | 0.039 |
| GPTZero AI score | 0.824 (flagged) | **0.394** (passes) | +2.53 | 0.001 |
| Copyleaks AI score | 0.774 (flagged) | **0.053** (passes) | +3.39 | 0.002 |
| Binoculars AI score | 0.531 (flagged) | **0.160** (passes) | +0.99 | 0.026 |

![**Figure 5**. Four-detector AI scores across pipeline stages. The persona (Dana) baseline is unanimously flagged (0.72–0.98). Surgical v10.2 partially defeats Pangram (0.30) but remains flagged by the other three detectors. Cross-model 3-way v2 defeats three of four detectors (≤ 0.16) but GPTZero still partially flags (0.39). Dotted line at 0.50 = detector decision threshold.](figures_v09/fig2_detectors.png){ width=6in fig-alt="Grouped bar chart. Three pipeline stages on the x-axis (Dana persona, surgical v10.2, cross-model 3-way v2). Four bars per stage, one for each detector (Pangram, GPTZero, Copyleaks, Binoculars). Y-axis is AI score from 0 to 1, with a horizontal dotted line at 0.50 marking the decision threshold. Dana bars are all above the threshold (0.72 to 0.98). The v10.2 Pangram bar falls below the threshold (0.30); the other three v10.2 bars stay above it. In the 3-way v2 stage, Pangram, Copyleaks, and Binoculars bars all fall below 0.16; only GPTZero remains close to the threshold at 0.39." }

Every row tells the same story in opposite directions. The text that matches human writing on density variance (v10.2, d = −0.002 from human) is the text that three of four detectors flag (GPTZero 0.82, Copyleaks 0.77, Binoculars 0.53; Pangram passes at 0.30). The text that passes three of four detectors (3-way v2, with GPTZero remaining ambiguous at 0.39) is the text that deviates most from human writing on density variance (d = −3.15 from v10.2).

This inversion is Goodhart's Law applied at the linguistic level: optimizing for the proxy (detector score) via cross-model mixing forced the information-density structure *away* from human baselines. The detector score becomes the target, and it ceases to track the linguistic property against which it was previously correlated. The reader-side manifestation of the same dynamic — that defeating detectors also degrades reader-perceived quality — is established in §5.5 and §5.5.7.

The mechanism is clear. Cross-model sentence mixing replaces approximately 33% of sentences with rephrasings from different model families (Qwen 2.5 14B, Mistral Nemo 12B). This disrupts the distributional fingerprint that detectors rely on — the statistical signature of a single model's token selection patterns. But it simultaneously disrupts the information-theoretic structure of the text, because sentences rewritten by different models carry different information densities, creating artificial variance that does not match the organic density patterns of human writing.

### 5.4.1 Crowd–Detector Disagreement

A second, independent paradox emerges when detector scores are compared directly to human-reader judgments rather than to linguistic metrics. Using the crowd AI-call rate computed in §5.5 (fraction of n = 33 raters who classified each passage as AI, after the pre-registered reading-rate exclusion described in §5.5.1), we computed Spearman rank correlations between each detector's ai_score and the crowd rate across the eight survey passages.

**Table 5a: Machine detector × human-crowd AI-call rate (Spearman ρ, n = 33)**

| Detector | All 8 passages | p | AI passages only (n = 5) | p |
|---|---|---|---|---|
| Pangram | −0.429 | 0.289 | **−0.803** | 0.102 |
| GPTZero | −0.085 | 0.842 | −0.616 | 0.269 |
| Copyleaks | −0.250 | 0.550 | −0.711 | 0.179 |
| Binoculars | −0.582 | 0.130 | −0.308 | 0.614 |

Seven of eight correlations are negative; the one near-zero correlation is GPTZero across all 8 passages (ρ = −0.085). Across the five AI-generated passages specifically, all four detectors show negative correlations with the crowd AI-call rate, ranging from ρ = −0.31 (Binoculars) to ρ = −0.80 (Pangram). None reaches conventional statistical significance at n = 5, but the direction is consistent. Machines and humans trend in opposite directions on this task, though the small AI-passage sample (n = 5) limits the statistical power to detect correlation magnitudes reliably. Figure 6 visualizes the per-passage dispersion across all four detectors.

![**Figure 6**. Machine detectors vs. human crowd, per passage. Each point is one of the eight survey passages (A–H); green = human-authored, red = AI-generated. All four detectors show negative Spearman correlations with the crowd AI-call rate across all 8 passages (ρ ∈ [−0.58, −0.09]); Binoculars is the strongest on the full set and Pangram the strongest on the AI-only subset. Dotted lines at 0.50 = detector decision threshold and 50% crowd AI-call rate.](figures_v09/fig6_crowd_vs_detector.png){ width=6in fig-alt="Two-by-two grid of scatter plots, one panel per detector (Pangram top-left, GPTZero top-right, Copyleaks bottom-left, Binoculars bottom-right). In each panel the x-axis is detector ai_score from 0 to 1 and the y-axis is crowd AI-call rate from 0 to 1. Each panel plots eight points, one per survey passage A through H, labeled with the passage letter. Green markers indicate human-authored passages, red markers indicate AI-generated. A dotted line at x = 0.5 and y = 0.5 divides each panel into quadrants. All four panels show negatively sloped trend lines: high-detector-score passages tend to receive low crowd AI-call rates. The annotated Spearman ρ values in each panel title are negative, with Binoculars showing the steepest slope on the full 8-passage set and Pangram the steepest on the AI-only subset." }

The anti-correlation is visible per-passage. Table 5b contrasts the crowd's AI-call rate with each detector's ai_score for the five AI passages.

**Table 5b: Per-passage detector scores vs. crowd AI-call rate (AI passages only)**

| Passage | Condition | Crowd AI% | Pangram | GPTZero | Copyleaks | Binoculars |
|---|---|---|---|---|---|---|
| H | Persona (Dana) | 27.3% | 1.00 | 1.00 | 1.00 | 0.82 |
| B | Surgical v10.2 | 39.4% | 0.00 | 0.79 | 0.87 | 0.85 |
| G | Cross-model v2 | 39.4% | 0.16 | 0.42 | 0.00 | 0.02 |
| E | Cross-model v2 | 42.4% | 0.00 | 0.32 | 0.37 | 0.04 |
| C | Cross-model v2 | 54.5% | 0.00 | 0.51 | 0.00 | 0.05 |

The persona-engineered passage (H, Dana) is the hardest text for humans to identify (only 27.3% correctly call it AI) but is unanimously flagged by all four machines (ai_score ≥ 0.82). The cross-model passages (C/E/G) are easier for humans to identify (39–55% call AI) but three of four detectors rate them at or near zero. The crowd's highest-ranking AI passage (C at 54.5%) is among the machines' *least*-AI passages (Pangram 0.00, Copyleaks 0.00, Binoculars 0.05).

On binary classification against ground truth, GPTZero correctly labels 6 of 8 passages (75%); the crowd majority correctly labels 4 of 8 (50%), with the crowd majority flipping to "AI" for Passage C (cross-model v2) at 54.5%. Cohen's κ between crowd-majority and the best-accuracy detector (GPTZero) is +0.39, rising above zero for the first time because the crowd agrees with GPTZero on Passage C. Against the remaining detectors, Cohen's κ is negative to marginally negative (−0.14 to −0.25), indicating the crowd and those detectors produce uncorrelated-to-anticorrelated error patterns on the shared task.

Two of the three human-authored survey passages trigger Binoculars false positives: the Brooker/AWS essay (Passage D, 2015) scores 0.874 and the Olah/colah essay (Passage F, 2015) scores 0.851. Both are canonical pre-ChatGPT technical explanations by recognized practitioners. The crowd correctly identifies both as human (72.7% and 63.6% accuracy respectively), concurring with the aggregate Binoculars false-positive rate of 3/6 on the full corpus (50%, §5.3). The decoupling runs in both directions: machines miss some texts humans easily read as human, and machines flag as AI some texts humans unambiguously recognize as human prose.

The combined picture is that neither machines nor humans, nor linguistic/information-theoretic metrics, are measuring the same underlying property. The detector paradox of §5.4 (calibrated pipeline flagged, detector-optimized pipeline passing) holds pairwise for every comparison we have made: detector scores diverge from density variance, from the other detectors' scores, from human judgment, and from ground truth.

## 5.5 Human Evaluation

To assess whether the linguistic and information-theoretic divergences identified in §§5.1–5.4 correspond to perceptible differences for actual readers, we conducted a blind evaluation with 43 technology professionals, of whom 33 passed a pre-registered reading-rate exclusion criterion (see §5.5.1).

### 5.5.1 Methodology

Participants were recruited via Prolific (n = 38) and organically via direct URL (n = 5), for a total of 43 responses. All participants were screened for self-reported technical reading frequency and professional experience. The cohort included software engineers, DevOps/SRE practitioners, solutions architects, technical writers, and support engineers, with professional experience ranging from 2 to 16+ years. The study was administered through a custom web survey (hosted at study.verovu.ai) and required approximately 25 minutes to complete. Median completion time was 34 minutes among retained participants.

Each participant read eight passages (~800 words each) drawn from the study corpus (§4.1): three human baselines (Brandur Leach/Stripe 2017; Marc Brooker/AWS 2015; Chris Olah/colah.github.io 2015), one persona-engineered baseline (Dana, Claude Opus 4 at t = 1; see §4.1 for the persona's design), one v10.2 surgical-calibration output, and three cross-model v2 outputs (on idempotency, exponential backoff, and Bloom filters respectively). Passages were presented in per-participant randomized order; participants were blinded to the human/AI ratio and to passage origin.

For each passage, participants provided:

- **Origin classification**: a binary choice (human or AI)
- **Six Likert ratings** on a 1–5 scale: confidence (how confident the writing sounds), naturalness, clarity, engagement, authority, and overall quality
- **Optional free-text reasoning** describing the features that informed their classification

After the eight passages, participants completed a final questionnaire identifying the single passage they considered highest-quality (all 8 passages listed unlabeled, without origin cues), describing which features they used to distinguish AI from human writing, and providing optional free-form comments.

**Pre-registered exclusion criterion.** Participants whose mean reading rate exceeded 500 words per minute across the 6,611-word passage battery were excluded from the primary analysis. This threshold was selected in advance on the basis of established comprehension-rate norms: Carver's (1992) reading-gear framework places "learning" (≈ 200 WPM) and "rauding" (Carver's coined term for reading-for-comprehension of familiar prose, ≈ 300 WPM) as the typical ranges for comprehension-oriented reading, and Rayner (1998) reports 250–300 WPM as the typical rate for skilled adult silent reading. Technical prose typically falls at or below these ranges; rates above 500 WPM sit well above Carver's skimming range (≈ 450 WPM) and are consistent with skimming rather than reading for comprehension. Ten participants met the exclusion criterion, with page-based reading rates of 554, 599, 697, 735, 776, 797, 899, 1,009, 1,217, and 1,377 WPM, leaving **n = 33** retained for primary analysis. Directional and significance findings on the unfiltered n = 43 cohort are reported as a sensitivity check in Appendix C.1; the direction of every reported effect is preserved, and the AI-detection-below-chance result holds at the same significance level (p = 0.003 on the unfiltered cohort versus p = 0.010 on the retained cohort).

### 5.5.2 Origin Classification

Human readers could not distinguish AI-generated from human-written passages at above-chance rates. Overall classification accuracy was 49.6% (131/264 judgments; binomial p = 0.95 against chance). Decomposing by ground-truth class reveals a striking asymmetry:

- **AI-detection rate** (correctly identifying AI passages): 40.6% (67/165), 95% CI [33.0%, 48.5%]. One-sided binomial test against chance: **p = 0.010** — significantly **below** chance.
- **Human-specificity** (correctly identifying human passages): 64.6% (64/99), 95% CI [54.4%, 74.0%]. One-sided binomial against chance: p = 0.002.

Readers defaulted to a "human" classification when uncertain. Signal detection analysis (Macmillan & Creelman, 2005) quantifies this: sensitivity d′ = 0.138 (bootstrap 95% CI [−0.18, +0.47], encompassing zero) and response criterion c = +0.31 (95% CI [+0.15, +0.47], significantly greater than zero). The crowd has effectively **no discriminative ability** and a systematic bias toward "human" responses.

The bias was sufficient that the crowd majority classified **every passage** in the study as "human" — including the Dana persona baseline (Passage H) — with the lone exception of Passage C (a cross-model v2 output), where 54.5% of raters called AI. Fleiss’ κ (Fleiss, 1971) across the 33 raters and 8 passages was −0.001, indicating no inter-rater agreement beyond chance.

### 5.5.3 Per-Passage Accuracy

Table 6 reports per-passage classification accuracy.

**Table 6: Per-passage human classification accuracy (n = 33)**

| Passage | Source | Condition | Correct | Accuracy | 95% CI | p vs. chance |
|---|---|---|---|---|---|---|
| A | Human (Stripe) | human | 19/33 | 57.6% | [39.2, 74.5] | 0.487 |
| D | Human (AWS) | human | 24/33 | **72.7%** | [54.5, 86.7] | **0.014** |
| F | Human (colah) | human | 21/33 | 63.6% | [45.1, 79.6] | 0.163 |
| B | AI | surgical v10.2 | 13/33 | 39.4% | [22.9, 57.9] | 0.296 |
| C | AI | cross-model v2 | 18/33 | 54.5% | [36.4, 71.9] | 0.728 |
| E | AI | cross-model v2 | 14/33 | 42.4% | [25.5, 60.8] | 0.487 |
| G | AI | cross-model v2 | 13/33 | 39.4% | [22.9, 57.9] | 0.296 |
| H | AI | persona (Dana) | 9/33 | **27.3%** | [13.3, 45.5] | **0.014** |

Two passages deviate significantly from chance: Passage D (Brooker/AWS) above (72.7%, p = 0.014) and Passage H (Dana persona) below (27.3%, p = 0.014). The persona-engineered passage — the **easiest** text for machine detectors to classify, with all four detectors scoring ai_score ≥ 0.82 on H — is the text humans are **least** able to correctly identify. Cross-model and surgical-calibration outputs cluster near chance (39–55%), overlapping with the human baselines (58–73%) in per-passage accuracy.

Condition-level analysis reveals a counterintuitive ordering: the persona-engineered baseline is harder for humans to detect (27.3%) than either surgical-calibrated (39.4%) or cross-model (45.4% pooled across C/E/G) outputs. Humanization interventions that reduce detector scores do **not** reduce reader detection — if anything, they modestly increase it. The trend runs opposite to the direction predicted by detector performance. The persona-vs-humanized comparison trends in the predicted direction on all three cohorts (Fisher's exact p = 0.112 at n = 33, p = 0.082 at n = 43, p = 0.036 at the n = 30 post-hoc subset of Appendix C.2) but reaches conventional significance only under the n = 30 filter; we treat it as directional evidence rather than a significance claim.

### 5.5.4 Likert Quality Ratings

For each Likert dimension we computed paired per-participant differences between mean AI-passage and mean human-passage ratings, tested by Wilcoxon signed-rank, with Cohen's d as effect size. Table 7 reports the results with Benjamini–Hochberg false discovery rate (FDR) correction (Benjamini & Hochberg, 1995) across the six dimensions.

**Table 7: Mean Likert ratings — AI vs. human passages (n = 33 paired differences)**

| Dimension | AI mean | Human mean | Δ (AI − H) | Cohen's d | Wilcoxon p | BH-FDR sig. |
|---|---|---|---|---|---|---|
| Confidence | 3.73 | 3.72 | +0.02 | +0.03 | 0.793 | n.s. |
| Naturalness | 3.51 | 3.63 | −0.12 | −0.14 | 0.452 | n.s. |
| Authority | 3.75 | 3.83 | −0.08 | −0.09 | 0.969 | n.s. |
| Engagement | 3.16 | 3.41 | −0.25 | −0.36 | 0.071 | n.s. |
| Clarity | 3.68 | 4.00 | **−0.32** | **−0.43** | **0.031** | n.s. |
| Overall quality | 3.44 | 3.80 | **−0.36** | **−0.51** | **0.010** | n.s. |

Overall quality and clarity both reach significance at α = 0.05 uncorrected (overall quality d = −0.51, p = 0.010; clarity d = −0.43, p = 0.031). However, when Benjamini–Hochberg FDR correction is applied across the six Likert dimensions, no single dimension survives (the threshold for the smallest p-value at rank 1 of 6 is 0.00833 at α = 0.05, which neither p = 0.010 nor p = 0.031 meets). The overall-quality and clarity effects are therefore significant at α = 0.05 *without* multiple-comparisons correction but do not survive FDR. Engagement shows a comparable effect direction (d = −0.36, p = 0.071); the remaining three dimensions — confidence, naturalness, and authority — do not differ meaningfully between AI and human passages at this sample size. Readers perceive AI text as slightly lower in overall quality and clarity, but we decline to claim statistical separation beyond the uncorrected test.

When asked to identify the single highest-quality passage, 16 of 33 participants (48.5%, 95% CI [30.8%, 66.5%]) selected an AI-generated passage. The base rate for an AI passage being selected at random is 5/8 = 62.5%; readers' selection rate is 14.0 percentage points below base rate, trending in the direction of preferring human-authored passages but not reaching statistical significance at n = 33 (binomial p = 0.107, two-sided vs. 62.5% base rate). On the unfiltered n = 43 cohort the comparison is even weaker (Appendix C.1, p = 0.155). The direction of the effect — readers picking AI at below chance — is consistent with the paper's thesis, but we do not claim it as a significant finding.

Figure 7 visualizes the per-passage composite quality ranking, with each bar colored by ground truth and annotated with the four detectors' ai_scores. The ordering shows the core tension: the persona-engineered AI baseline (Passage H) rates higher than any human-written passage and is flagged by all four detectors at ≥ 0.82, while the three cross-model v2 outputs rate lowest and are mostly passed by three of four detectors. Between these extremes the human-authored passages cluster at mid-quality with noisy detector responses (notably Binoculars false positives on D and F).

![**Figure 7**. Reader-perceived composite quality by passage (n = 33). Green = human-authored, red = AI-generated. Passage H (Dana persona) rates 4.21/5, above every human baseline (3.75–3.77). The three cross-model v2 outputs rate lowest (3.23–3.30). Machine-detector scores annotated at right (Pangram / GPTZero / Copyleaks / Binoculars): Dana (highest quality) is flagged by all four; cross-model v2 outputs (lowest quality) are mostly passed; human passages show noisy detector responses. Human-mean and AI-mean reference lines shown dashed.](figures_v09/fig7_reader_quality_per_passage.png){ width=6.5in fig-alt="Horizontal bar chart. Eight bars (one per passage, labeled A through H) ordered top-to-bottom by reader-perceived composite quality (highest at top). The x-axis is composite quality from 0 to 5. Green bars mark human-authored passages; red bars mark AI-generated passages. The highest bar at the top is Passage H (Dana persona, red) at 4.21. The three lowest bars at the bottom are cross-model 3-way v2 outputs (Passages C, E, G, all red) at 3.23 to 3.30. The three human-authored passages (A, D, F, all green) sit in the middle at 3.75 to 3.77. Two vertical dashed reference lines mark the human mean and the AI mean. Four detector scores per passage (Pangram, GPTZero, Copyleaks, Binoculars) are annotated as text to the right of each bar; the annotated scores are highest for Passage H (highest quality) and mostly near zero for the three cross-model passages (lowest quality), with the human passages showing noisy detector responses in between." }

### 5.5.5 Reader-Cited Features vs. Diagnostic Value

Free-text reasoning entries (n = 165 non-empty entries across 264 passage-judgments; Q8 is optional) were scanned for mentions of specific stylistic features. Table 8 reports, for each feature, how often it was cited in reasoning and how often the citing participant's origin classification was correct.

**Table 8: Features cited in reasoning × classification accuracy**

| Feature cited | Mentions | Accuracy when cited |
|---|---|---|
| Personal anecdote / experience | 35 | 28.6% |
| First-person voice present | 27 | 37.0% |
| Technical density | 23 | 56.5% |
| Typos / grammar errors | 18 | 33.3% |
| Formal / stiff / mechanical tone | 15 | 46.7% |
| Voice / tone (generic) | 10 | 50.0% |
| Polished / overly smooth flow | 10 | **60.0%** |
| "AI stereotype" / cliché | 7 | 14.3% |
| Generic / vague / bland | 7 | 57.1% |
| Conversational / casual | 6 | 50.0% |

The features readers *cite* as evidence are, with one exception, **anti-diagnostic**. When participants cited "personal anecdote" or "first-person voice" as evidence of human authorship, they were correct only 29–37% of the time — worse than chance. When they invoked an "AI stereotype" to justify an AI call, they were correct 14.3% of the time. Only "polished / overly smooth flow" (60.0% accuracy) functions as a weakly diagnostic cue.

These data suggest that readers possess a folk theory of AI writing — the absence of personal voice, the presence of typos, authorial warmth — that does not match the features actually distinguishing calibrated AI text from human text. The cross-model humanization pipeline explicitly preserves first-person pronouns and anecdotal constructions (cf. §5.1 on first-person plural inflation), which is precisely what readers accept as an authenticity signal.

### 5.5.6 Crowd vs. Machine Detectors

To directly test whether human judgment and machine classification agree on the same texts, we computed Spearman rank correlations between each detector's ai_score and the crowd's AI-call rate across the eight passages (§5.4, Table 5a). The headline finding: **crowd judgments correlate negatively with three of four detectors across the full 8-passage set and with all four detectors on AI passages alone** (Pangram ρ = −0.43, GPTZero ρ = −0.09, Copyleaks ρ = −0.25, Binoculars ρ = −0.58 across all 8 passages; on the 5 AI passages alone the correlations range from ρ = −0.31 (Binoculars) to ρ = −0.80 (Pangram), with Copyleaks at ρ = −0.71). None of the AI-only correlations reach conventional significance at n = 5, but the direction is consistent. Machine detectors outperform the crowd on ground-truth binary classification (GPTZero 75%, crowd 50%) but disagree with the crowd on *which* passages are AI.

### 5.5.7 What Predicts Perceived Quality

The classification disagreement established in §5.5.6 raises a second question: do reader *quality* judgments track the same signal as detector classification, or a different one? To test the hypothesis registered in the analysis plan — that reader quality judgments correlate more strongly with linguistic convergence than with detector classification — we computed Spearman rank correlations between the crowd's mean composite quality rating (averaged across clarity, engagement, authority, and overall quality) and each linguistic and detector metric across the eight passages. Composite quality ratings ranged from 3.23 (Passage C, cross-model v2) to 4.21 (Passage H, Dana persona).

**Table 9: Per-passage composite quality, linguistic metrics, detectors**

| Passage | Condition | Composite quality | Density variance | FPS /1k | Contractions /1k | Copyleaks | GPTZero |
|---|---|---|---|---|---|---|---|
| **H** | **Persona (Dana)** | **4.21** | **0.128** | 19.20 | 20.68 | 1.00 | 1.00 |
| F | Human (colah) | 3.77 | 0.000 | 5.38 | 19.91 | 0.00 | 0.05 |
| A | Human (Stripe) | 3.77 | 0.000 | 1.41 | 14.83 | 0.00 | 0.00 |
| D | Human (AWS) | 3.75 | 0.000 | 1.02 | 16.29 | 0.00 | 0.00 |
| B | Surgical v10.2 | 3.54 | 0.013 | 0.00 | 14.08 | 0.87 | 0.79 |
| E | Cross-model v2 | 3.30 | 0.096 | 0.84 | 6.73 | 0.37 | 0.32 |
| G | Cross-model v2 | 3.25 | 0.112 | 0.76 | 12.95 | 0.00 | 0.42 |
| C | Cross-model v2 | 3.23 | 0.034 | 0.00 | 12.59 | 0.00 | 0.51 |

A few per-passage notes on this table worth surfacing against the group-level claims in §§5.1–5.2:

- **All three human survey passages have density variance = 0.000** (DB-computed), because the metric returns near-zero for text with uniform paragraph density — which is typical of the Brandur/Brooker/Olah samples. The non-zero human group mean in Table 3 (0.0157) is driven by one outlier (hudson_go_gc_journey_2018 at 0.094) not used in the survey.
- **Passage H** has the highest density variance in the survey corpus at 0.128, 3.3× the Dana group mean of 0.0383 (Table 3) and 2.3× the next-highest Dana sample (Bloom filter baseline at 0.056). It is a structural outlier within the Dana group; the other six Dana samples range from 0.009 to 0.056. The high variance is consistent with the sample's prompt-driven structural heterogeneity (war-story opener, deliberate digression, listicle section, rhetorical shifts).
- **Cross-model v2 density variances span 0.034 (C) to 0.112 (G)** at the individual-passage level. Passage C in particular is at 0.034 — within 2× of the human-outlier reference — despite being the lowest-quality passage in the study. The group-level "cross-model breaks density variance" claim of §5.2 holds on means, but the per-passage relationship between density variance and reader quality is not monotonic.

Most importantly, density variance does **not** track reader-perceived quality at the passage level: Passage H (0.128, highest DV) is rated highest quality (4.21); Passage C (0.034, moderate DV) is rated lowest (3.23); the three human passages (0.000 DV) rate in the middle of the distribution (3.75–3.77). This is consistent with the Spearman correlation (ρ = −0.22, p = 0.60) reported in Table 10.

**Table 10: Spearman ρ — composite quality vs. linguistic and detector metrics**

| Predictor | All 8 passages | p | AI only (n = 5) | p |
|---|---|---|---|---|
| First-person singular /1k | **+0.898** | **0.002** | +0.564 | 0.322 |
| Contractions /1k | **+0.905** | **0.002** | +0.700 | 0.188 |
| Type-token ratio | **−0.714** | **0.047** | −0.500 | 0.391 |
| Burstiness | +0.515 | 0.192 | +0.359 | 0.553 |
| Information density variance | −0.220 | 0.601 | +0.300 | 0.624 |
| Consecutive similarity | +0.214 | 0.610 | −0.100 | 0.873 |
| Embedding surprisal variance | +0.071 | 0.867 | −0.200 | 0.747 |
| Pangram ai_score | +0.218 | 0.604 | +0.447 | 0.450 |
| GPTZero ai_score | −0.119 | 0.779 | +0.600 | 0.285 |
| Copyleaks ai_score | +0.300 | 0.470 | **+0.975** | **0.005** |
| Binoculars ai_score | +0.357 | 0.385 | +0.600 | 0.285 |

Two findings are notable.

**First, the linguistic features readers prefer are the ones the v10.2 calibration suppresses.** First-person singular pronoun density (ρ = +0.90, p = 0.002) and contraction density (ρ = +0.91, p = 0.002) correlate strongly and significantly with composite perceived quality. Type-token ratio — a common measure of lexical sophistication — correlates significantly negatively (ρ = −0.71, p = 0.047); higher vocabulary diversity corresponds to lower perceived quality. Information density variance, the strongest linguistic discriminator of the Dana persona from human writing in §5.2, is uncorrelated with quality (ρ = −0.22, p = 0.60).

**Second, within the AI passages, higher detector ai_score correlates positively with perceived quality** (Copyleaks ρ = +0.98, p = 0.005 on the 5 AI passages). Passage H (Dana persona) receives the highest composite quality rating of any passage in the study (4.21/5.00), exceeding every human baseline (3.75–3.77) and every humanization-pipeline output (3.23–3.54). The text that detectors most confidently identify as AI is the text readers rate as highest-quality. We note that the 5 AI passages span three pipeline stages by design (1 Dana, 1 v10.2, 3 3-way v2); the +0.98 correlation therefore partly reflects the pipeline-stage structure of the sample, not an independent within-stage ranking ability of detectors. The substantive claim the correlation supports is that Dana — the maximally-detected passage — is also the maximally-rated passage, with every later pipeline stage moving both axes downward.

The pattern generalizes: across every stage of the humanization pipeline, the features readers reward most (warmth overshoot) are suppressed in service of statistical convergence and detector evasion. §5.5.8 develops the supra-human-warmth observation that makes this unavoidable; §6.1 develops the pipeline-wide consequence.

### 5.5.8 Readers Prefer Supra-human Warmth, Not Human-statistical Means

A consequence of the §5.5.7 data deserves separate emphasis. The Dana passage's first-person singular density (19.20/1k) is 3.6× the highest of the three human baselines in the survey (Olah/colah.github.io at 5.38/1k), 13.6× the median of the three (Brandur at 1.41/1k), and 4.5× the human group mean of 4.26/1k computed across the full six-document human corpus (for context, the corpus-level human FPS maximum is Srivastav at 9.39/1k, giving a ratio of 2.0× at that reference). Its contraction density (20.68/1k) is 1.8× the human group mean (11.48/1k); the Dana group as a whole averages 27.14/1k, 2.4× the human group mean. On both features, Dana's densities *exceed* the human population — and Dana is rated the highest-quality passage in the study, above every human-authored comparison.

The v10.2 pipeline was calibrated toward *human statistical means* — a natural design target given the literature's framing of "humanness" as matching human population distributions (Culda et al., 2025; Georgiou, 2025). By that target, v10.2 succeeded: it brought FPS from 19.2/k down to ≈0.4/k, close to human mean 4.26/k, and contractions from 27.1/k to 12.4/k, within 1/k of the human mean. But this calibration moved *away* from the reader-preferred density, not toward it. The reader-preferred direction on these features is above human population means, not toward them.

This suggests that "how human a text reads" — to readers, not to detectors — is not reducible to matching human population statistics on warmth features. On technical writing in this corpus, readers prefer densities that human writers only occasionally reach. The v10.2 pipeline, by aiming at the statistical center of the human distribution, engineered away from this preference. The single most interpretable reader-side finding of the study is the one the humanization literature's standard target would have us miss: **calibrating toward human statistical means is not the same as calibrating toward reader-preferred writing**.

# 6. Discussion

## 6.1 Implications for the Content Industry

Stated as Goodhart's Law: the detector score, adopted as a proxy for writing quality, tracks the very warmth features readers most value — so optimizing against the proxy suppresses those features and degrades the quality it was meant to guarantee. Our corpus is arranged as a cumulative pipeline (§4.1), with each stage layered on top of the previous one and each stage designed to *converge* on human writing — on the metric the detectors explicitly test (distributional fingerprint), on the metrics our linguistic framework measures (function-word density, contractions, burstiness, density variance), and on the subjective impression a voice-engineered persona prompt is tuned to produce. The engineering pipeline successfully hit most of those targets:

- **Detector evasion**: passes Pangram, Copyleaks, and Binoculars at the 3-way v2 stage (only GPTZero still partially flags).
- **Surface linguistic convergence**: holds through the final stage on 8 of 13 metrics we measure, including sentence length, burstiness, type-token ratio, em-dashes, redundancy, and consecutive similarity.
- **Reader-perceived warmth**: the starting Dana persona produces text readers rate higher in quality than every actual human baseline in the study.

Despite these successes, reader-perceived quality declines *monotonically* at every stage of the pipeline (Dana 4.21 → v10.2 3.54 → 3-way v2 3.26 on composite quality, 5-point Likert). Every engineering step that succeeded at defeating detectors or converging on human statistics *also* reduced the signal readers attend to. The pipeline that statistically converges to human population means produces lower-quality text by reader judgment than the persona baseline it was built to improve upon. The pipeline that passes the most detectors produces the lowest-quality text in the study.

This is the full form of the content-industry paradox. The quality-gate architecture that rejects content flagged by any detector rewards exactly the text-engineering that degrades reader-perceived quality. But the paradox runs deeper than detectors alone: **every objective metric our pipeline was designed to optimize (detector evasion, surface linguistic convergence) was largely achieved, and readers still judged the output worse than the starting point.** A content producer who engineers detector-evasion and hits it does not, on our data, preserve the signal that distinguishes text their readers want to read.

Three clarifications follow from this reframing:

**The detector score is not an error proxy that better training could fix.** Every detector we tested responds to a mix of signals: linguistic-distribution deviation from human norms, and the token-level fingerprint of single-model LLM generation. Pangram weights the distribution signal most heavily; Binoculars weights the token-level signal most; GPTZero and Copyleaks use hybrid approaches that weigh both. The pipeline targets different points in this signal space at different stages, but the common feature across all detection architectures is that defeating them requires moving text away from the supra-human warmth signature readers experienced as high quality. On the five AI passages in the survey, the most-flagged passage (Dana, all four detectors ≥ 0.82) is also the highest-quality passage (4.21/5.00, above every human baseline). Making any detector more sensitive to the distribution signal would sharpen its detection of exactly the warmth features readers prize.

**Human evaluation does not substitute for detection.** §5.5 shows that readers are near-zero-discriminable between persona-engineered AI and human technical prose (d′ = 0.138, 95% CI encompassing zero). Crowd judgments and detector outputs produce compatible errors on *different* passages (Cohen's κ between crowd-majority and detectors ranges from −0.25 to +0.39 across the four detectors tested; no single detector agrees strongly with the crowd). A workflow that replaces detector-gating with human-review gating substitutes one set of systematic errors for another.

**Linguistic convergence to human baselines is not a quality criterion.** §5.5.7 shows that on technical blog writing, reader-perceived quality correlates with warmth-overshoot features (first-person density ρ = +0.90, contractions ρ = +0.91) rather than with structural properties. §5.5.8 strengthens the point: readers prefer *supra-human* warmth densities, not the human population means the calibration pipeline was tuned toward. The v10.2 pipeline's successful convergence on human density variance (0.016 ≈ human 0.016) is not a quality achievement; it is a statistical diagnostic that the pipeline performed what it was designed to do. Whether that design goal was worth pursuing is exactly what the reader data calls into question.

## 6.2 Implications for AI Detection Research

Our detector taxonomy reveals a fundamental limitation shared by all four architectures: they detect model-specific distributional fingerprints, not writing quality. Feature-engineered detectors (Pangram) detect surface patterns that are trivially adjustable. Distributional detectors (GPTZero, Copyleaks) detect statistical signatures that are disrupted by model mixing. Perplexity-ratio detectors (Binoculars) rely on assumptions about base-vs-instruct model relationships that may not hold across domains.

None of these approaches measure whether the text reads naturally, conveys information effectively, or demonstrates authentic expertise — the qualities that human writing evaluation actually assesses. Our data suggests this is not a fixable limitation: the features readers use to assess quality (§5.5.7) are the warmth markers a persona-engineered prompt can over-produce, while the statistical signatures detectors rely on are orthogonal to those markers. Detection research should not be expected to converge on quality assessment regardless of architecture improvements; these are separate measurement problems that happen to both concern AI-generated text.

## 6.3 The Measurement Framework as an Alternative

We position the linguistic battery and information-theoretic analysis of §3 as a **mechanistic diagnostic of what a text-engineering pipeline does to its output**, not as a quality proxy. The distinction matters because the reader data in §5.5.7 shows that no metric in our framework — density variance, consecutive similarity, embedding surprisal, lexical diversity, or any of the other 28 — predicts reader-perceived quality on technical writing. The features that do predict reader quality (first-person singular density, contraction density) correlate with the *presence* of warmth-overshoot in the text, not with convergence toward human population statistics.

Read as a mechanistic diagnostic, the framework remains valuable for four tasks:

- **It characterizes what each pipeline changes.** v10.2 suppresses first-person density (16.68 → 0.39 per 1k), normalizes contractions (27.14 → 12.37 per 1k), and brings density variance into human range (0.0383 → 0.0158); 3-way v2 inflates first-person plural density (10.05 → 21.85/1k against human 16.70/1k) and breaks density variance (0.0158 → 0.0771, ≈5× human baseline), while disrupting the consecutive-similarity structure that perplexity detectors rely on. The framework is how we know these statements are true.

- **It explains *why* detectors behave as they do.** Pangram, a feature-engineered detector, is partially defeated by v10.2 (score drops from 0.938 to 0.299) because v10.2 normalizes the surface features Pangram measures. GPTZero and Copyleaks are not, because they rely on distributional properties v10.2 does not touch. Cross-model mixing (3-way v2) defeats all four partial detectors precisely because it disrupts the distributional fingerprints they rely on — at the cost of the structural regularity we can measure.

- **It provides per-dimension interpretable output.** A content producer using the framework receives "your density variance is 0.077 against a human median of 0.016" rather than a binary pass/fail from a detector. This is useful for pipeline development regardless of whether the target dimension correlates with reader quality.

- **It is robust to detector-gaming obfuscation.** Cross-model mixing fools detectors but not the information-theoretic metrics — we can still see that density variance degrades to 5× human baseline even when Copyleaks drops to 0.05.

What the framework does *not* do — and what our data no longer supports claiming — is substitute for reader evaluation. The linguistic convergence of v10.2 to human statistical baselines does not produce reader-preferred text; the divergence of 3-way v2 does not produce reader-rejected text. Reader preference tracks a separate signal (surface warmth cues, in particular first-person density and contraction density) that the framework does not prioritize. A quality-assurance workflow needs the framework *and* direct human evaluation *and* detector scores — each measuring a distinct axis, none individually sufficient.

## 6.4 Limitations

Several limitations constrain generalizability.

**Sample size — corpus.** Our corpus comprises 34 documents across 5 conditions (n = 6–7 per group). While effect sizes are large and statistically significant, larger-scale replication across more topics would strengthen the findings.

**Sample size — human evaluation.** The blind evaluation enrolled 43 participants, of whom 33 were retained after the pre-registered reading-rate exclusion described in §5.5.1. The retained cohort produced 264 passage-level classifications and 165 AI-passage judgments. Primary binomial tests (AI-detection below chance; human-specificity above chance) are well-powered at this sample size (95% CI ± 8 points around the point estimates). Paired Likert contrasts with effect size d ≈ 0.5 are detectable at 80% power; smaller effects may not be. Demographic moderator analyses (experience × accuracy, role × accuracy, AI-confidence × accuracy) are underpowered at n = 33 with 4–5 cells per factor; we report only the primary sample-wide effects and flag moderator analysis as exploratory. Data from the unfiltered n = 43 cohort preserves the direction and significance of every primary effect (AI-detection rate 40.5%, p = 0.003 below chance on the full sample versus 40.6%, p = 0.010 on the n = 33 retained cohort), indicating that the exclusion criterion sharpens but does not manufacture the findings.

**Participant pool.** Participants were recruited via a single Prolific study (US/UK/CA/GB/AU countries; mostly technology professionals, self-reporting ≥2 years of technical reading). Results may not generalize to casual readers, to non-technical domains, or to populations with different literacy profiles. The "best quality" and Likert ratings reflect the aesthetic preferences of an English-speaking professional-technical audience at a particular historical moment (April 2026) — preferences that are themselves subject to drift as public exposure to AI writing increases.

**Quality-correlation sample.** The quality-metric correlations reported in §5.5.7 are computed across the eight passages selected for the survey (n = 8 for the "all passages" columns; n = 5 for AI-only columns). With n = 8, Spearman significance threshold is approximately |ρ| = 0.72 at α = 0.05; with n = 5, |ρ| = 0.90. We report exact correlations and p-values for all reported associations; the strong positive correlations between first-person singular density and composite quality (ρ = +0.90, p = 0.002) and between contraction density and composite quality (ρ = +0.91, p = 0.002) remain significant even under these stringent thresholds, while moderate correlations on the AI-only subsample should be replicated with a larger passage set before strong generalization.

**Domain specificity.** All text is technical writing about software engineering topics. The linguistic battery and information-theoretic analysis may behave differently in other domains (creative writing, journalism, academic prose).

**Single source model.** AI-generated text originates from a single model family (Claude Opus). The calibration pipeline and cross-model mixing may interact differently with text generated by GPT-4, Gemini, or open-source models.

**Human baseline heterogeneity.** The six human baselines come from different authors, years (2014–2018), and platforms. While this reflects real-world variation, it introduces confounds that would not be present with controlled human writing samples.

**Detector versions.** Commercial detectors update their models continuously. Our scores reflect detector behavior at the time of evaluation (April 2026) and may differ in future versions.

**Cross-model mixing scope.** We test one mixing architecture (random sentence-level replacement at ~33% rate) with two model families (Qwen, Mistral). Other mixing strategies, ratios, or model combinations may produce different quality-detection trade-offs.

**Passage-level confounds (topic, length, order).** Three potential confounds at the passage level warrant explicit disclosure:

- *Topic.* The eight survey passages are not matched on topic: three idempotency passages (A human, C cross-model v2, H Dana), two on exponential backoff (D human, E cross-model v2), and one each on attention, Bloom filters, and backpropagation. The within-idempotency triple spans the full quality range observed in the study (A 3.77, C 3.23, H 4.21; spread 0.98, matching the across-all-passages spread exactly), which argues against topic as the primary driver of the quality gradient — the same topic produces the top, middle, and bottom quality ratings depending on source. We cannot, however, fully rule out topic-condition interactions given the sparse per-topic coverage.
- *Length.* Full source documents range 964–1,779 words; the survey presented truncated versions of approximately 800 words each (range 720–910; Appendix B.2). We did not conduct a dedicated length-vs-rating analysis; a length-quality interaction cannot be ruled out.
- *Order.* Passage presentation order was randomized per participant via Fisher–Yates shuffle, which distributes position effects evenly across passages at the group-mean level reported in §5.5.4. A within-participant fatigue effect is present: mean overall-quality rating decreases from 4.00 at position 1 to 3.33 at position 8 (Spearman ρ = −0.21, p = 0.001 across 264 position-rating pairs). Because passages appear at each position across different participants, the per-passage means reported in the paper are unbiased by this effect; but individual raters' absolute scores reflect a fatigue component that future work with shorter batteries could reduce.

# 7. Conclusion

We have demonstrated the detector paradox — an empirical instance of Goodhart's Law — along a single corpus axis. Beginning from a voice-engineered persona baseline (the Dana prompt, §4.1) designed for reader-perceived warmth, each successive engineering step we applied to defeat AI-text detectors also reduced reader-perceived quality. Surgical linguistic calibration (v10.2) reduced one detector score and statistically converged on human population means — and lowered reader quality from 4.21 to 3.54. Cross-model sentence mixing (3-way v2) defeated three of four detectors — and lowered reader quality further to 3.26. Every engineering step that succeeded at defeating detectors failed at preserving the signal readers attend to.

The paradox in a sentence: **every objective target our pipeline was built to hit — detector evasion, surface linguistic convergence toward human means — was largely achieved, and reader-perceived quality declined at every stage anyway**. The Dana persona, unanimously flagged by every detector (ai_score ≥ 0.82), is the highest-quality passage in our study by reader ratings (4.21/5.00, n = 33) and the hardest for readers to correctly classify as AI (27.3% detection rate, p = 0.014 below chance). The 3-way v2 output, which passes three of four detectors and preserves linguistic convergence on 8 of 13 metrics (§5.1–5.2), is the lowest-quality text our readers evaluated.

The mechanism is one pipeline effect: every detector we tested responds to a mix of linguistic-distribution and token-level signals, and every engineering lever that lowers a detector's score routes through the supra-human warmth features readers most value (§6.1). Our 22-linguistic + 6-information-theoretic measurement framework is a mechanistic diagnostic of what a pipeline does to its output (§6.3), not a quality proxy. The content industry's current quality-gate architecture — rejecting text flagged by any AI detector — therefore rewards exactly the text-engineering that degrades reader-perceived quality. The question for future work is not how to build a better detector or a better humanization pipeline, but how to reason about writing quality when no single signal is sufficient and several plausible signals actively disagree.

# References

Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: A practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society: Series B*, 57(1), 289–300. https://doi.org/10.1111/j.2517-6161.1995.tb02031.x

Carver, R. P. (1992). Reading rate: Theory, research, and practical implications. *Journal of Reading*, 36(2), 84–95.

Cheng, Y., Sadasivan, V. S., Saberi, M., Saha, S., & Feizi, S. (2025). Adversarial paraphrasing: A universal attack for humanizing AI-generated text. In *Advances in Neural Information Processing Systems (NeurIPS)*. arXiv:2506.07001.

Culda, L. C., Nerişanu, R. A., Cristescu, M. P., Mara, D. A., Bâra, A., & Oprea, S.-V. (2025). Comparative linguistic analysis framework of human-written vs. machine-generated text. *Connection Science*, 37(1). https://doi.org/10.1080/09540091.2025.2507183

Fleiss, J. L. (1971). Measuring nominal scale agreement among many raters. *Psychological Bulletin*, 76(5), 378–382. https://doi.org/10.1037/h0031619

Gao, L., Schulman, J., & Hilton, J. (2023). Scaling laws for reward model overoptimization. In *Proceedings of the 40th International Conference on Machine Learning (ICML)*. arXiv:2210.10760.

Georgiou, G. P. (2025). Differentiating between human-written and AI-generated texts using automatically extracted linguistic features. *Information*, 16(11), 979. https://doi.org/10.3390/info16110979

Hans, A., Schwarzschild, A., Cherepanova, V., Kazemi, H., Saha, A., Goldblum, M., Geiping, J., & Goldstein, T. (2024). Spotting LLMs with Binoculars: Zero-shot detection of machine-generated text. In *Proceedings of the 41st International Conference on Machine Learning (ICML)*. arXiv:2401.12070.

Kirchenbauer, J., Geiping, J., Wen, Y., Katz, J., Miers, I., & Goldstein, T. (2023). A watermark for large language models. In *Proceedings of the 40th International Conference on Machine Learning (ICML)*. arXiv:2301.10226.

Krishna, K., Song, Y., Karpinska, M., Wieting, J., & Iyyer, M. (2023). Paraphrasing evades detectors of AI-generated text, but retrieval is an effective defense. In *Advances in Neural Information Processing Systems (NeurIPS)*. arXiv:2303.13408.

Kujur, A. (2025). A comparative analysis of AI-generated and human-written text: Linguistic patterns, detection accuracy, and implications for modern communication. *SSRN Working Paper* 5833302.

Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J. (2023). GPT detectors are biased against non-native English writers. *Patterns*, 4(7), 100779. https://doi.org/10.1016/j.patter.2023.100779

Macmillan, N. A., & Creelman, C. D. (2005). *Detection Theory: A User's Guide* (2nd ed.). Lawrence Erlbaum Associates.

Meng, W., Fan, S., Wei, C., Chen, M., Li, Y., Zhang, Y., Zhang, Z., & Chen, W. (2025). GradEscape: A gradient-based evader against AI-generated text detectors. In *Proceedings of the 34th USENIX Security Symposium*. arXiv:2506.08188.

Pudasaini, S., Miralles, L., Lillis, D., & Llorens Salvador, M. (2025). Benchmarking AI text detection: Assessing detectors against new datasets, evasion tactics, and enhanced LLMs. In *Proceedings of the 1st Workshop on GenAI Content Detection (GenAIDetect) at COLING 2025*, pp. 68–77.

Rayner, K. (1998). Eye movements in reading and information processing: 20 years of research. *Psychological Bulletin*, 124(3), 372–422.

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. In *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)*, pp. 3982–3992. https://doi.org/10.18653/v1/D19-1410 (arXiv:1908.10084)

Strathern, M. (1997). 'Improving ratings': Audit in the British University system. *European Review*, 5(3), 305–321.

Thomas, R. L., & Uminsky, D. (2022). Reliance on metrics is a fundamental challenge for AI. *Patterns*, 3(5), 100476. https://doi.org/10.1016/j.patter.2022.100476

Weber-Wulff, D., Anohina-Naumeca, A., Bjelobaba, S., Foltýnek, T., Guerrero-Dib, J., Pohlenz, P., ... & Waddington, L. (2023). Testing of detection tools for AI-generated text. *International Journal for Educational Integrity*, 19(1), 26. https://doi.org/10.1007/s40979-023-00146-z

Zhou, Y., He, B., & Sun, L. (2024). Humanizing machine-generated content: Evading AI-text detection through adversarial attack. In *Proceedings of COLING 2024*. arXiv:2404.01907.

# Declarations

## Ethics, informed consent, and participant protection

This study was conducted by an independent researcher with no institutional affiliation and is therefore exempt from institutional IRB review. The study meets the criteria for minimal-risk, anonymous online research: no personally identifiable information beyond a Prolific participant identifier is collected; participants are adults voluntarily enrolling through the Prolific platform; the task (reading eight short technical essays and rating them) presents no physical, psychological, financial, or reputational risk exceeding everyday internet activity.

Participants provided informed consent via a welcome screen prior to entering the study. The consent text disclosed: (a) the research purpose ("research investigating the gap between AI-generated and human-written technical content"); (b) anonymity ("responses are anonymous; no personally identifiable information is collected beyond the demographic questions"); (c) right to withdraw at any time without penalty; and (d) affirmative consent requirement before proceeding.

Participants were recruited exclusively through Prolific (prolific.com), which handles participant identity verification, eligibility screening, and compensation delivery. The researcher received only anonymous Prolific participant identifiers (PIDs), demographic self-report, IP-derived country code (retained by the Cloudflare infrastructure layer but not used in analysis), and session metadata. No participant name, email address, or other contact information was collected or stored.

**Compensation**: Participants received $6.00 USD per completed survey. At a 25-minute median task time this corresponds to $14.40/hour effective rate, exceeding the Prolific platform-recommended minimum of $8.00/hour. The researcher bore all participant compensation personally; no participant compensation was sponsored, pro-rated, or subsidized by any third party.

## Data availability

All data and derived artifacts supporting this study will be released publicly upon publication:

- **Corpus database** (`humanization.db`): SQLite database containing all 34 corpus documents, per-sample linguistic features (22 metrics), information-theoretic features (6 metrics), and machine-detector scores from four detectors (Pangram, GPTZero, Copyleaks, Binoculars), indexed by sample label and iteration.
- **Survey response data** (`survey_results_n37.json`, `survey_results_n43.json`): Complete JSON output of all statistical analyses reported in §5.5 and Appendix C. Raw survey responses (`responses_final.json`) will be released with Prolific PIDs stripped and replaced with randomized session identifiers; no PID cross-reference is retained.
- **Persona prompt** (`persona_dana_chen.txt`): The full 474-word Dana persona voice prompt used to generate the baseline samples (§4.1).
- **Pipeline outputs**: The surgical v10.2 chain (13-step intervention specification) and the cross-model v2 rewrite prompt, sufficient to reproduce the humanization pipelines described in §4.1.

Release channel: public GitHub repository at <https://github.com/lance-a-diamond/detector-paradox>, archived at Zenodo with DOI [10.5281/zenodo.19767696](https://doi.org/10.5281/zenodo.19767696) (version-specific) and concept DOI [10.5281/zenodo.19767695](https://doi.org/10.5281/zenodo.19767695) (always-newest). License: CC-BY 4.0 for data and text artifacts; MIT for code (see next).

## Code availability

All analysis and figure-generation code will be released publicly upon publication, including:

- `survey_analysis.py`: the complete statistical analysis pipeline used to generate every reported number (§§5.5, 5.5.7, Appendix C).
- `generate_paper_tables.py`: the source-of-truth table generator and validator used to verify every data-heavy table in the paper against underlying data (§§5.1–5.5, Appendix C.1).
- `generate_v09_figures.py` and individual figure scripts (`fig1_hero_paradox.py`, `fig6_crowd_vs_detector.py`, `fig7_reader_quality_per_passage.py`): the seven paper figures as reproducible Python scripts consuming `humanization.db` and `survey_results_n37.json`.
- `survey/` directory: the Cloudflare Worker code administering the blind-evaluation survey, including the consent gate and response capture.

Computational environment: Python 3.11+, scipy 1.17.1, numpy 2.4.4, matplotlib 3.9+, sqlite3 (standard library). Random seed for bootstrap signal-detection CIs (§5.5.2) is `42`, explicitly set in `section_a_classification` to `bootstrap_sdt`. All other analyses are deterministic given the frozen dataset.

License: MIT.

## Author information, funding, and competing interests

Lance Diamond ([ORCID 0009-0004-9691-4997](https://orcid.org/0009-0004-9691-4997)) is an independent researcher developing Scribe, a commercial AI text generation product. The research described in this paper emerged from engineering problems encountered during Scribe's development — specifically, the gap between detector-evasion performance and reader-perceived quality observed in the product's humanization pipelines. This study was entirely self-funded.

**Cost transparency**: detector API costs (Pangram, GPTZero, Copyleaks) and Prolific participant compensation ($6.00 × 43 participants = $258 direct study cost, plus detector API spend in the mid three figures) were paid out-of-pocket by the author. No detector vendor sponsored, discounted, pro-rated, or otherwise supported this work. No detector vendor reviewed this manuscript prior to submission. The author has no external funding to disclose.

**Competing interests disclosure**: The Scribe product operates in the AI text generation space and benefits, commercially, from demonstrated humanization-pipeline efficacy. A finding that humanization pipelines improve reader-perceived quality would favor the product; a finding that they degrade it would not. **The results reported here are of the second, unfavorable type.** Specifically, our data shows that the Dana persona baseline — before any humanization pipeline is applied — outperforms both the surgical v10.2 and cross-model v2 humanization outputs on reader-perceived quality (4.17 vs. 3.57 vs. 3.34 composite quality; §5.5.4, Table 7). This finding was unexpected at the time the study was designed and runs contrary to the commercial interest that motivated the research. We report it unchanged.

No other competing interests to declare.

## Use of AI assistants in research and writing

Per ACL 2024+ disclosure policy: AI coding assistants (Claude, GitHub Copilot) were used during the development of the analysis code and figure generation scripts released with this paper. The humanization pipelines under study (Dana persona generation, surgical v10.2 rewrites, cross-model v2 sentence replacement) use LLMs as the object of study, as described in §4.1. Manuscript drafting, revision, and fact-checking passes were conducted with AI-assistant review loops; all statistical claims, tables, and figures in the manuscript were validated against the source code and source data (see `generate_paper_tables.py --validate`). All scientific claims, experimental design choices, and interpretations are the author's own and were verified against the underlying data before inclusion.

## Potential risks and responsible use

The humanization pipelines studied here (surgical v10.2 and cross-model v2) are dual-use: they are designed to reduce detectability of AI-generated text by commercial detectors, and could be repurposed to bypass academic-integrity or content-authenticity screening. We report them because the paper's central finding — that detector-evasion engineering removes the warmth features readers most value, so policies that gate content on AI detection reject the AI text readers rate highest — is itself the strongest available argument against the current detector-gated content architecture. Releasing the pipeline specifications enables independent replication and invites scrutiny of the paradox rather than concealing it behind a proprietary product. Readers building on this work should attend to the broader implication: detector-evasion optimization moves text away from the features real readers value, so downstream use of these pipelines to produce "undetectable" content is unlikely to improve the text as experienced by its intended audience.

## Pre-registration and deviations from plan

The primary analysis protocol was specified prior to data collection:

- **Primary inclusion criterion** (pre-registered): mean reading rate across the 8-passage battery ≤ 500 words per minute, grounded in Carver's (1992) reading-gear framework (≈ 200 WPM learning, ≈ 300 WPM rauding, ≈ 450 WPM skimming) and Rayner's (1998) 250–300 WPM norm for skilled adult silent reading. Ten of 43 participants met the exclusion criterion; the retained sample is n = 33.
- **Primary outcomes** (pre-registered): (a) AI-detection rate vs. chance (one-sided binomial); (b) signal-detection d′ with 95% CI; (c) per-dimension Likert Δ (AI vs. human) with Benjamini–Hochberg FDR correction across six dimensions; (d) Spearman rank correlations between detector scores and crowd AI-call rate.
- **Secondary / exploratory** (registered as non-primary): (e) persona-vs-humanized Fisher's exact test on pooled AI-detection rates; (f) reasoning-text feature-mention coding; (g) per-passage quality × linguistic metric correlations.

**Deviations from the plan**: None. The analysis reported here follows the pre-registered protocol without post-hoc filter adjustment. The n = 43 unfiltered cohort is reported as a sensitivity check in Appendix C.1 rather than as the primary analysis. A secondary n = 30 top-quality-filter cohort (not pre-registered) is noted in Appendix C.2 for completeness but is not used for any reported headline claim; the Persona-vs-humanized Fisher's p = 0.036 finding that would emerge only under the n = 30 filter is reported transparently as filter-dependent and not claimed as a primary result.

# Appendix A: Metric Definitions

Linguistic metrics are computed in `linguistic_semantic_analysis.py` on text tokenized and sentence-segmented with spaCy's `en_core_web_sm` model (NER disabled). Readability metrics use `textstat`. Surface tells and quality signals (tell count, weighted severity, tricolons) are computed in `ai_tell_scanner.py`, a pure-Python surface-heuristic scanner built on phrase lexicons from Pangram, the Wikipedia "Signs of AI writing" community list, StyloMetrix, and the Mosteller–Wallace function-word tradition. Information-theoretic metrics use sentence embeddings from `sentence-transformers/all-mpnet-base-v2` (Reimers and Gurevych, 2019) and are computed in `information_theoretic_analysis.py`. Per-1k rates are computed as (count × 1000) / word_count. All source code is released in the paper's companion repository.

## A.1 Linguistic battery (22 metrics)

### Voice and person (4 metrics)

1. **First-person singular per 1k** (`first_person_per_1k`): count of tokens matching {I, me, my, mine, myself} (case-insensitive), normalized to per-1000-word rate.
2. **First-person plural per 1k** (`fpp_per_1k`): count of tokens matching {we, us, our, ours, ourselves}, normalized to per-1000-word rate.
3. **Second-person per 1k** (`second_person_per_1k`): count of tokens matching {you, your, yours, yourself, yourselves}, normalized to per-1000-word rate.
4. **Contractions per 1k** (`contractions_per_1k`): count of apostrophe-containing clitic contractions ('s, n't, 'll, 've, 're, 'd, 'm), normalized to per-1000-word rate.

### Readability and structure (5 metrics)

5. **Flesch reading ease**: standard Flesch Reading Ease Score (Kincaid et al., 1975). Computed as 206.835 − 1.015 × (words/sentences) − 84.6 × (syllables/words). Higher is easier.
6. **Mean sentence length** (`sent_mean_len`): arithmetic mean of token counts per sentence.
7. **Burstiness**: standard deviation of sentence lengths divided by mean sentence length (coefficient of variation on sentence length). Higher values indicate greater variation between short and long sentences.
8. **Very short sentence percentage** (`very_short_pct`): fraction of sentences with fewer than 8 tokens, expressed as a percentage.
9. **Very long sentence percentage** (`very_long_pct`): fraction of sentences with more than 35 tokens, expressed as a percentage.

### Lexical diversity (3 metrics)

10. **Type-token ratio** (`type_token_ratio`): unique word types divided by total word tokens. Computed on lower-cased, punctuation-stripped tokens.
11. **Average word length** (`avg_word_len`): mean character length per token (excluding punctuation).
12. **Hapax legomena ratio**: fraction of word types that appear exactly once in the sample. Computed as count of hapaxes divided by vocabulary size (unique types).

### Discourse markers (5 metrics)

13. **Hedging per 1k** (`hedging_per_1k`): count of tokens or bigrams matching a hedging lexicon {perhaps, possibly, somewhat, arguably, rather, quite, fairly, seemingly, apparently, presumably, approximately, roughly, relatively, generally, mostly, largely, often, usually, typically, sometimes, might, may, could, would, appears to, seems to, tends to}, normalized to per-1000-word rate.
14. **Comparatives per 1k** (`comparative_per_1k`): count of adjective-comparative and adverb-comparative POS tags (spaCy `JJR`, `RBR`) plus periphrastic comparatives (more + adjective), normalized to per-1000-word rate.
15. **Em-dashes per 1k** (`em_dashes_per_1k`): count of em-dash characters (—) plus double-hyphen sequences (`--`) not contained in markdown tables, normalized to per-1000-word rate.
16. **Semicolons per 1k** (`semicolons_per_1k`): count of semicolons, normalized to per-1000-word rate.
17. **Quotes per 1k** (`quotes_per_1k`): count of quotation-mark pairs (straight or curly), normalized to per-1000-word rate.

### Quality signals (5 metrics)

18. **Total tell count** (`tell_count`): integer from the surface scanner summing phrase-level hits (Pangram over-used phrases + Wikipedia "Signs of AI writing" lists era-1 and era-2 + cliché lexicon) plus structural-tell counts (copula-avoidance, negative-parallelism, present-participle endings). Full lexicons and detection regexes are released with the scanner source.
19. **Weighted severity** (`weighted_severity`): composite severity score combining the categories above with category-specific weights — Pangram-severity × 1 + era-1 hits × 5 + era-2 hits × 3 + cliché hits × 4 + copula-avoidance × 2 + negative-parallelism × 3 + present-participle × 2 + title-case-heading × 5. Intended as a single-scalar summary of "AI-tell density" for within-corpus ranking; not calibrated to an external benchmark.
20. **Bold/emphasis per 1k** (`bold_per_1k`): count of markdown bold constructions (`**...**` or `__...__`), normalized to per-1000-word rate.
21. **Tricolon count** (`tricolons`): count of rhetorical three-part parallel constructions, detected via a regex pattern matching ", X, and Y" and ", X, Y, and Z" structures with parallel-POS signatures.
22. **Pangram-phrase density per 1k**: count of exact-match hits against the Pangram over-used phrase list (e.g., "plays a crucial role", "it is important to note", "navigate the ... landscape", "delve into", "tapestry of"), normalized to per-1000-word rate. A subcomponent of metric 18 that we break out separately because it is the single strongest phrase-level discriminator in the literature (Pangram reports these phrases appear 70–700× more often in LLM outputs than in human text).

## A.2 Information-theoretic battery (6 metrics)

All six are computed from sentence embeddings produced by `all-mpnet-base-v2` (Reimers and Gurevych, 2019). Each sentence is encoded to a 768-dim unit vector; metrics below are computed on those vectors.

### Redundancy (2 metrics)

1. **Redundancy mean** (`redundancy_mean`): mean pairwise cosine similarity across all sentence-pair combinations in the sample. Higher values indicate repetitive content.
2. **Redundancy max** (`redundancy_max`): maximum pairwise cosine similarity across all sentence pairs. Captures the strongest single repetition in the text.

### Consecutive similarity (2 metrics)

3. **Consecutive similarity mean** (`consecutive_similarity_mean`): mean cosine similarity between adjacent sentence pairs (sentence *i* and *i+1*). Indicates average smoothness of information flow.
4. **Consecutive similarity standard deviation** (`consecutive_similarity_std`): standard deviation of adjacent-pair cosine similarity. Human writing exhibits higher std (topic shifts, asides); AI text tends toward lower std (uniform flow).

### Content-diversity variance (1 metric)

5. **Information density variance** (`density_variance`): per-paragraph content diversity, computed as the mean pairwise Euclidean distance between sentence embeddings within a paragraph, then the variance of that mean across paragraphs. Human writing tends to show higher density variance (technical paragraphs alternate with narrative ones); aligned AI pipelines converge on lower variance. The strongest single linguistic discriminator between AI and human writing in our corpus (§5.2).

### Embedding-transition variance (1 metric)

6. **Embedding surprisal variance** (`embedding_surprisal_variance`): variance of the Euclidean distance between consecutive sentence embeddings. High variance indicates a mixture of predictable transitions and surprising topic shifts, characteristic of human writing.

# Appendix B: Human Evaluation Instrument

The blind evaluation survey was deployed as a Cloudflare Worker with KV-store response capture at `study.verovu.ai`. Full source is released in the `survey/` directory of the release bundle (`build.py` generates the HTML survey; `src/worker.js` handles API endpoints and response storage).

## B.1 Survey flow

Participants encountered seven pages in fixed order:

1. **Welcome + consent** — study purpose, duration estimate (25–30 minutes), anonymity disclosure, affirmative-consent requirement.
2. **Demographics** — four required items: years of professional experience in enterprise technology (1–3 / 4–7 / 8–15 / 16+); current role (Technical Support Engineer / Senior or Escalation Engineer / Support Manager or Director / Software Engineer or Developer / Solutions or Systems Architect / DevOps SRE or Infrastructure / Other); technical-reading frequency (Daily / A few times a week / A few times a month / Rarely); self-assessed confidence in distinguishing AI from human text (1–5 Likert).
3. **Calibration screen** — instructions for the 8-passage task, reminder that human/AI ratio is not disclosed, reminder that the task is anonymous.
4. **Passages 1 through 8** — the eight passages presented in per-participant randomized order.
5. **Debrief** — ground-truth reveal table, per-participant accuracy count, three open-response questions, and one forced-choice "best AI quality" question.
6. **Thanks** — Prolific completion code + submission confirmation.

## B.2 Passage selection

The eight passages were drawn from the 34-document study corpus (§4.1) to span the full pipeline-stage range while holding topic diversity approximately constant:

| Passage | Source | Topic | Stage |
|---|---|---|---|
| A | Human (Brandur Leach / Stripe, 2017) | Idempotency keys | — |
| B | AI (surgical v10.2) | Attention | Stage 3 |
| C | AI (cross-model 3-way v2) | Idempotency keys | Stage 5 |
| D | Human (Marc Brooker / AWS, 2015) | Exponential backoff & jitter | — |
| E | AI (cross-model 3-way v2) | Exponential backoff & jitter | Stage 5 |
| F | Human (Chris Olah / colah.github.io, 2015) | Backpropagation | — |
| G | AI (cross-model 3-way v2) | Bloom filters | Stage 5 |
| H | AI (Dana persona baseline) | Idempotency keys | Stage 1 |

Passages were truncated to approximately 800 words each (range 720–910) at natural section boundaries. Passage C and Passage H share a topic (idempotency keys) at opposite ends of the pipeline; Passage D and Passage E share a topic (exponential backoff) across the human-vs-AI axis at the final pipeline stage. All three human baselines were selected to predate widespread LLM adoption (2015–2017 publication dates) to minimize detector cache-pollution risk (see the feedback rule in our public release on AI detector retrieval-not-classification behavior).

## B.3 Per-passage questions

Each passage page presented eight questions in fixed order:

- **Q1 (required)**: "Do you believe this passage was written by a human or generated by AI?" Binary radio (Human / AI).
- **Q2 (required)**: "How confident are you in your answer above?" 5-point Likert (Complete guess → Very confident).
- **Q3 (required)**: "Does the writing feel natural, like a real person wrote it?" 5-point Likert (Very artificial/mechanical → Completely natural).
- **Q4 (required)**: "Is the technical content explained clearly?" 5-point Likert (Confusing/hard to follow → Very clear).
- **Q5 (required)**: "Is the writing engaging to read?" 5-point Likert (Dull/lost interest → Very engaging).
- **Q6 (required)**: "Does the writer sound like they have real experience?" 5-point Likert (Textbook/no real experience → Deep experience).
- **Q7 (required)**: "How would you rate the overall writing quality?" 5-point Likert (Poor → Excellent).
- **Q8 (optional)**: "What made you think this was human-written or AI-generated?" Free-text field.

The six Likert items (Q2–Q7) compose the Likert battery used for composite quality (Q3–Q5, Q7 averaged) and per-dimension tests (§5.5.4). Q1 provides the binary classification analyzed in §5.5.1–5.5.3. Q8 free-text responses are thematically coded for the reader-cited-features analysis (§5.5.5).

## B.4 Randomization

Passage order is randomized per participant using a Fisher–Yates shuffle of the passage identifier list {A, B, C, D, E, F, G, H}, seeded from `crypto.randomUUID()` at session start. Within each passage page, question order is fixed (Q1–Q8) across participants. No per-participant randomization of Likert anchor order or polarity was applied; all scales are oriented so that 5 is the more favorable pole.

## B.5 Attention checks and exclusion

No forced attention-check items (e.g., "Please select option 3") were included, following Prolific's guidance that such items yield false-positive exclusions on careful readers. Instead, we pre-registered a reading-rate exclusion criterion (§5.5.1): participants with a mean reading rate across the 8-passage, 6,611-word battery exceeding 500 words per minute — a rate above both Carver's (1992) rauding ceiling (≈ 300 WPM) and Rayner's (1998) skilled-adult silent-reading norm (250–300 WPM), and consistent with Carver's "skimming" gear rather than reading for comprehension — are excluded from the primary analysis. Ten of 43 participants met this criterion; the retained n = 33 cohort is the primary analysis sample. The unfiltered n = 43 cohort is reported as a sensitivity check in Appendix C.1.

## B.6 Debrief

After submission of all eight passage evaluations, participants viewed a ground-truth table revealing each passage's source and topic, with their own AI/human guess for each and a running accuracy count. Four debrief questions followed:

- "Were you surprised by any of the answers? Which ones?" (optional free-text)
- "What features do you generally look for when identifying AI-generated text?" (optional free-text)
- "Which AI-generated passage had the highest quality writing?" (forced choice among the five AI passages)
- "Any other comments or observations?" (optional free-text)

The forced "best AI quality" question analyzed in §5.5.4 binds readers to one choice among the five AI passages and is used to test the aggregate preference reported there (16 of 33 = 48.5% selecting an AI passage, p = 0.107 below a 62.5% base rate).

## B.7 Compensation and participant flow

Participants were recruited via a single Prolific study targeting US/UK/CA/AU residents self-reporting professional technical-reading experience. Compensation was $6.00 USD per completed survey at a 25–30 minute target, corresponding to ≈ $14.40/hour median effective rate (Prolific platform minimum: $8.00/hour). See Declarations for ethics disclosures. 43 participants completed the survey; responses were captured in Cloudflare KV and are released in `responses_final.json` with Prolific PIDs replaced by randomized session identifiers.

# Appendix C: Sensitivity Analyses

## C.1 Primary results on the unfiltered n = 43 cohort

Our pre-registered primary analysis (§5.5.1) excludes ten participants whose mean page-based reading rates exceeded 500 WPM. Table C.1 repeats the headline findings on the full unfiltered cohort (n = 43) to confirm that the exclusion sharpens but does not manufacture the reported effects.

**Table C.1: Primary findings — preregistered n = 33 vs. unfiltered n = 43**

| Metric | n = 33 (primary) | n = 43 (unfiltered) |
|---|---|---|
| AI-detection rate | 40.6%, p = 0.010 below chance | 40.5%, p = 0.003 below chance |
| Human-specificity | 64.6%, p = 0.002 above chance | 62.8%, p = 0.002 above chance |
| Overall accuracy | 49.6%, p = 0.95 (at chance) | 48.8%, p = 0.71 (at chance) |
| Signal-detection d′ | 0.138, 95% CI [−0.18, +0.47] | 0.085, 95% CI [−0.19, +0.37] |
| Response criterion c | +0.31 (biased to "human") | +0.28 (biased to "human") |
| Passage H accuracy | 27.3%, p = 0.014 | 27.9%, p = 0.005 |
| Passage D accuracy | 72.7%, p = 0.014 | 72.1%, p = 0.005 |
| Persona vs. humanized (Fisher) | 27.3% vs. 43.9%, p = 0.112 | 27.9% vs. 43.6%, p = 0.082 |
| Quality Likert Δ (uncorrected) | Δ = −0.36, p = 0.010 (< α = 0.05) | Δ = −0.27, p = 0.035 (< α = 0.05) |
| Quality Likert Δ (BH-FDR) | n.s. (threshold 0.0083) | n.s. (threshold 0.0083) |
| Clarity Likert Δ (uncorrected) | Δ = −0.32, p = 0.031 (< α = 0.05) | Δ = −0.26, p = 0.050 |
| "Best-quality" pick = AI | 48.5%, p = 0.107 | 51.2%, p = 0.155 |

All primary effects retain direction; significance levels strengthen slightly under the stricter exclusion. One finding weakens:

- The **"best-quality pick" finding** — that readers pick AI below the 62.5% base rate — is trending in the predicted direction on both cohorts (48.5% at n = 33, 51.2% at n = 43, both below the 62.5% base rate) but does not reach conventional statistical significance under either filter (n = 33 p = 0.107; n = 43 p = 0.155). We report this as a directional finding only, not as a significant result.
- Signal-detection d′ falls from 0.138 (n = 33) to 0.085 (n = 43) when the ten excluded speed-runners are added back, consistent with speed-runners' near-random responses diluting the discrimination test. The 95% CI continues to encompass zero on the unfiltered cohort, so the substantive claim ("no discriminative ability") holds under either filter.

## C.2 Top-30 quality-filtered cohort (post-hoc robustness check)

For completeness we also report results on the top 30 responses by a composite quality score combining total duration, per-passage reading time, Likert variance, reasoning engagement, and origin-guess variety. This is a post-hoc, not pre-registered, filter. All primary effects again hold in direction and significance level; the Copyleaks-ρ anti-correlation on AI passages reaches ρ = −0.92 (p = 0.026) under this stricter filter, providing the strongest signal for the machine-crowd disagreement result. We report the pre-registered n = 33 analysis as primary to avoid any appearance of filter selection after observing the effects; the top-30 cohort is reported here as secondary evidence that the direction of findings is robust to filter choice.

# Appendix D: Glossary

Terms are grouped by scope; entries cover paper-specific usage rather than re-deriving well-known definitions.

## D.1 Corpus and pipeline

- **Dana persona** (also "persona baseline"): the 474-word voice-engineered system prompt used to produce the baseline AI sample in our humanization pipeline (§4.1). Dana is a senior engineer character with specified backstory, vocabulary register, and structural preferences. All AI corpus entries begin from a Dana generation; Dana is not "raw" GPT output.
- **Humanization pipeline**: the cumulative sequence of interventions applied to a Dana generation to reduce AI-detectability and move surface linguistic features toward human population means. Stages are additive, not alternative.
- **Surgical v10.2**: a 13-step rule-based rewrite chain that adjusts surface features (contractions, first-person density, sentence-length variance, hedging frequency, etc.) toward calibrated human targets. Applied on top of the Dana baseline.
- **Cross-model v2** (also "3-way mix v2", "3-way v2"): a stochastic sentence-level rewrite stage applied to surgical v10.2 output. Approximately 33% of sentences are randomly rewritten by Qwen 2.5 14B and Mistral Nemo 12B (local inference) under a calibrated rewrite prompt; the remaining sentences are retained from v10.2. "3-way" refers to the three model families contributing text: Claude Opus 4 (v10.2 base generation) plus Qwen and Mistral (sentence rewrites). "3-way v1" is an earlier variant using an uncalibrated rewrite prompt.
- **Cumulative pipeline**: Dana → surgical v10.2 → cross-model v2, applied in order. We also report each stage as a standalone sample group for ablation.

## D.2 Measurement framework

- **Linguistic battery**: 22 surface-level and stylistic metrics spanning lexical, syntactic, stylistic, register, and cohesion categories (Appendix A). Used to characterize per-sample profiles against a human baseline.
- **Information-theoretic battery**: 6 paragraph- and sentence-level metrics capturing structural variance in information flow. The two metrics most referenced in our results are:
  - **Density variance**: paragraph-level variance in information density (tokens per unit of sentence-BERT embedding displacement). High values indicate uneven compression across paragraphs.
  - **Embedding surprisal variance**: sentence-level variance in predicted-vs-actual semantic position under a sentence-BERT model. High values indicate a text whose next sentences are unusually hard to anticipate.
- **ai_score**: the 0–1 probability score produced by each detector, where 1.0 = "certain AI." Our decision threshold is 0.5 unless a detector publishes a different operating point; we report both raw scores and thresholded classifications.
- **Linguistic-distribution signal**: a detector's response to whether a text's surface linguistic statistics (first-person density, contractions, burstiness, sentence-length variance, etc.) match the distribution of human-authored text. Pangram weights this signal most heavily among the four detectors tested; defeating it requires moving linguistic statistics into the human distribution, which surgical v10.2 does directly.
- **Token-level fingerprint** (also "LLM fingerprint"): a detector's response to the characteristic token-selection pattern that arises from LLM text generation, independent of surface linguistic statistics. Binoculars responds to this signal most directly (via a perplexity ratio between a base and instruction-tuned LM); GPTZero and Copyleaks weight it significantly as part of hybrid approaches. Defeating it requires disrupting the single-model distribution, which cross-model v2 sentence mixing does.

## D.3 Reader evaluation

- **Crowd AI-call rate**: the fraction of the n = 33 readers who guessed "AI" for a given passage. Treated as the crowd-level analogue of a detector ai_score.
- **Reader-perceived quality** (also "composite quality"): the mean of a reader's four 1–5 Likert ratings on clarity, engagement, authority, and overall quality (six-dimension battery with two additional dimensions reported separately). A reader assigns one composite value per passage; the passage-level statistic is the across-readers mean.
- **Detection rate**: per-passage proportion of readers who called the passage AI, conditioned on the passage truly being AI. Reported in §5.5.1.
- **Human-specificity**: per-passage proportion of readers who called the passage human, conditioned on the passage truly being human. The symmetric complement of detection rate on human passages.
- **Warmth features**: the surface linguistic features that predict reader-perceived quality on technical writing in our corpus — first-person singular density (ρ = +0.87 with composite quality), contraction density (ρ = +0.93), and related warmth markers (war-story detail, deliberate digression, concrete personal anecdote). Called "warmth" because they are the features a technical-blog reader experiences as personal voice, in contrast to the impersonal register of conventional technical prose.
- **Supra-human warmth densities**: linguistic-feature densities that exceed human-corpus norms. At the Passage-H level, first-person singular reaches 19.20/1k — 4.5× the human corpus mean (4.26/1k), 2.0× the corpus-level human maximum (Srivastav 9.39/1k), and 3.6× the highest of the three human baselines in the survey (Olah 5.38/1k). At the Dana group level, the average FPS is 16.68/1k, ≈ 4× the human corpus mean; contractions average 27.14/1k, 2.4× the human corpus mean. §5.5.8 shows readers rate supra-human densities higher in quality than human-normal densities.

## D.4 Statistical conventions

- **d′ (d-prime)** and **c (response criterion)**: Signal Detection Theory measures (Macmillan & Creelman, 2005). d′ is the separation between a reader's internal AI and human distributions (zero = no discrimination); c is the reader's decision-threshold bias (positive = bias toward "human" responses). Reported per-reader, pooled across passages, with bootstrap 95% CIs.
- **Composite quality rho**: Spearman rank correlation between per-passage composite quality and per-passage crowd AI-call rate (or detector ai_score). Used in §5.5 to compare reader judgments against machine detectors.
- **Benjamini–Hochberg FDR**: controls the expected proportion of false discoveries across a family of tests. We apply BH-FDR at α = 0.05 across the six Likert dimensions (§5.5.4). The threshold for the smallest p-value is α/m = 0.0083 at m = 6.
- **Preregistered n = 33**: the primary-analysis cohort after applying the reading-rate exclusion. Unfiltered n = 43 is reported as a sensitivity check (Appendix C.1); post-hoc top-30 quality-filtered results appear in Appendix C.2.

# Appendix E: Reproducibility Checklist

This checklist follows the ACL Responsible NLP Checklist categories. Section references point to the authoritative source for each item within this paper.

## E.1 Every submission

- **Limitations** — §6.4.
- **Potential risks** — "Potential risks and responsible use" (Declarations).
- **Use of AI assistants** — "Use of AI assistants in research and writing" (Declarations).

## E.2 Artifacts used or created

- **Licenses and attribution for reused artifacts** — Detectors (Pangram, GPTZero, Copyleaks, Binoculars) are described with source and accession window in §3 and §5; all six human baseline URLs and authors are listed in §4.1 and §5.5 (Brandur Leach/Stripe 2017, Cockroach Labs *Parallel Commits* 2017, Marc Brooker/AWS 2015, Hudson *Go GC Journey* 2018, Srivastav *Bloom Filters* 2014, Chris Olah/colah.github.io 2015).
- **License for released artifacts** — MIT for code, CC-BY 4.0 for text and data; see "Code availability" and "Data availability" (Declarations).
- **Artifact use is consistent with intent** — All human blog posts are publicly licensed or published with permissive reuse terms for research citation; detector API use is consistent with each vendor's terms of service at the evaluation date (April 2026).
- **Documentation** — Released database schema, persona prompt text, pipeline specifications, and analysis scripts are described in "Code availability" and "Data availability" (Declarations).
- **Data statistics** — Corpus: 34 documents across 5 conditions (human n = 6; Dana n = 7; v10.2 n = 7; 3-way v1 n = 7; 3-way v2 n = 7). Survey battery: 8 passages of ~800 words each (6,611-word total). See §4.1, Table 1.
- **PII handling** — Survey responses are released with Prolific PIDs stripped and replaced with randomized session identifiers; no PID cross-reference is retained ("Data availability", Declarations).

## E.3 Computational experiments

- **Model versions** — Baseline generation: Claude Opus 4 at temperature = 1. Cross-model rewrite models: Qwen 2.5 14B and Mistral Nemo 12B via local inference (§4.1). Detector evaluation period: April 2026 (§6.4 Limitations).
- **Number of parameters** — Qwen 2.5 14B = 14B parameters; Mistral Nemo 12B = 12B parameters. Claude Opus 4 parameter count is not publicly disclosed.
- **Computational budget** — Local rewrite inference on a single workstation with an RTX A4500 GPU; total compute for cross-model generation ≈ 6 hours. Statistical analysis runs in under 1 minute end-to-end on a laptop CPU.
- **Hyperparameters** — Only temperature (t = 1) is varied for LLM generation; all other decoding parameters are model default. Rewrite prompts are released as part of the code package.
- **Software environment** — Python 3.11+, scipy 1.17.1, numpy 2.4.4, matplotlib 3.9+, sqlite3 (stdlib). Random seed = 42 for bootstrap signal-detection CIs ("Code availability", Declarations).
- **Summary statistics and significance** — All reported point estimates include confidence intervals or p-values where applicable; per-dimension Likert contrasts are corrected for multiple comparisons via Benjamini–Hochberg FDR (§5.5.4, Appendix D.4).

## E.4 Human subjects

- **Participant instructions** — Survey presented consent gate, task description, and per-passage instructions; full instrument released as part of the survey code ("Code availability", Declarations). Passage order was randomized per participant; human/AI ratio was not disclosed to participants (§5.5).
- **Recruitment and compensation** — Prolific platform; $6.00 USD per completed survey (≈ $14.40/hour median); see "Ethics, informed consent, and participant protection" (Declarations).
- **Informed consent** — Affirmative consent required before task entry; disclosed purpose, anonymity, right to withdraw ("Ethics", Declarations).
- **Ethics review** — Independent-researcher study meeting minimal-risk, anonymous-online-research exemption criteria; no institutional IRB ("Ethics", Declarations).
- **Participant demographics** — Recruited from US/UK/CA/AU; self-reported technical readers (≥ 2 years of technical-writing exposure); detailed distributions on experience, role, and AI confidence are released in the survey response JSON ("Data availability", Declarations). Moderator analyses by demographic stratum are flagged as underpowered at n = 33 (§6.4 Limitations).
