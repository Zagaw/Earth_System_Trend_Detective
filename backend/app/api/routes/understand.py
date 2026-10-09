from typing import Literal

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from app.api.deps import call_catalog, validate_period
from app.core.config import get_settings
from app.schemas.climate import ClimateVariable
from app.services.understand import action_evidence, explain_analysis, explain_page, render_report
from app.services.understand_ai import answer_question

router = APIRouter()


class UnderstandRequest(BaseModel):
    variable: ClimateVariable
    start_year: int = Field(default=2001, ge=1981, le=2100)
    end_year: int = Field(default=2025, ge=1981, le=2100)
    region_id: str | None = None
    compare_region_id: str | None = None


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=800)


class ActionRequest(UnderstandRequest):
    page: Literal["overview", "map", "fingerprint", "compare", "evidence"]
    map_mode: Literal["trend", "year", "change"] | None = None
    year: int | None = Field(default=None, ge=1981, le=2100)
    question: str | None = Field(default=None, max_length=800)
    history: list[ChatTurn] = Field(default_factory=list, max_length=6)

    @field_validator("question")
    @classmethod
    def question_has_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ChatRequest(UnderstandRequest):
    question: str = Field(min_length=1, max_length=800)
    history: list[ChatTurn] = Field(default_factory=list, max_length=6)

    @field_validator("question")
    @classmethod
    def question_has_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Enter a question about this analysis.")
        return cleaned


_PAGE_VARIABLES = ("temperature", "precipitation", "relative_humidity")


def _context(body: UnderstandRequest) -> dict:
    validate_period(body.start_year, body.end_year, "annual", None)
    return call_catalog(
        "understand_context",
        variable=body.variable,
        start_year=body.start_year,
        end_year=body.end_year,
        region_id=body.region_id,
        compare_region_id=body.compare_region_id,
    )


def _action_contexts(body: ActionRequest) -> list[dict]:
    variables = _PAGE_VARIABLES if body.page == "fingerprint" else (body.variable,)
    region_id = None if body.page in {"overview", "evidence"} else body.region_id
    compare_region_id = body.compare_region_id if body.page == "compare" else None
    contexts = []
    for variable in variables:
        validate_period(body.start_year, body.end_year, "annual", None)
        contexts.append(
            call_catalog(
                "understand_context",
                variable=variable,
                start_year=body.start_year,
                end_year=body.end_year,
                region_id=region_id,
                compare_region_id=compare_region_id,
            )
        )
    return contexts


@router.post("/understand/explain")
def explain(body: UnderstandRequest) -> dict:
    context = _context(body)
    explanation = explain_analysis(context)
    settings = get_settings()
    explanation["ai_available"] = bool(settings.understand_ai_api_key.strip())
    return explanation


@router.post("/understand/action")
def action(body: ActionRequest) -> dict:
    contexts = _action_contexts(body)
    map_mode = body.map_mode or ("trend" if body.page == "map" else None)
    manual = explain_page(body.page, contexts, map_mode, body.year)
    if not manual["ready_for_ai"]:
        return {
            "page": body.page,
            "title": manual["title"],
            "action": manual["action"],
            "manual": manual["text"],
            "mode": "manual",
            "answer": None,
            "notice": "A comparison needs two selected regions. The calculated explanation is shown instead.",
            "ai_available": False,
        }
    explanation = explain_analysis(contexts[0])
    evidence = action_evidence(body.page, contexts, map_mode, body.year, manual["text"])
    result = answer_question(
        get_settings(),
        contexts[0],
        explanation,
        body.question or manual["task"],
        [turn.model_dump() for turn in body.history],
        evidence=evidence,
    )
    answered = bool(result.get("answer"))
    return {
        "page": body.page,
        "title": manual["title"],
        "action": manual["action"],
        "manual": manual["text"],
        "mode": "ai" if answered else "manual",
        "answer": result.get("answer"),
        "notice": result.get("notice") or "",
        "ai_available": answered,
    }


@router.post("/understand/chat")
def chat(body: ChatRequest) -> dict:
    context = _context(body)
    explanation = explain_analysis(context)
    result = answer_question(
        get_settings(),
        context,
        explanation,
        body.question.strip(),
        [turn.model_dump() for turn in body.history],
    )
    result["manual_summary"] = explanation["summary"]
    result["figures"] = explanation["figures"]
    return result


@router.post("/understand/report")
def report(body: UnderstandRequest) -> Response:
    context = _context(body)
    explanation = explain_analysis(context)
    document = render_report(context, explanation)
    filename = f"earthtrend-{body.variable}-report.md"
    return Response(
        content=document,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
