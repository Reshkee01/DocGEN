from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


MODEL_NAME = "HuggingFaceTB/SmolLM2-360M-Instruct"


def load_model():
    """
    Load the local Hugging Face model.
    Uses Apple Silicon MPS when available.
    """

    device = "mps" if torch.backends.mps.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    model = model.to(device)

    return tokenizer, model, device


def generate_text(
    prompt: str,
    tokenizer,
    model,
    device: str,
    max_new_tokens: int = 150,
):
    """
    Generate text using the local LLM.
    """

    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    chat_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(
        chat_prompt,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )

    generated_tokens = output[0][
        inputs["input_ids"].shape[-1]:
    ]

    generated_text = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True,
    )

    return generated_text.strip()


def review_affidavit(
    generated_affidavit: str,
    mapped_data: dict,
    tokenizer,
    model,
    device,
):
    """
    Use the local LLM as a supporting reviewer.

    The LLM does NOT generate or modify the affidavit.
    It only reviews the generated document against
    the structured source information.
    """

    prompt = f"""
You are reviewing an automatically generated legal affidavit.

Your task is ONLY to identify possible problems.

Do not rewrite the affidavit.
Do not add legal advice.
Do not invent facts.

Compare the generated affidavit against the supplied structured
case information.

Look specifically for:
1. Wrong names
2. Wrong respondent numbers
3. Wrong case number or year
4. Wrong dates
5. Missing important information
6. Statements that appear unsupported by the supplied facts

If everything appears consistent, say:
"No obvious issues found."

Keep the review short and factual.

STRUCTURED CASE INFORMATION:
{mapped_data}

GENERATED AFFIDAVIT:
{generated_affidavit}
"""

    return generate_text(
        prompt,
        tokenizer,
        model,
        device,
        max_new_tokens=150,
    )


if __name__ == "__main__":

    print("Loading local LLM...")

    tokenizer, model, device = load_model()

    print(f"Model loaded successfully on: {device}")

    test_prompt = """
Explain in one sentence why deterministic validation is useful
when generating legal documents with an AI system.
"""

    result = generate_text(
        test_prompt,
        tokenizer,
        model,
        device,
    )

    print("\nLLM Test:")
    print(result)