import re
from typing import Dict, List


def analyze_affidavit_structure(text: str) -> Dict:
    """
    Analyze the structure of an Affidavit in Reply reference document.
    """

    sections = []

    # 1. Forum heading
    if re.search(r"IN THE HIGH COURT OF JUDICATURE AT", text, re.IGNORECASE):
        sections.append("forum_heading")

    # 2. Jurisdiction
    if re.search(r"JURISDICTION", text, re.IGNORECASE):
        sections.append("jurisdiction")

    # 3. Case number
    if re.search(
        r"(WRIT PETITION|PETITION|APPLICATION).*NO\.\s*\d+.*OF\s*\d{4}",
        text,
        re.IGNORECASE,
    ):
        sections.append("case_number")

    # 4. Cause title
    if re.search(r"\.\.\.Petitioner", text, re.IGNORECASE):
        sections.append("cause_title")

    if re.search(r"VERSUS", text, re.IGNORECASE):
        sections.append("versus")

    if re.search(r"\.\.\.Respondent No\.\s*\d+", text, re.IGNORECASE):
        sections.append("respondents")

    # 5. Affidavit title
    if re.search(
        r"AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO\.",
        text,
        re.IGNORECASE,
    ):
        sections.append("affidavit_title")

    # 6. Deponent clause
    if re.search(
        r"do hereby solemnly affirm and state as under",
        text,
        re.IGNORECASE,
    ):
        sections.append("deponent_clause")

    # 7. Numbered reply paragraphs
    # Only inspect the text between the deponent clause and PRAYER.
    # This prevents numbers elsewhere in the document from being
    # incorrectly counted as body paragraphs.

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

    body_paragraphs = []

    if deponent_start and prayer_start:
        body_text = text[deponent_start.end():prayer_start.start()]

        paragraph_numbers = re.findall(
            r"(?m)^\s*(\d+)\.\s+",
            body_text
        )

        body_paragraphs = [int(number) for number in paragraph_numbers]

    if body_paragraphs:
        sections.append("reply_paragraphs")
        
    # 8. Prayer
    if re.search(r"^\s*PRAYER\s*$", text, re.IGNORECASE | re.MULTILINE):
        sections.append("prayer")

    # 9. Jurat / attestation
    if re.search(r"Solemnly affirmed at", text, re.IGNORECASE):
        sections.append("jurat")

    if re.search(r"Before Me", text, re.IGNORECASE):
        sections.append("attestation")

    # 10. Verification
    if re.search(r"^\s*VERIFICATION\s*$", text, re.IGNORECASE | re.MULTILINE):
        sections.append("verification")

    # 11. Advocate block
    if re.search(r"Advocates for the Respondent", text, re.IGNORECASE):
        sections.append("advocate_block")

    return {
        "document_type": "Affidavit in Reply",
        "sections": sections,
        "body_paragraph_count": len(body_paragraphs),
        "body_paragraph_numbers": body_paragraphs,
    }


if __name__ == "__main__":
    from document_parser import extract_text_from_pdf

    sample_path = "data/02 Affidavit in Reply Sample.docx.pdf"

    text = extract_text_from_pdf(sample_path)
    structure = analyze_affidavit_structure(text)

    print("Template Analysis")
    print("-----------------")

    for key, value in structure.items():
        print(f"{key}: {value}")