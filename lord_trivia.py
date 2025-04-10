import discord
from config import DISCORD_TOKEN
import db
import logging


intents = discord.Intents.default()
client = discord.Client(intents=intents)

tree = discord.app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    logging.info(f'Logged in as {client.user}')
    db.initialize()

@tree.command(name="hello", description="Say hello!")
async def hello_command(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")

@tree.command(name="register", description="Register yourself to play trivia!")
async def register(interaction: discord.Interaction):
    user_id = interaction.user.id
    guild_id = interaction.guild.id if interaction.guild else None  # for PMs, guild is None

    if guild_id is None:
        await interaction.response.send_message("This command can only be used in a server.")
        return
    
    logging.info(f"adding user: user_id: {user_id}, guild_id: {guild_id}")
    try:
        if db.user_exists(guild_id, user_id):
            await interaction.response.send_message("You are already registered!")
            return
        db.add_user(guild_id, user_id)

    except:
        logging.error("Error adding user to DB!")
        await interaction.response.send_message("There was an error registering you for trivia")

    await interaction.response.send_message("You've been registered for trivia!")

client.run(DISCORD_TOKEN)