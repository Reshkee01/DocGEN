import os
import streamlit as st

from src.document_parser import extract_text_from_pdf
from src.entity_extractor import extract_case_entities
from src.template_analyzer import analyze_affidavit_structure
from src.mapper import map_case_to_affidavit
from src.generator import (
    generate_affidavit,
    validate_before_generation,
)
from src.evaluator import (
    evaluate_affidavit,
    generate_evaluation_report,
)
from src.llm_generator import (
    load_model,
    review_affidavit,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Legal Document Generation Agent",
    page_icon="⚖️",
    layout="wide",
)


# =========================================================
# CREATE OUTPUT DIRECTORY
# =========================================================

os.makedirs("outputs", exist_ok=True)


# =========================================================
# SESSION STATE
# =========================================================

if "workflow_completed" not in st.session_state:
    st.session_state.workflow_completed = False

if "mapped_data" not in st.session_state:
    st.session_state.mapped_data = None

if "evaluation" not in st.session_state:
    st.session_state.evaluation = None

if "report" not in st.session_state:
    st.session_state.report = None

if "output_path" not in st.session_state:
    st.session_state.output_path = None

if "ai_review" not in st.session_state:
    st.session_state.ai_review = None

if "template_structure" not in st.session_state:
    st.session_state.template_structure = None


# =========================================================
# TITLE
# =========================================================

st.title("⚖️ Legal Document Generation & Evaluation Agent")

st.write(
    "Extract case information, understand the reference affidavit "
    "structure, generate an Affidavit in Reply, validate it, "
    "and evaluate the generated document."
)

st.divider()


# =========================================================
# UPLOAD
# =========================================================

st.header("1. Upload Case Information")

uploaded_file = st.file_uploader(
    "Upload the Case Information PDF",
    type=["pdf"],
)


# =========================================================
# GENERATE BUTTON
# =========================================================

if uploaded_file is not None:

    if st.button(
        "🚀 Generate & Evaluate Affidavit",
        type="primary",
    ):

        try:

            # -------------------------------------------------
            # REFERENCE TEMPLATE ANALYSIS
            # -------------------------------------------------

            reference_path = (
                "data/02 Affidavit in Reply Sample.docx.pdf"
            )

            with st.spinner(
                "Understanding reference affidavit structure..."
            ):

                reference_text = extract_text_from_pdf(
                    reference_path
                )

                template_structure = analyze_affidavit_structure(
                    reference_text
                )

                required_sections = [
                    "forum_heading",
                    "jurisdiction",
                    "case_number",
                    "cause_title",
                    "versus",
                    "respondents",
                    "affidavit_title",
                    "deponent_clause",
                    "reply_paragraphs",
                    "prayer",
                    "jurat",
                    "attestation",
                    "verification",
                    "advocate_block",
                ]

                missing_sections = [
                    section
                    for section in required_sections
                    if section not in template_structure["sections"]
                ]

                if missing_sections:
                    raise ValueError(
                        "Reference template analysis failed. "
                        f"Missing sections: {', '.join(missing_sections)}"
                    )


            # -------------------------------------------------
            # SAVE UPLOADED PDF
            # -------------------------------------------------

            input_path = (
                "outputs/uploaded_case_information.pdf"
            )

            with open(
                input_path,
                "wb",
            ) as file:

                file.write(
                    uploaded_file.getbuffer()
                )


            # -------------------------------------------------
            # EXTRACT TEXT
            # -------------------------------------------------

            with st.spinner(
                "Extracting case information..."
            ):

                text = extract_text_from_pdf(
                    input_path
                )


            # -------------------------------------------------
            # EXTRACT ENTITIES
            # -------------------------------------------------

            with st.spinner(
                "Extracting structured case entities..."
            ):

                entities = extract_case_entities(
                    text
                )

                mapped_data = map_case_to_affidavit(
                    entities
                )


            # -------------------------------------------------
            # SAVE STRUCTURED CASE DATA
            # -------------------------------------------------

            mapped_data_path = (
                "outputs/mapped_case.json"
            )

            import json

            with open(
                mapped_data_path,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    mapped_data,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )


            # -------------------------------------------------
            # PRE-GENERATION VALIDATION
            # -------------------------------------------------

            with st.spinner(
                "Validating case information..."
            ):

                validate_before_generation(
                    mapped_data
                )


            # -------------------------------------------------
            # GENERATE AFFIDAVIT
            # -------------------------------------------------

            output_path = (
                "outputs/generated_affidavit.docx"
            )

            with st.spinner(
                "Generating Affidavit in Reply..."
            ):

                generate_affidavit(
                    mapped_data,
                    output_path,
                )


            # -------------------------------------------------
            # READ GENERATED TEXT
            # -------------------------------------------------

            generated_text_path = (
                "outputs/generated_affidavit.txt"
            )

            if not os.path.exists(
                generated_text_path
            ):

                raise FileNotFoundError(
                    "Generated affidavit text file was not created."
                )

            with open(
                generated_text_path,
                "r",
                encoding="utf-8",
            ) as file:

                generated_text = file.read()


            # -------------------------------------------------
            # DETERMINISTIC EVALUATION
            # -------------------------------------------------

            with st.spinner(
                "Evaluating generated affidavit..."
            ):

                evaluation = evaluate_affidavit(
                    generated_text,
                    mapped_data,
                )

                report = generate_evaluation_report(
                    evaluation
                )


            # -------------------------------------------------
            # LOCAL LLM REVIEW
            # -------------------------------------------------

            with st.spinner(
                "Running local AI review..."
            ):

                tokenizer, model, device = load_model()

                ai_review = review_affidavit(
                    generated_text,
                    mapped_data,
                    tokenizer,
                    model,
                    device,
                )


            # -------------------------------------------------
            # ADD TEMPLATE ANALYSIS TO REPORT
            # -------------------------------------------------

            template_report = (
                "\n\n## Reference Template Analysis\n\n"
                f"- Document type: "
                f"{template_structure['document_type']}\n"
                f"- Sections detected: "
                f"{len(template_structure['sections'])}\n"
                f"- Body paragraph count in reference: "
                f"{template_structure['body_paragraph_count']}\n"
                f"- Required template sections detected: "
                f"{len(required_sections)}/{len(required_sections)}\n"
            )

            report += template_report


            # -------------------------------------------------
            # ADD AI REVIEW TO REPORT
            # -------------------------------------------------

            report += (
                "\n\n## AI Review\n\n"
                + ai_review
            )


            # =================================================
            # AUTOMATICALLY SAVE FINAL EVALUATION REPORT
            # =================================================

            report_path = (
                "outputs/evaluation_report.md"
            )

            with open(
                report_path,
                "w",
                encoding="utf-8",
            ) as file:

                file.write(
                    report
                )


            # -------------------------------------------------
            # SAVE RESULTS IN SESSION STATE
            # -------------------------------------------------

            st.session_state.mapped_data = (
                mapped_data
            )

            st.session_state.evaluation = (
                evaluation
            )

            st.session_state.report = (
                report
            )

            st.session_state.output_path = (
                output_path
            )

            st.session_state.ai_review = (
                ai_review
            )

            st.session_state.template_structure = (
                template_structure
            )

            st.session_state.workflow_completed = True


            # -------------------------------------------------
            # SUCCESS MESSAGE
            # -------------------------------------------------

            st.success(
                "Complete workflow finished successfully!"
            )

            st.info(
                "Evaluation report automatically saved to "
                "`outputs/evaluation_report.md`"
            )


        except Exception as error:

            st.error(
                f"Workflow failed: {error}"
            )


# =========================================================
# DISPLAY RESULTS
# =========================================================

if st.session_state.workflow_completed:

    mapped_data = (
        st.session_state.mapped_data
    )

    evaluation = (
        st.session_state.evaluation
    )

    report = (
        st.session_state.report
    )

    output_path = (
        st.session_state.output_path
    )

    template_structure = (
        st.session_state.template_structure
    )


    # =====================================================
    # TEMPLATE ANALYSIS
    # =====================================================

    st.header(
        "2. Reference Template Analysis"
    )

    st.success(
        "✓ Reference affidavit structure analyzed successfully."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            label="Sections Detected",
            value=len(
                template_structure["sections"]
            ),
        )

    with col2:

        st.metric(
            label="Reference Body Paragraphs",
            value=template_structure[
                "body_paragraph_count"
            ],
        )

    with col3:

        st.metric(
            label="Document Type",
            value=template_structure[
                "document_type"
            ],
        )

    with st.expander(
        "View Detected Template Sections"
    ):

        for section in template_structure[
            "sections"
        ]:

            st.write(
                f"✓ {section.replace('_', ' ').title()}"
            )


    # =====================================================
    # EXTRACTED INFORMATION
    # =====================================================

    st.header(
        "3. Extracted Case Information"
    )

    document_data = (
        mapped_data["document"]
    )

    parties = (
        mapped_data["parties"]
    )

    deponent = (
        mapped_data["deponent"]
    )

    reply = (
        mapped_data["reply"]
    )

    attestation = (
        mapped_data["attestation"]
    )


    # -----------------------------------------------------
    # DOCUMENT
    # -----------------------------------------------------

    st.subheader(
        "Document"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"**Court:** "
            f"{document_data['court']}"
        )

        st.write(
            f"**Jurisdiction:** "
            f"{document_data['jurisdiction']}"
        )

        st.write(
            f"**Proceeding Type:** "
            f"{document_data['proceeding_type']}"
        )

    with col2:

        st.write(
            f"**Case Number:** "
            f"{document_data['case_number']}"
        )

        st.write(
            f"**Year:** "
            f"{document_data['year']}"
        )


    # -----------------------------------------------------
    # PARTIES
    # -----------------------------------------------------

    st.subheader(
        "Parties"
    )

    st.write(
        f"**Petitioner:** "
        f"{parties['petitioner']}"
    )

    st.write(
        f"**Respondent No.1:** "
        f"{parties['respondent_1']}"
    )

    st.write(
        f"**Respondent No.2:** "
        f"{parties['respondent_2']}"
    )


    # -----------------------------------------------------
    # DEPONENT
    # -----------------------------------------------------

    st.subheader(
        "Deponent"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"**Name:** "
            f"{deponent['name']}"
        )

        st.write(
            f"**Designation:** "
            f"{deponent['designation']}"
        )

    with col2:

        st.write(
            f"**Organisation:** "
            f"{deponent['organisation']}"
        )

        st.write(
            f"**Address:** "
            f"{deponent['address']}"
        )


    # -----------------------------------------------------
    # REPLY
    # -----------------------------------------------------

    st.subheader(
        "Reply Information"
    )

    st.write(
        f"**Communication Date:** "
        f"{reply['communication_date']}"
    )

    st.write(
        f"**Exhibit:** "
        f"{reply['exhibit']}"
    )


    # =====================================================
    # VALIDATION
    # =====================================================

    st.header(
        "4. Validation"
    )

    st.success(
        "✓ Reference template validation passed."
    )

    st.success(
        "✓ Pre-generation validation passed."
    )


    # =====================================================
    # GENERATED DOCUMENT
    # =====================================================

    st.header(
        "5. Generated Affidavit"
    )

    st.success(
        "✓ Affidavit generated successfully."
    )

    if os.path.exists(
        output_path
    ):

        with open(
            output_path,
            "rb",
        ) as file:

            st.download_button(
                label="📄 Download Affidavit (.docx)",
                data=file,
                file_name="generated_affidavit.docx",
                mime=(
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                key="download_affidavit",
            )


    # =====================================================
    # EVALUATION
    # =====================================================

    st.header(
        "6. Document Evaluation"
    )


    # -----------------------------------------------------
    # OVERALL SCORE
    # -----------------------------------------------------

    score = evaluation[
        "overall_score"
    ]

    st.metric(
        label="Overall Score",
        value=f"{score}/100",
    )


    # -----------------------------------------------------
    # DIMENSION SCORES
    # -----------------------------------------------------

    st.subheader(
        "Evaluation Dimensions"
    )

    dimensions = evaluation[
        "dimensions"
    ]

    col1, col2, col3 = st.columns(3)

    dimension_items = list(
        dimensions.items()
    )

    for index, (
        name,
        result,
    ) in enumerate(
        dimension_items
    ):

        column = [
            col1,
            col2,
            col3,
        ][index % 3]

        with column:

            st.metric(
                label=name,
                value=(
                    f"{result['score']}/"
                    f"{result['max_score']}"
                ),
            )


    # =====================================================
    # ISSUES
    # =====================================================

    st.subheader(
        "Detected Issues"
    )

    issues = evaluation[
        "issues"
    ]

    if issues:

        for issue in issues:

            st.warning(
                issue
            )

    else:

        st.success(
            "✓ No issues detected."
        )


    # =====================================================
    # AI REVIEW
    # =====================================================

    st.subheader(
        "🤖 AI Review"
    )

    st.info(
        st.session_state.ai_review
    )


    # =====================================================
    # FULL REPORT
    # =====================================================

    with st.expander(
        "View Full Evaluation Report"
    ):

        st.markdown(
            report
        )


    # =====================================================
    # DOWNLOAD EVALUATION REPORT
    # =====================================================

    st.header(
        "7. Download Evaluation Report"
    )

    st.download_button(
        label="📊 Download Evaluation Report (.md)",
        data=report,
        file_name="evaluation_report.md",
        mime="text/markdown",
        key="download_report",
    )

    st.success(
        "✓ Evaluation report is automatically saved at "
        "`outputs/evaluation_report.md`"
    )


    # =====================================================
    # COMPLETION MESSAGE
    # =====================================================

    st.divider()

    st.success(
        "🎉 All required assignment workflow steps are complete."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Prototype for the Brainwonders AI Intern Assignment — "
    "Legal Document Generation & Evaluation Agent."
)
