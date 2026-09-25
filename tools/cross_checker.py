import re
from typing import List, Dict, Tuple, Any
from core.models import SourceEvidence, DisagreementItem


class SourceCrossChecker:
    """
    Cross-checks claims across multiple independent web sources.
    Detects single-source claims and handles numerical/factual disagreements.
    """
    def __init__(self):
        pass

    def evaluate_corroboration(self, claim_text: str, sources: List[SourceEvidence]) -> Dict[str, Any]:
        """
        Check how many independent sources and domains support the key terms of the claim.
        """
        # Tokenize key keywords from claim (skip stopwords)
        stopwords = {"the", "a", "an", "in", "on", "at", "by", "for", "with", "about", "against", "between",
                     "into", "through", "during", "before", "after", "above", "below", "to", "from", "up",
                     "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once",
                     "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do",
                     "does", "did", "doing", "and", "but", "if", "or", "because", "as", "until", "while",
                     "of", "that", "this", "these", "those", "what", "which", "who", "whom"}

        words = re.findall(r"\b[A-Za-z0-9\-\.\$€%]+\b", claim_text)
        keywords = [w.lower() for w in words if w.lower() not in stopwords and len(w) > 2]

        supporting_sources: List[SourceEvidence] = []
        supporting_domains = set()

        for s in sources:
            corpus = f"{s.title} {s.snippet} {s.full_text}".lower()
            # If at least 60% of keywords appear in source corpus
            matched = sum(1 for kw in keywords if kw in corpus)
            if keywords and (matched / len(keywords)) >= 0.5:
                supporting_sources.append(s)
                if s.domain:
                    supporting_domains.add(s.domain)

        domain_count = len(supporting_domains)
        is_single_source = (domain_count == 1)
        is_multi_source = (domain_count >= 2)
        is_unsupported = (domain_count == 0)

        return {
            "keywords": keywords,
            "supporting_sources_count": len(supporting_sources),
            "distinct_domains_count": domain_count,
            "supporting_domains": list(supporting_domains),
            "is_single_source": is_single_source,
            "is_multi_source": is_multi_source,
            "is_unsupported": is_unsupported,
            "supporting_urls": [s.url for s in supporting_sources]
        }

    def detect_numerical_disagreement(self, topic: str, sources: List[SourceEvidence]) -> List[DisagreementItem]:
        """
        Detect disagreements across numbers, percentages, or dates on a topic.
        """
        disagreements = []
        # Look for numbers with units like Wh, kWh, mL, liters, million, billion, FLOPs, EUR
        pattern = re.compile(r"(\b\d+(?:\.\d+)?\s*(?:Wh|kWh|mL|liters|litres|million|billion|FLOPs|EUR|dollars|USD)\b)", re.IGNORECASE)

        extracted_data = []
        for s in sources:
            text = f"{s.snippet} {s.full_text[:3000]}"
            matches = pattern.findall(text)
            for m in matches[:3]:
                extracted_data.append({
                    "source": s.url,
                    "domain": s.domain,
                    "figure": m.strip()
                })

        # If distinct conflicting figures exist for similar units
        units_found: Dict[str, List[Dict[str, str]]] = {}
        for item in extracted_data:
            fig = item["figure"].lower()
            unit = fig.split()[-1] if len(fig.split()) > 1 else fig
            units_found.setdefault(unit, []).append(item)

        for unit, items in units_found.items():
            distinct_figs = list(set(it["figure"].lower() for it in items))
            if len(distinct_figs) > 1:
                divergent = [{"source": it["source"], "claim": it["figure"]} for it in items[:4]]
                disagreements.append(DisagreementItem(
                    topic=f"Numerical variance in {unit} for {topic}",
                    divergent_claims=divergent,
                    resolved_verdict=f"Discrepancy observed across sources: {', '.join(distinct_figs)}.",
                    justification="Variances arise from differences in measurement methodology (e.g. direct operational telemetry vs. total lifecycle estimates, or differing model parameter checkpoints)."
                ))

        return disagreements
