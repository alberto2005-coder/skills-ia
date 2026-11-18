import json
import sys
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import mock_server  # noqa: E402

SPEC = {
    "paths": {
        "/users": {
            "get": {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "example": [{"id": 1, "email": "user_1"}],
                            }
                        }
                    }
                }
            }
        }
    }
}


class TestMockServer(unittest.TestCase):

    def setUp(self):
        self.server, self.thread, port = mock_server.serve(SPEC)
        self.base = f"http://127.0.0.1:{port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_serves_the_contract_example(self):
        with urllib.request.urlopen(f"{self.base}/users", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload, [{"id": 1, "email": "user_1"}])

    def test_unknown_route_returns_404(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(f"{self.base}/desconocida", timeout=5)
        self.assertEqual(caught.exception.code, 404)

    def test_server_only_listens_on_loopback(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
