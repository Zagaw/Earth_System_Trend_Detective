def interpret_trend(result: dict) -> str:
    name = result["geography_name"]
    variable = result["variable_label"]
    if result["trend_status"] == "insufficient_data":
        return (
            f"The selected period for {variable} in {name} has only "
            f"{result['valid_years']} valid observations. The app therefore does not classify its trend."
        )
    start = result["effective_start_year"]
    end = result["effective_end_year"]
    met = "did" if str(result["trend_status"]).startswith("significant") else "did not"
    correction = result["multiple_testing_method"]
    correction_text = (
        "no multiple-testing correction, because this is a single series"
        if correction == "none"
        else correction.replace("_", " ")
    )
    coverage = result["coverage_fraction"]
    coverage_text = "unavailable" if coverage is None else f"{coverage:.0%}"
    return (
        f"Across {name} during {start}–{end}, {result['aggregation_label']} {variable} "
        f"changed at an estimated Sen's slope of {result['slope_text']} {result['slope_unit']}. "
        f"The trend {met} meet the selected significance threshold after {correction_text}. "
        f"Coverage was {coverage_text}."
    )


def interpret_impact(result: dict) -> str:
    if result["absolute_difference"] is None:
        return (
            f"The baseline or comparison window for {result['variable_label']} in "
            f"{result['geography_name']} does not have enough valid observations, so no "
            "difference is reported."
        )
    return (
        f"Compared with {result['baseline_start_year']}–{result['baseline_end_year']}, "
        f"mean {result['variable_label']} in {result['comparison_start_year']}–"
        f"{result['comparison_end_year']} differed by {result['difference_text']} "
        f"{result['unit']}. This is a climate indicator, not a direct measurement of "
        "a social, agricultural, or economic outcome."
    )
