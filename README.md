# Analyst and Auditor: Autonomous Web Research & Verification Agents

A working research-agent system solving **Problem 3: Analyst and Auditor**. Built to plan research, investigate using live web evidence, cross-verify sources, retain entity memory across questions, and audit claims independently.

---

## Key Capabilities

* **Analyst Agent**:

  * **Upfront Planning**: Formulates research plans and decomposed sub-queries before executing tools.
  * **Live Web Pipeline**: Conducts real web searches (DuckDuckGo Lite / Wikipedia) and parallel multi-threaded page fetching (`ThreadPoolExecutor`).
  * **Multi-Source Cross-Checking**: Detects single-source claims and numerical/temporal disagreements across sources.
  * **Cross-Question Entity Memory**: Carries verified knowledge across questions via a persistent `EntityMemoryStore`. Later queries about known entities bypass redundant searches and ground answers faster.
  * **Rigorous Citations & Uncertainty**: Attaches inline `[Source: URL]` citations to findings; explicitly declares unverified or proprietary aspects in a dedicated `Unverified / Ambiguous Points` section rather than hallucinating.

* **Auditor Agent**:

  * **Independent Verification**: Re-opens cited URLs directly, reads raw page text, and verifies whether the source text supports each claim.
  * **Strict Verdicts**: Classifies every claim into `SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, or `NO_CITATION`.
  * **Quote Extraction**: Pulls verbatim supporting quotes from source DOM text.
  * **Feedback Loop**: When an audit fails, issues structured critique back to the Analyst for automated re-search and revision.

* **Cost & Currency Observability**:

  * Tracks prompt and completion tokens.
  * Reports per-question and aggregate costs in both **USD** and **Indian Rupees (INR)** at configurable exchange rates (`USD_TO_INR_RATE=86.50`).

---

## 5-Minute Quickstart (Clean Machine)

### 1. Prerequisites

* Python 3.10 or higher (`python --version`)
* Git (`git --version`)

### 2. Clone and Setup

```bash
# Clone the repository
git clone <repo-url>

cd analyst_auditor

# Create and activate virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

The system includes a built-in autonomous engine intended to run without an external API key.

An external Gemini provider is optional.

```bash
# Copy example environment file
cp .env.example .env
```

Edit `.env` if using an external provider:

```env
GEMINI_API_KEY=your_gemini_key_here
USD_TO_INR_RATE=86.50
```

### 4. Run the Unit Test Suite

```bash
python test_system.py
```

Expected output:

```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.008s

OK
```

### 5. Run the Full 8-Question Benchmark

```bash
python run_research.py
```

The benchmark runs all 8 questions through the Analyst → live search/fetch → synthesis → Auditor pipeline.

A representative run produces output in this format:

```text
================================================================================
  ANALYST & AUDITOR RESEARCH AGENT SYSTEM: 8-QUESTION BENCHMARK RUN
================================================================================

Loaded 8 research questions with increasing difficulty.
Using USD/INR conversion rate: Rs 86.50 per USD.

--------------------------------------------------------------------------------
[Q1] (Low) Baseline Entity Fact Retrieval
Question: When was Mistral AI founded, who are its three co-founders, and what was
the valuation and amount raised in their initial seed round?

  [1/5] Analyst generating research plan...
        Entities identified: ['Mistral AI']
        [MEMORY HIT] Recalled from memory store: ['Mistral AI']
        Sub-queries generated: 3

  [2/5] Executing live web search and parallel page fetching...
        Retrieved 9 sources across 4 tool calls.

  [3/5] Analyst synthesizing findings and formulating citations...
        Formulated 15 testable claims with 5 citations.

  [4/5] Auditor independently fetching and verifying claims against cited pages...
        Audit Score: 86.7% | Supported: 13 | Unsupported: 2 |
        Contradicted: 0 | No Citation: 0

  [5/5] Audit completed without requiring revision loop.
  Done in 46.12s | Tokens: 1676 | Cost: Rs 0.0140 ($0.000162)

--------------------------------------------------------------------------------
[Q3] (Medium) Divergent Estimates & Source Disagreement

  [3/5] Analyst synthesizing findings and formulating citations...
        Formulated 16 testable claims with 5 citations.
        Detected 1 numerical source discrepancies.

  [4/5] Auditor independently fetching and verifying claims against cited pages...
        Audit Score: 75.0% | Supported: 12 | Unsupported: 3 |
        Contradicted: 0 | No Citation: 1

  [5/5] [FEEDBACK LOOP] Auditor flagged 4 issues.
        Triggering Analyst revision...

        Revised Audit Score: 77.8% | Supported: 14 | Unsupported: 3

--------------------------------------------------------------------------------
[Q4] (Medium) Entity Memory Recall & Commercial Evolution

--> Entity Memory Reuse Target: Reuses entity established in Q1

  [1/5] Analyst generating research plan...
        Entities identified: ['Mistral AI', 'Apache 2.0', 'Microsoft Azure']
        [MEMORY HIT] Recalled from memory store: ['Mistral AI', ...]
        Sub-queries generated: 3

--------------------------------------------------------------------------------
[Q7] (High) Dual-Entity Comparative Synthesis & Memory Reuse

--> Entity Memory Reuse Target: Reuses entity established in Q1, Q4, Q5

  [1/5] Analyst generating research plan...
        Entities identified: ['Compare DeepSeek', 'DeepSeek-V3',
        'Mistral AI', 'Mixtral 8x7B']
        [MEMORY HIT] Recalled from memory store: ['Mistral AI', ...]
        Sub-queries generated: 3

================================================================================
  EXECUTION SUMMARY & METRICS ACROSS 8 QUESTIONS
================================================================================

ID   | Difficulty  | Claims | Audited % | Memory | Tokens | Cost (INR) | Duration
--------------------------------------------------------------------------------
Q1   | Low         | 15     | 86.7%     | YES    | 1676   | Rs 0.0140  | 46.12s
Q2   | Low-Medium  | 15     | 100.0%    | YES    | 2421   | Rs 0.0184  | 15.09s
Q3   | Medium      | 18     | 77.8%     | YES    | 5251   | Rs 0.0404  | 21.16s
Q4   | Medium      | 13     | 92.3%     | YES    | 3693   | Rs 0.0287  | 15.01s
Q5   | Medium-High | 18     | 100.0%    | YES    | 2413   | Rs 0.0191  | 16.90s
Q6   | High        | 12     | 100.0%    | YES    | 2284   | Rs 0.0185  | 18.33s
Q7   | High        | 40     | 97.5%     | YES    | 6994   | Rs 0.0504  | 21.73s
Q8   | Very High   | 15     | 100.0%    | YES    | 2587   | Rs 0.0193  | 15.52s
--------------------------------------------------------------------------------
Total Session Tokens : 27319
Total Session Cost   : Rs 0.2089 ($0.002415)
Total Wall Duration  : 169.93s

All logs and traces saved to:
./logs/
```

The complete per-question traces and aggregate results are stored under `/logs`, including `run_summary.md`, `run_summary.json`, and `traces_q1.json` through `traces_q8.json`.

---

## Repository Structure

```text
analyst_auditor/

├── README.md                 # Quickstart guide & documentation
├── DECISIONS.md              # Architecture and engineering write-up
├── requirements.txt          # Project dependencies
├── .env.example              # Environment variables template
├── run_research.py           # 8-question benchmark runner & orchestrator
├── test_system.py            # Fast unit & integration test suite

├── data/
│   └── questions.json         # 8 research questions of increasing difficulty

├── core/
│   ├── config.py              # Configuration, timeouts, exchange rates, directory paths
│   ├── models.py              # Pydantic schemas (Claim, AuditReport, Plan, CostRecord)
│   └── llm.py                 # Unified LLM provider (Gemini, Groq, OpenAI, Local Reasoner)

├── tools/
│   ├── search.py              # Live DuckDuckGo Lite & Wikipedia search engine
│   ├── fetcher.py             # Parallel page fetcher & stack-based HTML text extractor
│   └── cross_checker.py       # Multi-source corroboration & disagreement detector

├── memory/
│   └── store.py               # Persistent cross-question EntityMemoryStore

├── cost_tracker/
│   └── tracker.py              # Token tracker & USD/INR financial converter

├── logs/
│   ├── session_transcript.md  # AI coding-session transcript
│   ├── traces_q1.json         # Per-question full execution trace
│   ├── ...
│   ├── traces_q8.json
│   ├── run_summary.json       # Machine-readable aggregate metrics
│   └── run_summary.md         # Human-readable benchmark report

└── memory_store/
    └── entity_store.json      # Persisted cross-session entity facts
```

---

## The 8 Research Questions

| ID     | Difficulty | Topic                                | Focus Area                                                |
| ------ | ---------- | ------------------------------------ | --------------------------------------------------------- |
| **Q1** | Low        | Mistral AI Founding & Seed Round     | Establishes Mistral AI in Entity Memory Store             |
| **Q2** | Low-Med    | Google Gemma 2 Specifications        | Multi-model architecture & sliding window attention       |
| **Q3** | Medium     | GPT-4 Energy & Water Consumption     | Divergent estimates & numerical disagreement resolution   |
| **Q4** | Medium     | Mistral AI Commercial Evolution      | **Exercises Entity Memory from Q1**                       |
| **Q5** | Med-High   | DeepSeek-V3 / R1 Architecture & Cost | Dense technical parameters & compute cost estimation      |
| **Q6** | High       | EU AI Act GPAI Systemic Risk         | Statutory enforcement tiers (10^25 FLOPs, EUR 35M fines)  |
| **Q7** | High       | DeepSeek vs. Mistral AI Comparison   | **Exercises Dual Memory from Q1, Q4, and Q5**             |
| **Q8** | Very High  | LK-99 Superconductivity Dispute      | Controversial synthesis & scientific refutation consensus |

---

## Verification & Audit Philosophy

The Auditor Agent does not trust text summaries blindly. It:

1. Re-fetches each cited source URL independently.
2. Performs keyword, numerical, and entity alignment against raw source DOM text.
3. Detects contradictions (e.g. claims claiming confirmation when papers report non-replication).
4. Strictly flags uncited claims as `NO_CITATION`.
5. Feeds critiques back to the Analyst when audit standards are not met.

---

## Benchmark Results

The recorded benchmark completed all eight questions with live retrieval, claim-level auditing, persistent memory reuse, and cost tracking.

The recorded run produced:

* **Total claims audited:** 146
* **Total session tokens:** 27,319
* **Total session cost:** Rs 0.2089 ($0.002415)
* **Total wall duration:** 169.93 seconds
* **Memory reuse:** Demonstrated across multiple questions, including Q4 and Q7
* **Auditor feedback loop:** Triggered during questions where unsupported or uncited claims were detected

Detailed results are available in:

* `/logs/run_summary.md`
* `/logs/run_summary.json`
* `/logs/traces_q1.json` through `/logs/traces_q8.json`

---

## Engineering Decisions

The main architecture and engineering decisions are documented in `DECISIONS.md`.

The write-up covers:

* Search pipeline selection and rejected alternatives
* HTML extraction approach and the observed parser failure
* Independent Auditor design
* Persistent entity-memory architecture
* Cost and currency observability
* Testing strategy
* Known failure modes and Auditor limitations
* Planned improvements with additional development time

---

## Known Limitations

* Live web retrieval depends on the availability and accessibility of external websites.
* Some sources may block automated requests, change their content, or expose incomplete page text.
* The Auditor verifies claims against the text it can retrieve; successful fetching does not guarantee that a source is authoritative or that every nuance of a claim is captured.
* Some claims may remain `UNSUPPORTED`, `CONTRADICTED`, or `NO_CITATION`; these results are retained rather than hidden.
* JavaScript-rendered pages and sites protected by bot-mitigation mechanisms may not be fully retrievable using the standard HTTP fetcher.
* External LLM providers are optional and may be subject to provider-side access, quota, or availability restrictions.
* The local autonomous engine provides a key-free execution path, but its reasoning quality can differ from externally hosted models.

---

## Reproducibility

The repository is intended to run from a clean checkout using the setup steps described above.

The repository includes:

* Source code for the Analyst and Auditor agents
* Live search and page-fetching components
* Persistent entity memory
* Cost tracking
* 8-question benchmark runner
* Per-question execution traces
* Full AI coding-session transcript
* Benchmark summary
* Architecture and engineering decisions
* `.env.example` configuration template

The recorded benchmark outputs are retained in `/logs` so that the implementation and reported results can be inspected together.

---

## License

This project is provided for evaluation and educational purposes as part of the Analyst and Auditor take-home assignment.
