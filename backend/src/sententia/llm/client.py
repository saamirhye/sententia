from functools import lru_cache

import anthropic

from sententia.config import ANTHROPIC_API_KEY


@lru_cache(maxsize=1)
def get_client() -> anthropic.Anthropic:
    """Shared Anthropic client, constructed with an explicit api_key so a
    missing/invalid key fails predictably here rather than depending on
    ambient CLI/OAuth credential resolution. Cached so repeated calls reuse
    one client instead of reconstructing per call."""
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
