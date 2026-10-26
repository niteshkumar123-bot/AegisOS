from app.config import get_settings
from app.providers.mock import MockProvider

def get_provider():
    name=get_settings().llm_provider.lower()
    if name == "mock": return MockProvider()
    if name == "openai":
        from app.providers.openai_provider import OpenAIProvider
        return OpenAIProvider()
    raise RuntimeError(f"Unsupported LLM_PROVIDER: {name}")
