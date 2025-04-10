import discord
from config import DISCORD_TOKEN
import db


intents = discord.Intents.default()
client = discord.Client(intents=intents)

tree = discord.app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f'Logged in as {client.user}')

@tree.command(name="hello", description="Say hello!")
async def hello_command(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")

@tree.command(name="register", description="Register yourself to play trivia!")
async def hello_command(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")

client.run(DISCORD_TOKEN)