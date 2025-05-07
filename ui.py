import discord
import logging
import models
import db
import asyncio
import string

class SPButtonContainer(discord.ui.View):
    def __init__(self, question: models.Question, timeout=30):
        super().__init__(timeout=timeout)
        self.question = question
        self.response = None

        # Create buttons based on the number of answers
        option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for i, _ in enumerate(self.question.answers):
            if i >= len(option_letters):
                break
            label = option_letters[i]
            self.add_item(SPAnswerButton(label=label, index=i))

    def repopulate_buttons(self):
        self.clear_items()
        option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for i, _ in enumerate(self.question.answers):
            if i >= len(option_letters):
                break
            label = option_letters[i]
            self.add_item(SPAnswerButton(label=label, index=i))
    
    async def on_timeout(self):
        logging.info("Trivia timed out!")
        self.clear_items()
        await self.message.edit(content="Your game session has ended", view=self)


class SPAnswerButton(discord.ui.Button):
    def __init__(self, label: str, index: int):
        super().__init__(style=discord.ButtonStyle.primary, label=label)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        question: models.Question = self.view.question
        user = db.get_user(interaction.guild_id, interaction.user.id)
        is_correct = (self.index == question.correct_index)

        # Disable all buttons after answer
        for item in self.view.children:
            item.disabled = True
        
        user.answers_total += 1
        
        if is_correct:
            point_add = 0
            match question.difficulty:
                case 'easy':
                    point_add = 1
                case 'medium':
                    point_add = 2
                case 'hard':
                    point_add = 3

            await interaction.response.edit_message(content=f"✅ Correct! You get {point_add} points!", view=self.view)
            user.answers_correct += 1

            user.points += point_add
            user.streak += 1
        else:
            correct_letter = ['A', 'B', 'C', 'D', 'E', 'F', 'G'][question.correct_index]
            await interaction.response.edit_message(
                content=f"❌ Wrong! Correct answer was **{correct_letter}**.",
                view=self.view
            )
            user.streak = 0
        db.update_user(user)

        await asyncio.sleep(1)
        await self.view.message.edit(content="Next Question in 3...", view=self.view)
        await asyncio.sleep(1)
        await self.view.message.edit(content="Next Question in 2...", view=self.view)
        await asyncio.sleep(1)
        await self.view.message.edit(content="Next Question in 1...", view=self.view)
        await asyncio.sleep(1)

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
        self.view.repopulate_buttons()
        await interaction.edit_original_response(content=content, view=self.view)



class MPButtonContainer(discord.ui.View):
    def __init__(self, question: models.Question, timeout=30):
        super().__init__(timeout=timeout)
        self.question = question
        self.user_answers = {}  # key: user_id, value: index
        self.message: discord.Message | None = None
        self.rounds = 3

        option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for i, _ in enumerate(self.question.answers):
            if i >= len(option_letters):
                break
            self.add_item(MPAnswerButton(label=option_letters[i], index=i))

    def repopulate_buttons(self):
        self.clear_items()
        option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for i, _ in enumerate(self.question.answers):
            if i >= len(option_letters):
                break
            self.add_item(MPAnswerButton(label=option_letters[i], index=i))

    async def on_timeout(self):
        self.clear_items()
        await self.message.edit(content="Trivia ended due to inactivity.", view=self)



class MPAnswerButton(discord.ui.Button):
    def __init__(self, label: str, index: int):
        super().__init__(style=discord.ButtonStyle.primary, label=label)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: MPButtonContainer = self.view
        user_id = interaction.user.id

        if user_id in view.user_answers:
            await interaction.response.send_message("You already answered!", ephemeral=True)
            return

        view.user_answers[user_id] = self.index

        await interaction.response.defer(thinking=False)

