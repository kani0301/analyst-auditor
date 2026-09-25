# Analyst and Auditor: Autonomous Web Research & Verification Agents

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Verification: Complete](https://img.shields.io/badge/Verification-Live_Web-brightgreen.svg)]()

A complete, production-grade research-agent system solving **Problem 3: Analyst and Auditor**. Built from first principles to plan, investigate, cross-verify live web evidence, retain entity memory across questions, and audit claims independently.

---

## Key Capabilities

- **Analyst Agent**:
  - **Upfront Planning**: Formulates research plans and decomposed sub-queries before executing tools.
  - **Live Web Pipeline**: Conducts real web searches (DuckDuckGo Lite / Wikipedia) and parallel multi-threaded page fetching (`ThreadPoolExecutor`).
  - **Multi-Source Cross-Checking**: Detects single-source claims and numerical/temporal disagreements across sources.
  - **Cross-Question Entity Memory**: Carries verified knowledge across questions via a persistent `EntityMemoryStore`. Later queries about known entities bypass redundant searches and ground answers faster.
  - **Rigorous Citations & Uncertainty**: Attaches inline `[Source: URL]` citations to every finding; explicitly declares unverified or proprietary aspects in a dedicated `Unverified / Ambiguous Points` section rather than hallucinating.
- **Auditor Agent**:
  - **Independent Verification**: Re-opens cited URLs directly, reads raw page text, and verifies whether the source text supports each claim.
  - **Strict Verdicts**: Classifies every claim into `SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, or `NO_CITATION`.
  - **Quote Extraction**: Pulls verbatim supporting quotes from source DOM text.
  - **Feedback Loop**: When an audit fails, issues structured critique back to the Analyst for automated re-search and revision.
- **Cost & Currency Observability**:
  - Tracks prompt and completion tokens.
  - Reports per-question and aggregate costs in both **USD** and **Indian Rupees (INR)** at configurable exchange rates (`USD_TO_INR_RATE=86.50`).

---

## 5-Minute Quickstart (Clean Machine)

### 1. Prerequisites
- Python 3.10 or higher (`python --version`)
- Git (`git --version`)

### 2. Clone and Setup
```bash
# Clone the repository
git clone <repo-url>
cd anti_gravity

# Create and activate virtual environment (optional but recommended)
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies (under 30 seconds)
pip install -r requirements.txt
```

### 3. Environment Configuration
The system works **completely out-of-the-box with zero keys** using the built-in autonomous engine.
To use Google Gemini (100% free via [Google AI Studio](https://aistudio.google.com/apikey)):

```bash
# Copy example environment file
cp .env.example .env
```
Edit `.env`:
```env
GEMINI_API_KEY=your_free_gemini_key_here
USD_TO_INR_RATE=86.50
```

### 4. Run the Unit Test Suite (5 seconds)
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
This executes the Analyst and Auditor across all 8 research questions, prints real-time logs, exercises the Entity Memory Store, runs the Auditor verification loop, and outputs the final cost and audit tables.

---

## Repository Structure

```text
anti_gravity/
├── README.md               # Quickstart guide & documentation
├── DECISIONS.md            # Two-page architecture and engineering write-up
├── requirements.txt        # Production dependencies
├── .env.example            # Environment variables template
├── run_research.py         # 8-question benchmark runner & orchestrator
├── test_system.py          # Fast unit & integration test suite
├── data/
│   └── questions.json      # 8 research questions of increasing difficulty
├── core/
│   ├── config.py           # Configuration, timeouts, exchange rates, directory paths
│   ├── models.py           # Pydantic schemas (Claim, AuditReport, Plan, CostRecord)
│   └── llm.py              # Unified LLM provider (Gemini, Groq, OpenAI, Local Reasoner)
├── tools/
│   ├── search.py           # Live DuckDuckGo Lite & Wikipedia search engine
│   ├── fetcher.py          # Parallel page fetcher & stack-based HTML text extractor
│   └── cross_checker.py    # Multi-source corroboration & disagreement detector
├── memory/
│   └── store.py            # Persistent cross-question EntityMemoryStore
├── cost_tracker/
│   └── tracker.py          # Token tracker & USD/INR financial converter
├── logs/                   # Full execution logs & traces
│   ├── traces_q1.json      # Per-question full execution trace
│   ├── ...
│   ├── traces_q8.json
│   ├── run_summary.json    # Machine-readable aggregate metrics
│   └── run_summary.md      # Human-readable benchmark report
└── memory_store/
    └── entity_store.json   # Persisted cross-session entity facts
```

---

## The 8 Research Questions

| ID | Difficulty | Topic | Focus Area |
|---|---|---|---|
| **Q1** | Low | Mistral AI Founding & Seed Round | Establishes Mistral AI in Entity Memory Store |
| **Q2** | Low-Med | Google Gemma 2 Specifications | Multi-model architecture & sliding window attention |
| **Q3** | Medium | GPT-4 Energy & Water Consumption | Divergent estimates & numerical disagreement resolution |
| **Q4** | Medium | Mistral AI Commercial Evolution | **Exercises Entity Memory from Q1** |
| **Q5** | Med-High | DeepSeek-V3 / R1 Architecture & Cost | Dense technical parameters & compute cost estimation |
| **Q6** | High | EU AI Act GPAI Systemic Risk | Statutory enforcement tiers (10^25 FLOPs, EUR 35M fines) |
| **Q7** | High | DeepSeek vs. Mistral AI Comparison | **Exercises Dual Memory from Q1, Q4, and Q5** |
| **Q8** | Very High | LK-99 Superconductivity Dispute | Controversial synthesis & scientific refutation consensus |

---

## Verification & Audit Philosophy

The Auditor Agent does not trust text summaries blindly. It:
1. Re-fetches each cited source URL independently.
2. Performs keyword, numerical, and entity alignment against raw source DOM text.
3. Detects contradictions (e.g. claims claiming confirmation when papers report non-replication).
4. Strictly flags un-cited claims as `NO_CITATION`.
5. Feeds critiques back to the Analyst when audit standards are not met.
