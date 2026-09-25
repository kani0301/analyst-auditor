from typing import Dict, List, Any
from core.config import USD_TO_INR_RATE
from core.models import CostRecord


class CostTracker:
    """
    Tracks token utilization and real monetary cost in USD and Indian Rupees (INR).
    Supports Gemini Flash, GPT-4o-mini, and local token estimation.
    """
    # Pricing per 1,000,000 tokens (USD)
    # Gemini 2.5 Flash / 1.5 Flash standard benchmark:
    # Prompt: $0.075 / 1M ($0.000075 / 1K), Completion: $0.30 / 1M ($0.00030 / 1K)
    PRICE_PER_1M_PROMPT = 0.075
    PRICE_PER_1M_COMPLETION = 0.30

    def __init__(self, inr_rate: float = USD_TO_INR_RATE):
        self.inr_rate = inr_rate
        self.per_question_costs: Dict[str, CostRecord] = {}
        self.session_prompt_tokens = 0
        self.session_completion_tokens = 0
        self.session_total_tokens = 0
        self.session_cost_usd = 0.0
        self.session_cost_inr = 0.0

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> tuple[float, float]:
        cost_usd = (prompt_tokens / 1_000_000 * self.PRICE_PER_1M_PROMPT) + \
                   (completion_tokens / 1_000_000 * self.PRICE_PER_1M_COMPLETION)
        cost_inr = cost_usd * self.inr_rate
        return cost_usd, cost_inr

    def record_usage(self, question_id: str, prompt_tokens: int, completion_tokens: int):
        total_tokens = prompt_tokens + completion_tokens
        cost_usd, cost_inr = self.calculate_cost(prompt_tokens, completion_tokens)

        if question_id not in self.per_question_costs:
            self.per_question_costs[question_id] = CostRecord()

        rec = self.per_question_costs[question_id]
        rec.prompt_tokens += prompt_tokens
        rec.completion_tokens += completion_tokens
        rec.total_tokens += total_tokens
        rec.cost_usd += cost_usd
        rec.cost_inr += cost_inr
        rec.call_count += 1

        self.session_prompt_tokens += prompt_tokens
        self.session_completion_tokens += completion_tokens
        self.session_total_tokens += total_tokens
        self.session_cost_usd += cost_usd
        self.session_cost_inr += cost_inr

    def get_question_cost(self, question_id: str) -> CostRecord:
        return self.per_question_costs.get(question_id, CostRecord())

    def get_summary(self) -> Dict[str, Any]:
        trend = []
        for q_id, rec in self.per_question_costs.items():
            trend.append({
                "question_id": q_id,
                "total_tokens": rec.total_tokens,
                "cost_usd": round(rec.cost_usd, 6),
                "cost_inr": round(rec.cost_inr, 4),
                "calls": rec.call_count
            })

        return {
            "session_total_tokens": self.session_total_tokens,
            "session_prompt_tokens": self.session_prompt_tokens,
            "session_completion_tokens": self.session_completion_tokens,
            "session_cost_usd": round(self.session_cost_usd, 6),
            "session_cost_inr": round(self.session_cost_inr, 4),
            "usd_to_inr_rate": self.inr_rate,
            "question_trend": trend
        }
