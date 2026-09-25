from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class ClaimVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    NO_CITATION = "NO_CITATION"


class SourceEvidence(BaseModel):
    url: str
    title: str
    snippet: str = ""
    full_text: str = ""
    domain: str = ""
    retrieved_at: str = ""


class ResearchPlan(BaseModel):
    question_id: str
    question: str
    entities: List[str] = Field(default_factory=list)
    reused_entities_from_memory: List[str] = Field(default_factory=list)
    sub_queries: List[str] = Field(default_factory=list)
    strategy_notes: str = ""


class DisagreementItem(BaseModel):
    topic: str
    divergent_claims: List[Dict[str, str]] = Field(default_factory=list)
    resolved_verdict: str
    justification: str


class Claim(BaseModel):
    claim_id: str
    text: str
    citations: List[str] = Field(default_factory=list)
    verdict: Optional[ClaimVerdict] = None
    audit_notes: str = ""
    verified_quote: str = ""
    flagged: bool = False


class AnalystResponse(BaseModel):
    question_id: str
    question: str
    answer_text: str
    claims: List[Claim] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    disagreements: List[DisagreementItem] = Field(default_factory=list)
    unverifiable_points: List[str] = Field(default_factory=list)
    memory_applied: bool = False
    revision_iteration: int = 0


class AuditReport(BaseModel):
    question_id: str
    total_claims: int = 0
    supported_count: int = 0
    unsupported_count: int = 0
    contradicted_count: int = 0
    no_citation_count: int = 0
    audit_score_pct: float = 0.0
    audited_claims: List[Claim] = Field(default_factory=list)
    feedback_notes: List[str] = Field(default_factory=list)
    passed: bool = True


class CostRecord(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    cost_inr: float = 0.0
    call_count: int = 0


class QuestionTrace(BaseModel):
    question_id: str
    question: str
    difficulty: str
    category: str
    plan: ResearchPlan
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    memory_hits: List[str] = Field(default_factory=list)
    analyst_initial_response: AnalystResponse
    analyst_revised_response: Optional[AnalystResponse] = None
    audit_initial_report: AuditReport
    audit_final_report: Optional[AuditReport] = None
    feedback_applied: bool = False
    cost: CostRecord
    duration_seconds: float = 0.0
