import os
from dotenv import load_dotenv
load_dotenv()
import json
from openai import OpenAI

# Perplexity client (OpenAI-compatible)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.perplexity.ai"
)

def extract_json(text: str) -> str:
    """
    Safely extract the first JSON object from a string.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON found in response:\n{text}")
    return text[start:end + 1]

def extract_transaction(message: str):
    prompt = f"""
You are a finance assistant.

Extract transaction details from the message below.

Message:
\"\"\"{message}\"\"\"

Respond with ONLY valid JSON.
No explanations. No markdown.

Return JSON in this exact schema:
{{
  "date": "YYYY-MM-DD" | null,
  "amount": number,
  "type": "income" | "expense",
  "category": string,
  "description": string,
  "payment_mode": string | null,
  "tds_percent": number | null
}}

Rules:
- Do NOT guess values
- If date not mentioned, return null
- Amount must be positive
- TDS must be a percentage (e.g. 10 for 10%)
- If TDS not mentioned, return null
"""

    response = client.chat.completions.create(
        model="sonar",
        messages=[
            {"role": "system", "content": "You output ONLY valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()
    json_text = extract_json(raw)
    return json.loads(json_text)

if __name__ == "__main__":
    test_messages = [
        "Salary credited 50000, TDS 10%",
        "Paid 450 for lunch via GPay",
        "Freelance payment 20000 with 5% TDS",
        "Uber 289 yesterday night",
        "Amazon shopping 1299 using credit card"
    ]

    for msg in test_messages:
        print("\nMessage:", msg)
        result = extract_transaction(msg)
        print(json.dumps(result, indent=2))
