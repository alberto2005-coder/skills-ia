import re
import unittest
from pathlib import Path

from config import SKILL_ROOT, all_markdown_files


LINK_PATTERN = re.compile(
    r"\[[^\]]*\]\(([^)]+)\)"
)


class TestReferences(unittest.TestCase):

    def test_markdown_links_exist(self):
        broken = []

        for document in all_markdown_files():
            content = document.read_text(encoding="utf-8")

            for target in LINK_PATTERN.findall(content):

                target = target.strip()

                if not target or target.startswith(
                    ("http://", "https://", "mailto:", "#")
                ):
                    continue

                target = target.split("#")[0]

                if not target:
                    continue

                destination = (
                    document.parent / target
                ).resolve()

                try:
                    destination.relative_to(
                        SKILL_ROOT.resolve()
                    )
                except ValueError:
                    broken.append(
                        f"{document.name}: path escapes skill root: {target}"
                    )
                    continue

                if not destination.exists():
                    broken.append(
                        f"{document.name}: {target}"
                    )

        self.assertEqual(
            broken,
            [],
            "Broken Markdown references:\n" + "\n".join(broken)
        )

    def test_no_empty_markdown_documents(self):
        empty = [
            str(path.relative_to(SKILL_ROOT))
            for path in all_markdown_files()
            if not path.read_text(encoding="utf-8").strip()
        ]

        self.assertEqual(empty, [])


if __name__ == "__main__":
    unittest.main()