"""
Free AI Helper - Uses Gemini (1M tokens/day free) + Groq fallback.

Imports of `google.generativeai` and `openai` are done lazily inside
``_init_clients`` so that the module can be imported even when those
optional dependencies are not installed (e.g. in unit-test environments).
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

from src.utils.logger import get_logger
from src.utils.sanitizer import sanitize

log = get_logger("ai")


class FreeAIHelper:
    """Multi-provider free AI helper with automatic fallback."""

    def __init__(self):
        self.gemini = None
        self.groq = None
        self._genai = None  # cached google.generativeai module
        self._init_clients()

    # ------------------------------------------------------------------ #
    # Initialisation
    # ------------------------------------------------------------------ #
    def _init_clients(self):
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key:
            try:
                import google.generativeai as genai  # type: ignore

                genai.configure(api_key=gemini_key)
                self.gemini = genai.GenerativeModel("gemini-1.5-flash")
                self._genai = genai
                log.info("Gemini client initialised")
            except ImportError:
                log.warning("google-generativeai not installed; Gemini disabled")
            except Exception as exc:  # noqa: BLE001
                log.error("Gemini init failed: %s", sanitize(exc))

        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            try:
                from openai import OpenAI  # type: ignore

                self.groq = OpenAI(
                    api_key=groq_key,
                    base_url="https://api.groq.com/openai/v1",
                )
                log.info("Groq client initialised")
            except ImportError:
                log.warning("openai not installed; Groq disabled")
            except Exception as exc:  # noqa: BLE001
                log.error("Groq init failed: %s", sanitize(exc))

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = False,
        max_retries: int = 3,
    ) -> str:
        errors: list[str] = []

        if self.gemini:
            for attempt in range(max_retries):
                try:
                    return self._call_gemini(prompt, system, json_mode)
                except Exception as exc:  # noqa: BLE001
                    err = f"Gemini attempt {attempt + 1}: {sanitize(exc)}"
                    errors.append(err)
                    log.warning("%s", err)
                    time.sleep(2 ** attempt)

        if self.groq:
            for attempt in range(max_retries):
                try:
                    return self._call_groq(prompt, system, json_mode)
                except Exception as exc:  # noqa: BLE001
                    err = f"Groq attempt {attempt + 1}: {sanitize(exc)}"
                    errors.append(err)
                    log.warning("%s", err)
                    time.sleep(2 ** attempt)

        try:
            return self._call_jina(prompt)
        except Exception as exc:  # noqa: BLE001
            err = f"Jina: {sanitize(exc)}"
            errors.append(err)
            log.error("%s", err)

        raise RuntimeError(f"All free APIs failed: {'; '.join(errors)}")

    def generate_survey_answers(
        self, survey_questions: str, persona: Optional[str] = None
    ) -> Dict[str, Any]:
        system = (
            "You are a survey response generator. Generate realistic, consistent answers.\n"
            "Rules: Be consistent, avoid extremes, mix response patterns, use realistic demographics.\n"
            'Return JSON: {"answers": [{"question": "...", "answer": "..."}]}'
        )
        persona_text = f"\nPersona: {persona}" if persona else ""
        prompt = (
            f"Generate survey answers:{persona_text}\n\n"
            f"Questions:\n{survey_questions}\n\n"
            "Return JSON format only."
        )
        result = self.generate(prompt=prompt, system=system, json_mode=True)
        return json.loads(result)

    # ------------------------------------------------------------------ #
    # Provider calls
    # ------------------------------------------------------------------ #
    def _call_gemini(self, prompt: str, system: Optional[str], json_mode: bool) -> str:
        if not self._genai:
            raise RuntimeError("Gemini module not initialised")
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        kwargs: Dict[str, Any] = {"temperature": 0.3, "max_output_tokens": 8192}
        if json_mode:
            kwargs["response_mime_type"] = "application/json"
        generation_config = self._genai.GenerationConfig(**kwargs)
        response = self.gemini.generate_content(
            full_prompt, generation_config=generation_config
        )
        return response.text

    def _call_groq(self, prompt: str, system: Optional[str], json_mode: bool) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response_format = {"type": "json_object"} if json_mode else None
        response = self.groq.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages,
            response_format=response_format,
            temperature=0.3,
            max_tokens=8192,
        )
        return response.choices[0].message.content

    def _call_jina(self, prompt: str) -> str:
        import requests  # local import: only needed for the Jina fallback

        url = "https://api.jina.ai/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "jina-deepsearch-v1",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------- #
# Singleton accessor
# ---------------------------------------------------------------------- #
_ai_helper: Optional[FreeAIHelper] = None


def get_ai_helper() -> FreeAIHelper:
    global _ai_helper
    if _ai_helper is None:
        _ai_helper = FreeAIHelper()
    return _ai_helper
