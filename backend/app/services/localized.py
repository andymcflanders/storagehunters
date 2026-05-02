"""Helpers for picking a language from a translations dict."""

from collections.abc import Mapping


def localized(
    translations: Mapping[str, str] | None,
    language: str | None,
    default_language: str = "en",
) -> str | None:
    """Return the translation for the user's language, or a fallback.

    Order:
      1. Exact match on the user's language.
      2. Fallback to default_language.
      3. Any value that's present, if neither of the above exists.
      4. None when the dict is empty/missing.

    Used both to resolve ai_names/ai_descriptions for API responses and
    to pick a single string for downstream consumers (printers, label
    summaries, Home Assistant search) that don't speak multilingual.
    """
    if not translations:
        return None
    if language and (value := translations.get(language)):
        return value
    if default_value := translations.get(default_language):
        return default_value
    for value in translations.values():
        if value:
            return value
    return None
