import shutil
import sys
import tempfile
from pathlib import Path
import unittest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cache_lib import ensure_storage, write_normalized_doc, rebuild_index, search_hierarchy


class IndexAndSearchTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="lk_layer_test_"))
        ensure_storage(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_search_prefers_project_then_skill_then_external(self):
        project_doc = write_normalized_doc(
            root=self.tmpdir,
            relative_path="knowledge/normalized/project/demo/specs/payment-intent.md",
            metadata={
                "id": "doc-project",
                "kind": "project_spec",
                "title": "Project Payment Intent Rule",
                "project": "demo",
                "service": "stripe",
                "source_url": "local://project",
                "source_type": "markdown",
                "last_checked": "2026-03-06T00:00:00Z",
                "freshness": "stable",
                "tags": ["payment", "intent"],
                "related": [],
                "sample_questions": ["How do we create payment intents in demo project?"],
            },
            body="# Rule\nUse payment intent with capture_method=automatic_async.",
        )

        write_normalized_doc(
            root=self.tmpdir,
            relative_path="knowledge/normalized/skills/payment-intent.md",
            metadata={
                "id": "doc-skill",
                "kind": "integration_note",
                "title": "Skill Payment Intent Note",
                "project": "",
                "service": "stripe",
                "source_url": "local://skill",
                "source_type": "markdown",
                "last_checked": "2026-03-06T00:00:00Z",
                "freshness": "medium",
                "tags": ["payment"],
                "related": [],
                "sample_questions": ["What is payment intent in our skill cache?"],
            },
            body="# Skill\nGeneric payment intent note.",
        )

        write_normalized_doc(
            root=self.tmpdir,
            relative_path="knowledge/normalized/external/services/stripe/payment_intent_create.md",
            metadata={
                "id": "doc-external",
                "kind": "api_spec",
                "title": "Stripe POST /v1/payment_intents",
                "project": "",
                "service": "stripe",
                "source_url": "https://docs.stripe.com/api/payment_intents/create",
                "source_type": "openapi",
                "last_checked": "2026-03-06T00:00:00Z",
                "freshness": "volatile",
                "tags": ["api", "stripe"],
                "related": [],
                "sample_questions": ["How to call stripe payment intent create endpoint?"],
            },
            body="# API\nPOST /v1/payment_intents",
        )

        rebuild_index(self.tmpdir)

        result = search_hierarchy(
            root=self.tmpdir,
            query="payment intent",
            top_n=3,
            project="demo",
            allow_web_fallback=False,
        )

        self.assertGreaterEqual(len(result["results"]), 1)
        self.assertEqual("project", result["results"][0]["layer"])
        self.assertEqual(str(project_doc.as_posix()), result["results"][0]["file_path"])


if __name__ == "__main__":
    unittest.main()
