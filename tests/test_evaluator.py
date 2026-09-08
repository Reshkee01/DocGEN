from src.document_parser import extract_text_from_pdf
from src.entity_extractor import extract_case_entities
from src.mapper import map_case_to_affidavit
from src.evaluator import evaluate_affidavit
from docx import Document


# -------------------------------------------------
# Read case information
# -------------------------------------------------

case_text = extract_text_from_pdf(
    "data/03_Case_Information.pdf"
)

case_entities = extract_case_entities(case_text)


# Convert extracted entities into structured mapped data
mapped_data = map_case_to_affidavit(case_entities)


# -------------------------------------------------
# Read the REAL generated document
# -------------------------------------------------

document = Document(
    "outputs/generated_affidavit.docx"
)

generated_text = "\n".join(
    paragraph.text
    for paragraph in document.paragraphs
    if paragraph.text.strip()
)


# -------------------------------------------------
# TEST 1 — Original Document
# -------------------------------------------------

print("\nTEST 1: Original Document")
print("========================")

result = evaluate_affidavit(
    generated_text,
    mapped_data
)

print(
    f"Score: {result['overall_score']}/100"
)

print("Issues:")

if result["issues"]:
    for issue in result["issues"]:
        print("-", issue)
else:
    print("- No issues detected.")


# -------------------------------------------------
# TEST 2 — Artificially create a WRONG version
# -------------------------------------------------

wrong_text = generated_text.replace(
    "WRIT PETITION NO. 1847 OF 2026",
    "WRIT PETITION NO. 9999 OF 2026"
)


print("\nTEST 2: Artificial Wrong Case Number")
print("====================================")

result_wrong = evaluate_affidavit(
    wrong_text,
    mapped_data
)

print(
    f"Score: {result_wrong['overall_score']}/100"
)

print("Issues:")

if result_wrong["issues"]:
    for issue in result_wrong["issues"]:
        print("-", issue)
else:
    print("- No issues detected.")