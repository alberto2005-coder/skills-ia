#!/usr/bin/env python3
"""
Auditor estilístico anti-IA avanzado en español.
Evalúa Burstiness, Perplexity léxica, Legibilidad (Fernández-Huerta),
clichés, guiones largos, voz pasiva y vicios sintácticos propios de LLMs.

Uso:
  python scripts/audit_style.py --text "Tu texto aquí..."
  python scripts/audit_style.py --file ruta/al/texto.txt
  python scripts/audit_style.py --file ruta/al/texto.txt --json
  python scripts/audit_style.py --file ruta/al/texto.txt --markdown
"""

import argparse
import json
import math
import re
import sys

BANNED_PHRASES = [
    r"\ben conclusi[oó]n\b",
    r"\bcabe destacar\b",
    r"\bes importante se[ñn]alar\b",
    r"\basimismo\b",
    r"\bpor otro lado\b",
    r"\bpor otra parte\b",
    r"\ben resumen\b",
    r"\ben suma\b",
    r"\ben el [aá]mbito de\b",
    r"\ben el panorama de\b",
    r"\bsin lugar a dudas\b",
    r"\bindudablemente\b",
    r"\ben [uú]ltima instancia\b",
    r"\ba fin de cuentas\b",
    r"\bvale la pena mencionar\b",
    r"\bconviene subrayar\b",
    r"\bcrucial\b",
    r"\bfascinante\b",
    r"\btapiz\b",
    r"\bpanorama en constante evoluci[oó]n\b",
    r"\bdesentra[ñn]ar\b",
    r"\bsumergirse en\b",
    r"\btestamento de\b",
    r"\bfaro de\b",
    r"\bcatalizador\b",
    r"\brevolucionar\b",
    r"\bpotenciar\b",
    r"\bbrindar\b",
    r"\babarcar\b",
    r"\bmultifac[eé]tico\b",
    r"\bmeticuloso\b",
    r"\bintrincado\b",
    r"\bparadigma\b",
    r"\bparadigm[aá]tico\b",
    r"\bsinergia\b",
    r"\bhol[ií]stico\b",
    r"\bempoderar\b",
    r"\bvanguardia\b",
    r"\bpiedra angular\b",
    r"\bprimordial\b",
    r"\binquebrantable\b",
    r"\bresonante\b",
    r"\barmon[ií]a de\b",
    r"\bsinfon[ií]a de\b",
    r"\bcrisol\b",
    r"\bapalancar\b",
    r"\borquestar\b",
    r"\bvislumbrar\b",
    r"\bentrelazar\b",
]

def count_syllables_es(word: str) -> int:
    """Aproximación heurística rápida de conteo de sílabas en español."""
    w = word.lower().strip()
    if not w:
        return 0
    # Agrupaciones vocálicas comunes
    vowels = r"[aeiouáéíóúü]"
    matches = re.findall(vowels, w)
    count = len(matches)
    # Ajuste para diptongos / triptongos habituales
    diphthongs = len(re.findall(r"[aeiouáéíóúü]{2}", w))
    triphthongs = len(re.findall(r"[aeiouáéíóúü]{3}", w))
    syllables = count - diphthongs - triphthongs
    return max(1, syllables)


def analyze_text(text: str) -> dict:
    clean_text = text.strip()
    if not clean_text:
        return {"error": "Texto vacío o sin oraciones detectables."}

    # Separar oraciones
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if s.strip()]
    sentence_words = [re.findall(r'\b[a-záéíóúüñA-ZÁÉÍÓÚÜÑ0-9_-]+\b', s) for s in sentences]
    lengths = [len(words) for words in sentence_words if len(words) > 0]

    if not lengths:
        return {"error": "No se encontraron palabras válidas en el texto."}

    total_words_count = sum(lengths)
    total_sentences_count = len(lengths)

    mean_len = total_words_count / total_sentences_count
    variance = sum((l - mean_len) ** 2 for l in lengths) / total_sentences_count
    std_dev = math.sqrt(variance)

    # Burstiness (Coeficiente de Variación)
    cv = (std_dev / mean_len) if mean_len > 0 else 0.0

    # Frases cortas y largas
    short_sentences = sum(1 for l in lengths if l <= 8)
    long_sentences = sum(1 for l in lengths if l >= 22)

    # Monotonía de longitudes consecutivas (3+ frases con delta <= 3 palabras)
    monotonic_runs = 0
    for i in range(len(lengths) - 2):
        window = lengths[i : i + 3]
        if max(window) - min(window) <= 3:
            monotonic_runs += 1

    # Búsqueda de clichés prohibidos
    found_banned = []
    lower_text = clean_text.lower()
    for pattern in BANNED_PHRASES:
        matches = re.findall(pattern, lower_text)
        if matches:
            found_banned.extend(matches)

    # Guiones largos o semilargos
    em_dashes = clean_text.count("—") + clean_text.count("–")

    # Detección de voz pasiva típica en español
    passive_matches = re.findall(r'\b(?:ha sido|fue|fueron|han sido|era|eran|ser[aá]n?)\s+[a-záéíóúüñ]+(?:d[oa]s?)\b', lower_text)

    # Diversidad léxica (Type-Token Ratio)
    all_words = re.findall(r'\b[a-záéíóúüñ]+\b', lower_text)
    ttr = (len(set(all_words)) / len(all_words)) if all_words else 0.0

    # Índice de Legibilidad Fernández-Huerta para español:
    # L = 206.84 - 60*(sílabas/palabras) - 102*(frases/palabras)
    total_syllables = sum(count_syllables_es(w) for w in all_words) if all_words else 1
    syll_per_word = total_syllables / max(1, len(all_words))
    sent_per_word = total_sentences_count / max(1, len(all_words))
    readability_fh = 206.84 - (60 * syll_per_word) - (102 * sent_per_word)
    readability_score = max(0.0, min(100.0, round(readability_fh, 1)))

    # Repetición de inicios de párrafo
    paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]
    first_words = [re.findall(r'^\w+', p.lower())[0] for p in paragraphs if re.findall(r'^\w+', p.lower())]
    repeated_starts = len(first_words) - len(set(first_words))

    issues = []
    if cv < 0.45 and total_sentences_count >= 4:
        issues.append(f"Burstiness baja (CV={cv:.2f}, objetivo >= 0.45). El texto tiene un ritmo monótono propio de IA. Alterna oraciones de 4-8 palabras con subordinadas de 22+ palabras.")
    if short_sentences == 0 and total_sentences_count >= 3:
        issues.append("Faltan frases cortas y contundentes (<= 8 palabras) para dar impacto y dinamismo.")
    if monotonic_runs > 0:
        issues.append(f"Se detectaron {monotonic_runs} secuencias de 3 o más frases seguidas con longitud casi idéntica.")
    if found_banned:
        unique_banned = sorted(set(found_banned))
        issues.append(f"Clichés o conectores IA detectados ({len(found_banned)}): {', '.join(unique_banned)}")
    if em_dashes > 0:
        issues.append(f"Se detectaron {em_dashes} guiones largos (—/–). Sustitúyelos por comas, paréntesis o punto y seguido.")
    if len(passive_matches) >= 3:
        issues.append(f"Abuso de voz pasiva ({len(passive_matches)} apariciones). Prefiere la voz activa en español.")
    if repeated_starts > 0:
        issues.append(f"Hay {repeated_starts} párrafos que inician con la misma palabra o conector.")

    return {
        "total_sentences": total_sentences_count,
        "total_words": total_words_count,
        "sentence_lengths": lengths,
        "mean_length": round(mean_len, 1),
        "std_dev": round(std_dev, 2),
        "burstiness_cv": round(cv, 2),
        "lexical_diversity_ttr": round(ttr, 2),
        "readability_score": readability_score,
        "short_sentences": short_sentences,
        "long_sentences": long_sentences,
        "banned_phrases_count": len(found_banned),
        "banned_phrases": sorted(set(found_banned)),
        "em_dashes_count": em_dashes,
        "passive_voice_count": len(passive_matches),
        "passed": len(issues) == 0,
        "issues": issues,
    }


def format_markdown(report: dict) -> str:
    status = "APROBADO" if report["passed"] else "REQUIERE REESCRITURA"
    lines = [
        "# Auditoría Estilística Anti-IA",
        "",
        f"- **Estado general:** `{status}`",
        f"- **Burstiness (Coef. Variación):** **{report['burstiness_cv']}** (Recomendado: ≥ 0.45)",
        f"- **Diversidad léxica (TTR):** {report['lexical_diversity_ttr']}",
        f"- **Índice de legibilidad (Fernández-Huerta):** {report['readability_score']}/100",
        f"- **Oraciones analizadas:** {report['total_sentences']} (Media: {report['mean_length']} palabras)",
        f"- **Frases cortas (≤8 palabras):** {report['short_sentences']} | **Frases largas (≥22 palabras):** {report['long_sentences']}",
        "",
        "## Hallazgos y Puntos a Corregir",
    ]
    if report["passed"]:
        lines.append("El texto presenta un ritmo dinámico, vocabulario natural y no contiene clichés evidentes de IA.")
    else:
        for issue in report["issues"]:
            lines.append(f"- {issue}")

    if report["banned_phrases"]:
        lines.extend(["", "### Clichés Detectados:", ", ".join(f"`{w}`" for w in report["banned_phrases"])])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audita textos en español contra patrones estadísticos y clichés de IA.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Texto directo a evaluar")
    group.add_argument("--file", type=str, help="Ruta a archivo .txt o .md a evaluar")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON estructurado")
    parser.add_argument("--markdown", action="store_true", help="Salida en formato Markdown para informes")
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"Error al leer archivo: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        content = args.text

    report = analyze_text(content)
    if "error" in report:
        print(f"ERROR: {report['error']}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(0 if report["passed"] else 2)

    if args.markdown:
        print(format_markdown(report))
        sys.exit(0 if report["passed"] else 2)

    # Salida estándar por consola
    print("=== AUDITORÍA ESTILÍSTICA ANTI-IA ===")
    print(f"Oraciones: {report['total_sentences']} | Palabras: {report['total_words']}")
    print(f"Media de longitud: {report['mean_length']} palabras | Desv. Estándar: {report['std_dev']}")
    print(f"Burstiness (CV): {report['burstiness_cv']} | Diversidad léxica (TTR): {report['lexical_diversity_ttr']}")
    print(f"Legibilidad (Fernández-Huerta): {report['readability_score']}/100")
    print(f"Frases cortas (<=8w): {report['short_sentences']} | Frases largas (>=22w): {report['long_sentences']}")
    print(f"Guiones largos: {report['em_dashes_count']} | Construcciones pasivas: {report['passive_voice_count']}")

    if report["passed"]:
        print("\nESTADO: APROBADO (Sin patrones estadísticos ni clichés evidentes de IA)")
        sys.exit(0)
    else:
        print("\nESTADO: REQUIERE REESCRITURA")
        for issue in report["issues"]:
            print(f"  [!] {issue}")
        sys.exit(2)


if __name__ == "__main__":
    main()
