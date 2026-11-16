import tempfile, unittest
import sys
from pathlib import Path

# Asegurar que seo-auditor está en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.source_audit import audit_source

class SourceTests(unittest.TestCase):
    def test_detects_missing_title(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,"index.html").write_text("<html><body><h1>Hola</h1></body></html>")
            result=audit_source(d)
            self.assertTrue(any("title" in x["title"].lower() for x in result["findings"]))

if __name__=="__main__": unittest.main()
