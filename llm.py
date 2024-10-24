from os import getenv

from langchain_google_genai import ChatGoogleGenerativeAI


DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
DEFAULT_EMBEDDING_MODEL = "models/text-embedding-004"


def create_llm(model_name: str = DEFAULT_GEMINI_MODEL) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=model_name, temperature=0.4, api_key=getenv("GEMINI_API_KEY"))
