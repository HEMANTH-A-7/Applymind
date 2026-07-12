"""
Shared Groq client + robust JSON-output helper.

Every agent that asks Groq for JSON goes through chat_json() so that:
  • a missing GROQ_API_KEY produces one clear error instead of a cryptic 401/500
  • markdown fences, chatter before/after the JSON, and truncated output
    are handled (extract → repair → retry) instead of crashing json.loads
  • Groq's native JSON mode (response_format=json_object) is used when possible
"""
import json
import re
from typing import Optional

from loguru import logger

from core.config import get_settings

_client = None


class GroqNotConfiguredError(RuntimeError):
    """Raised when GROQ_API_KEY is missing so routes can return a clear 503."""


def get_client():
    """Lazily build a singleton Groq client; fail loudly if key is missing."""
    global _client
    settings = get_settings()
    if not settings.groq_api_key or settings.groq_api_key == "your_groq_api_key_here":
        raise GroqNotConfiguredError(
            "GROQ_API_KEY is not configured. Add it to backend/.env "
            "(free key: https://console.groq.com/keys) and restart the backend."
        )
    if _client is None:
        from groq import Groq
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def extract_json(content: str):
    """Parse JSON out of an LLM reply that may have fences/chatter/truncation."""
    text = content.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Slice out the outermost object or array
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start, end = text.find(open_c), text.rfind(close_c)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue

    # Truncated output: close unterminated string, then close open brackets
    start = text.find("{")
    if start != -1:
        fragment = text[start:]
        if fragment.count('"') % 2 == 1:
            fragment += '"'
        fragment = re.sub(r",\s*$", "", fragment)
        stack = []
        in_str = escape = False
        for ch in fragment:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = in_str
                continue
            if ch == '"':
                in_str = not in_str
            elif not in_str:
                if ch in "{[":
                    stack.append("}" if ch == "{" else "]")
                elif ch in "}]" and stack:
                    stack.pop()
        repaired = fragment + "".join(reversed(stack))
        return json.loads(repaired)  # raises JSONDecodeError if still broken

    raise json.JSONDecodeError("No JSON object found in model output", content, 0)


def chat_json(
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int = 4000,
    json_mode: bool = True,
    retries: int = 1,
    model: Optional[str] = None,
):
    """
    Call Groq chat completions and return parsed JSON (dict or list).

    json_mode uses Groq's response_format=json_object (objects only — pass
    json_mode=False when the prompt asks for a bare JSON array).
    Retries once on parse failure with a stricter instruction.
    """
    client = get_client()
    settings = get_settings()
    model = model or settings.groq_model

    last_error: Exception = RuntimeError("chat_json: no attempts made")
    for attempt in range(retries + 1):
        kwargs = dict(
            model=model,
            messages=messages,
            temperature=temperature if attempt == 0 else 0.0,
            max_tokens=max_tokens,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = client.chat.completions.create(**kwargs)
        except Exception as e:
            # Older models/params may reject response_format — retry without it
            if json_mode and "response_format" in str(e):
                json_mode = False
                response = client.chat.completions.create(
                    **{k: v for k, v in kwargs.items() if k != "response_format"}
                )
            else:
                raise

        content = response.choices[0].message.content or ""
        try:
            return extract_json(content)
        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"[groq_llm] JSON parse failed (attempt {attempt + 1}): {e}")
            if attempt < retries:
                messages = messages + [
                    {"role": "assistant", "content": content[:2000]},
                    {"role": "user", "content": "That was not valid JSON. Return the complete response again as ONLY valid, well-formed JSON with no other text."},
                ]

    raise last_error
