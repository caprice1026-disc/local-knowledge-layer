import sys
from pathlib import Path
import unittest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cache_lib import extract_spec_links


class DiscoveryTests(unittest.TestCase):
    def test_extract_spec_links_from_html(self):
        html = """
        <html>
            <body>
                <a href=\"/docs\">Docs</a>
                <a href=\"https://api.example.com/openapi.json\">OpenAPI</a>
                <a href=\"/swagger.yaml\">Swagger Spec</a>
            </body>
        </html>
        """
        links = extract_spec_links("https://api.example.com", html)
        self.assertIn("https://api.example.com/openapi.json", links)
        self.assertIn("https://api.example.com/swagger.yaml", links)


if __name__ == "__main__":
    unittest.main()
