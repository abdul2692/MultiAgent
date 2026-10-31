"""
utils/llm_factory.py
─────────────────────────────────────────────────────────────────────────────
LLM Factory — returns the correct LLM based on environment.

CLOUD_MODE=true  → Groq API (free tier, llama-3.1-8b-instant, no local GPU needed)
CLOUD_MODE=false → Ollama (local, 100% private, requires installed Ollama server)

Every agent imports get_llm() from here instead of directly constructing ChatOllama.
This single toggle lets the SAME codebase run locally AND on Streamlit Community Cloud.
─────────────────────────────────────────────────────────────────────────────
"""
import os
import logging

logger = logging.getLogger("multi_agent.utils.llm_factory")


def is_cloud_mode() -> bool:
    """
    Returns True when CLOUD_MODE env var (or Streamlit secret) is 'true'.
    Checks both os.environ AND st.secrets (if Streamlit is running).
    """
    # First check environment variable
    env_val = os.getenv("CLOUD_MODE", "false").lower()
    if env_val == "true":
        return True

    # Then check Streamlit secrets (only available when running inside Streamlit)
    try:
        import streamlit as st
        secret_val = st.secrets.get("CLOUD_MODE", "false")
        return str(secret_val).lower() == "true"
    except Exception:
        pass

    return False


def get_llm(temperature: float = 0.2):
    """
    Returns the appropriate LLM instance based on deployment environment.

    Local mode  → ChatOllama (llama3.2:1b, runs entirely on your machine)
    Cloud mode  → ChatGroq  (llama-3.1-8b-instant, Groq free API, ~300 req/day)

    Usage in any agent:
        from utils.llm_factory import get_llm
        llm = get_llm()
    """
    if is_cloud_mode():
        return _get_groq_llm(temperature)
    else:
        return _get_ollama_llm(temperature)


def _get_ollama_llm(temperature: float):
    """Local Ollama LLM — starts Ollama server automatically if needed."""
    from langchain_ollama import ChatOllama
    from utils.ollama_manager import ensure_ollama_running

    ensure_ollama_running()

    model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

    logger.info(f"[LLM Factory] Using LOCAL Ollama: model={model}, url={base_url}")
    return ChatOllama(model=model, base_url=base_url, temperature=temperature)


def _get_groq_llm(temperature: float):
    """Cloud Groq LLM — free tier, no credit card for basic use."""
    try:
        from langchain_groq import ChatGroq
    except ImportError:
        raise ImportError(
            "langchain-groq is not installed. Run: pip install langchain-groq"
        )

    # Load API key: prefer Streamlit secrets, fallback to env var
    api_key = _load_groq_api_key()

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    logger.info(f"[LLM Factory] Using CLOUD Groq: model={model}")

    return ChatGroq(
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=2048,
    )


def _load_groq_api_key() -> str:
    """Loads Groq API key from Streamlit secrets or environment variable."""
    # Try Streamlit secrets first (Streamlit Community Cloud)
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass

    # Fallback to environment variable (local .env file)
    key = os.getenv("GROQ_API_KEY", "")
    if key:
        return key

    raise ValueError(
        "GROQ_API_KEY not found. Set it in:\n"
        "  • Streamlit Cloud: App Settings → Secrets\n"
        "  • Local: Add GROQ_API_KEY=gsk_... to your .env file"
    )

