import discord
from config import DISCORD_TOKEN
import db
import logging
import models
import string
import asyncio


intents = discord.Intents.default()
client = discord.Client(intents=intents)

tree = discord.app_commands.CommandTree(client)


class AnswerButtons(discord.ui.View):
    def __init__(self, question: models.Question, timeout=30):
        super().__init__(timeout=timeout)
        self.question = question
        self.response = None
        self.message: discord.Message | None = None  

        # Create buttons based on the number of answers
        option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for i, _ in enumerate(self.question.answers):
            if i >= len(option_letters):
                break
            label = option_letters[i]
            self.add_item(AnswerButton(label=label, index=i))
    
    async def on_timeout(self):
        logging.info("Trivia timed out!")
        self.clear_items()
        await self.message.edit(content="Your game session has ended", view=self)


class AnswerButton(discord.ui.Button):
    def __init__(self, label: str, index: int):
        super().__init__(style=discord.ButtonStyle.primary, label=label)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        question: models.Question = self.view.question
        is_correct = (self.index == question.correct_index)

        # Disable all buttons after answer
        for item in self.view.children:
            item.disabled = True

        if is_correct:
            await interaction.response.edit_message(content="✅ Correct!", view=self.view)
        else:
            correct_letter = ['A', 'B', 'C', 'D', 'E', 'F', 'G'][question.correct_index]
            await interaction.response.edit_message(
                content=f"❌ Wrong! Correct answer was **{correct_letter}**.",
                view=self.view
            )

        await asyncio.sleep(5)

        new_question = db.get_random_question()
        letters = string.ascii_uppercase
        answer_lines = "\n".join(
            f"{letters[i]}: {answer}"
            for i, answer in enumerate(new_question.answers)
        )
        content = f"{new_question.prompt}\n{answer_lines}"
        self.view.question = new_question
        for item in self.view.children:
            item.disabled = False
        await interaction.edit_original_response(content=content, view=self.view)





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
    letters = string.ascii_uppercase
    answer_lines = "\n".join(
        f"{letters[i]}: {answer}"
        for i, answer in enumerate(question.answers)
    )
    content = f"{question.prompt}\n{answer_lines}"
    view=AnswerButtons(question)
    await interaction.response.send_message(content, view=view)
    view.message = await interaction.original_response()  
    


client.run(DISCORD_TOKEN)