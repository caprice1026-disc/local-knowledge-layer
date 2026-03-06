import sys
from pathlib import Path
import unittest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cache_lib import normalize_openapi_spec


class NormalizeOpenApiTests(unittest.TestCase):
    def test_normalize_openapi_spec_splits_operations(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Stripe-like API"},
            "paths": {
                "/v1/payment_intents": {
                    "post": {
                        "operationId": "createPaymentIntent",
                        "summary": "Create payment intent",
                        "parameters": [
                            {"name": "amount", "in": "query", "schema": {"type": "integer"}},
                            {"name": "currency", "in": "query", "schema": {"type": "string"}},
                        ],
                        "responses": {"200": {"description": "ok"}, "400": {"description": "bad request"}},
                    }
                },
                "/v1/payment_intents/{id}/confirm": {
                    "post": {
                        "operationId": "confirmPaymentIntent",
                        "summary": "Confirm payment intent",
                        "responses": {"200": {"description": "ok"}},
                    }
                },
            },
        }

        docs = normalize_openapi_spec(
            spec=spec,
            service="stripe",
            source_url="https://example.com/openapi.json",
            freshness="volatile",
        )

        self.assertEqual(2, len(docs))
        first = docs[0]
        self.assertEqual("api_spec", first["metadata"]["kind"])
        self.assertEqual("stripe", first["metadata"]["service"])
        self.assertIn("POST /v1/payment_intents", first["metadata"]["title"])
        self.assertIn("## Method", first["body"])
        self.assertIn("## Parameters", first["body"])


if __name__ == "__main__":
    unittest.main()
