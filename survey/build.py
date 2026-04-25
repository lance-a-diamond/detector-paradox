#!/usr/bin/env python3
"""Build survey/public/index.html from template + passage data."""
import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
STIMULI = os.path.join(DIR, '..', 'human_eval_stimuli.json')
OUTPUT = os.path.join(DIR, 'public', 'index.html')


def main():
    with open(STIMULI) as f:
        raw = json.load(f)

    passages = {}
    for k, v in raw.items():
        pid = k.replace('passage_', '')
        passages[pid] = {'text': v['text'], 'wordCount': v['word_count']}

    pjson = json.dumps(passages, ensure_ascii=False)
    pjson = pjson.replace('</', '<\\/')  # prevent </script> injection

    html = TEMPLATE.replace('"__PASSAGE_DATA__"', pjson)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'Generated {OUTPUT} ({len(html):,} bytes, {len(html)/1024:.1f} KB)')


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive">
<title>Technical Writing Quality Evaluation</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"
      crossorigin="anonymous">
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: #f5f5f7;
  color: #1d1d1f;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

#app {
  max-width: 720px;
  margin: 0 auto;
  padding: 0 1.25rem 3rem;
  min-height: 100vh;
}

.progress-wrap {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #f5f5f7;
  padding: 1.25rem 0 0.75rem;
}

.progress-track {
  height: 5px;
  background: #e5e5ea;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #0066cc;
  border-radius: 3px;
  transition: width 0.4s ease;
}

.progress-label {
  font-size: 0.8rem;
  color: #86868b;
  margin-top: 0.35rem;
  text-align: right;
}

.page {
  background: #fff;
  border-radius: 16px;
  padding: 2.5rem;
  margin-top: 0.75rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
}

h1 { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.75rem; }
h2 { font-size: 1.4rem; font-weight: 600; letter-spacing: -0.01em; margin-bottom: 0.5rem; }
h3 { font-size: 1.15rem; font-weight: 600; margin-bottom: 0.4rem; }

.lead { font-size: 1.1rem; color: #424245; margin-bottom: 1.25rem; line-height: 1.7; }
.section-desc { color: #6e6e73; margin-bottom: 1.5rem; }
.instruction { color: #6e6e73; font-size: 0.95rem; margin-bottom: 0.5rem; }

p + p { margin-top: 0.75rem; }

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.7rem 1.75rem;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary { background: #0066cc; color: #fff; }
.btn-primary:hover { background: #0055b3; }
.btn-primary:disabled { background: #99c8f0; cursor: not-allowed; }

.btn-secondary { background: #f5f5f7; color: #1d1d1f; border: 1px solid #d2d2d7; }
.btn-secondary:hover { background: #ececf0; }

.btn-submit { background: #34c759; color: #fff; font-weight: 600; padding: 0.8rem 2.5rem; font-size: 1rem; }
.btn-submit:hover { background: #2db84e; }
.btn-submit:disabled { background: #a8e6be; cursor: not-allowed; }

.nav-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #f0f0f2;
}

.question-group { margin-bottom: 1.75rem; }

.question-label {
  display: block;
  font-weight: 600;
  font-size: 0.95rem;
  margin-bottom: 0.6rem;
  color: #1d1d1f;
}

.required::after { content: ' *'; color: #ff3b30; font-weight: 400; }

.radio-group label {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.65rem 0.9rem;
  margin: 0.35rem 0;
  border: 1px solid #e5e5ea;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 0.95rem;
}

.radio-group label:hover { background: #f0f5ff; border-color: #99c8f0; }
.radio-group input[type="radio"] { accent-color: #0066cc; flex-shrink: 0; }
.radio-group input[type="radio"]:checked ~ span { color: #0066cc; font-weight: 500; }

.likert { margin: 0.5rem 0 0.25rem; }

.likert-row {
  display: flex;
  justify-content: center;
  gap: 0.6rem;
}

.likert-option { cursor: pointer; text-align: center; }
.likert-option input { display: none; }

.likert-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  border: 2px solid #d2d2d7;
  font-size: 1rem;
  font-weight: 500;
  color: #86868b;
  transition: all 0.15s ease;
  user-select: none;
}

.likert-option:hover .likert-circle { border-color: #99c8f0; color: #0066cc; }
.likert-option input:checked + .likert-circle {
  background: #0066cc;
  border-color: #0066cc;
  color: #fff;
}

.likert-anchors {
  display: flex;
  justify-content: space-between;
  margin-top: 0.35rem;
  font-size: 0.78rem;
  color: #86868b;
  padding: 0 0.25rem;
}

.passage-card {
  background: #fff;
  border: 1px solid #e0e0e3;
  border-radius: 14px;
  padding: 2.5rem 2.75rem;
  margin: 1rem 0 2rem;
  font-family: Georgia, 'Times New Roman', 'Noto Serif', serif;
  font-size: 1.05rem;
  line-height: 1.9;
  color: #2c2c2e;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.passage-card p { margin-bottom: 1.15rem; }
.passage-card p:last-child { margin-bottom: 0; }

.passage-card h2 {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  font-size: 1.45rem;
  font-weight: 700;
  margin: 0 0 0.4rem;
  color: #1d1d1f;
  letter-spacing: -0.01em;
}

.passage-card h2 + p { margin-top: 0.5rem; }

.passage-card h3 {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  font-size: 1.2rem;
  font-weight: 700;
  margin: 2.25rem 0 0.6rem;
  padding-top: 1.25rem;
  border-top: 1px solid #f0f0f2;
  color: #1d1d1f;
}

.passage-card h2 + h3,
.passage-card h3:first-child { margin-top: 0; padding-top: 0; border-top: none; }

.passage-card ul {
  padding-left: 1.5rem;
  margin-bottom: 1.15rem;
}

.passage-card li {
  margin-bottom: 0.5rem;
  padding-left: 0.25rem;
}

.passage-card pre {
  background: #f7f7f8;
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
  overflow-x: auto;
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', Menlo, monospace;
  font-size: 0.82rem;
  line-height: 1.6;
  margin: 1.25rem 0;
  border: 1px solid #e8e8eb;
}

.passage-card code:not(pre code) {
  background: #f0f0f2;
  padding: 0.15em 0.4em;
  border-radius: 4px;
  font-size: 0.87em;
  font-family: 'SF Mono', 'Fira Code', Menlo, monospace;
}

.passage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.passage-counter {
  font-size: 0.85rem;
  font-weight: 600;
  color: #5856d6;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

textarea {
  width: 100%;
  min-height: 90px;
  padding: 0.75rem 1rem;
  border: 1px solid #d2d2d7;
  border-radius: 10px;
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 0.15s;
}

textarea:focus { outline: none; border-color: #0066cc; box-shadow: 0 0 0 3px rgba(0,102,204,0.15); }
textarea::placeholder { color: #aeaeb2; }

.validation-error {
  color: #ff3b30;
  font-size: 0.88rem;
  margin-top: 0.5rem;
  display: none;
  padding: 0.5rem 0.75rem;
  background: #fff2f2;
  border-radius: 8px;
  border: 1px solid #ffd6d6;
}

.example-box {
  margin: 1.25rem 0;
  padding: 1.25rem 1.5rem;
  border-radius: 12px;
  border-left: 4px solid;
}

.example-human { background: #f0faf0; border-color: #34c759; }
.example-ai { background: #fff8f0; border-color: #ff9500; }

.example-label { font-weight: 600; font-size: 0.9rem; margin-bottom: 0.6rem; }

blockquote {
  font-family: Georgia, serif;
  font-style: italic;
  color: #424245;
  line-height: 1.7;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
  margin: 1rem 0 2rem;
}

.results-table th {
  text-align: left;
  padding: 0.6rem 0.75rem;
  background: #f5f5f7;
  border-bottom: 2px solid #e5e5ea;
  font-weight: 600;
  font-size: 0.82rem;
  color: #86868b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.results-table td {
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid #f0f0f2;
  vertical-align: top;
}

.results-table .correct td { background: #f0faf0; }
.results-table .incorrect td { background: #fff8f6; }

.badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.badge-human { background: #d1fae5; color: #065f46; }
.badge-ai { background: #fde68a; color: #92400e; }

.score-banner {
  text-align: center;
  padding: 1rem;
  margin: 1rem 0 1.5rem;
  background: #f0f5ff;
  border-radius: 12px;
  font-size: 1.1rem;
}

.table-container { overflow-x: auto; }

.page-thanks { text-align: center; padding: 3rem 2rem; }
.page-thanks h1 { font-size: 2rem; margin-bottom: 1rem; }
.page-thanks .lead { max-width: 500px; margin: 0 auto 1rem; }

@media (max-width: 600px) {
  .page { padding: 1.5rem; border-radius: 12px; }
  .passage-card { padding: 1.25rem 1rem; }
  .likert-circle { width: 40px; height: 40px; font-size: 0.9rem; }
  .likert-row { gap: 0.4rem; }
  h1 { font-size: 1.4rem; }
  .results-table { font-size: 0.82rem; }
  .results-table th, .results-table td { padding: 0.4rem; }
}
</style>
</head>
<body>
<div id="app"></div>

<script type="application/json" id="pdata">"__PASSAGE_DATA__"</script>

<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"
        crossorigin="anonymous"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
        crossorigin="anonymous"></script>

<script>
(function() {
  'use strict';

  // ===== PASSAGE DATA =====
  var PASSAGES = JSON.parse(document.getElementById('pdata').textContent);

  // ===== ANSWER KEY =====
  var ANSWERS = {
    A: { source: 'Human', detail: 'Brandur Leach, Stripe Engineering Blog (2017)', topic: 'Idempotency Keys' },
    B: { source: 'AI',    detail: 'Humanized via surgical pipeline + function-word calibration', topic: 'Idempotency Keys' },
    C: { source: 'AI',    detail: 'Humanized + cross-model sentence mixing (3 models)', topic: 'Idempotency Keys' },
    D: { source: 'Human', detail: 'Marc Brooker, AWS Architecture Blog (2015)', topic: 'Exponential Backoff & Jitter' },
    E: { source: 'AI',    detail: 'Humanized + cross-model sentence mixing (3 models)', topic: 'Exponential Backoff & Jitter' },
    F: { source: 'Human', detail: 'Chris Olah, colah.github.io (2015)', topic: 'Backpropagation' },
    G: { source: 'AI',    detail: 'Humanized + cross-model sentence mixing (3 models)', topic: 'Bloom Filters' },
    H: { source: 'AI',    detail: 'Raw AI generation (no humanization)', topic: 'Idempotency Keys' }
  };

  // ===== STATE =====
  var state = {
    page: 0,
    sessionId: crypto.randomUUID(),
    startTime: new Date().toISOString(),
    passageOrder: shuffle(Object.keys(PASSAGES)),
    demographics: {},
    passages: {},
    debrief: {},
    submitted: false,
    pageStart: Date.now()
  };

  // Restore saved progress
  try {
    var saved = localStorage.getItem('survey_progress');
    if (saved) {
      var parsed = JSON.parse(saved);
      if (!parsed.submitted && parsed.page > 0) {
        if (confirm('You have saved progress (page ' + (parsed.page + 1) + '). Resume where you left off?')) {
          state = parsed;
          state.pageStart = Date.now();
        }
      }
    }
  } catch(e) { /* ignore */ }

  // ===== UTILITIES =====
  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function esc(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function saveProgress() {
    try { localStorage.setItem('survey_progress', JSON.stringify(state)); } catch(e) {}
  }

  // ===== TEXT RENDERING =====
  function isHeading(block) {
    if (block.split('\n').length > 1) return false;
    if (block.length > 100) return false;
    if (/[.;,:]$/.test(block)) return false;          // ends with sentence punctuation
    if ((block.match(/[.]/g) || []).length > 1) return false; // multiple periods = sentence
    if (!/^[A-Z"\u201c]/.test(block)) return false;
    if (block.split(' ').length > 14) return false;
    // Reject if it reads like a sentence (starts with article/pronoun + verb pattern)
    if (/^(The |A |An |In |On |If |So |But |For |When |While |Or |Upon |Each |Our |This |With |We |It |That |There )/.test(block) && block.split(' ').length > 6) return false;
    return true;
  }

  function renderText(text) {
    // Extract code blocks first (1-3 backtick delimiters)
    var codes = [];
    text = text.replace(/`{1,3}(\w*)\n([\s\S]*?)`{1,3}/g, function(m, lang, code) {
      var idx = codes.length;
      codes.push('<pre><code>' + esc(code.trim()) + '</code></pre>');
      return '\n\n%%CODE' + idx + '%%\n\n';
    });

    // Split into raw blocks
    var rawBlocks = text.split(/\n\n+/).map(function(b) { return b.trim(); }).filter(Boolean);

    // Group consecutive bullet items into single lists
    var grouped = [];
    var bulletBuf = [];
    for (var i = 0; i < rawBlocks.length; i++) {
      if (/^[-\u2022]\s/.test(rawBlocks[i])) {
        bulletBuf.push(rawBlocks[i]);
      } else {
        if (bulletBuf.length) { grouped.push({ t: 'ul', items: bulletBuf }); bulletBuf = []; }
        grouped.push({ t: 'block', text: rawBlocks[i] });
      }
    }
    if (bulletBuf.length) grouped.push({ t: 'ul', items: bulletBuf });

    var isFirst = true;
    return grouped.map(function(item) {
      if (item.t === 'ul') {
        return '<ul>' + item.items.map(function(b) {
          return '<li>' + b.replace(/^[-\u2022]\s/, '') + '</li>';
        }).join('') + '</ul>';
      }

      var block = item.text;

      // Code placeholder
      var cm = block.match(/^%%CODE(\d+)%%$/);
      if (cm) return codes[parseInt(cm[1])];

      // Heading detection
      if (isHeading(block)) {
        var tag = isFirst ? 'h2' : 'h3';
        isFirst = false;
        return '<' + tag + '>' + block + '</' + tag + '>';
      }
      isFirst = false;

      // Regular paragraph — handle inline code
      block = block.replace(/`([^`\n]+)`/g, '<code>$1</code>');
      return '<p>' + block.replace(/\n/g, ' ') + '</p>';
    }).join('\n');
  }

  // ===== LIKERT RENDERER =====
  function likert(name, leftLbl, rightLbl, val) {
    var h = '<div class="likert"><div class="likert-row">';
    for (var i = 1; i <= 5; i++) {
      h += '<label class="likert-option">'
        + '<input type="radio" name="' + name + '" value="' + i + '"'
        + (val === i ? ' checked' : '') + '>'
        + '<span class="likert-circle">' + i + '</span></label>';
    }
    h += '</div><div class="likert-anchors"><span>' + leftLbl + '</span><span>' + rightLbl + '</span></div></div>';
    return h;
  }

  // ===== RADIO GROUP =====
  function radioGroup(name, options, selected) {
    return '<div class="radio-group" data-field="' + name + '">'
      + options.map(function(opt) {
          return '<label><input type="radio" name="' + name + '" value="' + opt + '"'
            + (selected === opt ? ' checked' : '') + '><span>' + opt + '</span></label>';
        }).join('')
      + '</div>';
  }

  // ===== PAGE RENDERERS =====

  function pgWelcome() {
    return '<div class="page">'
      + '<h1>Technical Writing Quality Evaluation</h1>'
      + '<p class="lead">Thank you for participating in this research study on technical writing quality.</p>'
      + '<p>You will read <strong>8 short passages</strong> (~800 words each) about various software engineering topics and evaluate each one.</p>'
      + '<p>The study takes approximately <strong>25\u201330 minutes</strong>.</p>'
      + '<p>Your responses are anonymous. No personally identifiable information is collected beyond the demographic questions on the next page.</p>'
      + '<p style="margin-top:1.25rem">By proceeding, you consent to participate in this study. You may stop at any time.</p>'
      + '<div class="nav-buttons"><div></div>'
      + '<button class="btn btn-primary" onclick="SV.next()">Begin Study \u2192</button>'
      + '</div></div>';
  }

  function pgDemographics() {
    var d = state.demographics;
    return '<div class="page">'
      + '<h2>About You</h2>'
      + '<p class="section-desc">These questions help us understand the background of our evaluators.</p>'

      + '<div class="question-group">'
      + '<label class="question-label required">How many years of professional experience in enterprise technology do you have?</label>'
      + radioGroup('experience', ['1\u20133 years','4\u20137 years','8\u201315 years','16+ years'], d.experience)
      + '</div>'

      + '<div class="question-group">'
      + '<label class="question-label required">Which best describes your current role?</label>'
      + radioGroup('role', ['Technical Support Engineer','Senior / Escalation Engineer','Support Manager / Director','Software Engineer / Developer','Solutions / Systems Architect','DevOps / SRE / Infrastructure','Other'], d.role)
      + '</div>'

      + '<div class="question-group">'
      + '<label class="question-label required">How often do you read technical documentation, blog posts, or knowledge base articles?</label>'
      + radioGroup('readFrequency', ['Daily','A few times a week','A few times a month','Rarely'], d.readFrequency)
      + '</div>'

      + '<div class="question-group">'
      + '<label class="question-label required">How confident are you in your ability to distinguish AI-generated text from human-written text?</label>'
      + likert('aiConfidence', 'Not at all confident', 'Very confident', d.aiConfidence)
      + '</div>'

      + '<div id="vmsg" class="validation-error"></div>'
      + '<div class="nav-buttons">'
      + '<button class="btn btn-secondary" onclick="SV.prev()">\u2190 Back</button>'
      + '<button class="btn btn-primary" onclick="SV.next()">Continue \u2192</button>'
      + '</div></div>';
  }

  function pgCalibration() {
    return '<div class="page">'
      + '<h2>Calibration</h2>'
      + '<p>Before you begin, here are two examples to calibrate your expectations.</p>'

      + '<div class="example-box example-human">'
      + '<div class="example-label">Example A \u2014 Written by a human engineer:</div>'
      + '<blockquote>\u201CI\u2019ve been mass-deleting projects from my GitHub and mass-archiving emails, which feels great. '
      + 'There\u2019s something satisfying about declaring technical bankruptcy on old ideas that will never ship. '
      + 'My three-year-old Kubernetes operator that was going to revolutionize config management? Archived. '
      + 'The half-finished CLI tool that already has twelve better alternatives? Deleted.\u201D</blockquote>'
      + '</div>'

      + '<div class="example-box example-ai">'
      + '<div class="example-label">Example B \u2014 Generated by an AI language model:</div>'
      + '<blockquote>\u201CConfiguration management represents a critical component of modern infrastructure operations. '
      + 'Organizations must carefully evaluate their tooling choices to ensure alignment with operational requirements '
      + 'and scalability objectives. The selection of appropriate configuration management frameworks directly impacts '
      + 'deployment reliability and system maintainability.\u201D</blockquote>'
      + '</div>'

      + '<p>Notice the differences: the human example uses first-person narrative, specific details, casual voice, and humor. '
      + 'The AI example uses abstract language, formal tone, and generic statements.</p>'
      + '<p><strong>However</strong>, not all AI text is this obvious \u2014 modern AI can produce much more '
      + 'natural-sounding prose. Use your best judgment on each passage.</p>'

      + '<div class="nav-buttons">'
      + '<button class="btn btn-secondary" onclick="SV.prev()">\u2190 Back</button>'
      + '<button class="btn btn-primary" onclick="SV.next()">Begin Evaluation \u2192</button>'
      + '</div></div>';
  }

  function pgPassage(passageId, num) {
    var r = state.passages[passageId] || {};

    return '<div class="page">'
      + '<div class="passage-header"><span class="passage-counter">Passage ' + num + ' of 8</span></div>'
      + '<p class="instruction">Read the following passage carefully, then answer the questions below.</p>'
      + '<div class="passage-card" id="passage-text">' + renderText(PASSAGES[passageId].text) + '</div>'

      + '<div class="questions">'

      + '<div class="question-group">'
      + '<label class="question-label required">Q1. Do you believe this passage was written by a human or generated by AI?</label>'
      + '<div class="radio-group" data-field="origin">'
      + '<label><input type="radio" name="origin" value="human"' + (r.origin==='human'?' checked':'') + '><span>Written by a human</span></label>'
      + '<label><input type="radio" name="origin" value="ai"' + (r.origin==='ai'?' checked':'') + '><span>Generated by AI</span></label>'
      + '</div></div>'

      + '<div class="question-group">'
      + '<label class="question-label required">Q2. How confident are you in your answer above?</label>'
      + likert('confidence', 'Complete guess', 'Very confident', r.confidence) + '</div>'

      + '<div class="question-group">'
      + '<label class="question-label required">Q3. Does the writing feel natural, like a real person wrote it?</label>'
      + likert('naturalness', 'Very artificial / mechanical', 'Completely natural', r.naturalness) + '</div>'

      + '<div class="question-group">'
      + '<label class="question-label required">Q4. Is the technical content explained clearly?</label>'
      + likert('clarity', 'Confusing / hard to follow', 'Very clear', r.clarity) + '</div>'

      + '<div class="question-group">'
      + '<label class="question-label required">Q5. Is the writing engaging to read?</label>'
      + likert('engagement', 'Dull / lost interest', 'Very engaging', r.engagement) + '</div>'

      + '<div class="question-group">'
      + '<label class="question-label required">Q6. Does the writer sound like they have real experience?</label>'
      + likert('authority', 'Textbook / no real experience', 'Deep experience', r.authority) + '</div>'

      + '<div class="question-group">'
      + '<label class="question-label required">Q7. How would you rate the overall writing quality?</label>'
      + likert('quality', 'Poor', 'Excellent', r.quality) + '</div>'

      + '<div class="question-group">'
      + '<label class="question-label">Q8. What made you think this was human-written or AI-generated? (optional)</label>'
      + '<textarea name="reasoning" placeholder="What specific features did you notice?">' + (r.reasoning||'') + '</textarea>'
      + '</div>'

      + '</div>'

      + '<div id="vmsg" class="validation-error"></div>'
      + '<div class="nav-buttons">'
      + '<button class="btn btn-secondary" onclick="SV.prev()">\u2190 ' + (num===1?'Back to Calibration':'Previous Passage') + '</button>'
      + '<button class="btn btn-primary" onclick="SV.next()">' + (num===8?'Continue to Debrief':'Next Passage') + ' \u2192</button>'
      + '</div></div>';
  }

  function pgDebrief() {
    var db = state.debrief;
    var correctCount = 0;

    var rows = state.passageOrder.map(function(id, idx) {
      var ans = ANSWERS[id];
      var guess = (state.passages[id] || {}).origin;
      var correct = (guess === 'human' && ans.source === 'Human') ||
                    (guess === 'ai' && ans.source === 'AI');
      if (correct) correctCount++;
      return '<tr class="' + (correct ? 'correct' : 'incorrect') + '">'
        + '<td>Passage ' + (idx+1) + '</td>'
        + '<td><span class="badge badge-' + ans.source.toLowerCase() + '">' + ans.source + '</span></td>'
        + '<td>' + ans.detail + '</td>'
        + '<td>' + ans.topic + '</td>'
        + '<td>' + (correct ? '\u2713' : '\u2717') + '</td>'
        + '</tr>';
    }).join('');

    // Build AI-passage options for "best AI" question
    var aiOptions = state.passageOrder
      .filter(function(id) { return ANSWERS[id].source === 'AI'; })
      .map(function(id) {
        var num = state.passageOrder.indexOf(id) + 1;
        return '<label><input type="radio" name="bestAi" value="' + id + '"'
          + (db.bestAi === id ? ' checked' : '')
          + '><span>Passage ' + num + ' \u2014 ' + ANSWERS[id].topic + '</span></label>';
      }).join('');

    return '<div class="page">'
      + '<h2>Results &amp; Debrief</h2>'
      + '<p>Thank you for completing the evaluation! Here are the answers:</p>'
      + '<div class="score-banner">You correctly identified <strong>' + correctCount + ' out of 8</strong> passages.</div>'

      + '<div class="table-container"><table class="results-table">'
      + '<thead><tr><th>#</th><th>Source</th><th>Details</th><th>Topic</th><th>Result</th></tr></thead>'
      + '<tbody>' + rows + '</tbody></table></div>'

      + '<h3>Final Questions</h3>'

      + '<div class="question-group">'
      + '<label class="question-label">Were you surprised by any of the answers? Which ones?</label>'
      + '<textarea name="surprised" placeholder="Tell us which results surprised you...">' + (db.surprised||'') + '</textarea></div>'

      + '<div class="question-group">'
      + '<label class="question-label">What features do you generally look for when identifying AI-generated text?</label>'
      + '<textarea name="features" placeholder="What clues do you look for?">' + (db.features||'') + '</textarea></div>'

      + '<div class="question-group">'
      + '<label class="question-label">Which AI-generated passage had the highest quality writing?</label>'
      + '<div class="radio-group" data-field="bestAi">' + aiOptions + '</div></div>'

      + '<div class="question-group">'
      + '<label class="question-label">Any other comments or observations?</label>'
      + '<textarea name="comments" placeholder="Optional">' + (db.comments||'') + '</textarea></div>'

      + '<div id="vmsg" class="validation-error"></div>'
      + '<div class="nav-buttons">'
      + '<button class="btn btn-secondary" onclick="SV.prev()">\u2190 Back</button>'
      + '<button class="btn btn-submit" onclick="SV.submit()">Submit Survey</button>'
      + '</div></div>';
  }

  function pgThanks() {
    return '<div class="page page-thanks">'
      + '<h1>\u2705 Thank You!</h1>'
      + '<p class="lead">Your responses have been recorded successfully.</p>'
      + '<p>This study is part of research investigating the gap between AI-generated and human-written technical content. '
      + 'Your evaluations will help us understand how professionals perceive writing quality across different generation methods.</p>'
      + '<p style="margin-top:1.5rem;color:#86868b">You may now close this tab.</p>'
      + '</div>';
  }

  // ===== NAVIGATION =====
  // Total: 0=welcome, 1=demographics, 2=calibration, 3-10=passages, 11=debrief, 12=thanks

  function render() {
    state.pageStart = Date.now();
    var pct = state.page >= 12 ? 100 : Math.round((state.page / 12) * 100);
    var lbl = '';
    if (state.page === 0) lbl = 'Welcome';
    else if (state.page === 1) lbl = 'Demographics';
    else if (state.page === 2) lbl = 'Calibration';
    else if (state.page >= 3 && state.page <= 10) lbl = 'Passage ' + (state.page - 2) + '/8';
    else if (state.page === 11) lbl = 'Debrief';
    else lbl = 'Complete';

    var html = '<div class="progress-wrap">'
      + '<div class="progress-track"><div class="progress-fill" style="width:' + pct + '%"></div></div>'
      + '<div class="progress-label">' + lbl + '</div></div>';

    if (state.page === 0) html += pgWelcome();
    else if (state.page === 1) html += pgDemographics();
    else if (state.page === 2) html += pgCalibration();
    else if (state.page >= 3 && state.page <= 10) {
      var idx = state.page - 3;
      html += pgPassage(state.passageOrder[idx], idx + 1);
    }
    else if (state.page === 11) html += pgDebrief();
    else html += pgThanks();

    document.getElementById('app').innerHTML = html;
    window.scrollTo(0, 0);

    // KaTeX rendering for math passages
    if (typeof renderMathInElement === 'function') {
      var el = document.getElementById('passage-text');
      if (el) {
        renderMathInElement(el, {
          delimiters: [
            {left: '\\(', right: '\\)', display: false},
            {left: '\\[', right: '\\]', display: true}
          ],
          throwOnError: false
        });
      }
    }

    saveProgress();
  }

  // ===== DATA COLLECTION =====

  function collect() {
    if (state.page === 1) {
      document.querySelectorAll('.radio-group input:checked').forEach(function(inp) {
        var g = inp.closest('.radio-group');
        if (g && g.dataset.field) state.demographics[g.dataset.field] = inp.value;
      });
      document.querySelectorAll('.likert input:checked').forEach(function(inp) {
        state.demographics[inp.name] = parseInt(inp.value);
      });
    }
    else if (state.page >= 3 && state.page <= 10) {
      var pid = state.passageOrder[state.page - 3];
      var r = {};
      var oi = document.querySelector('input[name="origin"]:checked');
      if (oi) r.origin = oi.value;
      ['confidence','naturalness','clarity','engagement','authority','quality'].forEach(function(n) {
        var el = document.querySelector('input[name="' + n + '"]:checked');
        if (el) r[n] = parseInt(el.value);
      });
      var ta = document.querySelector('textarea[name="reasoning"]');
      if (ta) r.reasoning = ta.value;
      r.timeOnPage = Math.round((Date.now() - state.pageStart) / 1000);
      state.passages[pid] = r;
    }
    else if (state.page === 11) {
      ['surprised','features','comments'].forEach(function(n) {
        var el = document.querySelector('textarea[name="' + n + '"]');
        if (el) state.debrief[n] = el.value;
      });
      var bi = document.querySelector('input[name="bestAi"]:checked');
      if (bi) state.debrief.bestAi = bi.value;
    }
  }

  // ===== VALIDATION =====

  function validate() {
    if (state.page === 1) {
      var d = state.demographics;
      if (!d.experience || !d.role || !d.readFrequency || !d.aiConfidence)
        return 'Please answer all questions before continuing.';
    }
    else if (state.page >= 3 && state.page <= 10) {
      var pid = state.passageOrder[state.page - 3];
      var r = state.passages[pid];
      if (!r || !r.origin || !r.confidence || !r.naturalness || !r.clarity ||
          !r.engagement || !r.authority || !r.quality)
        return 'Please answer all required questions (Q1\u2013Q7) before continuing.';
    }
    return null;
  }

  function showError(msg) {
    var el = document.getElementById('vmsg');
    if (el) { el.textContent = msg; el.style.display = 'block'; }
  }

  // ===== PUBLIC API =====

  window.SV = {
    next: function() {
      collect();
      var err = validate();
      if (err) { showError(err); return; }
      state.page++;
      render();
    },
    prev: function() {
      collect();
      if (state.page > 0) { state.page--; render(); }
    },
    submit: function() {
      collect();

      var payload = {
        sessionId: state.sessionId,
        startedAt: state.startTime,
        completedAt: new Date().toISOString(),
        passageOrder: state.passageOrder,
        demographics: state.demographics,
        passages: state.passages,
        debrief: state.debrief
      };

      var btn = document.querySelector('.btn-submit');
      if (btn) { btn.disabled = true; btn.textContent = 'Submitting\u2026'; }

      fetch('/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).then(function(resp) {
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        return resp.json();
      }).then(function() {
        state.submitted = true;
        state.page = 12;
        localStorage.removeItem('survey_progress');
        render();
      }).catch(function(err) {
        if (btn) { btn.disabled = false; btn.textContent = 'Submit Survey'; }
        showError('Failed to submit. Please check your connection and try again.');
      });
    }
  };

  // ===== INIT =====
  render();

})();
</script>
</body>
</html>"""


if __name__ == '__main__':
    main()
