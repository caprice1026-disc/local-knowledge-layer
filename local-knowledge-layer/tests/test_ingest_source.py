import json
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import cache_lib
from ingest_source import ingest


class IngestSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="lk_ingest_test_"))
        cache_lib.ensure_storage(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_ingest_local_file_avoids_local_urls_and_absolute_paths(self):
        file_url_scheme = "file:" + "//"
        source_file = self.tmpdir / "fixtures" / "project-spec.md"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text(
            "\n".join(
                [
                    "# Checkout Flow",
                    "",
                    "Requirement: Checkout must support card and wallet.",
                    "Constraint: Order must be idempotent for retry.",
                ]
            ),
            encoding="utf-8",
        )

        result = ingest(
            SimpleNamespace(
                root=str(self.tmpdir),
                kind="project_spec",
                layer="project",
                input_path=str(source_file),
                source_url=None,
                content=None,
                source_type=None,
                title="Checkout Spec",
                project="demo-shop",
                service="",
                freshness="medium",
                tags="",
                related="",
                sample_questions="",
            )
        )

        self.assertNotIn(file_url_scheme, json.dumps(result))
        self.assertTrue(result["raw_path"].startswith("knowledge/"))
        self.assertTrue(all(path.startswith("knowledge/") for path in result["normalized_paths"]))

        normalized_doc = self.tmpdir / result["normalized_paths"][0]
        self.assertTrue(normalized_doc.exists())
        self.assertNotIn(file_url_scheme, normalized_doc.read_text(encoding="utf-8"))

        manifest = json.loads((self.tmpdir / "manifests" / "sources.json").read_text(encoding="utf-8"))
        self.assertEqual(1, len(manifest["sources"]))
        source_entry = manifest["sources"][0]
        self.assertNotIn(file_url_scheme, source_entry["source_url"])
        self.assertEqual("manual://project-spec-md", source_entry["source_url"])
        self.assertTrue(source_entry["raw_path"].startswith("knowledge/"))
        self.assertTrue(all(path.startswith("knowledge/") for path in source_entry["normalized_paths"]))


if __name__ == "__main__":
    unittest.main()
