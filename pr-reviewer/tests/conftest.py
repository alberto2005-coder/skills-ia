import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACKAGE / "scripts"))

# Las fixtures no son tests: el parche y los informes solo se leen.
collect_ignore_glob = ["fixtures/*"]
