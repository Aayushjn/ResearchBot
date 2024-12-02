from datetime import timedelta
from os import getenv

import google.generativeai as genai
from google.api_core.exceptions import PermissionDenied


DEFAULT_GEMINI_MODEL = "gemini-1.5-flash-002"
DEFAULT_EMBEDDING_MODEL = "models/text-embedding-004"


def configure_llm():
    genai.configure(api_key=getenv("GEMINI_API_KEY"))


def create_llm(system_instruction: str, model_name: str = DEFAULT_GEMINI_MODEL) -> genai.GenerativeModel:
    return genai.GenerativeModel(
        model_name=model_name,
        generation_config=genai.GenerationConfig(temperature=0.4),
        system_instruction=system_instruction,
    )


def create_llm_from_cache(
    cache_name: str,
    system_instruction: str,
    cache_content: list[genai.types.ContentsType],
    model_name: str = DEFAULT_GEMINI_MODEL,
):
    try:
        cache = genai.caching.CachedContent.get(cache_name)
    except PermissionDenied:
        cache = genai.caching.CachedContent.create(
            model=model_name,
            display_name=cache_name,
            system_instruction=system_instruction,
            contents=cache_content,
            ttl=timedelta(hours=1),
        )

    return genai.GenerativeModel.from_cached_content(cache, generation_config=genai.GenerationConfig(temperature=0.4))
