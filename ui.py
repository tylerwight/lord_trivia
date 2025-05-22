import discord
import logging
import models
import db
import asyncio
import string
import random

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
        self.user_totals = {}
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




class GMBButtonContainer(discord.ui.View):
    def __init__(self, wager: int, timeout=30):
        super().__init__(timeout=timeout)
        self.flip_cost = wager
        self.message: discord.Message | None = None
        self.add_item(GMBAnswerButton(label="Heads"))
        self.add_item(GMBAnswerButton(label="Tails"))

    async def on_timeout(self):
        self.clear_items()
        if self.message:
            await self.message.edit(content="⏱️ Coin flip timed out.", view=self)




class GMBAnswerButton(discord.ui.Button):
    def __init__(self, label: str):
        super().__init__(style=discord.ButtonStyle.primary, label=label)
        self.choice = label.lower()

    async def callback(self, interaction: discord.Interaction):
        user = db.get_user(interaction.guild_id, interaction.user.id)
        cost = self.view.flip_cost

        # Not enough points
        if user.points < cost:
            await interaction.response.send_message(
                f"❌ You don't have enough points to wager ({cost} required).",
                ephemeral=True
            )
            return

        # Deduct wager cost
        user.points -= cost
        db.update_user(user)

        # Coin flip
        await interaction.response.defer(thinking=False)
        for item in self.view.children:
            item.disabled = True
        await self.view.message.edit(content="Flipping coin...", view=self.view)
        await asyncio.sleep(1)

        result = random.choice(["Heads", "Tails"])
        win = (self.choice == result.lower())
        gif_url = (
            "https://media.tenor.com/nEu74vu_sT4AAAAM/heads-coinflip.gif"
            if result == "Heads"
            else "https://media.tenor.com/kK8D7hQXX5wAAAAM/coins-tails.gif"
        )

        # Reward or loss
        if win:
            winnings = 2 * cost
            user.points += winnings
            user.gambling_winnings += winnings
            outcome_text = "🎉 You won!"
        else:
            user.gambling_losses += cost
            outcome_text = "💸 You lost!"

        db.update_user(user)

        # Build embed
        embed = discord.Embed(
            title="🪙 Coin Flip Result",
            description=f"You chose **{self.choice.title()}**\nThe coin landed on **{result}**!",
            color=discord.Color.green() if win else discord.Color.red()
        )
        embed.set_image(url=gif_url)
        embed.add_field(name="Result", value=outcome_text, inline=False)
        embed.set_footer(text=f"Current Points: {user.points}")

        # Update view and message
        for item in self.view.children:
            item.disabled = False
        await interaction.edit_original_response(content=None, embed=embed, view=self.view)

        await asyncio.sleep(2)
        await self.view.message.channel.send(
            content="💰 Want to play again? Choose a new wager!",
            view=WagerSelectView()
        )
        


class WagerSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        for amount in [5, 10, 25]:
            self.add_item(WagerButton(amount))

    async def on_timeout(self):
        if hasattr(self, "message"):
            await self.message.edit(content="⏱️ Wager selection timed out.", view=None)

class WagerButton(discord.ui.Button):
    def __init__(self, amount: int):
        super().__init__(label=f"{amount} pts", style=discord.ButtonStyle.success)
        self.amount = amount

    async def callback(self, interaction: discord.Interaction):
        user = db.get_user(interaction.guild_id, interaction.user.id)

        if user.points < self.amount:
            await interaction.response.send_message(
                f"❌ You don't have enough points to wager {self.amount}.",
                ephemeral=True
            )
            return

        # Replace message with coin flip view
        flip_view = GMBButtonContainer(wager=self.amount)
        await interaction.response.edit_message(
            content=f"🪙 You've wagered **{self.amount} points**. Choose Heads or Tails!",
            view=flip_view
        )
        flip_view.message = await interaction.original_response()

