"""Coherencia entre maestros y sub-skills.

Automatiza la revisión manual del paquete:
1. ninguna sub-skill repite prosa de su maestro (los comandos CLI sí pueden
   repetirse: son referencia de uso, no reglas);
2. todas las sub-skills tienen `## Gate de salida` y `## Handoff`;
3. no reaparecen contradicciones ya corregidas ni rutas de comando relativas;
4. el maestro indexa sus sub-skills y su tamaño no vuelve a crecer sin control.

Sin red y solo stdlib, como el resto del repo.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MASTER_MAX_LINES = 200
MASTER_MAX_COMMANDS = 6
MIN_LONG_LINE = 70

# Líneas que sí pueden repetirse: son ejemplos de ejecución, no reglas.
COMMAND_PREFIXES = ("py ", "python ", "python3 ", "$ ")

# Contradicciones y duplicados que ya se corrigieron. Si reaparecen, el test falla.
FORBIDDEN = [
    ("replica/SKILL.md", "dos condiciones", "la fase 12 tiene tres condiciones, no dos"),
    ("replica/SKILL.md", "no disponible", "el estado de la fase omitida es `n/a`"),
    ("humanizador-anti-ia/SKILL.md", "### Quick en detalle", "procedimiento duplicado; vive en `humanizar`"),
    ("humanizador-anti-ia/SKILL.md", "Flujo de trabajo obligatorio", "flujo duplicado; vive en `humanizar`"),
    ("seo-auditor/SKILL.md", "## Módulos (8 bloques", "la tabla de módulos vive en `seo-audit`"),
    ("seo-auditor/SKILL.md", "cli.py serp pagina.html", "el bloque de comandos vive en USAGE.md"),
    ("seo-auditor/seo-compare/SKILL.md", "re-score offline", "`rescore` pertenece a `seo-audit`"),
]

# Frases que no deben aparecer en ningún SKILL.md.
GLOBAL_FORBIDDEN = [
    ("py scripts/", "los comandos se ejecutan desde la raíz del repositorio"),
    ("py ../scripts/", "los comandos se ejecutan desde la raíz del repositorio"),
    ("python scripts/", "los comandos se ejecutan desde la raíz del repositorio"),
    ("python ../scripts/", "los comandos se ejecutan desde la raíz del repositorio"),
    ("Instala esta sub-skill con la carpeta", "lo dice el maestro; no se repite en cada sub-skill"),
]


def load_packages():
    """Devuelve [{name, base, skills: [{name, path, file, is_master, text}]}]."""
    index = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
    packages = []
    for package in index["packages"]:
        manifest = json.loads((ROOT / package["manifest"]).read_text(encoding="utf-8"))
        base = ROOT / package["path"]
        skills = []
        for entry in manifest["skills"]:
            path = entry["path"]
            file = base / path
            skills.append({
                "name": entry["name"],
                "path": path,
                "file": file,
                "is_master": path == "SKILL.md",
                "text": file.read_text(encoding="utf-8"),
            })
        packages.append({"name": package["name"], "base": base, "skills": skills})
    return packages


def frontmatter_name(text):
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    found = re.search(r"^name:\s*(.+?)\s*$", match.group(1), re.M) if match else None
    return found.group(1) if found else None


def long_lines(text):
    return {
        line.strip()
        for line in text.splitlines()
        if len(line.strip()) >= MIN_LONG_LINE and not line.strip().startswith(COMMAND_PREFIXES)
    }


def command_lines(text):
    return [line for line in text.splitlines() if line.strip().startswith(COMMAND_PREFIXES)]


class CoherenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packages = load_packages()

    def masters(self):
        for package in self.packages:
            for skill in package["skills"]:
                if skill["is_master"]:
                    yield package, skill

    def subs(self):
        for package in self.packages:
            for skill in package["skills"]:
                if not skill["is_master"]:
                    yield package, skill

    # 1. Estructura mínima -------------------------------------------------
    def test_every_manifest_entry_resolves(self):
        for package, skill in self.masters():
            with self.subTest(package=package["name"]):
                self.assertTrue(skill["file"].exists())
        for package, skill in self.subs():
            with self.subTest(skill=skill["name"]):
                self.assertTrue(skill["file"].exists(), f"falta {skill['file']}")
                self.assertEqual(frontmatter_name(skill["text"]), skill["name"])
                self.assertEqual(skill["file"].parent.name, skill["name"],
                                 "la carpeta debe llamarse como el `name`")

    def test_master_indexes_its_subskills(self):
        for package, master in self.masters():
            subs = [s for s in package["skills"] if not s["is_master"]]
            for sub in subs:
                with self.subTest(package=package["name"], sub=sub["name"]):
                    self.assertIn(sub["name"], master["text"],
                                  f"{master['name']} no menciona {sub['name']}")

    # 2. Gate y handoff en todas las sub-skills ----------------------------
    def test_every_subskill_has_gate_and_handoff(self):
        for _, skill in self.subs():
            with self.subTest(skill=skill["name"]):
                headings = re.findall(r"^##\s+(.+)$", skill["text"], re.M)
                self.assertIn("Gate de salida", headings,
                              f"{skill['name']} no declara su gate")
                self.assertIn("Handoff", headings,
                              f"{skill['name']} no declara a quién entrega")

    # 3. Sin prosa duplicada ----------------------------------------------
    def test_subskill_does_not_repeat_master_prose(self):
        for package in self.packages:
            master = next(s for s in package["skills"] if s["is_master"])
            master_lines = long_lines(master["text"])
            for sub in package["skills"]:
                if sub["is_master"]:
                    continue
                repeated = master_lines & long_lines(sub["text"])
                with self.subTest(sub=sub["name"]):
                    self.assertFalse(repeated,
                                     f"{sub['name']} repite {len(repeated)} línea(s) de {master['name']}: "
                                     f"{sorted(repeated)[:2]}")

    def test_command_examples_do_not_become_a_whole_block(self):
        """Los comandos pueden repetirse, pero no copiarse en bloque."""
        for package in self.packages:
            master = next(s for s in package["skills"] if s["is_master"])
            master_commands = {line.strip() for line in command_lines(master["text"])}
            for sub in package["skills"]:
                if sub["is_master"]:
                    continue
                shared = master_commands & {line.strip() for line in command_lines(sub["text"])}
                with self.subTest(sub=sub["name"]):
                    self.assertLessEqual(len(shared), MASTER_MAX_COMMANDS,
                                         f"{sub['name']} copia {len(shared)} comandos del maestro")

    # 4. Contradicciones ya corregidas ------------------------------------
    def test_corrected_contradictions_do_not_return(self):
        for relative, needle, reason in FORBIDDEN:
            path = ROOT / relative
            with self.subTest(file=relative, needle=needle):
                self.assertTrue(path.exists(), f"no existe {relative}")
                self.assertNotIn(needle, path.read_text(encoding="utf-8"),
                                 f"reaparece «{needle}» en {relative}: {reason}")

    def test_global_forbidden_phrases(self):
        for path in ROOT.glob("**/SKILL.md"):
            if "tests" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for needle, reason in GLOBAL_FORBIDDEN:
                with self.subTest(file=str(path.relative_to(ROOT)), needle=needle):
                    self.assertNotIn(needle, text, f"{reason}: {path.relative_to(ROOT)}")

    def test_phase_12_conditions_are_stated_once(self):
        master = (ROOT / "replica/SKILL.md").read_text(encoding="utf-8")
        static = (ROOT / "replica/replica-static/SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("tres condiciones", master,
                         "el maestro no debe redefinir las condiciones de la fase 12")
        self.assertIn("las tres", static,
                      "replica-static es la dueña de las condiciones de la fase 12")
        self.assertIn("`n/a`", master,
                      "la fase 12 omitida se marca `n/a`")

    def test_rescore_command_is_defined_once(self):
        owners = [
            path.relative_to(ROOT).as_posix()
            for path in ROOT.glob("**/SKILL.md")
            if "tests" not in path.parts
            and "cli.py rescore" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(owners, ["seo-auditor/seo-audit/SKILL.md"],
                         f"`rescore` debe documentarse solo en seo-audit: {owners}")

    # 5. Comandos ejecutables y maestros contenidos ------------------------
    def test_documented_scripts_exist(self):
        pattern = re.compile(r"(?:py|python3?) ([\w-]+/scripts/[\w./-]+\.py)")
        for path in ROOT.glob("**/SKILL.md"):
            if "tests" in path.parts:
                continue
            for relative in pattern.findall(path.read_text(encoding="utf-8")):
                with self.subTest(file=str(path.relative_to(ROOT)), script=relative):
                    self.assertTrue((ROOT / relative).exists(),
                                    f"{path.relative_to(ROOT)} cita un script inexistente: {relative}")

    def test_masters_stay_compact(self):
        for package, master in self.masters():
            if len(package["skills"]) == 1:
                continue
            with self.subTest(master=master["name"]):
                lines = len(master["text"].splitlines())
                self.assertLessEqual(lines, MASTER_MAX_LINES,
                                     f"{master['name']} tiene {lines} líneas; máx {MASTER_MAX_LINES}")
                commands = len(command_lines(master["text"]))
                self.assertLessEqual(commands, MASTER_MAX_COMMANDS,
                                     f"{master['name']} acumula {commands} comandos; "
                                     f"delega el catálogo a USAGE.md o a su sub-skill")


if __name__ == "__main__":
    unittest.main(verbosity=2)
