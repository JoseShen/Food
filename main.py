from typing import Final 
import base64
import os
from dotenv import load_dotenv
from discord import Intents, Message, Embed, TextChannel 
from discord.ext import commands, tasks
from gpt import get_chatgpt_response, get_chatgpt_image_response
from weather import get_weather
load_dotenv()

# Get the Discord bot token from environment variables
DISCORD_BOT_TOKEN: Final[str] = os.getenv('DISCORD_BOT_TOKEN')




intents: Intents = Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="$", intents=intents)

@bot.event 
async def on_ready() -> None:
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message: Message) -> None:
    if message.author == bot.user: # prevents bot from talking to itself
        return

    await bot.process_commands(message) # Processes commands in chat

@bot.group()
async def gpt(ctx):
    if ctx.invoked_subcommand is None:
        # Create an embed with available commands
        embed = Embed(
            title="GPT Commands",
            description="Available GPT operations. Use $gpt [command] [question/upload] to interact with GPT.",
            color=0x00ff00
        )
        await ctx.send(embed=embed)


@gpt.command()
async def ask(ctx: commands.Context) -> None:
    
    await ctx.typing() # Shows that the bot is typing

    if ctx.message.content == "$ask":
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
    



@gpt.command()
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
        return await ctx.reply("No attachments found, upload an image of a food!.")




def split_response(response):
    return [response[i:i + 4096] for i in range(0, len(response), 4096)]




@tasks.loop(hours=1)
async def update_weather():
    try:
        print("Weather update task running...")
        city = "Toronto"
        weather_data = get_weather(city)
        
        if weather_data is None:
            print("Failed to get weather data")
            return
            
        channel = bot.get_channel(1097009652576817243)
        
        if channel:
            new_name = f'{city} - {weather_data["main"]["temp"]}°C'
            print(f"Updating channel name to: {new_name}")
            await channel.edit(name=new_name)
            print("Channel name updated successfully")
        else:
            print(f"Channel not found: {1097009652576817243}")
            
    except Exception as e:
        print(f"Error in update_weather task: {str(e)}")

@update_weather.before_loop
async def before_update():
    await bot.wait_until_ready()
    print("Bot is ready, starting weather update loop")

# Modify your on_ready event to start the task
@bot.event 
async def on_ready() -> None:
    print(f"Logged in as {bot.user}")
    update_weather.start()
    print("Weather update task started")

@bot.command()
async def force_update(ctx):
    await update_weather()
    await ctx.send("Weather update task triggered")

if __name__ == '__main__':
    bot.run(DISCORD_BOT_TOKEN)



