"""Explainability + text analytics (pure Python, no heavy models).

diff_words      -> which words changed (highlighting)
explain         -> what changed / structure change / meaning preserved
text_stats      -> counts + readability (Flesch)
detect_tone     -> lexicon-based tone detection
grammar_fix     -> light rule-based grammar correction
"""
import difflib
import re

TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?|[^\sA-Za-z0-9]")
PUNCT_RE = re.compile(r"^[^\w\s]$")


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def _words(text: str) -> list[str]:
    return [t.lower() for t in tokens(text) if not PUNCT_RE.match(t)]


def lexical_change(a: str, b: str) -> float:
    """0 = identical wording, 1 = completely different wording."""
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return 0.0
    return 1.0 - difflib.SequenceMatcher(a=wa, b=wb, autojunk=False).ratio()


def diff_words(original: str, rephrased: str) -> dict:
    a, b = tokens(original), tokens(rephrased)
    sm = difflib.SequenceMatcher(a=[x.lower() for x in a], b=[x.lower() for x in b], autojunk=False)
    orig_t, new_t, changes = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        A, B = a[i1:i2], b[j1:j2]
        if tag == "equal":
            orig_t += [{"t": x, "type": "equal"} for x in A]
            new_t += [{"t": x, "type": "equal"} for x in B]
            continue
        orig_t += [{"t": x, "type": "removed"} for x in A]
        new_t += [{"t": x, "type": "added"} for x in B]
        kind = {"replace": "replace", "delete": "remove", "insert": "add"}[tag]
        changes.append({"type": kind, "from": " ".join(A), "to": " ".join(B)})
    return {"original_tokens": orig_t, "rephrased_tokens": new_t, "changes": changes}


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def structure_analysis(original: str, rephrased: str) -> dict:
    wa, wb = _words(original), _words(rephrased)
    order_sim = difflib.SequenceMatcher(a=wa, b=wb, autojunk=False).ratio() if wa and wb else 1.0
    sa, sb = _sentences(original), _sentences(rephrased)
    avg_a = len(wa) / max(1, len(sa))
    avg_b = len(wb) / max(1, len(sb))
    notes = []
    if len(sa) != len(sb):
        notes.append(f"Sentence count changed from {len(sa)} to {len(sb)}")
    if abs(avg_a - avg_b) >= 3:
        notes.append(f"Average sentence length changed from {avg_a:.1f} to {avg_b:.1f} words")
    if len(wb) < len(wa) * 0.8:
        notes.append("The text became shorter")
    elif len(wb) > len(wa) * 1.2:
        notes.append("The text became longer")
    changed = order_sim < 0.75 or bool(notes)
    if order_sim < 0.75:
        notes.append("Word order / phrasing was substantially reorganised")
    if not notes:
        notes.append("Sentence structure is largely unchanged")
    return {"word_order_similarity": round(order_sim, 3), "structure_changed": changed, "notes": notes}


def explain(original: str, rephrased: str, similarity: float) -> dict:
    diff = diff_words(original, rephrased)
    replaced = [c for c in diff["changes"] if c["type"] == "replace"]
    added = [c["to"] for c in diff["changes"] if c["type"] == "add"]
    removed = [c["from"] for c in diff["changes"] if c["type"] == "remove"]
    structure = structure_analysis(original, rephrased)
    preserved = similarity >= 0.80
    label = ("Meaning preserved" if preserved else
             "Meaning mostly preserved" if similarity >= 0.70 else "Meaning may have changed")
    summary = (f"{len(replaced)} replacement(s), {len(added)} addition(s), {len(removed)} deletion(s). "
               f"{structure['notes'][0]}. {label} ({similarity * 100:.0f}% semantic similarity).")
    return {
        "changes": diff["changes"][:25], "replaced": replaced[:20], "added": added[:20], "removed": removed[:20],
        "structure": structure, "meaning_preserved": preserved, "meaning_label": label,
        "similarity_percent": round(similarity * 100, 1), "summary": summary,
    }


# ---------------- statistics & readability ----------------
def count_syllables(word: str) -> int:
    word = word.lower()
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return 0
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups)
    if word.endswith("e") and not word.endswith("le") and n > 1:
        n -= 1
    return max(1, n)


def readability(text: str) -> dict:
    words = _words(text)
    sents = max(1, len(_sentences(text)))
    if not words:
        return {"flesch_reading_ease": 0, "grade_level": 0, "label": "n/a"}
    syl = sum(count_syllables(w) for w in words)
    wps, spw = len(words) / sents, syl / len(words)
    ease = 206.835 - 1.015 * wps - 84.6 * spw
    grade = 0.39 * wps + 11.8 * spw - 15.59
    bands = [(90, "Very easy"), (80, "Easy"), (70, "Fairly easy"), (60, "Standard"),
             (50, "Fairly difficult"), (30, "Difficult"), (-1000, "Very difficult")]
    label = next(l for t, l in bands if ease >= t)
    return {"flesch_reading_ease": round(ease, 1), "grade_level": round(max(grade, 0), 1), "label": label}


def text_stats(text: str) -> dict:
    words = _words(text)
    sents = _sentences(text)
    return {
        "characters": len(text), "words": len(words), "sentences": len(sents),
        "avg_word_length": round(sum(map(len, words)) / len(words), 2) if words else 0,
        "avg_sentence_length": round(len(words) / max(1, len(sents)), 1),
        "unique_words": len(set(words)),
        "reading_time_sec": round(len(words) / 200 * 60),
        "readability": readability(text), "tone": detect_tone(text),
    }


# ---------------- tone detection ----------------
FORMAL = {"therefore", "furthermore", "moreover", "consequently", "regarding", "utilize", "approximately",
          "thus", "hence", "whereas", "accordingly", "commence", "facilitate", "additionally", "subsequently",
          "demonstrate", "enhance", "ensure", "pursuant", "nevertheless"}
CASUAL = {"gonna", "wanna", "kinda", "hey", "yeah", "stuff", "cool", "awesome", "really", "pretty", "guys",
          "okay", "ok", "super", "lots", "bunch", "totally", "basically", "anyway", "btw", "thanks"}
ACADEMIC = {"hypothesis", "analysis", "empirical", "significant", "literature", "framework", "methodology",
            "paradigm", "thereby", "examine", "investigate", "findings", "evidence", "furthermore",
            "theoretical", "demonstrates", "indicates", "variables", "correlation", "approach"}


def detect_tone(text: str) -> dict:
    words = _words(text)
    if not words:
        return {"label": "neutral", "scores": {}}
    n = len(words)
    contractions = len(re.findall(r"\b\w+'(?:t|s|re|ll|ve|d|m)\b", text.lower()))
    scores = {
        "formal": sum(w in FORMAL for w in words) / n * 10,
        "casual": (sum(w in CASUAL for w in words) + contractions + text.count("!")) / n * 10,
        "academic": sum(w in ACADEMIC for w in words) / n * 10,
    }
    top = max(scores, key=scores.get)
    label = top if scores[top] >= 0.4 else "neutral"
    return {"label": label, "scores": {k: round(v, 2) for k, v in scores.items()}}


# ---------------- grammar correction (rule-based) ----------------
def grammar_fix(text: str) -> tuple[str, list[str]]:
    fixes, out = [], text
    new = re.sub(r"\s+([.,!?;:])", r"\1", out)
    if new != out:
        fixes.append("removed space before punctuation"); out = new
    new = re.sub(r"([.,!?;:])(?=[A-Za-z])", r"\1 ", out)
    if new != out:
        fixes.append("added space after punctuation"); out = new
    new = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", out, flags=re.I)
    if new != out:
        fixes.append("removed repeated words"); out = new
    new = re.sub(r"\bi\b", "I", out)
    if new != out:
        fixes.append("capitalised pronoun 'I'"); out = new
    new = re.sub(r"\b([Aa])\s+(?!uni|use|eur|one|ubiq|ut)([aeiouAEIOU]\w*)", lambda m: f"{m.group(1)}n {m.group(2)}", out)
    if new != out:
        fixes.append("a -> an before vowel"); out = new
    new = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), out)
    if new != out:
        fixes.append("capitalised sentence start"); out = new
    new = re.sub(r"\s{2,}", " ", out).strip()
    if new != out:
        fixes.append("collapsed whitespace"); out = new
    return out, fixes
