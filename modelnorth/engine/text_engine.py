"""ModelNorth HyperBrowser: Text Generation Engine for Form Values."""

from __future__ import annotations

import re

import httpx


class TextGenerationEngine:
    """Extracts or generates required field input strings with zero or minimal latency."""

    def __init__(
        self,
        api_base: str = "http://localhost:11434/v1",
        model_name: str = "qwen2.5-coder:1.5b",
        api_key: str = "ollama",
    ) -> None:
        self.api_base = api_base
        self.model_name = model_name
        self.api_key = api_key
        self._http_client = httpx.AsyncClient(timeout=5.0)

    async def generate_text(self, field_name: str, goal: str) -> str:
        """Generates target input string using fast regex heuristics or local LLM."""
        field_lower = field_name.lower()

        # 1. Fast-Path Heuristic Extraction (< 1 ms)
        if "from" in field_lower or "origin" in field_lower or "where from" in field_lower:
            m = re.search(r"from\s+([A-Za-z0-9\(\)\s]+?)(?:\s+to|\s+on|\s+for|\.|$)", goal, re.IGNORECASE)
            if m:
                return m.group(1).strip()

        if "to" in field_lower or "destination" in field_lower or "where to" in field_lower or "where else" in field_lower:
            m = re.search(r"to\s+([A-Za-z0-9\(\)\s]+?)(?:\s+on|\s+for|\s+from|\.|$)", goal, re.IGNORECASE)
            if m:
                return m.group(1).strip()

        if "date" in field_lower or "departure" in field_lower:
            m = re.search(r"(?:on|date)\s+([A-Za-z0-9,\s]+?)(?:\s+for|\s+in|\.|$)", goal, re.IGNORECASE)
            if m:
                return m.group(1).strip()

        # 2. Local LLM Generation via Ollama / vLLM (30–60 ms)
        try:
            prompt = f"Goal: {goal}\nField Name: {field_name}\nRespond ONLY with the exact text string to type into this field. No quotes or explanations."
            response = await self._http_client.post(
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 30,
                },
            )
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                return content.strip("\"'")
        except Exception:
            pass

        # Fallback: simple token extract
        return goal.split()[-1] if goal else ""
