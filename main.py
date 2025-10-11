from typing import Final 
import base64
import os
from dotenv import load_dotenv
from discord import Intents, Message, Embed, TextChannel 
from discord.ext import commands, tasks
from gpt import get_chatgpt_response, get_chatgpt_image_response
from weather import get_weather
from aiohttp import web
import asyncio
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




@tasks.loop(minutes=5)
async def update_weather():
    try:
        print("Weather update task running...")
        city = "Toronto"
        weather_data = get_weather(city)
        
        if weather_data is None:
            print("Failed to get weather data")
            return
            
        channel = bot.get_channel(1097009652576817243)
        channel_update = bot.get_channel(1324530733276069951)
        feel = bot.get_channel(1187223395612508260)
        feels = bot.get_channel(1200277412370448554)
        temperature = weather_data["main"]["temp"]
        feels_like = weather_data["main"]["feels_like"]
        new_name = f'{city}: {temperature}°C'
        if temperature < 0:
            final_name = f'{new_name} \u2744'
        elif temperature >= 0 and temperature < 25:
            final_name = f'{new_name} \U0001F341'
        elif temperature >= 25:
            final_name = f'{new_name} \U0001F525'

        print(f"Updating channel name to: {final_name}")
        await channel.edit(name=final_name)
        await feel.edit(name="feels like")
        await feels.edit(name=f'{feels_like}°C')
        await channel_update.send("Weather updated successfully")
        print("Channel name updated successfully")

            
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

# ========== WEB SERVER SETUP ==========

async def handle_index(request):
    """Main dashboard page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Discord Bot Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #36393f;
                color: #dcddde;
            }
            h1 { color: #7289da; }
            .card {
                background-color: #2f3136;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
            }
            a {
                color: #00aff4;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <h1>🤖 Discord Bot Dashboard</h1>
        <div class="card">
            <h2>Status</h2>
            <p>Bot is currently online and running!</p>
        </div>
        <div class="card">
            <h2>API Endpoints</h2>
            <ul>
                <li><a href="/api/status">/api/status</a> - Bot status information</li>
                <li><a href="/api/stats">/api/stats</a> - Bot statistics</li>
            </ul>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def handle_status(request):
    """API endpoint for bot status"""
    return web.json_response({
        "status": "online",
        "bot_name": str(bot.user) if bot.user else "Not logged in",
        "server_count": len(bot.guilds),
        "user_count": sum(guild.member_count for guild in bot.guilds)
    })

async def handle_stats(request):
    """API endpoint for detailed stats"""
    guild_info = [
        {"name": guild.name, "members": guild.member_count}
        for guild in bot.guilds
    ]
    return web.json_response({
        "guilds": guild_info,
        "total_guilds": len(bot.guilds),
        "total_members": sum(guild.member_count for guild in bot.guilds)
    })

async def start_web_server():
    """Initialize and start the web server"""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/status', handle_status)
    app.router.add_get('/api/stats', handle_stats)
    
    # Start the web server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 3000)
    await site.start()
    print("Web server started on http://0.0.0.0:3000")

async def main():
    """Main async function to run both bot and web server"""
    # Start web server
    await start_web_server()
    
    # Start Discord bot
    async with bot:
        await bot.start(DISCORD_BOT_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())