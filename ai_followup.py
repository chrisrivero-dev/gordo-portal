# ai_followup.py  — demo-safe version, NO external APIs

def generate_followup(customer, company, product, notes):
    """
    Simple, local follow-up generator for demo.
    No OpenAI / Gemini / API calls. Just formats a clean message.
    """
    name = (customer or "there").strip()
    comp = (company or "").strip()
    prod = (product or "your last order").strip()
    extra = notes.strip() if notes else ""

    intro = f"Hey {name},"
    body = f" just wanted to check in about {prod}"
    if comp:
        body += f" from {comp}"
    body += ". "

    if extra:
        body += extra + " "

    closing = "Let me know if you need a refill or have any questions."

    return (intro + body + closing).strip()
