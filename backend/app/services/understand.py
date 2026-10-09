"""Plain-language explanations of results the analysis service already calculated."""

from __future__ import annotations


def explain_analysis(context: dict) -> dict:
    selected = context["selected"]
    figures = _figures(context, selected)
    limitations = _limitations(context, selected)
    summary = _summary(context, selected)
    comparison = _comparison(context) if context.get("compare") else None
    return {
        "mode": "manual",
        "is_sample": bool(context.get("is_sample")),
        "title": _title(context, selected),
        "summary": summary,
        "statistics": {
            "direction": _direction(context, selected),
            "magnitude": _magnitude(context, selected),
            "significance": _significance(context, selected),
            "uncertainty": _uncertainty(context, selected),
            "assumptions": _assumptions(context, selected),
        },
        "map": _map_section(context, selected),
        "comparison": comparison,
        "limitations": limitations,
        "figures": figures,
        "context": {
            "variable": context["variable"],
            "variable_label": context["variable_label"],
            "region_id": selected["geography_id"],
            "region_name": selected["geography_name"],
            "start_year": context["start_year"],
            "end_year": context["end_year"],
            "source": context["source"],
            "source_parameter": context["parameter"],
            "community": context["community"],
            "analysis_unit": context["analysis_unit"],
            "aggregation_rule": context["aggregation_rule"],
            "spatial_resolution": context["spatial_resolution"],
        },
    }


def render_report(context: dict, explanation: dict) -> str:
    selected = context["selected"]
    figures = explanation["figures"]
    lines = [
        f"# {explanation['title']}",
        "",
        "This report repeats the analysis already calculated for the selected case. It is an interpretation of those results.",
        "",
        "## Investigation",
        f"- Area: {selected['geography_name']}",
        f"- Variable: {context['variable_label']} ({context['parameter']})",
        f"- Period: {context['start_year']}–{context['end_year']}",
        f"- Aggregation: {context['aggregation_rule']}",
        f"- Analysis unit: {context['analysis_unit']}",
        f"- Slope unit: {context['slope_unit']}",
        f"- Source: {context['source']}, community {context['community']}",
        f"- Grid spacing: {context['spatial_resolution']}",
        "",
        "## Yearly series shown on the investigation chart",
        "",
        "| Year | Value | Anomaly |",
        "| --- | --- | --- |",
    ]
    for point in selected.get("series") or []:
        lines.append(
            f"| {point['year']} | {_cell(point.get('value'))} | {_cell(point.get('anomaly'))} |"
        )
    lines.extend(
        [
            "",
            "## Calculated statistics",
            f"- Status: {figures['trend_status']}",
            f"- Sen's slope: {_cell(figures['sen_slope'])} {context['slope_unit']}",
            f"- Slope per 10 years: {_cell(figures['slope_per_decade'])} {context['decade_unit']}",
            f"- Raw p-value: {_cell(figures['p_value'])}",
            f"- Corrected p-value: {_cell(figures['adjusted_p_value'])}",
            f"- 95% confidence interval: {_interval(figures['confidence_interval_95'], context['slope_unit'])}",
            f"- Valid years: {figures['valid_years']} of {figures['expected_years']}",
            f"- Year coverage: {_coverage(figures['coverage_fraction'])}",
            f"- {context['baseline_start_year']}–{context['baseline_end_year']} mean: {_cell(figures['baseline_mean'])} {context['analysis_unit']}",
            f"- {context['comparison_start_year']}–{context['comparison_end_year']} mean: {_cell(figures['comparison_mean'])} {context['analysis_unit']}",
            f"- Test: {figures['test_method']}; autocorrelation handling: {figures['autocorrelation_method']}",
            f"- Multiple testing: {figures['multiple_testing_method']}",
            "",
            "## Plain-language interpretation",
            explanation["summary"],
            "",
            explanation["statistics"]["direction"],
            "",
            explanation["statistics"]["magnitude"],
            "",
            explanation["statistics"]["significance"],
            "",
            explanation["statistics"]["uncertainty"],
            "",
            "## Map",
            explanation["map"]["text"],
            "",
        ]
    )
    if explanation.get("comparison"):
        lines.extend(["## Comparison", explanation["comparison"]["text"], ""])
    lines.extend(["## Limitations", *[f"- {item}" for item in explanation["limitations"]], ""])
    lines.append(
        "AI text is not included unless an AI interpretation was requested separately. "
        "The numbers above come from the analysis service."
    )
    if context.get("is_sample"):
        lines.extend(["", "SAMPLE DATA - NOT REAL NASA RESULTS"])
    return "\n".join(lines) + "\n"


def compact_evidence(context: dict, explanation: dict) -> dict:
    """Small packet for an AI call. Other regions keep their verdicts, not their yearly series."""
    selected = dict(context["selected"])
    compare = context.get("compare")
    compare_packet = None
    if compare:
        compare_packet = {key: value for key, value in compare.items() if key != "series" and key != "trend_line"}
    return {
        "source": context["source"],
        "community": context["community"],
        "parameter": context["parameter"],
        "variable": context["variable"],
        "variable_label": context["variable_label"],
        "aggregation_rule": context["aggregation_rule"],
        "analysis_unit": context["analysis_unit"],
        "slope_unit": context["slope_unit"],
        "decade_unit": context["decade_unit"],
        "period": [context["start_year"], context["end_year"]],
        "baseline_period": [context["baseline_start_year"], context["baseline_end_year"]],
        "comparison_period": [context["comparison_start_year"], context["comparison_end_year"]],
        "significance_alpha": context["significance_alpha"],
        "spatial_resolution": context["spatial_resolution"],
        "selected": selected,
        "compare": compare_packet,
        "region_verdicts": context["region_summaries"],
        "manual_summary": explanation["summary"],
        "map_counts": explanation["map"]["counts"],
        "limitations": explanation["limitations"],
        "note": (
            "Region verdicts are separate tests. A significant result in one region and "
            "a non-significant result in another is not a test that the two trends differ."
        ),
    }


def explain_page(page: str, contexts: list[dict], map_mode: str | None = None, year: int | None = None) -> dict:
    """Deterministic wording for the page the user is looking at."""
    primary = contexts[0]
    selected = primary["selected"]
    name = selected["geography_name"]
    label = _series_name(primary)
    window = f"{primary['start_year']}–{primary['end_year']}"
    if page == "compare":
        return _compare_page(primary, label, window)
    if page == "fingerprint":
        return _fingerprint_page(contexts, name, window)
    if page == "evidence":
        return _evidence_page(primary, label, name, window)
    if page == "map" and map_mode == "year":
        return _year_page(primary, selected, label, name, year)
    if page == "map" and map_mode == "change":
        return _change_page(primary, selected, label, name)
    prefix = (
        f"You are reading the case overview for {label} in {name}, {window}."
        if page == "overview"
        else f"You are looking at the trend map for {label} in {name}, {window}."
    )
    text = f"{prefix} {_summary(primary, selected)} {_map_section(primary, selected)['text']}"
    title = f"{primary['variable_label']} in {name}, {window}"
    action = prefix
    task = (
        "Explain what the user is looking at on this page. "
        "Use the authoritative explanation and do not add a cause or a new measurement."
    )
    return _page_result(page, title, action, text, True, task)


def action_evidence(page: str, contexts: list[dict], map_mode: str | None, year: int | None, authoritative_text: str) -> dict:
    """Compact packet for Gemini. Yearly series stay out unless one stored year is in view."""
    analyses = []
    for context in contexts:
        packet = compact_evidence(context, explain_analysis(context))
        packet["selected"] = _public_place(packet["selected"])
        if packet.get("compare"):
            packet["compare"] = _public_place(packet["compare"])
        if page == "map" and map_mode == "year":
            packet["focus_year"] = _year_point(context["selected"], year)
        analyses.append(packet)
    return {
        "page": page,
        "map_mode": map_mode,
        "focus_year": year,
        "authoritative_explanation": authoritative_text,
        "analyses": analyses,
    }


def _page_result(page: str, title: str, action: str, text: str, ready: bool, task: str) -> dict:
    return {
        "page": page,
        "title": title,
        "action": action,
        "text": text,
        "ready_for_ai": ready,
        "task": task,
    }


def _compare_page(primary: dict, label: str, window: str) -> dict:
    selected = primary["selected"]
    other = primary.get("compare")
    if not other:
        if selected.get("level") == "ADM0":
            text = (
                "A comparison needs two regions. No pair is selected, "
                "so there is no comparison to explain until both regions are chosen."
            )
        else:
            text = (
                f"A comparison needs two regions. {selected['geography_name']} is selected, "
                "but the second region is not. There is no comparison to explain until both regions are chosen."
            )
        return _page_result("compare", f"{primary['variable_label']} comparison", "A comparison needs two regions.", text, False, "")
    text = (
        f"You compared {selected['geography_name']} with {other['geography_name']} for {label} during {window}. "
        f"{_comparison(primary)['text']}"
    )
    return _page_result(
        "compare",
        f"{selected['geography_name']} and {other['geography_name']}, {window}",
        f"You compared {selected['geography_name']} with {other['geography_name']} for {label}.",
        text,
        True,
        "Explain this comparison. Do not say the two trends differ significantly.",
    )


def _fingerprint_page(contexts: list[dict], name: str, window: str) -> dict:
    parts = [f"You are reading the fingerprint for {name} during {window}."]
    if all(context["selected"].get("level") == "ADM0" for context in contexts):
        parts.append("No state is selected, so each sentence uses the national series.")
    for context in contexts:
        parts.append(_summary(context, context["selected"]))
    parts.append(
        "Each sentence uses that variable's own stored test. "
        "Reading them together does not show a shared cause, and it is not a test that one variable's trend differs from another."
    )
    statuses = [context["selected"]["trend_status"] for context in contexts]
    if "significant_increasing" in statuses and "significant_decreasing" in statuses:
        parts.append(
            "The stored statuses include both a significant increase and a significant decrease across these variables."
        )
    else:
        parts.append(
            "The stored statuses do not include both a significant increase and a significant decrease across these variables."
        )
    return _page_result(
        "fingerprint",
        f"Fingerprint for {name}, {window}",
        f"You are reading the fingerprint for {name}.",
        " ".join(parts),
        True,
        "Explain these variables together. Keep each result as its own test and do not give a shared cause.",
    )


def _evidence_page(primary: dict, label: str, name: str, window: str) -> dict:
    evidence = primary["evidence"]
    text = " ".join(
        [
            f"You opened the evidence locker for {label} in {name}, {window}.",
            f"The series is {primary['source']} {primary['parameter']}, community {primary['community']}, at {primary['spatial_resolution']}.",
            primary["aggregation_rule"],
            evidence["trend_method"] + ".",
            evidence["significance_test"],
            f"The threshold is {primary['significance_alpha']}.",
            evidence["multiple_testing_regions"] + ".",
            evidence["multiple_testing_national"] + ".",
            " ".join(evidence["limitations"]),
            _summary(primary, primary["selected"]),
        ]
    )
    return _page_result(
        "evidence",
        f"Evidence for {label} in {name}",
        f"You opened the evidence locker for {label} in {name}.",
        text,
        True,
        "Explain how this result was calculated and what limits it. Do not add a cause or a new measurement.",
    )


def _year_page(primary: dict, selected: dict, label: str, name: str, year: int | None) -> dict:
    point = _year_point(selected, year)
    if year is None or point is None:
        shown_year = "That year" if year is None else str(year)
        text = (
            f"You are looking at a single year on the {label} map for {name}. "
            f"{shown_year} is not in the stored series, so there is no value or anomaly to explain."
        )
        action = "That year is not in the stored series."
    else:
        baseline = f"{primary['baseline_start_year']}–{primary['baseline_end_year']}"
        text = (
            f"You are looking at {year} for {label} in {name}. "
            f"The stored value is {_shown(point.get('value'))} {primary['analysis_unit']}. "
            f"The stored anomaly versus the {baseline} average is {_shown(point.get('anomaly'))} {primary['analysis_unit']}. "
            "This is one year in the series. It is not the trend test."
        )
        action = f"You are looking at {year} for {label} in {name}."
    return _page_result(
        "map",
        f"{year or 'Year'} {primary['variable_label']} in {name}",
        action,
        text,
        True,
        "Explain this stored year only. Do not turn one year into a trend or a cause.",
    )


def _change_page(primary: dict, selected: dict, label: str, name: str) -> dict:
    earlier = f"{primary['baseline_start_year']}–{primary['baseline_end_year']}"
    later = f"{primary['comparison_start_year']}–{primary['comparison_end_year']}"
    unit = primary["analysis_unit"]
    text = (
        f"You are comparing {earlier} with {later} for {label} in {name}. "
        f"The stored earlier mean is {_shown(selected.get('baseline_mean'))} {unit}. "
        f"The stored later mean is {_shown(selected.get('comparison_mean'))} {unit}. "
        f"The stored absolute difference is {_shown(selected.get('absolute_difference'))} {unit}. "
        "This is a difference of averages. It is not a separate significance test."
    )
    relative = selected.get("relative_difference_percent")
    if primary["variable"] == "precipitation" and relative is not None:
        text += f" The stored relative difference is {_shown(relative)} percent."
    return _page_result(
        "map",
        f"Then versus now for {primary['variable_label']} in {name}",
        f"You are comparing {earlier} with {later} for {label} in {name}.",
        text,
        True,
        "Explain this difference of stored averages. Do not call it a significance test or a cause.",
    )


def _public_place(place: dict) -> dict:
    return {key: value for key, value in place.items() if key not in {"series", "trend_line"}}


def _year_point(selected: dict, year: int | None):
    if year is None:
        return None
    for point in selected.get("series") or []:
        if int(point["year"]) == int(year):
            return {"year": int(point["year"]), "value": point.get("value"), "anomaly": point.get("anomaly")}
    return None


def _shown(value) -> str:
    if value is None or value == "":
        return "unavailable"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return f"{float(value):.4g}"
    return str(value)


def _title(context: dict, selected: dict) -> str:
    return (
        f"{context['variable_label']} in {selected['geography_name']}, "
        f"{context['start_year']}–{context['end_year']}"
    )


def _summary(context: dict, selected: dict) -> str:
    name = selected["geography_name"]
    label = _series_name(context)
    window = f"{context['start_year']}–{context['end_year']}"
    if selected["trend_status"] == "insufficient_data" or selected["sen_slope"] is None:
        return (
            f"For {label} in {name} during {window}, the series has "
            f"{selected['valid_years']} valid years. That is not enough for this app to classify a trend, "
            "so there is no magnitude or significance claim for this selection."
        )
    direction = "increases" if selected["sen_slope"] > 0 else "decreases" if selected["sen_slope"] < 0 else "is estimated at zero"
    verdict = _verdict_sentence(context, selected)
    return (
        f"For {label} in {name} during {window}, the estimated Sen's slope "
        f"{direction} at {selected['slope_text']} {context['slope_unit']} "
        f"({_decade(selected)} {context['decade_unit']}). {verdict} "
        f"Year coverage is {_coverage(selected.get('coverage_fraction'))}."
    )


def _direction(context: dict, selected: dict) -> str:
    label = _series_name(context)
    if selected["trend_status"] == "insufficient_data" or selected["sen_slope"] is None:
        return (
            f"The direction is inconclusive. {label.capitalize()} does not have enough valid years "
            "for a Sen's slope to be classified."
        )
    if selected["sen_slope"] > 0:
        sentence = f"The estimated {label} increases over {context['start_year']}–{context['end_year']}."
    elif selected["sen_slope"] < 0:
        sentence = f"The estimated {label} decreases over {context['start_year']}–{context['end_year']}."
    else:
        sentence = "The estimated slope is zero."
    if selected["trend_status"] == "not_significant":
        sentence += " The significance test does not confirm that this direction is distinguishable from no trend."
    return sentence


def _magnitude(context: dict, selected: dict) -> str:
    label = _series_name(context)
    if selected["sen_slope"] is None:
        return f"No slope is reported for {label}, so the size of the change is unavailable."
    return (
        f"The slope is the estimated change in {label} per year: "
        f"{selected['slope_text']} {context['slope_unit']}. "
        f"Over 10 years that scale is {_decade(selected)} {context['decade_unit']}. "
        f"{_unit_meaning(context)}"
    )


def _significance(context: dict, selected: dict) -> str:
    alpha = context["significance_alpha"]
    status = selected["trend_status"]
    if status == "insufficient_data" or selected.get("adjusted_p_value") is None and status == "insufficient_data":
        return (
            f"No significance claim is made. The threshold used elsewhere in the app is {alpha}, "
            "but this series was not classified."
        )
    corrected = _cell(selected.get("adjusted_p_value"))
    raw = _cell(selected.get("p_value"))
    method = selected.get("multiple_testing_method") or "the recorded method"
    if str(status).startswith("significant"):
        return (
            f"The status is {status.replace('_', ' ')}. The corrected p-value is {corrected} "
            f"(raw p-value {raw}) after {method.replace('_', ' ')}. "
            f"At the threshold {alpha}, the test gives evidence against a no-trend hypothesis, "
            "subject to the method's assumptions. The p-value is not the size of the change, "
            "and the status is not a cause."
        )
    return (
        f"The status is no clear trend. The corrected p-value is {corrected} "
        f"(raw p-value {raw}) after {method.replace('_', ' ')}. "
        f"At the threshold {alpha}, the test does not provide sufficient evidence to reject a no-trend hypothesis. "
        "That is not a finding that no change occurred. The slope is still reported so the estimate can be read with the test."
    )


def _uncertainty(context: dict, selected: dict) -> str:
    interval = selected.get("confidence_interval_95")
    coverage = _coverage(selected.get("coverage_fraction"))
    parts = [
        f"Valid years: {selected['valid_years']} of {selected['expected_years']}. Year coverage: {coverage}.",
        f"The 95% confidence interval for the yearly Sen's slope is {_interval(interval, context['slope_unit'])}.",
    ]
    if interval and interval[0] is not None and interval[1] is not None and interval[0] < 0 < interval[1]:
        parts.append("The interval includes both negative and positive slopes.")
    parts.append(
        f"Autocorrelation handling for this series: {selected.get('autocorrelation_method') or 'not recorded'}. "
        f"Spatial rule: a regional year is kept only when valid cells cover at least "
        f"{context['evidence']['minimum_spatial_coverage']} of the area weight."
    )
    return " ".join(parts)


def _assumptions(context: dict, selected: dict) -> list[str]:
    return [
        context["evidence"]["trend_method"] + ".",
        context["evidence"]["significance_test"],
        (
            "State and region p-values use "
            f"{context['evidence']['multiple_testing_regions']}. "
            f"The national series uses {context['evidence']['multiple_testing_national']}."
        ),
        f"The recorded test for this series is {selected.get('test_method') or 'unavailable'}.",
        "The explanation does not rerun the test and does not replace the stored status.",
    ]


def _map_section(context: dict, selected: dict) -> dict:
    rows = context.get("region_summaries") or []
    counts = {
        "significant_increasing": sum(row["trend_status"] == "significant_increasing" for row in rows),
        "significant_decreasing": sum(row["trend_status"] == "significant_decreasing" for row in rows),
        "not_significant": sum(row["trend_status"] == "not_significant" for row in rows),
        "insufficient_data": sum(row["trend_status"] == "insufficient_data" for row in rows),
    }
    if not rows:
        return {
            "supported": False,
            "counts": counts,
            "text": "A state-by-state breakdown is not available for this selection, so the map is not interpreted.",
        }
    text = (
        f"Among {len(rows)} states and regions, {counts['significant_increasing']} are a significant increase, "
        f"{counts['significant_decreasing']} are a significant decrease, "
        f"{counts['not_significant']} have no clear trend, and "
        f"{counts['insufficient_data']} do not have enough data. "
        "Each status is that area's own test. These counts do not show that one area's trend is statistically different from another's."
    )
    if selected.get("level") != "ADM0":
        text += (
            f" The selected area, {selected['geography_name']}, is stored as "
            f"{str(selected['trend_status']).replace('_', ' ')} with a per-decade slope of {_decade(selected)} "
            f"{context['decade_unit']}. No between-region test is included."
        )
    return {"supported": True, "counts": counts, "text": text}


def _comparison(context: dict) -> dict:
    selected = context["selected"]
    other = context["compare"]
    return {
        "text": (
            f"{selected['geography_name']} is {str(selected['trend_status']).replace('_', ' ')} "
            f"with slope {_cell(selected.get('sen_slope'))} {context['slope_unit']}. "
            f"{other['geography_name']} is {str(other['trend_status']).replace('_', ' ')} "
            f"with slope {_cell(other.get('sen_slope'))} {context['slope_unit']}. "
            "These are separate tests. One significant result and one non-significant result do not, by themselves, "
            "show that the two trends differ."
        )
    }


def _limitations(context: dict, selected: dict) -> list[str]:
    items = list(context["evidence"]["limitations"])
    items.append(
        f"{context['source']} {context['parameter']} is a gridded climate series at {context['spatial_resolution']}, "
        "not a reading from a single weather station."
    )
    items.append(_unit_meaning(context))
    if selected["trend_status"] == "not_significant":
        items.append("A non-significant test is not proof that the series is unchanged.")
    return items


def _figures(context: dict, selected: dict) -> dict:
    return {
        "trend_status": selected["trend_status"],
        "sen_slope": selected.get("sen_slope"),
        "slope_text": selected.get("slope_text"),
        "slope_per_decade": selected.get("slope_per_decade"),
        "p_value": selected.get("p_value"),
        "adjusted_p_value": selected.get("adjusted_p_value"),
        "confidence_interval_95": selected.get("confidence_interval_95"),
        "valid_years": selected.get("valid_years"),
        "expected_years": selected.get("expected_years"),
        "coverage_fraction": selected.get("coverage_fraction"),
        "baseline_mean": selected.get("baseline_mean"),
        "comparison_mean": selected.get("comparison_mean"),
        "absolute_difference": selected.get("absolute_difference"),
        "test_method": selected.get("test_method"),
        "autocorrelation_method": selected.get("autocorrelation_method"),
        "multiple_testing_method": selected.get("multiple_testing_method"),
        "analysis_unit": context["analysis_unit"],
        "slope_unit": context["slope_unit"],
        "decade_unit": context["decade_unit"],
    }


def _verdict_sentence(context: dict, selected: dict) -> str:
    if str(selected["trend_status"]).startswith("significant"):
        return (
            f"The stored test meets the {context['significance_alpha']} threshold after the recorded correction, "
            "subject to the method's assumptions."
        )
    if selected["trend_status"] == "not_significant":
        return (
            "The stored test does not meet that threshold. The data do not provide sufficient evidence "
            "to reject a no-trend hypothesis, which is not the same as evidence that nothing changed."
        )
    return "The series is not classified."


def _series_name(context: dict) -> str:
    if context["variable"] == "temperature":
        return "annual mean air temperature"
    if context["variable"] == "precipitation":
        return "annual rainfall total"
    return "annual mean relative humidity"


def _unit_meaning(context: dict) -> str:
    if context["variable"] == "temperature":
        return "Temperature is an annual mean in °C, built from monthly means. It is not a sum of temperatures."
    if context["variable"] == "precipitation":
        return "Rainfall is an annual total in mm, built by turning each month's mean daily rate into a monthly amount and summing the months."
    return "Relative humidity is an annual mean in percent. Its slope is in percentage points per year, not a multiplied percent."


def _decade(selected: dict) -> str:
    value = selected.get("slope_per_decade")
    if value is None:
        return "unavailable"
    return f"{float(value):.2f}"


def _coverage(value) -> str:
    if value is None:
        return "unavailable"
    return f"{float(value):.0%}"


def _cell(value) -> str:
    if value is None:
        return ""
    return str(value)


def _interval(interval, unit: str) -> str:
    if not interval or interval[0] is None or interval[1] is None:
        return "unavailable"
    return f"{interval[0]} to {interval[1]} {unit}"
