"""Fast tests that need no ML model downloads:  pytest -q"""
from app.services import analysis_service as a
from app.services.preprocessing import chunk_sentences, clean_text
from app.services.prompt_service import build_prompt


def test_clean_text():
    assert clean_text("Hello   world ! ") == "Hello world!"


def test_chunking():
    text = " ".join(["This is a sentence with several words in it."] * 30)
    assert len(chunk_sentences(text, max_words=40)) > 1


def test_prompt_styles():
    assert "academic" in build_prompt("x", "academic").lower()
    assert build_prompt("hello", "standard").endswith("Text: hello")


def test_explain_detects_replacements():
    o = "Students use technology to improve their learning."
    r = "Technology helps students enhance their learning experience."
    e = a.explain(o, r, 0.92)
    assert e["meaning_preserved"] and e["similarity_percent"] == 92.0
    assert e["structure"]["structure_changed"]


def test_lexical_change_bounds():
    assert a.lexical_change("same text here", "same text here") == 0
    assert a.lexical_change("alpha beta gamma", "one two three") == 1


def test_grammar_and_tone():
    fixed, fixes = a.grammar_fix("i went to a apple store  . it was cool")
    assert fixed.startswith("I") and "an apple" in fixed
    assert a.detect_tone("Furthermore, we therefore demonstrate the findings.")["label"] in ("formal", "academic")
