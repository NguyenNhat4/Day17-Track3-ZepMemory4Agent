"""Thin OpenAI wrapper for the demo UI chat reply.

This is the ONLY place the lab calls a generative LLM. Benchmark scoring never
uses an LLM (see LAB.md): retrieval evidence is graded deterministically. Here
OpenAI only turns retrieved memory context into a grounded assistant reply so
the mini-product feels real.

Default model: gpt-4.1-mini (override with OPENAI_MODEL).
"""

from __future__ import annotations

from .config import settings

SYSTEM_INSTRUCTION = (
    "You are the assistant of a personal memory agent for VinUni Lab 17. "
    "Answer the user grounded ONLY in the retrieved memory context provided. "
    "If the context does not contain the answer, say so plainly instead of "
    "inventing facts. Be concise and cite the concrete markers/ids you used. "
    "You may reply in the user's language (Vietnamese or English)."
)


def openai_available() -> bool:
    """True when a key is configured. UI uses this to show status."""
    return bool(settings.openai_api_key)


def _to_messages(history: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep only valid chat roles and non-empty messages for OpenAI."""
    messages: list[dict[str, str]] = []
    for msg in history:
        role = msg.get("role")
        text = msg.get("content", "")
        if role not in {"user", "assistant"} or not text:
            continue
        messages.append({"role": role, "content": text})
    return messages


def generate_reply(
    memory_context: str,
    history: list[dict[str, str]],
    user_message: str,
    *,
    model: str | None = None,
) -> str:
    """Generate a grounded assistant reply with OpenAI.

    Raises RuntimeError if no key, and lets SDK/network errors bubble up so the
    UI can surface them. `history` should include the latest user turn or not —
    `user_message` is appended as the final user turn regardless.
    """
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Copy .env.example to .env and add an "
            "OpenAI API key to enable chat replies."
        )

    # Lazy import so the rest of the package works without openai installed
    # (tests, report generation, retrieval benchmarks never need it).
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    model_name = model or settings.openai_model

    grounding = (
        "Retrieved memory context for this turn:\n"
        "-------------------------------------\n"
        f"{memory_context.strip() or '(no memory retrieved)'}\n"
        "-------------------------------------\n\n"
        f"User message: {user_message}"
    )

    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        *_to_messages(history),
        {"role": "user", "content": grounding},
    ]

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.3,
        max_tokens=800,
    )
    return (response.choices[0].message.content or "").strip()
