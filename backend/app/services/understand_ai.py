"""Optional OpenRouter rewrite. The analysis service remains the source of the numbers."""

from __future__ import annotations

import json

import httpx

from app.core.config import Settings
from app.services.understand import compact_evidence

SYSTEM_PROMPT = (
    "You explain one EarthTrend Myanmar investigation for a non-expert. "
    "Use only the JSON evidence in the user message, including authoritative_explanation. "
    "Rephrase that evidence in plain language. "
    "Do not invent measurements, p-values, confidence intervals, sample sizes, dataset names, or citations. "
    "Do not give a physical, agricultural, health, or economic cause for the trend. "
    "Do not say a non-significant result means the climate did not change. "
    "Do not say two regions, or two variables, differ significantly. The evidence has no between-region test. "
    "Separate the calculated result from your interpretation. "
    "If the evidence cannot answer, say what is missing. "
    "Name the data source only as it appears in the evidence. "
    "Write plain sentences, without markdown. "
    "Keep the reply under 180 words."
)


def answer_question(
    settings: Settings,
    context: dict,
    explanation: dict,
    question: str,
    history: list[dict],
    evidence: dict | None = None,
) -> dict:
    if not settings.understand_ai_api_key.strip():
        return {
            "ai_available": False,
            "answer": None,
            "notice": "AI explanations are not configured. The calculated explanation is still available.",
        }
    packet = evidence if evidence is not None else compact_evidence(context, explanation)
    payload = {
        "model": settings.understand_ai_model,
        "temperature": 0.2,
        "max_tokens": 800,
        "reasoning": {"enabled": False},
        "messages": _messages(history, json.dumps({"evidence": packet, "question": question}, default=str)),
    }
    answer = ""
    for _attempt in range(2):
        try:
            response = httpx.post(
                settings.understand_ai_base_url.rstrip("/") + "/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.understand_ai_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:5173",
                    "X-Title": "EarthTrend Myanmar",
                },
                json=payload,
                timeout=settings.understand_ai_timeout_seconds,
            )
        except httpx.TimeoutException:
            return _fallback("The AI service timed out. The calculated explanation is unchanged.")
        except httpx.HTTPError:
            return _fallback("The AI service could not be reached. The calculated explanation is unchanged.")
        if response.status_code >= 400:
            return _fallback(_rejection_notice(response))
        try:
            answer = _read_answer(response.json())
        except (KeyError, IndexError, TypeError, ValueError):
            return _fallback("The AI service returned an unreadable reply. The calculated explanation is unchanged.")
        if answer:
            break
    if not answer:
        return _fallback("The AI service returned an empty reply. The calculated explanation is unchanged.")
    return {
        "ai_available": True,
        "answer": answer,
        "notice": "This reply interprets the calculated analysis. It is not a new measurement.",
    }


def _messages(history: list[dict], question_text: str) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history[-6:]:
        role = turn.get("role")
        text = str(turn.get("content") or "").strip()[:800]
        if role not in {"user", "assistant"} or not text:
            continue
        if messages[-1]["role"] == role:
            continue
        messages.append({"role": role, "content": text})
    if len(messages) > 1 and messages[1]["role"] == "assistant":
        messages.pop(1)
    if messages[-1]["role"] == "user":
        messages.pop()
    messages.append({"role": "user", "content": question_text})
    return messages


def _read_answer(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content")
    text = ""
    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, str):
                texts.append(part)
                continue
            if not isinstance(part, dict) or part.get("type") == "reasoning":
                continue
            part_text = part.get("text") or part.get("content") or ""
            if part_text:
                texts.append(str(part_text))
        text = "".join(texts).strip()
    if text:
        return text
    reasoning = message.get("reasoning")
    if isinstance(reasoning, str):
        return reasoning.strip()
    return ""


def _rejection_notice(response: httpx.Response) -> str:
    if response.status_code == 429:
        return "The AI service is rate limited. The calculated explanation is unchanged."
    message = ""
    try:
        payload = response.json()
        error = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(error, dict):
            message = str(error.get("message") or "")
        elif isinstance(error, str):
            message = error
    except (ValueError, AttributeError):
        message = ""
    if "location is not supported" in message.lower():
        return "The AI service is not available for this location. The calculated explanation is unchanged."
    return "The AI service rejected the request. The calculated explanation is unchanged."


def _fallback(notice: str) -> dict:
    return {"ai_available": True, "answer": None, "notice": notice}
