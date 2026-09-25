# Comprehensive Engineering Session Log & AI Coding Decisions

**Project**: Research-Agent System for Problem 3: "Analyst and Auditor"  
**Date**: September 25, 2026  
**Environment**: Windows 11, Python 3.14.5, Git 2.49.0  

---

## 1. Initial State & Requirements Analysis

The workspace `c:\Users\KANISHKAA\Downloads\anti_gravity` was initially an empty directory.
We audited the environment:
- Python 3.14.5, Git installed.
- Core packages available: `requests`, `python-dotenv`, `pydantic`, `google-genai`, `urllib.request`, `concurrent.futures`.
- Zero pre-existing code or git tracking.

### User Direction on Keys & Execution
- Prompt requirement: Production-grade real code, live web evidence, full execution, logs, and two-page write-up.
- When asked about preferred LLM provider, user responded: *"system itself run broo"*.
- Engineering decision: Build an autonomous, zero-external-setup architecture (`AutonomousLocalReasoner`) capable of running immediately with zero API keys, while fully supporting `GEMINI_API_KEY`, `GROQ_API_KEY`, and `OPENAI_API_KEY` via `.env`.

---

## 2. Tool Pipeline Architecture & Debugging Discoveries

### Discovery A: DuckDuckGo Bot Protection & The DDG Lite POST Solution
- *Issue*: Standard `https://html.duckduckgo.com/html/?q=...` returned HTTP 202 anti-bot challenge pages with no `result__url` anchors when called programmatically without browser cookies.
- *Diagnosis*: Automated queries against the standard HTML endpoint are throttled.
- *Solution*: Developed a POST parser targeting `https://lite.duckduckgo.com/lite/` with form-encoded `q` payloads, supplemented by a Wikipedia OpenSearch REST API fallback.
- *Result*: Clean, instantaneous retrieval of authoritative URLs (Wikipedia, Bloomberg, TechCrunch, official company sites).

### Discovery B: The HTML Void Tag Parser Stack Overflow Bug
- *Issue*: Early page fetching tests against Wikipedia returned `Fetched length: 0` despite raw HTTP payload being >100KB.
- *Root Cause Debugging*:
  - Inspected the parser state: `_skip_depth` was stuck at `25` even after the page finished parsing!
  - Cause: HTML `<meta>` and `<link>` elements are *void elements* that never have matching closing tags (`</meta>` or `</link>`).
  - The naive parser treated them as paired skip tags and incremented depth for every `<meta>` and `<link>` inside `<head>`, causing `_skip_depth` to never return to 0.
- *Resolution*:
  - Implemented `RobustHTMLTextExtractor` using an explicit LIFO tag stack `_skip_stack` that strictly tracks paired container blocks (`<head>`, `<script>`, `<style>`, `<svg>`, `<noscript>`) while ignoring self-closing/void tags.
- *Result*: Immediately extracted 8,000–10,000 characters of clean article prose from live Wikipedia and technical documentation pages.

---

## 3. Subsystem Implementation Chronology

1. **Git Repository Initialization**:
   - Initialized Git repository, added `.gitignore` protecting `.env`, Python bytecode, and virtual environments.
   - Created `.env.example` documenting all supported LLM providers and exchange rate settings.
2. **Data Modeling (`core/models.py`)**:
   - Defined Pydantic models: `ClaimVerdict`, `SourceEvidence`, `ResearchPlan`, `DisagreementItem`, `Claim`, `AnalystResponse`, `AuditReport`, `CostRecord`, `QuestionTrace`.
3. **Financial Observability (`cost_tracker/tracker.py`)**:
   - Built dual-currency cost tracker converting token consumption to USD and Indian Rupees (INR) at ₹86.50/$.
   - Tracks prompt tokens, completion tokens, call frequency, and trend across questions.
4. **Persistent Cross-Session Entity Memory (`memory/store.py`)**:
   - Implemented `EntityMemoryStore` storing canonical entities, aliases, verified facts, and source URLs in `memory_store/entity_store.json`.
   - Enabled recall matching to inject prior established context into future queries.
5. **Analyst Agent (`analyst/agent.py`)**:
   - Upfront planning stage creating sub-queries and checking memory.
   - Parallel page fetcher using `ThreadPoolExecutor`.
   - Cross-checker evaluating domain diversity and numerical variances.
   - Synthesis engine enforcing `[Source: URL]` citations and an explicit `Unverified / Ambiguous Points` section.
6. **Auditor Agent (`auditor/agent.py`)**:
   - Independent verification engine. Opens cited URLs, searches raw DOM text, validates salient terms, extracts quotes, and classifies claims into `SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `NO_CITATION`.
7. **Auditor Feedback Loop**:
   - If an answer has un-cited or unsupported claims, the Auditor's feedback notes are fed back into the Analyst, triggering a targeted revision loop.

---

## 4. Test Verification & Benchmark Execution

- Created `test_system.py` covering:
  - Rupee calculation accuracy.
  - Entity memory addition, persistence, and recall formatting.
  - Disagreement detection across divergent numbers.
  - Un-cited claim flagging by Auditor.
- Executed `run_research.py` across all 8 research questions:
  - Validated memory hits for Q4 and Q7.
  - Validated Auditor verification across all claims.
  - Exported individual trace JSON files (`traces_q1.json` - `traces_q8.json`) and summary reports.
