from typing import Final 
import base64
import os
from dotenv import load_dotenv
import discord
from discord import Intents, Embed, Interaction, Attachment, app_commands
from discord.ext import commands, tasks
from gpt import get_chatgpt_response, get_chatgpt_image_response
from weather import get_weather
from aiohttp import web
import asyncio
load_dotenv()

# Get the Discord bot token from environment variables
DISCORD_BOT_TOKEN: Final[str] = os.getenv('DISCORD_BOT_TOKEN')
GUILD_IDS = [
    int(guild_id.strip())
    for guild_id in os.getenv('DISCORD_GUILD_IDS', '').split(',')
    if guild_id.strip()
]




intents: Intents = Intents.default()
intents.message_content = True 


class GPTCommands(app_commands.Group):
    """Slash command group for GPT-powered interactions."""

    def __init__(self) -> None:
        super().__init__(name="gpt", description="Interact with GPT capabilities.")

    @app_commands.command(name="ask", description="Ask ChatGPT a question.")
    @app_commands.describe(prompt="Prompt to send to ChatGPT")
    async def ask(self, interaction: Interaction, prompt: str) -> None:
        await interaction.response.defer(thinking=True)
        response = await get_chatgpt_response(prompt)

        if not response:
            await interaction.followup.send("No response from ChatGPT.")
            return

        if len(response) > 4096:
            for chunk in split_response(response):
                embed = Embed(description=chunk, color=0x00FF00)
                await interaction.followup.send(embed=embed)
        else:
            embed = Embed(description=response, color=0x00FF00)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="upload", description="Analyze a food image with ChatGPT.")
    @app_commands.describe(image="Image of food to analyze")
    async def upload(self, interaction: Interaction, image: Attachment) -> None:
        await interaction.response.defer(thinking=True)

        if image.content_type and not image.content_type.startswith("image/"):
            await interaction.followup.send("Please upload a valid image file.")
            return

        response = await get_chatgpt_image_response(image.url)

        if not response:
            await interaction.followup.send("No response from ChatGPT.")
            return

        if len(response) > 4096:
            for chunk in split_response(response):
                embed = Embed(description=chunk, color=0x00FF00)
                await interaction.followup.send(embed=embed)
        else:
            embed = Embed(description=response, color=0x00FF00)
            await interaction.followup.send(embed=embed)



class GPTSlashBot(commands.Bot):
    """Discord bot configured to use slash commands."""

    def __init__(self) -> None:
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self) -> None:
        if not self.tree.get_command('gpt'):
            self.tree.add_command(GPTCommands())

        if GUILD_IDS:
            for guild_id in GUILD_IDS:
                guild = discord.Object(id=guild_id)
                synced_cmds = await self.tree.sync(guild=guild)
                print(f"Synced {len(synced_cmds)} slash commands to guild {guild_id}.")
        else:
            synced_cmds = await self.tree.sync()
            print(f"Synced {len(synced_cmds)} global slash commands.")

        for command in self.tree.walk_commands():
            print(f"Loaded command: /{command.qualified_name}")

        await super().setup_hook()


bot = GPTSlashBot()


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

    if not update_weather.is_running():
        update_weather.start()
        print("Weather update task started")

    if GUILD_IDS:
        print(f"Slash commands registered for guilds: {', '.join(str(guild) for guild in GUILD_IDS)}")
    else:
        print("Slash commands registered globally; propagation may take up to an hour.")


@bot.tree.command(name="force_update", description="Trigger the weather update task immediately.")
async def force_update(interaction: Interaction) -> None:
    await interaction.response.defer(thinking=True)
    await update_weather()
    await interaction.followup.send("Weather update task triggered")

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
