"""La versión de un paquete no puede divergir entre frontmatter, manifiesto e índice."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

METADATA_RE = re.compile(r"^metadata:\s*$")
VERSION_RE = re.compile(r"^\s+version:\s*[\"']?([^\"'\s]+)")


def declared_version(skill_md: Path) -> str:
    """`metadata.version` del frontmatter, leído sin dependencias externas."""
    parts = skill_md.read_text(encoding="utf-8").split("---", 2)
    if len(parts) < 3:
        raise AssertionError("sin bloque de frontmatter: %s" % skill_md)
    in_metadata = False
    for line in parts[1].splitlines():
        if METADATA_RE.match(line):
            in_metadata = True
            continue
        if not in_metadata:
            continue
        match = VERSION_RE.match(line)
        if match:
            return match.group(1)
        if line and not line[0].isspace():
            break
    raise AssertionError("sin metadata.version: %s" % skill_md)


class VersionSyncTests(unittest.TestCase):
    def setUp(self):
        self.index = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))

    def test_frontmatter_manifest_and_index_agree(self):
        for entry in self.index["packages"]:
            package = ROOT / entry["path"]
            manifest = json.loads((package / "skills.json").read_text(encoding="utf-8"))
            skill_files = sorted(
                path for path in package.glob("**/SKILL.md")
                if path.is_file() and "tests" not in path.relative_to(package).parts
            )
            with self.subTest(package=entry["name"]):
                self.assertEqual(entry["version"], manifest["version"])
                self.assertEqual(len(skill_files), entry["skill_count"])
                for skill_md in skill_files:
                    self.assertEqual(
                        declared_version(skill_md),
                        manifest["version"],
                        "versión divergente en %s" % skill_md.relative_to(ROOT).as_posix(),
                    )

    def test_index_version_and_date_keep_their_shape(self):
        self.assertRegex(self.index["version"], r"^\d+\.\d+\.\d+$")
        self.assertRegex(self.index["updated"], r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
