import discord
from config import DISCORD_TOKEN
import db
import logging
import models


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
    question = db.get_random_question()
    await interaction.response.send_message(question.prompt)

@tree.context_menu(name='Report to Moderators')
async def report_message(interaction: discord.Interaction, message: discord.Message):
    # We're sending this response message with ephemeral=True, so only the command executor can see it
    await interaction.response.send_message(
        f'Thanks for reporting this message by {message.author.mention} to our moderators.', ephemeral=True
    )

    # Handle report by sending it into a log channel
    log_channel = interaction.guild.get_channel(534427957452603402)  # replace with your channel id

    embed = discord.Embed(title='Reported Message')
    if message.content:
        embed.description = message.content

    embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    embed.timestamp = message.created_at

    url_view = discord.ui.View()
    url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))

    await log_channel.send(embed=embed, view=url_view)

# This context menu command only works on members
@tree.context_menu(name='Show Join Date')
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(member.joined_at)}')

client.run(DISCORD_TOKEN)