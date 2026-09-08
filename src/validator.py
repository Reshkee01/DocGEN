import re
from typing import Dict
from docx import Document

def extract_text_from_docx(docx_path: str) -> str:
    document = Document(docx_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text.strip())

    return "\n".join(paragraphs)

def validate_affidavit(text: str) -> Dict:
    checks = []

    # -------------------------------------------------
    # Check 1: Required sections
    # -------------------------------------------------
    required_sections = [
        "IN THE HIGH COURT OF JUDICATURE AT BOMBAY",
        "ORDINARY ORIGINAL CIVIL JURISDICTION",
        "WRIT PETITION NO.",
        "AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO.",
        "PRAYER",
        "VERIFICATION",
    ]

    missing_sections = [
        section
        for section in required_sections
        if section.lower() not in text.lower()
    ]

    checks.append({
        "check": "Required sections",
        "passed": len(missing_sections) == 0,
        "details": (
            "All required sections are present."
            if not missing_sections
            else f"Missing sections: {missing_sections}"
        ),
    })

    # -------------------------------------------------
    # Check 2: Paragraph numbering
    # -------------------------------------------------
    deponent_start = re.search(
        r"do hereby solemnly affirm and state as under:",
        text,
        re.IGNORECASE,
    )

    prayer_start = re.search(
        r"^\s*PRAYER\s*$",
        text,
        re.IGNORECASE | re.MULTILINE,
    )

    if deponent_start and prayer_start:
        body_text = text[deponent_start.end():prayer_start.start()]

        paragraph_numbers = [
            int(number)
            for number in re.findall(
                r"(?m)^\s*(\d+)\.\s+",
                body_text
            )
        ]
    else:
        paragraph_numbers = []

    expected_numbers = list(range(1, len(paragraph_numbers) + 1))

    checks.append({
        "check": "Paragraph numbering",
        "passed": paragraph_numbers == expected_numbers,
        "details": (
            f"Paragraphs found: {paragraph_numbers}"
        ),
    })

    # -------------------------------------------------
    # Check 3: Verification range matches
    # paragraph count
    # -------------------------------------------------
    verification_match = re.search(
        r"paragraphs\s+1\s+to\s+(\d+)",
        text,
        re.IGNORECASE,
    )

    if verification_match:
        verified_end = int(verification_match.group(1))
        paragraph_count = len(paragraph_numbers)

        passed = verified_end == paragraph_count

        details = (
            f"Verification says paragraphs 1 to {verified_end}; "
            f"actual body paragraph count is {paragraph_count}."
        )
    else:
        passed = False
        details = "Verification paragraph range was not found."

    checks.append({
        "check": "Verification paragraph range",
        "passed": passed,
        "details": details,
    })

    # -------------------------------------------------
    # Check 4: Verification/jurat verb consistency
    # -------------------------------------------------
    jurat_affirm = bool(
        re.search(r"Solemnly affirmed at", text, re.IGNORECASE)
    )

    verification_affirm = bool(
        re.search(r"do hereby verify", text, re.IGNORECASE)
    )

    passed = jurat_affirm and verification_affirm

    checks.append({
        "check": "Verification consistency",
        "passed": passed,
        "details": (
            "Jurat uses 'Solemnly affirmed' and "
            "verification uses 'do hereby verify'."
            if passed
            else "Jurat/verification wording is inconsistent or missing."
        ),
    })

    # -------------------------------------------------
    # Check 5: Exhibit reference
    # -------------------------------------------------
    exhibit_found = bool(
        re.search(r"EXHIBIT[-–—]?['‘]?A['’]?", text, re.IGNORECASE)
    )

    checks.append({
        "check": "Exhibit reference",
        "passed": exhibit_found,
        "details": (
            "EXHIBIT-'A' reference is present."
            if exhibit_found
            else "EXHIBIT-'A' reference is missing."
        ),
    })

    return {
        "total_checks": len(checks),
        "passed_checks": sum(
            1 for check in checks if check["passed"]
        ),
        "failed_checks": sum(
            1 for check in checks if not check["passed"]
        ),
        "checks": checks,
    }


if __name__ == "__main__":
    docx_path = "outputs/generated_affidavit.docx"

    text = extract_text_from_docx(docx_path)
    result = validate_affidavit(text)

    print("Affidavit Validation")
    print("--------------------")
    print(f"Total checks: {result['total_checks']}")
    print(f"Passed: {result['passed_checks']}")
    print(f"Failed: {result['failed_checks']}")
    print()

    for check in result["checks"]:
        status = "PASS" if check["passed"] else "FAIL"

        print(f"[{status}] {check['check']}")
        print(f"      {check['details']}")