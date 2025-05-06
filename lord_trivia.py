import discord
from config import DISCORD_TOKEN
import db
import logging
import models
import string
import asyncio
from ui import AnswerButton, AnswerButtons


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
    
    try:
        if db.user_exists(guild_id, user_id):
            logging.info(f"REGISTER: User alredy exists in DB!: user_id: {user_id}, guild_id: {guild_id}")
            await interaction.response.send_message("You are already registered!")
            return
        logging.info(f"REGISTER: Adding user: user_id: {user_id}, guild_id: {guild_id}")
        db.add_user(guild_id, user_id)

    except:
        logging.error("Error adding user to DB!")
        await interaction.response.send_message("There was an error registering you for trivia")

    await interaction.response.send_message("You've been registered for trivia!")


@tree.command(name="play", description="Play some Trivia!")
async def play(interaction: discord.Interaction):
    if not db.user_exists(interaction.guild_id, interaction.user.id):
        await interaction.response.send_message("You aren't registered, please use the /register command!")
        return

    question = db.get_random_question()
    letters = string.ascii_uppercase
    answer_lines = "\n".join(
        f"{letters[i]}: {answer}"
        for i, answer in enumerate(question.answers)
    )
    content = f"{question.prompt}\n{answer_lines}"
    view=AnswerButtons(question)
    await interaction.response.send_message(content, view=view)
    view.message = await interaction.original_response()  
    
@tree.command(name="mystats", description="Show your stats")
async def mystats(interaction: discord.Interaction):
    if not db.user_exists(interaction.guild_id, interaction.user.id):
        await interaction.response.send_message("You aren't registered, please use the /register command!")
        return
    

    user = db.get_user(interaction.guild_id, interaction.user.id)
    content = f"username: {interaction.user.name}\nPoints: {user.points}\n Streak: {user.streak}\n Total Q's Answered: {user.answers_total}\n Correct Q's: {user.answers_total}\nWinnings: {user.gambling_winnings}\n Losses: {user.gambling_losses}"
    await interaction.response.send_message(content)

client.run(DISCORD_TOKEN)