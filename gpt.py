import os
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def _run_response_request(input_payload) -> Optional[str]:
    try:
        response = await client.responses.create(
            model=OPENAI_MODEL,
            input=input_payload,
        )
    except Exception as exc:
        print(f"Error while contacting OpenAI: {exc}")
        return None

    try:
        return response.output_text
    except AttributeError:
        print("Unexpected response structure from OpenAI.")
        return None


async def get_chatgpt_response(prompt: str) -> Optional[str]:
    """Return GPT text for a user prompt via the configured model."""
    input_payload = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "You are a master chef that knows every recipe. "
                        "Reply with formatted Discord markdown using headings and subheadings. "
                        "Only respond to messages about food and never mention markdown explicitly."
                    ),
                }
            ],
        },
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt}],
        },
    ]
    return await _run_response_request(input_payload)


async def get_chatgpt_image_response(image_url: str) -> Optional[str]:
    """Return GPT analysis for an image URL containing food."""
    input_payload = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "You are a master chef that knows every recipe. "
                        "Reply with formatted Discord markdown using headings and subheadings. "
                        "If the image does not look like food, advise the user it is inedible. "
                        "Do not mention markdown explicitly."
                    ),
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "How do I make this dish?"},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        },
    ]
    return await _run_response_request(input_payload)
