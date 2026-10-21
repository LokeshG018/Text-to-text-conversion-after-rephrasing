"""Prompt engineering: dynamic instruction templates per rewriting style."""

STYLE_INSTRUCTIONS = {
    "standard": "Rephrase the following text while preserving its original meaning. "
                "Change the wording and sentence structure, and avoid unnecessary changes.",
    "professional": "Rephrase the following text while preserving its original meaning. "
                    "Use a professional tone, improve clarity, and avoid unnecessary changes.",
    "simple": "Rewrite the following text in simple, plain English that is easy to understand. "
              "Use short sentences and common words, and keep the original meaning.",
    "academic": "Rewrite the following text using formal academic language. Preserve the original meaning, "
                "improve grammatical structure and vocabulary, and avoid introducing new information.",
    "creative": "Rewrite the following text in a creative, vivid and engaging way. "
                "Keep the original meaning and do not add new facts.",
    "formal": "Rewrite the following text in a formal tone suitable for official communication. "
              "Avoid contractions and slang, and preserve the original meaning.",
    "casual": "Rewrite the following text in a relaxed, casual and conversational tone. "
              "Keep the original meaning.",
    "concise": "Rewrite the following text in fewer words. Remove redundancy but keep every key fact "
               "and the original meaning.",
    "expand": "Rewrite the following text with more detail and clearer explanation. "
              "Elaborate on the ideas without changing the original meaning.",
}

STYLE_DESCRIPTIONS = {
    "standard": "Balanced paraphrase", "professional": "Clear, business-ready tone",
    "simple": "Plain, easy words", "academic": "Scholarly vocabulary",
    "creative": "Vivid and expressive", "formal": "Official, no contractions",
    "casual": "Conversational", "concise": "Shorter, same meaning", "expand": "More detail",
}


def build_prompt(text: str, style: str = "standard") -> str:
    instruction = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["standard"])
    return f"{instruction}\n\nText: {text}"
