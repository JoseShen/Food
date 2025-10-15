import os
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", OPENAI_MODEL)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def _run_chat_completion(*, model: str, messages: list) -> Optional[str]:
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
    except Exception as exc:
        error_message = f"OpenAI API error: {exc}"
        print(error_message)
        return error_message

    try:
        return response.choices[0].message.content
    except (AttributeError, IndexError, KeyError) as exc:
        error_message = f"Unexpected OpenAI response structure: {exc}"
        print(error_message)
        return error_message


async def get_chatgpt_response(prompt: str) -> Optional[str]:
    """Return GPT text for a user prompt via the configured model."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a master chef that knows every recipe. "
                "Reply with formatted Discord markdown using headings and subheadings. "
                "Only respond to messages about food and never mention markdown explicitly."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    return await _run_chat_completion(model=OPENAI_MODEL, messages=messages)


async def get_chatgpt_image_response(image_url: str) -> Optional[str]:
    """Return GPT analysis for an image URL containing food."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a master chef that knows every recipe. "
                "Reply with formatted Discord markdown using headings and subheadings. "
                "If the image does not look like food, advise the user it is inedible. "
                "Do not mention markdown explicitly."
            ),
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "How do I make this dish?"},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        },
    ]
    return await _run_chat_completion(model=OPENAI_IMAGE_MODEL, messages=messages)
