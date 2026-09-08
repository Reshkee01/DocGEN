from typing import Dict
import json


def map_case_to_affidavit(entities: Dict) -> Dict:
    """
    Convert extracted case entities into a structured
    intermediate representation for affidavit generation.
    """

    reply_points = entities.get("reply_points", {})

    mapped = {
        "document": {
            "type": entities.get("document_type", ""),
            "court": entities.get("court", ""),
            "jurisdiction": entities.get("jurisdiction", ""),
            "proceeding_type": entities.get("proceeding_type", ""),
            "case_number": entities.get("case_number", ""),
            "year": entities.get("year", ""),
        },

        "parties": {
            "petitioner": entities.get("petitioner", ""),
            "respondent_1": entities.get("respondent_1", ""),
            "respondent_2": entities.get("respondent_2", ""),
        },

        "deponent": {
            "name": entities.get("deponent", ""),
            "designation": entities.get("designation", ""),
            "organisation": entities.get("organisation", ""),
            "address": entities.get("address", ""),
            "acting_for": entities.get("filed_on_behalf_of", ""),
        },

        "reply": {
            "points": reply_points,
            "communication_date": entities.get("communication_date", ""),
            "exhibit": entities.get("exhibit", ""),
        },

        "attestation": {
            "place": entities.get("attestation_place", ""),
            "date": entities.get("attestation_date", ""),
            "verification_verb": entities.get("verification_verb", ""),
        },

        "advocate": {
            "firm": entities.get("advocate_firm", ""),
            "acting_for": entities.get("acting_for", ""),
        },
    }

    return mapped


if __name__ == "__main__":
    from document_parser import extract_text_from_pdf
    from entity_extractor import extract_case_entities

    case_path = "data/03_Case_Information.pdf"

    text = extract_text_from_pdf(case_path)
    entities = extract_case_entities(text)
    mapped_data = map_case_to_affidavit(entities)

    # Create outputs folder if it does not exist
    import os
    os.makedirs("outputs", exist_ok=True)

    # Save structured intermediate representation
    json_path = "outputs/mapped_case.json"

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(
            mapped_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("Mapped Affidavit Data")
    print("---------------------")

    for section, data in mapped_data.items():
        print(f"\n[{section}]")
        print(data)

    print(f"\nStructured case data saved to: {json_path}")