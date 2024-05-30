from typing import Final 
import base64
import os
from dotenv import load_dotenv
from discord import Intents, Message, Embed
from discord.ext import commands
from gpt import get_chatgpt_response, get_chatgpt_image_response

load_dotenv()

# Get the Discord bot token from environment variables
DISCORD_BOT_TOKEN: Final[str] = os.getenv('DISCORD_BOT_TOKEN')




intents: Intents = Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event 
async def on_ready() -> None:
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message: Message) -> None:
    if message.author == bot.user: # prevents bot from talking to itself
        return

    await bot.process_commands(message) # Processes commands in chat

@bot.command()
async def ask(ctx: commands.Context) -> None:
    
    await ctx.typing() # Shows that the bot is typing

    if ctx.message.content == "!ask":
        return await ctx.reply("Please provide a prompt.")
    
    prompt = ctx.message.content[6:]
    response = await get_chatgpt_response(prompt)  

    if response is not None:
        # Handles large responses from ChatGPT
        if len(response) > 4096:
            chunks = split_response(response)
            for chunk in chunks:
                embed = Embed(description=chunk, color=0x00ff00)
                await ctx.reply(embed=embed)
        else:
            embed = Embed(description=response, color=0x00ff00) # Create an embed with the ChatGPT response
            await ctx.reply(embed=embed) # Reply to user with the response
    else:
        await ctx.reply("No response from ChatGPT.") # Handle the case when response is None
    



@bot.command()
async def upload(ctx: commands.Context) -> None:
    await ctx.typing()

    if ctx.message.attachments:
        # Get the URLs of the message
        attachment_urls = [attachment.url for attachment in ctx.message.attachments]

       
        response = await get_chatgpt_image_response(attachment_urls[0])

        if response is not None:
            # Handles large responses from ChatGPT
            if len(response) > 4096:
                chunks = split_response(response)
                for chunk in chunks:
                    embed = Embed(description=chunk, color=0x00ff00)
                    await ctx.reply(embed=embed)
            else:
                embed = Embed(description=response, color=0x00ff00)  # Create an embed with the ChatGPT response
                await ctx.reply(embed=embed)  # Reply to user with the response
        else:
            await ctx.reply("No response from ChatGPT.")  # Handle the case when response is None

    else:
        return await ctx.reply("No attachments found, upload an image of a food.")





def split_response(response):
    return [response[i:i + 4096] for i in range(0, len(response), 4096)]



if __name__ == '__main__':
    bot.run(DISCORD_BOT_TOKEN)