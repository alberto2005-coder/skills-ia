#!/usr/bin/env python3
"""
Auditor estilístico anti-IA en español.

Mide lo que se puede contar (palabras, frases, patrones) y lo traduce a una
puntuación 0-100 donde **más alto = más señales de IA**. Todo el cálculo es
determinista y reproducible desde el texto: no hay red, ni modelos, ni azar.

Uso (compatible con el anterior):
  python scripts/audit_style.py --text "Tu texto aquí..."
  python scripts/audit_style.py --file ruta/al/texto.txt
  python scripts/audit_style.py --file ruta/al/texto.txt --json
  python scripts/audit_style.py --file ruta/al/texto.txt --markdown
  python scripts/audit_style.py --file ruta/al/texto.txt --score

Puntuación (--score imprime JSON):
  total                 0-100, MÁS ALTO = MÁS IA
  vocabulario_ia        densidad de clichés por cada 1000 palabras
  uniformidad_frases    % de frases dentro de ±20% de la media (plano = IA)
  patrones_estructurales  tríadas, «no solo X sino Y», cierres, listas simétricas
  artefactos_chatbot    «como modelo de lenguaje», «espero que te ayude», etc.

Código de salida: 0 = aprobado, 2 = requiere reescritura, 1 = error.
Con --score el código es 0 (es una medición, no un veredicto).
"""

import argparse
import json
import math
import re
import sys

# ---------------------------------------------------------------------------
# Vocabulario IA (Tier 1 y Tier 2 del catálogo; ver references/lista-negra.md)
# ---------------------------------------------------------------------------
BANNED_PHRASES = [
    r"\ben conclusi[oó]n\b",
    r"\bcabe destacar\b",
    r"\bes importante se[ñn]alar\b",
    r"\basimismo\b",
    r"\bpor otro lado\b",
    r"\bpor otra parte\b",
    r"\ben resumen\b",
    r"\ben suma\b",
    r"\ben definitiva\b",
    r"\ben el [aá]mbito de\b",
    r"\ben el panorama de\b",
    r"\ben el panorama actual\b",
    r"\ben la era digital\b",
    r"\ben el vertiginoso\b",
    r"\bsin lugar a dudas\b",
    r"\bsin duda\b",
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
    r"\bsumerg(?:erse|e|ido|ida|i[oó]) en\b",
    r"\btestamento de\b",
    r"\bfaro de\b",
    r"\bcatalizador\b",
    r"\brevolucionar\b",
    r"\bpotenciar\b",
    r"\bpotencia(?:mos|ndo)\b",
    r"\bbrindar\b",
    r"\bbrinda\b",
    r"\babarcar\b",
    r"\bmultifac[eé]tico\b",
    r"\bmeticuloso\b",
    r"\bintrincado\b",
    r"\bparadigma\b",
    r"\bparadigm[aá]tico\b",
    r"\bsinergia\b",
    r"\bsin[eé]rgic[oa]\b",
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
    r"\boptimizar\b",
    r"\bfomentar\b",
    r"\bmaximizar\b",
    r"\bagilizar\b",
    r"\bdisruptiv[oa]\b",
    r"\brobusto\b",
    r"\btransformador(?:a)?\b",
    r"\bilimitad[oa]\b",
    r"\bjuega un papel\b",
    r"\bdesempe[ñn]a un papel\b",
    r"\bmarca un hito\b",
    r"\bdeja huella\b",
    r"\bdejar huella\b",
    r"\bun antes y un despu[eé]s\b",
    r"\bel futuro es ahora\b",
    r"\bm[aá]s que nunca\b",
    r"\bllevar(?:lo)? al siguiente nivel\b",
    r"\bdesbloquear el potencial\b",
    r"\bdescubre c[oó]mo\b",
    r"\bel poder de\b",
    r"\bno es solo\b",
]

# ---------------------------------------------------------------------------
# Patrones estructurales (grupo D del catálogo)
# ---------------------------------------------------------------------------
NO_SOLO_SINO = r"\bno solo\b[^.;!?]{1,90}?\bsino(?: que)?(?: tambi[eé]n)?\b"
MORALEJA = (
    r"\b(?:en definitiva|a medida que (?:avanzamos|miramos|nos adentramos|"
    r"seguimos)|el futuro (?:es|ser[aá]|nos|pertenece)|el camino (?:por recorrer|"
    r"hacia)|no es (?:una opci[oó]n|el final) sino|solo el (?:comienzo|principio)|"
    r"el verdadero (?:desaf[ií]o|poder|valor) (?:est[aá]|radica|reside)|"
    r"escribir[aá]n el pr[oó]ximo cap[ií]tulo|sigamos creciendo)\b"
)
ROADMAP = (
    r"\bprimero\b(?:[^.]{0,140}?)\b(?:despu[eé]s|luego|segundo|a continuaci[oó]n)\b"
    r"(?:[^.]{0,140}?)\b(?:por [uú]ltimo|finalmente|tercero|para terminar)\b"
)
TRIADA = r"\b([a-záéíóúüñ]{3,}),\s+([a-záéíóúüñ]{3,})\s+y\s+([a-záéíóúüñ]{3,})\b"
TRÍADA_STOP = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "con", "por", "para", "que", "y", "o", "en", "su", "sus", "mi", "mis",
    "tu", "tus", "se", "lo", "le", "les", "más", "muy", "sin", "sobre",
    "entre", "desde", "hasta", "como", "pero", "este", "esta", "ese", "esa",
    "nos", "te", "me", "si", "no", "ya", "hay", "son", "fue", "era",
}

# ---------------------------------------------------------------------------
# Artefactos de chatbot (grupo E)
# ---------------------------------------------------------------------------
CHATBOT_ARTIFACTS = [
    r"\bcomo (?:un )?modelo de lenguaje\b",
    r"\bno (?:puedo|tengo la capacidad de) (?:acceder|navegar|ver|consultar)\b",
    r"\bcomo (?:asistente|ia|inteligencia artificial)\b",
    r"\bclaro,? aqu[ií] (?:tienes|est[aá])\b",
    r"\baqu[ií] (?:tienes|te dejo|te presento) (?:el|la|un|una|los|las)\b",
    r"\ba continuaci[oó]n (?:te )?(?:dejo|presento|muestro)\b",
    r"\bespero que (?:esto|esta informaci[oó]n|te) (?:te )?(?:ayude|sirva|resulte)\b",
    r"\b(?:av[ií]same|dime|cu[eé]ntame) si (?:quieres|necesitas|te gustar[ií]a)\b",
    r"\b¿quieres que (?:lo |la |te )?(?:ampl[ií]e|profundice|desarrolle|haga|adapte)\b",
    r"\btienes raz[oó]n,? (?:perm[ií]teme|d[eé]jame)\b",
    r"\bperm[ií]teme (?:reformular|corregir|aclarar)\b",
    r"\ben (?:esta|mi) (?:respuesta|conversaci[oó]n)\b",
    r"\bquedo a la espera de tu (?:respuesta|confirmaci[oó]n)\b",
    r"\bno dudes en (?:preguntar|escribir|contactar)\b",
]

# ---------------------------------------------------------------------------
# Protección de estructura: código, frontmatter, enlaces, correos, inline code
# ---------------------------------------------------------------------------
PROTECTED_PATTERN = re.compile(
    r"(?P<frontmatter>\A---\r?\n.*?\r?\n---\r?\n)"
    r"|(?P<code_block>```.*?```|~~~.*?~~~)"
    r"|(?P<inline_code>`[^`\n]+`)"
    r"|(?P<enlace>(?:https?://|www\.)[^\s<>\"')\]]+|mailto:[^\s<>\"')\]]+"
    r"|\b[\w.+-]+@[\w-]+\.[A-Za-z]{2,}\b)",
    re.S,
)

PLACEHOLDER_RE = re.compile(r"\[\[PROTEGIDO_\d+\]\]")

# ---------------------------------------------------------------------------
# Datos sin fuente
# ---------------------------------------------------------------------------
STAT_PATTERNS = [
    (r"\b\d+(?:[.,]\d+)?\s?%", "porcentaje"),
    (r"\b\d+(?:[.,]\d+)?\s?(?:millones|mill[oó]n|mil|billones|billion)\b", "cifra absoluta"),
    (r"\b\d+(?:[.,]\d+)?\s?(?:euros|d[oó]lares|USD|EUR|pesos)\b", "importe"),
    (r"\b\d+\s+de\s+cada\s+\d+\b", "proporción"),
]
VAGUE_ATTRIBUTION = [
    r"\bestudios?\s+(?:demuestran|revelan|indican|muestran|confirman)\b",
    r"\bexpertos?\s+(?:coinciden|se[ñn]alan|afirman|aseguran)\b",
    r"\binvestigaciones?\s+(?:demuestran|muestran|revelan|confirman)\b",
    r"\bse dice que\b",
    r"\bes bien sabido que\b",
    r"\btodo el mundo sabe\b",
]
SOURCE_MARKERS = re.compile(
    r"seg[uú]n|de acuerdo con|conforme a|fuente|citad[oa]s? en|\[\[PROTEGIDO_"
    r"|\b(?:informe|estudio|encuesta|an[aá]lisis|paper|art[ií]culo|libro)\s+"
    r"(?:de|del|publicado|realizada|realizado|titulado)",
    re.I,
)

PESOS = {
    "vocabulario_ia": 0.30,
    "uniformidad_frases": 0.25,
    "patrones_estructurales": 0.30,
    "artefactos_chatbot": 0.15,
}

# Base mínima de palabras para las densidades. Evita extrapolar una sola
# aparición de un texto de 80 palabras a «20 por cada 1000»: un texto corto no
# da evidencia suficiente y el score no debe dispararse por muestreo pequeño.
SCORE_BASE_WORDS = 250


# ---------------------------------------------------------------------------
# Utilidades de texto
# ---------------------------------------------------------------------------
def count_syllables_es(word: str) -> int:
    """Aproximación heurística rápida de conteo de sílabas en español."""
    w = word.lower().strip()
    if not w:
        return 0
    vowels = r"[aeiouáéíóúü]"
    matches = re.findall(vowels, w)
    count = len(matches)
    diphthongs = len(re.findall(r"[aeiouáéíóúü]{2}", w))
    triphthongs = len(re.findall(r"[aeiouáéíóúü]{3}", w))
    syllables = count - diphthongs - triphthongs
    return max(1, syllables)


def mask_protected(text):
    """Sustituye código, frontmatter, enlaces y correos por marcadores.

    Devuelve (texto_enmascarado, segmentos). El enmascarado es reversible con
    restore_masked(), de modo que una reescritura puede operar sobre el texto
    sin tocar nunca el contenido protegido.
    """
    if not isinstance(text, str):
        text = ""
    segments = []
    out = []
    last = 0
    for match in PROTECTED_PATTERN.finditer(text):
        if match.group("frontmatter") is not None:
            kind = "frontmatter"
        elif match.group("code_block") is not None:
            kind = "code_block"
        elif match.group("inline_code") is not None:
            kind = "inline_code"
        else:
            kind = "enlace"
        out.append(text[last:match.start()])
        token = "[[PROTEGIDO_%d]]" % len(segments)
        segments.append({"tipo": kind, "texto": match.group(0), "indice": len(segments)})
        out.append(token)
        last = match.end()
    out.append(text[last:])
    return "".join(out), segments


def restore_masked(masked, segments):
    """Devuelve el texto original a partir del enmascarado y sus segmentos."""
    result = masked
    for seg in sorted(segments, key=lambda s: s["indice"], reverse=True):
        token = "[[PROTEGIDO_%d]]" % seg["indice"]
        result = result.replace(token, seg["texto"])
    return result


def analysis_text(masked):
    """Quita los marcadores protegidos y normaliza espacios sin perder párrafos."""
    lines = []
    for line in masked.split("\n"):
        if PLACEHOLDER_RE.fullmatch(line.strip()):
            continue
        lines.append(PLACEHOLDER_RE.sub(" ", line))
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def split_sentences(text):
    return [
        s.strip()
        for s in re.split(r"(?<!\bSr)(?<!\bSra)(?<!\bDr)(?<!\bDra)(?<!\betc)(?<!\bp\. ej)(?<=[.!?])\s+", text)
        if s.strip()
    ]


def _words(text):
    return re.findall(r"\b[a-záéíóúüñA-ZÁÉÍÓÚÜÑ0-9_-]+\b", text)


def _saturate(points, k):
    """Convierte una densidad (por 1000 palabras) en 0-100 con saturación suave.

    Curva exponencial: 100 * (1 - e^(-densidad/k)). Reproducible y monótona.
    """
    if points <= 0:
        return 0.0
    return round(100.0 * (1.0 - math.exp(-points / k)), 1)


def _nivel(total):
    if total < 20:
        return "bajo"
    if total < 40:
        return "moderado"
    if total < 60:
        return "medio"
    if total < 80:
        return "alto"
    return "muy alto"


# ---------------------------------------------------------------------------
# Detección de datos sin fuente (honestidad factual)
# ---------------------------------------------------------------------------
def detect_data_to_verify(text):
    """Marca datos y atribuciones que no tienen fuente en el propio texto.

    No valora si el dato es verdadero ni lo corrige: solo avisa de que hay que
    verificarlo antes de publicar. Nunca se reescribe inventando una cifra.
    """
    masked, _ = mask_protected(text)
    clean = analysis_text(masked)
    findings = []
    for sentence in split_sentences(clean):
        if not sentence:
            continue
        found = []
        for pattern, label in STAT_PATTERNS:
            for hit in re.findall(pattern, sentence, re.I):
                found.append(hit if isinstance(hit, str) else hit[0])
        vague = []
        for pattern in VAGUE_ATTRIBUTION:
            vague.extend(re.findall(pattern, sentence, re.I))
        if not found and not vague:
            continue
        if SOURCE_MARKERS.search(sentence):
            continue
        snippet = re.sub(r"\s+", " ", sentence).strip()
        if len(snippet) > 180:
            snippet = snippet[:177].rstrip() + "..."
        if found:
            findings.append({
                "texto": snippet,
                "tipo": "dato sin fuente",
                "detalle": ", ".join(sorted(set(found))),
                "accion": "verificar la fuente antes de publicar; no reescribir el dato ni completarlo",
            })
        if vague:
            findings.append({
                "texto": snippet,
                "tipo": "atribución vaga",
                "detalle": ", ".join(sorted(set(vague))),
                "accion": "verificar quién lo afirma; no inventar autor ni estudio",
            })
        if len(findings) >= 20:
            break
    return findings


# ---------------------------------------------------------------------------
# Señales estructurales
# ---------------------------------------------------------------------------
def _paragraphs(clean_text):
    return [p.strip() for p in clean_text.split("\n\n") if re.search(r"\w", p)]


def _bullet_groups(clean_text):
    """Agrupa viñetas consecutivas y devuelve sus recuentos de palabras."""
    groups = []
    current = []
    previous_line = None
    for index, line in enumerate(clean_text.split("\n")):
        stripped = line.strip()
        is_bullet = bool(re.match(r"^(?:[-*•]|\d+[.)])\s+\S", stripped))
        if is_bullet:
            if previous_line is not None and index - previous_line > 1:
                if len(current) >= 2:
                    groups.append(current)
                current = []
            current.append(len(_words(re.sub(r"^(?:[-*•]|\d+[.)])\s+", "", stripped))))
            previous_line = index
        elif stripped:
            if len(current) >= 2:
                groups.append(current)
            current = []
            previous_line = None
    if len(current) >= 2:
        groups.append(current)
    return groups


def _structural_signals(clean_text):
    points = 0.0
    detail = {}
    base_words = max(SCORE_BASE_WORDS, len(_words(clean_text)), 1)

    no_solo = len(re.findall(NO_SOLO_SINO, clean_text, re.I))
    detail["no_solo_sino"] = no_solo
    points += 1.0 * no_solo

    triadas = 0
    for match in re.finditer(TRIADA, clean_text, re.I):
        words_tri = [w.lower() for w in match.groups()]
        if not any(w in TRÍADA_STOP for w in words_tri):
            triadas += 1
    detail["triadas"] = triadas
    points += 0.5 * triadas

    parrafos = _paragraphs(clean_text)
    cierre = 0
    if parrafos and re.search(MORALEJA, parrafos[-1], re.I):
        cierre = 1
    detail["cierre_moralizante"] = cierre
    points += 2.0 * cierre

    roadmap = len(re.findall(ROADMAP, clean_text, re.I | re.S))
    detail["recorrido_anunciado"] = roadmap
    points += 1.5 * roadmap

    listas = 0
    for group in _bullet_groups(clean_text):
        if len(group) >= 3 and (max(group) - min(group)) <= 2:
            listas += 1
    detail["listas_simetricas"] = listas
    points += 1.5 * listas

    parrafos_uniformes = 0
    if len(parrafos) >= 4:
        lengths = [len(_words(p)) for p in parrafos]
        mean = sum(lengths) / len(lengths)
        if mean > 0:
            variance = sum((length - mean) ** 2 for length in lengths) / len(lengths)
            cv_parrafos = math.sqrt(variance) / mean
            if cv_parrafos < 0.22:
                parrafos_uniformes = 1
    detail["parrafos_uniformes"] = parrafos_uniformes
    points += 2.0 * parrafos_uniformes

    starts = [p.lower().split()[0] for p in parrafos if p.split()]
    repeated = len(starts) - len(set(starts))
    detail["aperturas_repetidas"] = repeated
    points += 0.5 * repeated

    ellipsis = len(re.findall(r"…|\.\.\.", clean_text))
    detail["puntos_suspensivos"] = ellipsis
    points += 0.25 * min(ellipsis, 4)

    density = points * 1000.0 / base_words
    detail["puntos_por_1000_palabras"] = round(density, 2)
    return density, detail


# ---------------------------------------------------------------------------
# Análisis
# ---------------------------------------------------------------------------
def _sentence_stats(lengths):
    """Media, desviación, CV y rachas monótonas de la longitud de frase."""
    total = len(lengths)
    mean_len = sum(lengths) / total
    variance = sum((length - mean_len) ** 2 for length in lengths) / total
    std_dev = math.sqrt(variance)
    cv = (std_dev / mean_len) if mean_len > 0 else 0.0

    monotonic_runs = 0
    for index in range(total - 2):
        window = lengths[index:index + 3]
        if max(window) - min(window) <= 3:
            monotonic_runs += 1

    return {
        "total": total,
        "mean": mean_len,
        "std": std_dev,
        "cv": cv,
        "short": sum(1 for length in lengths if length <= 8),
        "long": sum(1 for length in lengths if length >= 22),
        "runs": monotonic_runs,
    }


def _text_signals(clean_text, lower_text):
    """Clichés, guiones largos, voz pasiva y diversidad léxica."""
    found_banned = []
    for pattern in BANNED_PHRASES:
        matches = re.findall(pattern, lower_text)
        if matches:
            found_banned.extend(matches)

    passive_matches = re.findall(
        r"\b(?:ha sido|fue|fueron|han sido|era|eran|ser[aá]n?)\s+[a-záéíóúüñ]+(?:d[oa]s?)\b",
        lower_text,
    )

    all_words = re.findall(r"\b[a-záéíóúüñ]+\b", lower_text)
    ttr = (len(set(all_words)) / len(all_words)) if all_words else 0.0

    return {
        "banned": found_banned,
        "em_dashes": clean_text.count("—") + clean_text.count("–"),
        "passive": passive_matches,
        "words": all_words,
        "ttr": ttr,
    }


def _readability_score(all_words, total_words, total_sentences):
    """Flesch-Hardinak (reading ease en español)."""
    # 206.835 - 84.6*(sílabas/palabra) - 1.015*(palabras/frase). El segundo
    # término va con PALABRAS/FRASE (≈10-20), no con frases/palabra (≈0.05),
    # que dejaba la métrica saturada.
    total_syllables = sum(count_syllables_es(w) for w in all_words) if all_words else 1
    syll_per_word = total_syllables / max(1, len(all_words))
    words_per_sentence = total_words / max(1, total_sentences)
    readability_fh = 206.835 - (84.6 * syll_per_word) - (1.015 * words_per_sentence)
    return max(0.0, min(100.0, round(readability_fh, 1)))


def _repeated_starts(clean_text):
    paragraphs = _paragraphs(clean_text)
    first_words = [re.findall(r"^\w+", p.lower())[0] for p in paragraphs if re.findall(r"^\w+", p.lower())]
    return len(first_words) - len(set(first_words))


def _score_block(signals, stats, lengths, structural, artifact_hits, total_words):
    structural_density, structural_detail = structural
    """Cuatro señales ponderadas → bloque `score` del informe."""
    base_words = max(SCORE_BASE_WORDS, total_words, 1)
    banned_hits = len(signals["banned"])
    vocab_density = banned_hits * 1000.0 / base_words
    vocab_score = _saturate(vocab_density, 6.0)

    inside = 0
    if stats["total"] >= 4:
        inside = sum(1 for length in lengths if abs(length - stats["mean"]) <= 0.20 * stats["mean"])
        uniform_pct = 100.0 * inside / stats["total"]
    else:
        uniform_pct = 0.0
    uniform_score = round(uniform_pct, 1)

    structural_score = _saturate(structural_density, 5.0)

    artifact_density = len(artifact_hits) * 1000.0 / base_words
    artifact_score = _saturate(artifact_density, 3.0)

    total = round(
        vocab_score * PESOS["vocabulario_ia"]
        + uniform_score * PESOS["uniformidad_frases"]
        + structural_score * PESOS["patrones_estructurales"]
        + artifact_score * PESOS["artefactos_chatbot"],
        1,
    )

    return {
        "total": total,
        "nivel": _nivel(total),
        "vocabulario_ia": vocab_score,
        "uniformidad_frases": uniform_score,
        "patrones_estructurales": structural_score,
        "artefactos_chatbot": artifact_score,
        "detalle": {
            "palabras": total_words,
            "frases": stats["total"],
            "vocabulario": {
                "apariciones": banned_hits,
                "por_1000_palabras": round(vocab_density, 2),
                "terminos": sorted(set(signals["banned"])),
            },
            "uniformidad": {
                "frases_dentro_de_20pct": inside,
                "porcentaje": round(uniform_pct, 1),
                "media_palabras": round(stats["mean"], 1),
                "burstiness_cv": round(stats["cv"], 2),
            },
            "estructura": structural_detail,
            "artefactos": {
                "apariciones": len(artifact_hits),
                "por_1000_palabras": round(artifact_density, 2),
                "terminos": sorted(set(artifact_hits)),
            },
        },
    }


def _issue_list(signals, stats, repeated_starts):
    issues = []
    if stats["cv"] < 0.45 and stats["total"] >= 4:
        issues.append(
            "Burstiness baja (CV=%.2f, objetivo >= 0.45). El texto tiene un ritmo monótono propio de IA. "
            "Alterna oraciones de 4-8 palabras con subordinadas de 22+ palabras." % stats["cv"]
        )
    if stats["short"] == 0 and stats["total"] >= 3:
        issues.append("Faltan frases cortas y contundentes (<= 8 palabras) para dar impacto y dinamismo.")
    if stats["runs"] > 0:
        issues.append(
            "Se detectaron %d secuencias de 3 o más frases seguidas con longitud casi idéntica." % stats["runs"]
        )
    if signals["banned"]:
        unique_banned = sorted(set(signals["banned"]))
        issues.append(
            "Clichés o conectores IA detectados (%d): %s"
            % (len(signals["banned"]), ", ".join(unique_banned))
        )
    if signals["em_dashes"] > 0:
        issues.append(
            "Se detectaron %d guiones largos (—/–). Sustitúyelos por comas, paréntesis o punto y seguido."
            % signals["em_dashes"]
        )
    if len(signals["passive"]) >= 3:
        issues.append(
            "Abuso de voz pasiva (%d apariciones). Prefiere la voz activa en español." % len(signals["passive"])
        )
    if repeated_starts > 0:
        issues.append("Hay %d párrafos que inician con la misma palabra o conector." % repeated_starts)
    return issues


def analyze_text(text):
    masked, segments = mask_protected(text)
    clean_text = analysis_text(masked)
    if not clean_text.strip():
        return {"error": "Texto vacío o sin oraciones detectables."}

    sentences = split_sentences(clean_text)
    sentence_words = [_words(s) for s in sentences]
    lengths = [len(words) for words in sentence_words if words]

    if not lengths:
        return {"error": "No se encontraron palabras válidas en el texto."}

    total_words_count = sum(lengths)
    total_sentences_count = len(lengths)
    lower_text = clean_text.lower()

    stats = _sentence_stats(lengths)
    signals = _text_signals(clean_text, lower_text)

    structural_density, structural_detail = _structural_signals(clean_text)

    artifact_hits = []
    for pattern in CHATBOT_ARTIFACTS:
        artifact_hits.extend(re.findall(pattern, lower_text, re.I))

    score = _score_block(signals, stats, lengths, (structural_density, structural_detail),
                         artifact_hits, total_words_count)

    repeated_starts = _repeated_starts(clean_text)
    issues = _issue_list(signals, stats, repeated_starts)

    protected_counts = {"code_block": 0, "inline_code": 0, "enlace": 0, "frontmatter": 0}
    for seg in segments:
        protected_counts[seg["tipo"]] = protected_counts.get(seg["tipo"], 0) + 1

    return {
        "total_sentences": total_sentences_count,
        "total_words": total_words_count,
        "sentence_lengths": lengths,
        "mean_length": round(stats["mean"], 1),
        "std_dev": round(stats["std"], 2),
        "burstiness_cv": round(stats["cv"], 2),
        "lexical_diversity_ttr": round(signals["ttr"], 2),
        "readability_score": _readability_score(
            signals["words"], total_words_count, total_sentences_count
        ),
        "short_sentences": stats["short"],
        "long_sentences": stats["long"],
        "banned_phrases_count": len(signals["banned"]),
        "banned_phrases": sorted(set(signals["banned"])),
        "em_dashes_count": signals["em_dashes"],
        "passive_voice_count": len(signals["passive"]),
        "protected_segments": protected_counts,
        "datos_a_verificar": detect_data_to_verify(text),
        "score": score,
        "passed": len(issues) == 0,
        "issues": issues,
    }


def score_text(text):
    """Devuelve solo el bloque de puntuación (más los datos a verificar)."""
    report = analyze_text(text)
    if "error" in report:
        return {"error": report["error"]}
    result = dict(report["score"])
    result["datos_a_verificar"] = report["datos_a_verificar"]
    return result


def format_markdown(report: dict) -> str:
    status = "APROBADO" if report["passed"] else "REQUIERE REESCRITURA"
    score = report.get("score", {})
    lines = [
        "# Auditoría Estilística Anti-IA",
        "",
        f"- **Estado general:** `{status}`",
        f"- **Puntuación IA (0-100, más alto = más IA):** **{score.get('total', '—')}** — nivel `{score.get('nivel', '—')}`",
        f"- **Burstiness (Coef. Variación):** **{report['burstiness_cv']}** (Recomendado: ≥ 0.45)",
        f"- **Oraciones analizadas:** {report['total_sentences']} (Media: {report['mean_length']} palabras)",
        f"- **Frases cortas (≤8 palabras):** {report['short_sentences']} | **Frases largas (≥22 palabras):** {report['long_sentences']}",
        "",
        "## Puntuación por señal",
        "",
        "| Señal | Puntuación 0-100 | Peso | Qué mide |",
        "|---|---|---|---|",
        f"| Vocabulario IA | {score.get('vocabulario_ia', '—')} | 30% | Clichés por cada 1000 palabras |",
        f"| Uniformidad de frases | {score.get('uniformidad_frases', '—')} | 25% | % de frases dentro de ±20% de la media |",
        f"| Patrones estructurales | {score.get('patrones_estructurales', '—')} | 30% | Tríadas, «no solo X sino Y», cierres, listas simétricas |",
        f"| Artefactos de chatbot | {score.get('artefactos_chatbot', '—')} | 15% | «Como modelo de lenguaje», «espero que te ayude» |",
        "",
        "> Más alto = más señales de IA. Un texto humano con registro informal suele quedar por debajo de 25.",
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

    findings = report.get("datos_a_verificar", [])
    lines.extend(["", "## Datos a Verificar (no reescribir)", ""])
    if not findings:
        lines.append("No se detectaron estadísticas ni atribuciones sin fuente en el texto.")
    else:
        lines.append("| Fragmento | Tipo | Detalle | Acción |")
        lines.append("|---|---|---|---|")
        for item in findings:
            safe = item["texto"].replace("|", "\\|")
            lines.append(f"| {safe} | {item['tipo']} | `{item['detalle']}` | {item['accion']} |")

    protegidos = report.get("protected_segments", {})
    lines.extend([
        "",
        "## Contenido protegido (intacto)",
        "",
        f"- Bloques de código: {protegidos.get('code_block', 0)} · Código en línea: {protegidos.get('inline_code', 0)} · "
        f"Enlaces: {protegidos.get('enlace', 0)} · Frontmatter: {protegidos.get('frontmatter', 0)}",
    ])

    return "\n".join(lines)


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (AttributeError, ValueError, OSError):
                pass

    parser = argparse.ArgumentParser(
        description=(
            "Audita textos en español contra patrones de escritura IA. "
            "La puntuación va de 0 a 100 y MÁS ALTO SIGNIFICA MÁS IA."
        ),
        epilog=(
            "Ejemplos: py scripts/audit_style.py --file texto.md --score | "
            "py scripts/audit_style.py --text \"...\" --markdown"
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Texto directo a evaluar")
    group.add_argument("--file", type=str, help="Ruta a archivo .txt o .md a evaluar")
    parser.add_argument("--json", action="store_true", help="Salida JSON del análisis completo")
    parser.add_argument("--markdown", action="store_true", help="Salida Markdown lista para el informe")
    parser.add_argument(
        "--score",
        action="store_true",
        help=(
            "Imprime JSON con la puntuación 0-100 (más alto = más IA): total, "
            "vocabulario_ia, uniformidad_frases, patrones_estructurales, artefactos_chatbot"
        ),
    )
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

    if args.score:
        payload = dict(report["score"])
        payload["datos_a_verificar"] = report["datos_a_verificar"]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(0 if report["passed"] else 2)

    if args.markdown:
        print(format_markdown(report))
        sys.exit(0 if report["passed"] else 2)

    print("=== AUDITORÍA ESTILÍSTICA ANTI-IA ===")
    print(f"Oraciones: {report['total_sentences']} | Palabras: {report['total_words']}")
    print(f"Media de longitud: {report['mean_length']} palabras | Desv. Estándar: {report['std_dev']}")
    print(f"Frases cortas (<=8w): {report['short_sentences']} | Frases largas (>=22w): {report['long_sentences']}")
    print(f"Guiones largos: {report['em_dashes_count']} | Construcciones pasivas: {report['passive_voice_count']}")
    score = report["score"]
    print(f"Puntuación IA (0-100, más alto = más IA): {score['total']} ({score['nivel']})")
    print(
        "  vocabulario=%s | uniformidad=%s | estructura=%s | artefactos=%s"
        % (
            score["vocabulario_ia"],
            score["uniformidad_frases"],
            score["patrones_estructurales"],
            score["artefactos_chatbot"],
        )
    )
    if report["datos_a_verificar"]:
        print(f"Datos a verificar: {len(report['datos_a_verificar'])} (ver --markdown)")

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
