import unittest
import tempfile
from pathlib import Path
from core.models import SourceEvidence, Claim, ClaimVerdict, AnalystResponse, ResearchPlan
from memory.store import EntityMemoryStore
from cost_tracker.tracker import CostTracker
from tools.cross_checker import SourceCrossChecker
from auditor.agent import AuditorAgent


class TestResearchAgentSubsystems(unittest.TestCase):
    def test_cost_tracker_rupee_calculation(self):
        tracker = CostTracker(inr_rate=86.5)
        # 1,000,000 prompt tokens ($0.075) + 1,000,000 completion tokens ($0.30) = $0.375
        # In INR: 0.375 * 86.5 = Rs 32.4375
        tracker.record_usage("Q_TEST", 1_000_000, 1_000_000)
        cost = tracker.get_question_cost("Q_TEST")
        self.assertAlmostEqual(cost.cost_usd, 0.375, places=4)
        self.assertAlmostEqual(cost.cost_inr, 32.4375, places=3)
        self.assertEqual(cost.total_tokens, 2_000_000)

    def test_entity_memory_store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_file = Path(tmpdir) / "test_memory.json"
            store = EntityMemoryStore(persistence_file=store_file)

            store.add_entity("Mistral AI", aliases=["Mistral"], summary="French AI lab founded in 2023.")
            store.add_fact("Mistral AI", "Co-founded by Arthur Mensch, Guillaume Lample, and Timothée Lacroix.", "https://example.com")

            # Recall test
            hits = store.search_entities_for_text("Tell me about Mistral models")
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["name"], "Mistral AI")
            self.assertEqual(len(hits[0]["facts"]), 1)

            # Context formatting
            formatted = store.format_memory_context(hits)
            self.assertIn("Mistral AI", formatted)
            self.assertIn("Arthur Mensch", formatted)

    def test_cross_checker_disagreement_detection(self):
        checker = SourceCrossChecker()
        s1 = SourceEvidence(
            url="https://source1.com",
            title="Study A",
            snippet="GPT-4 requires an estimated 500 mL of water per query for data center cooling.",
            domain="source1.com"
        )
        s2 = SourceEvidence(
            url="https://source2.com",
            title="Study B",
            snippet="OpenAI estimates water consumption at approximately 120 mL per standard query.",
            domain="source2.com"
        )

        disagreements = checker.detect_numerical_disagreement("GPT-4 water consumption", [s1, s2])
        self.assertTrue(len(disagreements) >= 1)
        self.assertIn("ml", disagreements[0].topic.lower())

    def test_auditor_flags_unattributed_claim(self):
        tracker = CostTracker()
        auditor = AuditorAgent(cost_tracker=tracker)

        # Claim without citations
        claim_no_cite = Claim(
            claim_id="C1",
            text="The moon is made of green cheese with 99% certainty.",
            citations=[]
        )
        resp = AnalystResponse(
            question_id="Q_AUDIT",
            question="What is the moon made of?",
            answer_text="The moon is made of green cheese.",
            claims=[claim_no_cite],
            citations=[]
        )

        report = auditor.audit(resp)
        self.assertEqual(report.no_citation_count, 1)
        self.assertEqual(report.audited_claims[0].verdict, ClaimVerdict.NO_CITATION)
        self.assertTrue(report.audited_claims[0].flagged)
        self.assertFalse(report.passed)


if __name__ == "__main__":
    unittest.main()
