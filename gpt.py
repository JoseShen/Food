
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

client = AsyncOpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

async def get_chatgpt_response(prompt: str) -> str:
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a master chef that knows every recipe. Reply with formatted discord markdown, use headings and sub headings. Make sure to only respond to messages about food and nothing else. Also do not mention you are using markdown" },
            {"role": "user", "content": prompt}
            ],
        temperature=0.7
    )

    return response.choices[0].message.content

async def get_chatgpt_image_response(image_url):
    response = await client.chat.completions.create(
        model = "gpt-4-turbo",
        messages =[
            {"role": "system", "content": "You are a master chef that knows every recipe. Reply with formatted discord markdown, use headings and sub headings. If the image does not look look like a food, tell the user that they can't eat that. Do not mention markdown"},
            {"role": "user", "content": [
                    {"type": "text", "text": "How do I make this/these dish(es)?"},
                    {"type": "image_url", "image_url": {"url": image_url} }
                    ]
            }
        ]
    )

    return response.choices[0].message.content


