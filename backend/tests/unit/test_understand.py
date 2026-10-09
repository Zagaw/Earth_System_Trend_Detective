import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.services.catalog import UnknownRegion
from app.services.understand import action_evidence, compact_evidence, explain_analysis, explain_page, render_report
from app.services.understand_ai import answer_question

client = TestClient(app)


def _context(status="significant_increasing", slope=0.2, years=25, compare=False):
    selected = _place("Mandalay", status, slope, years)
    other = _place("Yangon", "not_significant", -0.1, years) if compare else None
    return {
        "is_sample": False,
        "source": "NASA POWER",
        "community": "SB",
        "parameter": "T2M",
        "source_unit": "C",
        "analysis_unit": "degC",
        "slope_unit": "degC/year",
        "decade_unit": "degC per 10 years",
        "aggregation_rule": "Annual values are means of valid monthly values.",
        "variable": "temperature",
        "variable_label": "Air temperature at 2 m",
        "start_year": 2001,
        "end_year": 2025,
        "baseline_start_year": 2001,
        "baseline_end_year": 2010,
        "comparison_start_year": 2016,
        "comparison_end_year": 2025,
        "significance_alpha": 0.05,
        "spatial_resolution": "0.5° latitude by 0.625° longitude",
        "evidence": {
            "minimum_spatial_coverage": 0.5,
            "trend_method": "Sen's slope, using year as the x coordinate",
            "significance_test": "Mann–Kendall on the annual series.",
            "multiple_testing_regions": "Benjamini–Hochberg across the 14 states and regions",
            "multiple_testing_national": "none, because the national series is a single test",
            "limitations": [
                "Results describe NASA POWER climate series, not crop loss, health, floods, or economic cost."
            ],
        },
        "selected": selected,
        "compare": other,
        "region_summaries": [
            {"geography_id": "a", "geography_name": "Mandalay", "trend_status": status, "sen_slope": slope, "slope_per_decade": None if slope is None else slope * 10, "adjusted_p_value": selected["adjusted_p_value"], "valid_years": years},
            {"geography_id": "b", "geography_name": "Yangon", "trend_status": "not_significant", "sen_slope": -0.1, "slope_per_decade": -1.0, "adjusted_p_value": 0.4, "valid_years": 25},
        ],
    }


def _place(name, status, slope, years):
    return {
        "geography_id": name.lower(),
        "geography_name": name,
        "level": "ADM1",
        "sen_slope": slope,
        "slope_per_decade": None if slope is None else slope * 10,
        "slope_text": "unavailable" if slope is None else f"{slope:.3f}",
        "p_value": None if status == "insufficient_data" else 0.01,
        "adjusted_p_value": None if status == "insufficient_data" else (0.01 if status.startswith("significant") else 0.4),
        "confidence_interval_95": None if slope is None else [slope - 0.05, slope + 0.05],
        "trend_status": status,
        "valid_years": years,
        "expected_years": 25,
        "coverage_fraction": years / 25,
        "baseline_mean": 26.0,
        "comparison_mean": 26.4,
        "absolute_difference": 0.4,
        "test_method": "original",
        "autocorrelation_method": "none",
        "multiple_testing_method": "benjamini_hochberg",
        "series": [{"year": 2001, "value": 26.0, "anomaly": -0.2}, {"year": 2002, "value": None, "anomaly": None}],
        "trend_line": [],
    }


def test_increasing_explanation_keeps_units_and_does_not_give_a_cause() -> None:
    explanation = explain_analysis(_context("significant_increasing", 0.2))
    text = explanation["summary"] + explanation["statistics"]["direction"]
    assert "increases" in text
    assert "degC/year" in explanation["statistics"]["magnitude"]
    assert "annual mean" in explanation["statistics"]["magnitude"]
    assert "caused" not in text.lower()
    assert explanation["figures"]["sen_slope"] == 0.2


def test_decreasing_explanation_states_the_direction() -> None:
    explanation = explain_analysis(_context("significant_decreasing", -0.2))
    assert "decreases" in explanation["statistics"]["direction"]


def test_nonsignificant_explanation_does_not_claim_the_climate_is_unchanged() -> None:
    explanation = explain_analysis(_context("not_significant", 0.2))
    combined = explanation["summary"] + explanation["statistics"]["significance"]
    assert "not the same as evidence that nothing changed" in combined or "not a finding that no change occurred" in combined
    assert "unchanged" not in explanation["summary"].split("not the same")[0]


def test_insufficient_data_makes_no_magnitude_claim() -> None:
    explanation = explain_analysis(_context("insufficient_data", None, years=4))
    assert "not enough" in explanation["summary"]
    assert explanation["figures"]["sen_slope"] is None
    assert "No slope is reported" in explanation["statistics"]["magnitude"]


def test_map_text_does_not_treat_separate_tests_as_a_difference_test() -> None:
    explanation = explain_analysis(_context())
    assert explanation["map"]["supported"] is True
    assert "do not show that one area's trend is statistically different" in explanation["map"]["text"]


def test_comparison_does_not_declare_the_regions_different() -> None:
    explanation = explain_analysis(_context(compare=True))
    assert "do not, by themselves, show that the two trends differ" in explanation["comparison"]["text"]


def test_report_contains_the_series_unit_and_source() -> None:
    context = _context()
    document = render_report(context, explain_analysis(context))
    assert "NASA POWER" in document
    assert "degC/year" in document
    assert "| 2001 | 26.0 | -0.2 |" in document
    assert "| 2002 |  |  |" in document
    assert "SAMPLE DATA" not in document


def test_ai_evidence_keeps_the_selected_series_and_drops_the_other_region_series() -> None:
    context = _context(compare=True)
    explanation = explain_analysis(context)
    evidence = compact_evidence(context, explanation)
    assert evidence["selected"]["series"][0]["year"] == 2001
    assert "series" not in evidence["compare"]
    assert evidence["selected"]["geography_name"] == "Mandalay"
    assert evidence["region_verdicts"][1]["geography_name"] == "Yangon"


def test_missing_ai_key_keeps_the_manual_path(monkeypatch) -> None:
    def fail_post(*_args, **_kwargs):
        raise AssertionError("The AI service should not be called without a key.")

    monkeypatch.setattr(httpx, "post", fail_post)
    settings = Settings(understand_ai_api_key="")
    result = answer_question(settings, _context(), explain_analysis(_context()), "What does the p-value mean?", [])
    assert result["ai_available"] is False
    assert result["answer"] is None


def test_ai_timeout_does_not_replace_the_manual_summary(monkeypatch) -> None:
    def timeout(*_args, **_kwargs):
        raise httpx.TimeoutException("slow")

    monkeypatch.setattr(httpx, "post", timeout)
    settings = Settings(understand_ai_api_key="test-key")
    result = answer_question(settings, _context(), explain_analysis(_context()), "Why did it warm?", [])
    assert result["answer"] is None
    assert "timed out" in result["notice"]


def test_explain_route_reads_the_catalog_result(monkeypatch) -> None:
    context = _context()

    class FakeCatalog:
        def understand_context(self, **_kwargs):
            return context

    monkeypatch.setattr("app.api.deps.get_catalog", lambda: FakeCatalog())
    response = client.post(
        "/api/v1/understand/explain",
        json={"variable": "temperature", "region_id": "mandalay", "start_year": 2001, "end_year": 2025},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "manual"
    assert body["figures"]["sen_slope"] == 0.2
    assert body["context"]["region_name"] == "Mandalay"


def test_chat_route_rejects_an_empty_question() -> None:
    response = client.post(
        "/api/v1/understand/chat",
        json={"variable": "temperature", "start_year": 2001, "end_year": 2025, "question": "  "},
    )
    assert response.status_code == 422


def test_unknown_region_is_not_explained_from_client_numbers(monkeypatch) -> None:
    class FakeCatalog:
        def understand_context(self, **_kwargs):
            raise UnknownRegion("missing")

    monkeypatch.setattr("app.api.deps.get_catalog", lambda: FakeCatalog())
    response = client.post(
        "/api/v1/understand/explain",
        json={"variable": "temperature", "region_id": "missing", "start_year": 2001, "end_year": 2025},
    )
    assert response.status_code == 404
    assert response.json()["error"] == "unknown_region"


def test_report_route_downloads_markdown(monkeypatch) -> None:
    class FakeCatalog:
        def understand_context(self, **_kwargs):
            return _context()

    monkeypatch.setattr("app.api.deps.get_catalog", lambda: FakeCatalog())
    response = client.post(
        "/api/v1/understand/report",
        json={"variable": "temperature", "start_year": 2001, "end_year": 2025},
    )
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    assert "Mandalay" in response.text
    assert "degC/year" in response.text


def test_comparison_page_keeps_both_results_and_refuses_a_difference_claim() -> None:
    page = explain_page("compare", [_context(compare=True)])
    assert page["ready_for_ai"] is True
    assert "Mandalay" in page["text"]
    assert "Yangon" in page["text"]
    assert "do not, by themselves, show that the two trends differ" in page["text"]


def test_comparison_without_a_second_region_is_not_sent_to_ai() -> None:
    page = explain_page("compare", [_context(compare=False)])
    assert page["ready_for_ai"] is False
    assert "two regions" in page["text"]
    assert "Mandalay is selected" in page["text"]


def test_year_page_uses_the_stored_value_and_anomaly() -> None:
    page = explain_page("map", [_context()], "year", 2001)
    assert "2001" in page["text"]
    assert "26" in page["text"]
    assert "-0.2" in page["text"]
    assert "not the trend test" in page["text"]


def test_missing_year_makes_no_value_claim() -> None:
    page = explain_page("map", [_context()], "year", 2016)
    assert "not in the stored series" in page["text"]
    assert "26.4" not in page["text"]


def test_change_page_uses_stored_means_and_is_not_a_significance_test() -> None:
    page = explain_page("map", [_context()], "change", None)
    assert "26" in page["text"]
    assert "26.4" in page["text"]
    assert "0.4" in page["text"]
    assert "not a separate significance test" in page["text"]


def test_fingerprint_keeps_each_variable_as_its_own_test() -> None:
    contexts = []
    for variable, status, slope in (
        ("temperature", "significant_increasing", 0.2),
        ("precipitation", "significant_decreasing", -1.0),
        ("relative_humidity", "not_significant", 0.1),
    ):
        context = _context(status, slope)
        context["variable"] = variable
        contexts.append(context)
    page = explain_page("fingerprint", contexts)
    assert "own stored test" in page["text"]
    assert "significant increase and a significant decrease" in page["text"]
    assert "shared cause" in page["text"]


def test_action_evidence_for_a_year_drops_the_series() -> None:
    evidence = action_evidence("map", [_context()], "year", 2001, "Use the stored year.")
    selected = evidence["analyses"][0]["selected"]
    assert "series" not in selected
    assert evidence["analyses"][0]["focus_year"]["anomaly"] == -0.2
    assert evidence["authoritative_explanation"] == "Use the stored year."


def test_openrouter_answer_reads_the_message_and_skips_reasoning(monkeypatch) -> None:
    def post(url, headers, json, timeout):
        assert url.endswith("/chat/completions")
        assert "key=" not in url
        assert headers["Authorization"] == "Bearer test-key"
        assert json["model"] == "nvidia/nemotron-3-ultra-550b-a55b:free"
        assert "authoritative_explanation" in json["messages"][-1]["content"]

        class Response:
            status_code = 200

            def json(self):
                return {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {"type": "reasoning", "text": "hidden"},
                                    {"type": "text", "text": "The stored slope increases."},
                                ]
                            }
                        }
                    ]
                }

        return Response()

    monkeypatch.setattr(httpx, "post", post)
    settings = Settings(
        understand_ai_api_key="test-key",
        understand_ai_base_url="https://example.test/v1",
        understand_ai_model="nvidia/nemotron-3-ultra-550b-a55b:free",
    )
    result = answer_question(settings, _context(), explain_analysis(_context()), "Explain this case.", [], evidence={"authoritative_explanation": "increases"})
    assert result["answer"] == "The stored slope increases."
    assert "hidden" not in result["answer"]


def test_empty_model_reply_is_retried_once(monkeypatch) -> None:
    calls = {"count": 0}

    def post(*_args, **_kwargs):
        calls["count"] += 1

        class Response:
            status_code = 200

            def json(self):
                if calls["count"] == 1:
                    return {"choices": [{"message": {"content": ""}}]}
                return {"choices": [{"message": {"content": "The stored slope decreases."}}]}

        return Response()

    monkeypatch.setattr(httpx, "post", post)
    settings = Settings(understand_ai_api_key="test-key")
    result = answer_question(settings, _context(), explain_analysis(_context()), "Explain this case.", [])
    assert calls["count"] == 2
    assert result["answer"] == "The stored slope decreases."


def test_location_rejection_does_not_copy_the_provider_body(monkeypatch) -> None:
    def post(*_args, **_kwargs):
        class Response:
            status_code = 400

            def json(self):
                return {"error": {"message": "User location is not supported for the API use. token SECRETVALUE"}}

        return Response()

    monkeypatch.setattr(httpx, "post", post)
    settings = Settings(understand_ai_api_key="test-key")
    result = answer_question(settings, _context(), explain_analysis(_context()), "Explain this case.", [])
    assert result["answer"] is None
    assert "location" in result["notice"]
    assert "SECRETVALUE" not in result["notice"]


def test_incomplete_comparison_route_does_not_call_ai(monkeypatch) -> None:
    def fail(*_args, **_kwargs):
        raise AssertionError("AI should not be called before two regions are selected.")

    monkeypatch.setattr(httpx, "post", fail)

    class FakeCatalog:
        def understand_context(self, **_kwargs):
            return _context(compare=False)

    monkeypatch.setattr("app.api.deps.get_catalog", lambda: FakeCatalog())
    monkeypatch.setattr("app.api.routes.understand.get_settings", lambda: Settings(understand_ai_api_key="test-key"))
    response = client.post(
        "/api/v1/understand/action",
        json={"page": "compare", "variable": "temperature", "region_id": "mandalay", "start_year": 2001, "end_year": 2025},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "manual"
    assert body["answer"] is None
    assert "two regions" in body["manual"]


def test_action_route_uses_the_manual_text_when_the_model_rejects(monkeypatch) -> None:
    def post(*_args, **_kwargs):
        class Response:
            status_code = 400

            def json(self):
                return {"error": {"message": "API key not valid SECRETVALUE"}}

        return Response()

    monkeypatch.setattr(httpx, "post", post)

    class FakeCatalog:
        def understand_context(self, **_kwargs):
            return _context(compare=True)

    monkeypatch.setattr("app.api.deps.get_catalog", lambda: FakeCatalog())
    monkeypatch.setattr("app.api.routes.understand.get_settings", lambda: Settings(understand_ai_api_key="test-key"))
    response = client.post(
        "/api/v1/understand/action",
        json={
            "page": "compare",
            "variable": "temperature",
            "region_id": "mandalay",
            "compare_region_id": "yangon",
            "start_year": 2001,
            "end_year": 2025,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "manual"
    assert body["answer"] is None
    assert "Mandalay" in body["manual"]
    assert "Yangon" in body["manual"]
    assert "SECRETVALUE" not in body["notice"]
    assert "rejected" in body["notice"]
