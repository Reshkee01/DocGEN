import re
from typing import Dict


def extract_case_entities(text: str) -> Dict:
    """
    Extract structured entities from the Case Information document.
    """

    entities = {}

    def extract_field(label: str, next_label: str) -> str:
        pattern = rf"{re.escape(label)}\s*(.*?)\s*(?={re.escape(next_label)})"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            return " ".join(match.group(1).split()).strip()

        return ""

    # Basic case details
    entities["document_type"] = extract_field(
        "Document Type", "Court"
    )

    court_match = re.search(
        r"\bCourt\s*\n?\s*(IN THE HIGH COURT OF JUDICATURE AT [A-Z]+)",
        text,
        re.IGNORECASE,
    )

    entities["court"] = (
        court_match.group(1).strip()
        if court_match
        else ""
    )

    entities["jurisdiction"] = extract_field(
        "Jurisdiction", "Proceeding Type"
    )

    entities["proceeding_type"] = extract_field(
        "Proceeding Type", "Case Number"
    )

    entities["case_number"] = extract_field(
        "Case Number", "Year"
    )

    entities["year"] = extract_field(
        "Year", "Petitioner"
    )

    entities["petitioner"] = extract_field(
        "Petitioner", "Respondent No. 1"
    )

    entities["respondent_1"] = extract_field(
        "Respondent No. 1", "Respondent No. 2"
    )

    entities["respondent_2"] = extract_field(
        "Respondent No. 2", "Filed on behalf of"
    )

    entities["filed_on_behalf_of"] = extract_field(
        "Filed on behalf of", "2. Deponent Details"
    )

    # Deponent details
    entities["deponent"] = extract_field(
        "Name", "Designation"
    )

    entities["designation"] = extract_field(
        "Designation", "Organisation"
    )

    entities["organisation"] = extract_field(
        "Organisation", "Address"
    )

    entities["address"] = extract_field(
        "Address", "Verification verb"
    )

    entities["verification_verb"] = extract_field(
        "Verification verb", "3. Reply Points"
    )
    # Reply points
    reply_points = {}

    point_pattern = re.compile(
        r"Point\s+(\d+)\s+—\s+(.*?)(?=Point\s+\d+\s+—|4\.\s*Prayer|Prayer:|$)",
        re.IGNORECASE | re.DOTALL,
        )

    for match in point_pattern.finditer(text):
        point_number = int(match.group(1))
        point_text = match.group(2).replace("●", "")
        point_text = point_text.replace("\u200b", "")
        point_text = " ".join(point_text.split())
        reply_points[point_number] = point_text

    entities["reply_points"] = reply_points

    # Communication date
    communication_match = re.search(
        r"communication dated\s+(\d{1,2}\s+\w+\s+\d{4})",
        text,
        re.IGNORECASE,
    )

    entities["communication_date"] = (
        communication_match.group(1)
        if communication_match
        else ""
    )

    # Exhibit reference
    exhibit_match = re.search(
        r"EXHIBIT[-–—]?['‘]?A['’]?",
        text,
        re.IGNORECASE,
    )

    entities["exhibit"] = (
        exhibit_match.group(0)
        if exhibit_match
        else ""
    )

    # Attestation details
    place_match = re.search(
        r"Place\s+([A-Za-z ,]+?)(?=\s+Date)",
        text,
        re.IGNORECASE,
    )

    date_match = re.search(
        r"Date\s+(\d{1,2}\s+\w+\s+\d{4})",
        text,
        re.IGNORECASE,
    )

    entities["attestation_place"] = (
        place_match.group(1).strip()
        if place_match
        else ""
    )

    entities["attestation_date"] = (
        date_match.group(1).strip()
        if date_match
        else ""
    )

    # Advocate details
    advocate_match = re.search(
        r"Advocate Firm\s+(.+?)\s+Acting for",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    entities["advocate_firm"] = (
        " ".join(advocate_match.group(1).split())
        if advocate_match
        else ""
    )

    acting_for_match = re.search(
        r"Acting for\s+(.+?)(?=\s+This file contains|$)",
        text,
        re.IGNORECASE | re.DOTALL,
        )

    entities["acting_for"] = (
        " ".join(acting_for_match.group(1).split())
        if acting_for_match
        else ""
    )
    # Clean common extraction artifacts
    entities = {
        key: value.replace("●", "").strip() if isinstance(value, str) else value
        for key, value in entities.items()
        }

    return entities


if __name__ == "__main__":
    from document_parser import extract_text_from_pdf

    case_path = "data/03_Case_Information.pdf"

    text = extract_text_from_pdf(case_path)

    entities = extract_case_entities(text)

    print("Extracted Case Entities")
    print("----------------------")

    for key, value in entities.items():
        print(f"{key}: {value}")