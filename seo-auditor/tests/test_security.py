import unittest
import sys
from pathlib import Path

# Asegurar que seo-auditor está en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.security import validate_target

class SecurityTests(unittest.TestCase):
    def test_rejects_file_scheme(self):
        with self.assertRaises(ValueError):
            validate_target("file:///etc/passwd")
    def test_local_requires_allow_flag(self):
        with self.assertRaises(ValueError):
            validate_target("http://localhost:3000")
    def test_local_allowed_explicitly(self):
        validate_target("http://localhost:3000",allow_local=True)

if __name__=="__main__":
    unittest.main()
