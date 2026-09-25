import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()

# Models and Pricing
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gemini-2.5-flash")

# Currency Conversion (1 USD to INR)
USD_TO_INR_RATE = float(os.getenv("USD_TO_INR_RATE", "86.50"))

# Search and Execution Configuration
SEARCH_ENGINE = os.getenv("SEARCH_ENGINE", "duckduckgo")
MAX_SEARCH_RESULTS_PER_QUERY = 5
MAX_PARALLEL_FETCHES = 6
REQUEST_TIMEOUT_SECONDS = 12
MAX_AUDIT_FEEDBACK_LOOPS = 1  # Stretch goal: Auditor -> Analyst feedback iterations

# Paths
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"
MEMORY_DIR = ROOT_DIR / "memory_store"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
