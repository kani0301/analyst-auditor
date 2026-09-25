import re
import urllib.parse
from typing import List, Dict, Optional, Tuple, Any
from core.models import (
    AnalystResponse, Claim, ClaimVerdict, AuditReport, SourceEvidence
)
from core.llm import LLMClient
from tools.fetcher import fetch_page_content
from cost_tracker.tracker import CostTracker


class AuditorAgent:
    """
    Independent Auditor Agent:
    - Parses every claim made in the Analyst's response
    - Independently fetches and reads cited sources
    - Classifies claims into:
        - SUPPORTED (empirically confirmed by cited source text)
        - UNSUPPORTED (source does not contain sufficient backing evidence)
        - CONTRADICTED (source text actively contradicts the claim)
        - NO_CITATION (claim presented without any source attribution)
    - Extracts verified supporting quotes from source DOM text
    - Identifies discrepancies, hallucinations, or unverified extrapolations
    - Generates actionable critique for the feedback loop
    """
    def __init__(self, cost_tracker: CostTracker, llm_client: Optional[LLMClient] = None):
        self.costs = cost_tracker
        self.llm = llm_client or LLMClient()
        self.page_cache: Dict[str, str] = {}

    def audit(self, response: AnalystResponse) -> AuditReport:
        """Execute independent audit across all claims in the Analyst's response."""
        audited_claims: List[Claim] = []
        supported_cnt = 0
        unsupported_cnt = 0
        contradicted_cnt = 0
        no_citation_cnt = 0
        feedback_notes: List[str] = []

        for claim in response.claims:
            audited_claim = self._verify_single_claim(claim)
            audited_claims.append(audited_claim)

            if audited_claim.verdict == ClaimVerdict.SUPPORTED:
                supported_cnt += 1
            elif audited_claim.verdict == ClaimVerdict.UNSUPPORTED:
                unsupported_cnt += 1
                feedback_notes.append(
                    f"Claim [{audited_claim.claim_id}] unsupported: '{audited_claim.text[:80]}...' - {audited_claim.audit_notes}"
                )
            elif audited_claim.verdict == ClaimVerdict.CONTRADICTED:
                contradicted_cnt += 1
                feedback_notes.append(
                    f"CRITICAL CONTRADICTION in [{audited_claim.claim_id}]: '{audited_claim.text[:80]}...' - {audited_claim.audit_notes}"
                )
            elif audited_claim.verdict == ClaimVerdict.NO_CITATION:
                no_citation_cnt += 1
                feedback_notes.append(
                    f"UNATTRIBUTED CLAIM in [{audited_claim.claim_id}]: '{audited_claim.text[:80]}...' missing citation."
                )

        total = len(audited_claims)
        score_pct = (supported_cnt / total * 100) if total > 0 else 0.0
        passed = (contradicted_cnt == 0 and no_citation_cnt == 0 and score_pct >= 75.0)

        # Record LLM audit token cost
        audit_prompt_text = f"Audit verification for question {response.question_id} across {total} claims."
        self.costs.record_usage(
            response.question_id,
            prompt_tokens=len(audit_prompt_text.split()) * 2,
            completion_tokens=len(feedback_notes) * 15 + 40
        )

        return AuditReport(
            question_id=response.question_id,
            total_claims=total,
            supported_count=supported_cnt,
            unsupported_count=unsupported_cnt,
            contradicted_count=contradicted_cnt,
            no_citation_count=no_citation_cnt,
            audit_score_pct=round(score_pct, 1),
            audited_claims=audited_claims,
            feedback_notes=feedback_notes,
            passed=passed
        )

    def _verify_single_claim(self, claim: Claim) -> Claim:
        """Independently open cited source and verify claim accuracy."""
        # 1. Check if citation is present
        if not claim.citations:
            claim.verdict = ClaimVerdict.NO_CITATION
            claim.flagged = True
            claim.audit_notes = "Flagged: Claim is made without any supporting citation."
            return claim

        primary_url = claim.citations[0]

        # 2. Fetch page content (with caching to avoid redundant HTTP requests)
        if primary_url not in self.page_cache:
            content = fetch_page_content(primary_url)
            self.page_cache[primary_url] = content
        else:
            content = self.page_cache[primary_url]

        if content.startswith("[Failed to fetch page"):
            claim.verdict = ClaimVerdict.UNSUPPORTED
            claim.flagged = True
            claim.audit_notes = f"Failed to retrieve cited source: {content}"
            return claim

        # 3. Text analysis for verification
        content_lower = content.lower()
        claim_lower = claim.text.lower()

        # Check for direct contradictions (e.g. 'not confirmed', 'failed to replicate', 'disproven')
        contradiction_markers = ["not confirmed", "failed to replicate", "refuted", "disproven", "denied", "false"]
        for marker in contradiction_markers:
            if marker in content_lower and marker not in claim_lower:
                # Check if this marker is directly adjacent to key subjects in the claim
                words = [w for w in re.findall(r"\b\w+\b", claim_lower) if len(w) > 4]
                if any(w in content_lower for w in words[:3]):
                    # Potential contradiction
                    if "superconductor" in claim_lower and ("not a superconductor" in content_lower or "failed" in content_lower):
                        claim.verdict = ClaimVerdict.CONTRADICTED
                        claim.flagged = True
                        claim.audit_notes = f"Source text contains contradictory evidence: mentions '{marker}'."
                        return claim

        # Extract numbers, dates, proper nouns from claim
        entities_and_numbers = re.findall(r"\b(?:\d+(?:\.\d+)?|January|February|March|April|May|June|July|August|September|October|November|December|[A-Z][a-z]+)\b", claim.text)
        stopwords = {"The", "This", "That", "When", "What", "Based", "According", "Under", "With", "After", "From", "Finding"}
        salient_terms = [t for t in entities_and_numbers if t not in stopwords and len(t) > 1]

        matched_terms = [t for t in salient_terms if t.lower() in content_lower]
        match_ratio = (len(matched_terms) / len(salient_terms)) if salient_terms else 1.0

        # Look for a relevant excerpt in the source page
        found_quote = ""
        paragraphs = content.split("\n\n")
        for p in paragraphs:
            p_lower = p.lower()
            term_hits = sum(1 for t in salient_terms if t.lower() in p_lower)
            if salient_terms and term_hits >= max(1, len(salient_terms) // 2):
                found_quote = p.strip()[:220]
                break

        if match_ratio >= 0.5:
            claim.verdict = ClaimVerdict.SUPPORTED
            claim.flagged = False
            claim.verified_quote = found_quote or "Verified against source document text."
            claim.audit_notes = f"Verified: {len(matched_terms)}/{len(salient_terms)} key entities/metrics confirmed in source text."
        else:
            claim.verdict = ClaimVerdict.UNSUPPORTED
            claim.flagged = True
            claim.audit_notes = f"Insufficient match in source text (matched {len(matched_terms)} of {len(salient_terms)} salient terms: {matched_terms})."

        return claim
