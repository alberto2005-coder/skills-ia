"""Tests de activación (trigger) de las 39 skills del repositorio.

Sin red y solo stdlib. Cargan los `SKILL.md`, puntúan frases reales contra sus
descripciones y comprueban cuatro invariantes:

1. cada skill gana sus propias frases, también dentro de su paquete;
2. ninguna sub-skill pierde una de sus frases contra una hermana (sin solape);
3. las frases de otro dominio no activan ninguna skill;
4. si hay empate en cabeza, solo puede ser con el maestro del propio paquete
   (jerarquía maestro/sub-skill), nunca entre dos sub-skills hermanas.

El router es un fixture de test, no un producto: si una descripción cambia y
pierde sus frases, el test señala exactamente qué skill y qué frase.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import trigger_router as tr  # noqa: E402  (tras ajustar sys.path)

TESTS_DIR = Path(__file__).resolve().parent
ROOT = TESTS_DIR.parent


class TriggerTest(unittest.TestCase):
    """Base con el corpus cargado una sola vez."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.router = tr.Router.from_repo(ROOT)
        cls.data = json.loads((TESTS_DIR / "phrases.json").read_text(encoding="utf-8"))
        cls.skills = cls.data["skills"]
        cls.masters = {
            skill.package: skill.name
            for skill in cls.router.skills.values()
            if skill.name == skill.package
        }

    def top(self, phrase: str, limit: int = 3) -> str:
        return ", ".join(f"{name} {value:.2f}" for name, value in self.router.ranking(phrase)[:limit])


class CorpusTest(TriggerTest):
    """El dataset cubre exactamente las skills que existen."""

    def test_dataset_covers_every_skill(self) -> None:
        self.assertEqual(len(self.router.names), 39, "el repo debe tener 39 skills")
        self.assertEqual(
            set(self.skills),
            self.router.names,
            "phrases.json debe cubrir todas las SKILL.md y ninguna inexistente",
        )

    def test_folded_skill_description_is_loaded(self) -> None:
        description = self.router.skills["premium-web-designer"].description
        self.assertIn("Premium digital agency website design", description)

    def test_each_skill_has_positives_and_negatives(self) -> None:
        for name, entry in self.skills.items():
            with self.subTest(skill=name):
                self.assertGreaterEqual(len(entry.get("positives", [])), 2,
                                        f"{name} necesita al menos 2 frases positivas")
                self.assertGreaterEqual(len(entry.get("negatives", [])), 1,
                                        f"{name} necesita al menos 1 frase negativa")

    def test_descriptions_are_distinct(self) -> None:
        seen: dict[str, str] = {}
        for name, skill in self.router.skills.items():
            normalized = tr.normalize(skill.description)
            with self.subTest(skill=name):
                self.assertNotIn(normalized, seen,
                                 f"{name} repite la descripción de {seen.get(normalized)}")
            seen[normalized] = name


class PositiveTriggerTest(TriggerTest):
    """Cada frase de activación debe ganar su propia skill."""

    def test_positive_phrase_wins_globally(self) -> None:
        for name, entry in self.skills.items():
            for phrase in entry["positives"]:
                with self.subTest(skill=name, phrase=phrase):
                    winner, _ = self.router.best(phrase)
                    self.assertEqual(winner, name, f"«{phrase}» activa {winner}; top3: {self.top(phrase)}")

    def test_positive_phrase_wins_inside_its_package(self) -> None:
        for name, entry in self.skills.items():
            package = self.router.skills[name].package
            for phrase in entry["positives"]:
                with self.subTest(skill=name, phrase=phrase):
                    winner, _ = self.router.best_in(phrase, package)
                    self.assertEqual(winner, name,
                                     f"«{phrase}» pierde contra {winner} dentro de {package}; top3: {self.top(phrase)}")

    def test_positive_phrase_ranks_above_every_sibling(self) -> None:
        for name, entry in self.skills.items():
            for phrase in entry["positives"]:
                for sibling in self.router.siblings(name):
                    with self.subTest(skill=name, sibling=sibling, phrase=phrase):
                        position = [n for n, _ in self.router.ranking(phrase)]
                        self.assertLess(position.index(name), position.index(sibling),
                                        f"«{phrase}» coloca {sibling} por delante de {name}; top3: {self.top(phrase)}")

    def test_ties_at_top_are_only_with_the_package_master(self) -> None:
        """Un empate con el maestro es jerarquía; con una hermana es solapamiento."""
        for name, entry in self.skills.items():
            package = self.router.skills[name].package
            master = self.masters.get(package)
            for phrase in entry["positives"]:
                with self.subTest(skill=name, phrase=phrase):
                    ties = set(self.router.top_ties(phrase))
                    allowed = {name, master} if master else {name}
                    self.assertTrue(ties <= allowed,
                                    f"«{phrase}» empata con {sorted(ties - allowed)}; top3: {self.top(phrase)}")




class ThresholdTest(TriggerTest):
    """Una frase positiva debe superar el umbral, no solo ganar el ranking."""

    def test_positive_phrases_clear_the_threshold(self) -> None:
        threshold = self.data["threshold"]
        for name, entry in self.skills.items():
            for phrase in entry["positives"]:
                with self.subTest(skill=name, phrase=phrase):
                    value = self.router.score(phrase, name)
                    self.assertGreaterEqual(
                        value,
                        threshold,
                        f"«{phrase}» puntúa {value:.2f} en {name}, por debajo del umbral {threshold}",
                    )

class NegativeTriggerTest(TriggerTest):
    """Una frase de otra función no debe activar la skill equivocada."""

    def test_negative_phrase_does_not_activate_the_owner(self) -> None:
        for name, entry in self.skills.items():
            for negative in entry.get("negatives", []):
                phrase = negative["phrase"]
                with self.subTest(skill=name, phrase=phrase):
                    winner, _ = self.router.best(phrase)
                    self.assertNotEqual(winner, name,
                                        f"«{phrase}» no debería activar {name}; top3: {self.top(phrase)}")

    def test_negative_phrase_activates_the_expected_skill(self) -> None:
        for name, entry in self.skills.items():
            for negative in entry.get("negatives", []):
                phrase, expected = negative["phrase"], negative["winner"]
                with self.subTest(skill=name, expected=expected, phrase=phrase):
                    winner, _ = self.router.best(phrase)
                    self.assertEqual(winner, expected,
                                     f"«{phrase}» debería activar {expected} y activa {winner}; top3: {self.top(phrase)}")


class OutOfDomainTest(TriggerTest):
    """Frases ajenas al repositorio no activan ninguna skill."""

    def test_out_of_domain_phrases_stay_below_threshold(self) -> None:
        threshold = self.data["threshold"]
        for phrase in self.data["out_of_domain"]:
            with self.subTest(phrase=phrase):
                winner, value = self.router.best(phrase)
                self.assertLess(value, threshold,
                                f"«{phrase}» activa {winner} con {value:.2f} (umbral {threshold})")


class DeterminismTest(TriggerTest):
    """El router no depende de red, hora ni orden de iteración."""

    def test_same_phrase_same_result(self) -> None:
        phrase = "compara dos auditorías y clasifica mejorado, empeorado y resuelto"
        first = self.router.ranking(phrase)
        second = self.router.ranking(phrase)
        self.assertEqual(first, second)

    def test_ranking_is_a_total_order_over_the_corpus(self) -> None:
        ranking = self.router.ranking("audita el SEO de una web")
        self.assertEqual(len(ranking), len(self.router.names))
        self.assertEqual(len({name for name, _ in ranking}), len(ranking))


if __name__ == "__main__":
    unittest.main(verbosity=2)
