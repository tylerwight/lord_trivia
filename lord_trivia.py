import discord
from config import DISCORD_TOKEN
import db
import logging
import models
import string
import asyncio
import ui
from mp_game_loop import mp_trivia_loop
from gmb_game_loop import gmb_game_loop


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user}')
    db.initialize()

@client.event
async def setup_hook():
    logging.info("SETUPHOOK: syncing commands")
    tree.copy_global_to(guild=discord.Object(id=533036168892383242))
    await tree.sync(guild=discord.Object(id=533036168892383242))
    await tree.sync()

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


@tree.command(name="playsp", description="Play some Trivia single player!")
async def playsp(interaction: discord.Interaction):
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
    view=ui.SPButtonContainer(question)
    await interaction.response.send_message(content, view=view)
    view.message = await interaction.original_response()  


@tree.command(name="playmp", description="Play some Trivia multiplayer!")
async def playmp(interaction: discord.Interaction):
    if not db.user_exists(interaction.guild_id, interaction.user.id):
        await interaction.response.send_message("You aren't registered, please use the /register command!")
        return

    asyncio.create_task(mp_trivia_loop(interaction))


@tree.command(name="mystats", description="Show your stats")
async def mystats(interaction: discord.Interaction):
    if interaction.guild_id is None:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    if not db.user_exists(interaction.guild_id, interaction.user.id):
        await interaction.response.send_message("You aren't registered, please use the /register command!", ephemeral=True)
        return

    user = db.get_user(interaction.guild_id, interaction.user.id)

    embed = discord.Embed(
        title=f"📊 Stats for {interaction.user.display_name}",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="🏅 Points", value=str(user.points), inline=True)
    embed.add_field(name="🔥 Streak", value=str(user.streak), inline=True)
    embed.add_field(name="❓ Questions Answered", value=str(user.answers_total), inline=False)
    embed.add_field(name="✅ Correct Answers", value=str(user.answers_correct), inline=True)
    embed.add_field(name="💰 Winnings", value=str(user.gambling_winnings), inline=True)
    embed.add_field(name="💸 Losses", value=str(user.gambling_losses), inline=True)

    await interaction.response.send_message(embed=embed)

@tree.command(name="gamble", description="Gamble your points for chance to win big!")
async def gamble(interaction: discord.Interaction):
    if not db.user_exists(interaction.guild_id, interaction.user.id):
        await interaction.response.send_message("You aren't registered, please use the /register command!")
        return
    
    asyncio.create_task(gmb_game_loop(interaction))

client.run(DISCORD_TOKEN)