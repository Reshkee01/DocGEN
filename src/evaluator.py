import re
from typing import Dict, List


def extract_body_paragraphs(text: str) -> List[int]:
    """
    Extract numbered affidavit paragraphs between the deponent
    clause and the PRAYER section.
    """

    deponent_match = re.search(
        r"do hereby solemnly affirm and state as under:",
        text,
        re.IGNORECASE,
    )

    prayer_match = re.search(
        r"^\s*PRAYER\s*$",
        text,
        re.IGNORECASE | re.MULTILINE,
    )

    if not deponent_match or not prayer_match:
        return []

    body_text = text[
        deponent_match.end():prayer_match.start()
    ]

    numbers = re.findall(
        r"(?m)^\s*(\d+)\.\s+",
        body_text,
    )

    return [int(number) for number in numbers]


def check_entity_accuracy(
    generated_text: str,
    mapped_data: Dict,
) -> Dict:
    """
    Check whether important case entities from the source
    appear correctly in the generated affidavit.
    """

    expected_entities = {
        "Court": mapped_data["document"]["court"],
        "Jurisdiction": mapped_data["document"]["jurisdiction"],
        "Case Number": mapped_data["document"]["case_number"],
        "Year": mapped_data["document"]["year"],
        "Petitioner": mapped_data["parties"]["petitioner"],
        "Respondent No.1": mapped_data["parties"]["respondent_1"],
        "Respondent No.2": mapped_data["parties"]["respondent_2"],
        "Deponent": mapped_data["deponent"]["name"],
        "Designation": mapped_data["deponent"]["designation"],
        "Organisation": mapped_data["deponent"]["organisation"],
        "Address": mapped_data["deponent"]["address"],
    }

    missing = []

    for name, value in expected_entities.items():
        if value and value.lower() not in generated_text.lower():
            missing.append(f"{name}: {value}")

    total_entities = len(expected_entities)
    correct_entities = total_entities - len(missing)

    score = round(
        25 * correct_entities / total_entities,
        2,
    )

    return {
        "score": score,
        "max_score": 25,
        "missing": missing,
    }


def check_completeness(
    generated_text: str,
    mapped_data: Dict,
) -> Dict:
    """
    Check whether important source information is present.
    """

    required_items = [
        "do hereby solemnly affirm and state as under",
        "PRAYER",
        "Solemnly affirmed",
        "VERIFICATION",
        "DEPONENT",
        "EXHIBIT",
    ]

    missing = []

    for item in required_items:
        if item.lower() not in generated_text.lower():
            missing.append(item)

    communication_date = mapped_data["reply"].get(
        "communication_date",
        "",
    )

    if communication_date:
        formatted_date = format_communication_date(
            communication_date
        )

        if formatted_date.lower() not in generated_text.lower():
            missing.append(
                f"Communication date: {formatted_date}"
            )

    total_items = len(required_items)

    if communication_date:
        total_items += 1

    present_items = total_items - len(missing)

    score = round(
        15 * present_items / total_items,
        2,
    )

    return {
        "score": max(score, 0),
        "max_score": 15,
        "missing": missing,
    }


def check_structure(generated_text: str) -> Dict:
    """
    Check the required affidavit sections.
    """

    required_sections = [
        "IN THE HIGH COURT OF JUDICATURE AT",
        "JURISDICTION",
        "NO.",
        "VERSUS",
        "AFFIDAVIT IN REPLY",
        "PRAYER",
        "Solemnly affirmed",
        "Before Me",
        "VERIFICATION",
        "DEPONENT",
    ]

    missing = []

    for section in required_sections:
        if section.lower() not in generated_text.lower():
            missing.append(section)

    present_sections = (
        len(required_sections) - len(missing)
    )

    score = round(
        20 * present_sections / len(required_sections),
        2,
    )

    return {
        "score": score,
        "max_score": 20,
        "missing": missing,
    }


def check_consistency(
    generated_text: str,
    mapped_data: Dict,
) -> Dict:
    """
    Check internal consistency such as paragraph numbering,
    verification range and respondent number.
    """

    issues = []

    paragraphs = extract_body_paragraphs(
        generated_text
    )

    # ---------------------------------------------------------
    # Paragraph numbering
    # ---------------------------------------------------------

    expected_numbers = list(
        range(1, len(paragraphs) + 1)
    )

    if paragraphs != expected_numbers:
        issues.append(
            f"Paragraph numbering is not continuous: "
            f"{paragraphs}"
        )

    # ---------------------------------------------------------
    # Verification paragraph range
    # ---------------------------------------------------------

    verification_match = re.search(
        r"paragraphs\s+1\s+to\s+(\d+)",
        generated_text,
        re.IGNORECASE,
    )

    if verification_match:
        verification_number = int(
            verification_match.group(1)
        )

        if verification_number != len(paragraphs):
            issues.append(
                f"Verification says paragraphs 1 to "
                f"{verification_number}, but "
                f"{len(paragraphs)} body paragraphs "
                f"were found."
            )
    else:
        issues.append(
            "Verification paragraph range not found."
        )

    # ---------------------------------------------------------
    # Respondent number
    # ---------------------------------------------------------

    if (
        "AFFIDAVIT IN REPLY ON BEHALF OF "
        "RESPONDENT NO. 2"
        not in generated_text.upper()
    ):
        issues.append(
            "Affidavit title does not specify "
            "Respondent No. 2."
        )

    # ---------------------------------------------------------
    # Deponent name
    # ---------------------------------------------------------

    deponent_name = mapped_data["deponent"].get(
        "name",
        "",
    )

    if (
        deponent_name
        and deponent_name.lower()
        not in generated_text.lower()
    ):
        issues.append(
            "Deponent name is inconsistent or missing."
        )

    score = max(
        15 - (5 * len(issues)),
        0,
    )

    return {
        "score": score,
        "max_score": 15,
        "issues": issues,
        "paragraphs_found": paragraphs,
    }


def check_template_fidelity(
    generated_text: str,
) -> Dict:
    """
    Check important formatting and structural conventions
    from the supplied reference.
    """

    issues = []

    # ---------------------------------------------------------
    # Prayer
    # ---------------------------------------------------------

    prayer_match = re.search(
        r"PRAYER(.*?)(?=Solemnly affirmed)",
        generated_text,
        re.IGNORECASE | re.DOTALL,
    )

    if prayer_match:
        prayer_text = prayer_match.group(1)

        if not re.search(
            r"\(a\)",
            prayer_text,
            re.IGNORECASE,
        ):
            issues.append(
                "Prayer item (a) is missing."
            )

        if not re.search(
            r"\(b\)",
            prayer_text,
            re.IGNORECASE,
        ):
            issues.append(
                "Prayer item (b) is missing."
            )

        if not re.search(
            r"\(c\)",
            prayer_text,
            re.IGNORECASE,
        ):
            issues.append(
                "Prayer item (c) is missing."
            )

    else:
        issues.append(
            "Prayer section could not be analysed."
        )

    # ---------------------------------------------------------
    # Affidavit title
    # ---------------------------------------------------------

    if not re.search(
        r"AFFIDAVIT IN REPLY ON BEHALF OF "
        r"RESPONDENT NO\.\s*2",
        generated_text,
        re.IGNORECASE,
    ):
        issues.append(
            "Affidavit title does not match "
            "reference structure."
        )

    # ---------------------------------------------------------
    # Verification
    # ---------------------------------------------------------

    if not re.search(
        r"^\s*VERIFICATION\s*$",
        generated_text,
        re.IGNORECASE | re.MULTILINE,
    ):
        issues.append(
            "Verification heading is missing."
        )

    # ---------------------------------------------------------
    # Status labels
    # ---------------------------------------------------------

    if not re.search(
        r"\.\.\.Petitioner",
        generated_text,
        re.IGNORECASE,
    ):
        issues.append(
            "Petitioner status label is missing."
        )

    if not re.search(
        r"\.\.\.Respondent No\.1",
        generated_text,
        re.IGNORECASE,
    ):
        issues.append(
            "Respondent No.1 status label is missing."
        )

    if not re.search(
        r"\.\.\.Respondent No\.2",
        generated_text,
        re.IGNORECASE,
    ):
        issues.append(
            "Respondent No.2 status label is missing."
        )

    score = max(
        15 - (3 * len(issues)),
        0,
    )

    return {
        "score": score,
        "max_score": 15,
        "issues": issues,
    }


def check_hallucinations(
    generated_text: str,
    mapped_data: Dict,
) -> Dict:
    """
    Deterministic hallucination check.

    Checks for unexpected case numbers and dates.

    Respondent numbers and paragraph numbers are deliberately
    ignored because they are not case numbers.
    """

    issues = []

    expected_case_number = str(
        mapped_data["document"]["case_number"]
    )

    expected_year = str(
        mapped_data["document"]["year"]
    )

    # ---------------------------------------------------------
    # CASE NUMBER CHECK
    # ---------------------------------------------------------
    # Only inspect the actual case-number line.
    #
    # Example:
    # WRIT PETITION NO. 1847 OF 2026
    #
    # This avoids incorrectly treating:
    # 1. State of Maharashtra
    # 2. MMRDA
    # 1. paragraph
    # 2. paragraph
    # as case numbers.

    case_match = re.search(
        r"(?:WRIT PETITION|PETITION|APPLICATION)"
        r"\s+NO\.\s*(\d+)\s+OF\s+(\d{4})",
        generated_text,
        re.IGNORECASE,
    )

    if not case_match:
        issues.append(
            "Case number pattern could not be identified."
        )

    else:
        generated_case_number = case_match.group(1)
        generated_case_year = case_match.group(2)

        if generated_case_number != expected_case_number:
            issues.append(
                f"Unexpected case number found: "
                f"{generated_case_number}"
            )

        if generated_case_year != expected_year:
            issues.append(
                f"Unexpected case year found: "
                f"{generated_case_year}"
            )

    # ---------------------------------------------------------
    # DATE CHECK
    # ---------------------------------------------------------

    dates = re.findall(
        r"\b\d{1,2}(?:st|nd|rd|th)?\s+"
        r"[A-Za-z]+\s+\d{4}\b",
        generated_text,
    )

    allowed_dates = []

    communication_date = mapped_data["reply"].get(
        "communication_date",
        "",
    )

    attestation_date = mapped_data["attestation"].get(
        "date",
        "",
    )

    if communication_date:
        allowed_dates.append(
            format_communication_date(
                communication_date
            )
        )

    if attestation_date:
        allowed_dates.append(
            format_attestation_date(
                attestation_date
            )
        )

    for date in dates:
        if date not in allowed_dates:
            issues.append(
                f"Unexpected date found: {date}"
            )

    # ---------------------------------------------------------
    # EXPECTED YEAR
    # ---------------------------------------------------------

    if expected_year not in generated_text:
        issues.append(
            f"Expected year {expected_year} not found."
        )

    # ---------------------------------------------------------
    # SCORE
    # ---------------------------------------------------------

    if not issues:
        score = 10
    else:
        score = max(
            10 - (3 * len(issues)),
            0,
        )

    return {
        "score": score,
        "max_score": 10,
        "issues": issues,
    }


def format_communication_date(
    date_text: str,
) -> str:
    """
    Convert:
        15 July 2026

    into:
        15th July 2026
    """

    match = re.match(
        r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})",
        date_text.strip(),
    )

    if not match:
        return date_text

    day = int(match.group(1))
    month = match.group(2)
    year = match.group(3)

    if 10 < day % 100 < 14:
        suffix = "th"
    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd",
        }.get(day % 10, "th")

    return f"{day}{suffix} {month} {year}"


def format_attestation_date(
    date_text: str,
) -> str:
    """
    Convert:
        5 September 2026

    into:
        5th day of September 2026
    """

    match = re.match(
        r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})",
        date_text.strip(),
    )

    if not match:
        return date_text

    day = int(match.group(1))
    month = match.group(2)
    year = match.group(3)

    if 10 < day % 100 < 14:
        suffix = "th"
    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd",
        }.get(day % 10, "th")

    return f"{day}{suffix} day of {month} {year}"


def evaluate_affidavit(
    generated_text: str,
    mapped_data: Dict,
) -> Dict:
    """
    Run all evaluation dimensions and produce
    an overall score and issue list.
    """

    entity_result = check_entity_accuracy(
        generated_text,
        mapped_data,
    )

    completeness_result = check_completeness(
        generated_text,
        mapped_data,
    )

    structure_result = check_structure(
        generated_text,
    )

    consistency_result = check_consistency(
        generated_text,
        mapped_data,
    )

    template_result = check_template_fidelity(
        generated_text,
    )

    hallucination_result = check_hallucinations(
        generated_text,
        mapped_data,
    )

    dimensions = {
        "Entity Accuracy": entity_result,
        "Completeness": completeness_result,
        "Structure": structure_result,
        "Consistency": consistency_result,
        "Template Fidelity": template_result,
        "Hallucination": hallucination_result,
    }

    overall_score = sum(
        result["score"]
        for result in dimensions.values()
    )

    issues = []

    issues.extend(
        entity_result["missing"]
    )

    issues.extend(
        completeness_result["missing"]
    )

    issues.extend(
        structure_result["missing"]
    )

    issues.extend(
        consistency_result["issues"]
    )

    issues.extend(
        template_result["issues"]
    )

    issues.extend(
        hallucination_result["issues"]
    )

    return {
        "overall_score": round(
            overall_score,
            2,
        ),
        "dimensions": dimensions,
        "issues": issues,
    }


def generate_evaluation_report(
    evaluation: Dict,
) -> str:
    """
    Convert evaluation results into Markdown.
    """

    lines = []

    lines.append(
        "# Legal Document Evaluation Report"
    )

    lines.append("")

    lines.append(
        f"## Overall Score: "
        f"{evaluation['overall_score']}/100"
    )

    lines.append("")

    lines.append(
        "## Dimension Scores"
    )

    lines.append("")

    for name, result in evaluation[
        "dimensions"
    ].items():

        lines.append(
            f"- **{name}:** "
            f"{result['score']}/"
            f"{result['max_score']}"
        )

    lines.append("")

    lines.append(
        "## Issues Detected"
    )

    lines.append("")

    if evaluation["issues"]:

        for issue in evaluation["issues"]:
            lines.append(
                f"- {issue}"
            )

    else:
        lines.append(
            "- No issues detected."
        )

    lines.append("")

    lines.append(
        "## Evaluation Method"
    )

    lines.append("")

    lines.append(
        "The generated affidavit was evaluated "
        "against the structured case information "
        "and the required affidavit structure using "
        "deterministic Python checks. The evaluation "
        "covers entity accuracy, completeness, "
        "structure, consistency, template fidelity "
        "and potential hallucinated dates or case "
        "numbers."
    )

    return "\n".join(lines)


if __name__ == "__main__":

    from document_parser import extract_text_from_pdf
    from entity_extractor import extract_case_entities
    from mapper import map_case_to_affidavit

    case_path = (
        "data/03_Case_Information.pdf"
    )

    generated_path = (
        "outputs/generated_affidavit.txt"
    )

    # ---------------------------------------------------------
    # Read case information
    # ---------------------------------------------------------

    case_text = extract_text_from_pdf(
        case_path
    )

    # ---------------------------------------------------------
    # Extract entities
    # ---------------------------------------------------------

    entities = extract_case_entities(
        case_text
    )

    # ---------------------------------------------------------
    # Create structured mapping
    # ---------------------------------------------------------

    mapped_data = map_case_to_affidavit(
        entities
    )

    # ---------------------------------------------------------
    # Read generated affidavit
    # ---------------------------------------------------------

    try:

        with open(
            generated_path,
            "r",
            encoding="utf-8",
        ) as file:

            generated_text = file.read()

    except FileNotFoundError:

        print(
            "Generated affidavit text file not found."
        )

        print(
            "Expected file:"
        )

        print(
            "outputs/generated_affidavit.txt"
        )

        raise SystemExit

    # ---------------------------------------------------------
    # Evaluate
    # ---------------------------------------------------------

    evaluation = evaluate_affidavit(
        generated_text,
        mapped_data,
    )

    # ---------------------------------------------------------
    # Generate report
    # ---------------------------------------------------------

    report = generate_evaluation_report(
        evaluation
    )

    # ---------------------------------------------------------
    # Save report
    # ---------------------------------------------------------

    import os

    os.makedirs(
        "outputs",
        exist_ok=True,
    )

    report_path = (
        "outputs/evaluation_report.md"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(report)

    # ---------------------------------------------------------
    # Print results
    # ---------------------------------------------------------

    print(report)

    print("")

    print(
        f"Evaluation report saved to: "
        f"{report_path}"
    )