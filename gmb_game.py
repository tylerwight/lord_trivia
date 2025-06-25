import discord
import db
import string
import asyncio
import logging
import models
import random

async def gmb_game_loop(interaction: discord.Interaction):
    view = GamePickerView()
    await interaction.response.send_message(
        content="Pick your game:",
        view=view
    )
    view.message = await interaction.original_response()



async def gmb_coinflip_sp(interaction: discord.Interaction, wager):
        next_view = CoinflipButtonContainer(wager=wager)
        await interaction.response.edit_message(
            content=f"You've wagered **{wager} points**. Choose Heads or Tails!",
            view=next_view
        )


        next_view.message = await interaction.original_response()


async def gmb_pig_mp(interaction: discord.Interaction, wager):
    view = WagerSelectView()
    await interaction.response.send_message(
        content="💰 Choose your wager amount:",
        view=view
    )
    view.message = await interaction.original_response()



class CoinflipButtonContainer(discord.ui.View):
    def __init__(self, wager: int, timeout=30):
        super().__init__(timeout=timeout)
        self.flip_cost = wager
        self.message: discord.Message | None = None
        self.add_item(CoinflipAnswerButton(label="Heads"))
        self.add_item(CoinflipAnswerButton(label="Tails"))

    async def on_timeout(self):
        self.clear_items()
        if self.message:
            await self.message.edit(content="⏱️ Coin flip timed out.", view=self)




class CoinflipAnswerButton(discord.ui.Button):
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
        #embed.set_image(url=gif_url)
        embed.add_field(name="Result", value=outcome_text, inline=False)
        embed.set_footer(text=f"Current Points: {user.points}")

        # Update view and message
        for item in self.view.children:
            item.disabled = False
        await interaction.edit_original_response(content=None, embed=embed, view=self.view)

        await asyncio.sleep(2)
        


class WagerSelectView(discord.ui.View):
    def __init__(self, game='coinflip'):
        super().__init__(timeout=30)
        self.game = game
        for amount in [5, 10, 25, 100, 500 , 1000, 10000]:
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
        if self.view.game == 'coinflip':
            await gmb_coinflip_sp(interaction, self.amount)
        


class GamePickerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.add_item(GamePickerButton('Coin Flip'))

    async def on_timeout(self):
        if hasattr(self, "message"):
            await self.message.edit(content="⏱️ Wager selection timed out.", view=None)

class GamePickerButton(discord.ui.Button):
    def __init__(self, game: string):
        super().__init__(label=f"{game}", style=discord.ButtonStyle.success)
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        user = db.get_user(interaction.guild_id, interaction.user.id)

        # Replace message with coin flip view
        if self.game == 'Coin Flip':
            view = WagerSelectView(game='coinflip')
            await interaction.response.send_message(
            content="💰 Choose your wager amount:",
            view=view
            )
        view.message = await interaction.original_response()
