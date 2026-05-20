class LLMClient:
    """Placeholder adapter for a future LLM provider integration."""

    def generate(self, prompt: str) -> str:
        """Reserve the LLM call boundary without binding v1 to a provider."""
        raise NotImplementedError("LLM provider integration is not implemented in v1.")
