import discord
import db
import string
import asyncio
import logging
import models
import random
import itertools 
import time



async def gmb_game_loop(interaction: discord.Interaction):
    view = GamePickerView()
    await interaction.response.send_message(
        content="Pick your game:",
        view=view
    )
    view.message = await interaction.original_response()



class WagerSelectView(discord.ui.View):
    def __init__(self, game='coinflip'):
        super().__init__(timeout=120)
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

        elif self.view.game == 'pigs':              
            await gmb_pig_mp(interaction, self.amount)
        
        self.view.stop()   
        


class GamePickerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.add_item(GamePickerButton('Coin Flip'))
        self.add_item(GamePickerButton('Pass the Pigs')) 

    async def on_timeout(self):
        if hasattr(self, "message"):
            await self.message.edit(content="⏱️ Game picker selection timed out.", view=None)

class GamePickerButton(discord.ui.Button):
    def __init__(self, game: string):
        super().__init__(label=f"{game}", style=discord.ButtonStyle.success)
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        user = db.get_user(interaction.guild_id, interaction.user.id)

        # Replace message with coin flip view
        if self.game == 'Coin Flip':
            next_view = WagerSelectView(game='coinflip')

        elif self.game == 'Pass the Pigs':                 
            next_view = WagerSelectView(game='pigs')

        await interaction.response.edit_message(
            content="💰 Choose your wager amount:",
            view=next_view
        )

        next_view.message = interaction.message
        self.view.stop()




# ------------------------------------------------------------------
# ------------------------------------------------------------------
# ------------------------------------------------------------------
#  COIN FLIP
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# ------------------------------------------------------------------
async def gmb_coinflip_sp(interaction: discord.Interaction, wager):
        next_view = CoinflipButtonContainer(wager=wager)
        await interaction.response.edit_message(
            content=f"You've wagered **{wager} points**. Choose Heads or Tails!",
            view=next_view
        )


        next_view.message = await interaction.original_response()


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


# ------------------------------------------------------------------
# ------------------------------------------------------------------
# ------------------------------------------------------------------
#  Pass The Pigs
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# ------------------------------------------------------------------

PIG_POSES = [
    ("Side-No-Dot",      1, 34.9),   # opposite sides are how we detect Pig-Out
    ("Side-Dot",         1, 30.2),
    ("Razorback",        5, 22.4),
    ("Trotter",          5,  8.8),
    ("Snouter",         10,  3.0),
    ("Leaning Jowler",  15,  0.6),
]

SIDE_NAMES = {"Side-No-Dot", "Side-Dot"}    
_POSE_WEIGHTS = [w for *_, w in PIG_POSES]    

TARGET_SCORE = 100                            # first to / wins pot
active_pig_games: dict[int, "PigGameState"] = {}   # per-channel

def roll_pig() -> tuple[str, int]:
    name, pts, _ = random.choices(PIG_POSES, weights=_POSE_WEIGHTS, k=1)[0]
    return name, pts

def score_roll():
    n1, p1 = roll_pig()
    n2, p2 = roll_pig()

    side1 = n1 in SIDE_NAMES
    side2 = n2 in SIDE_NAMES

    # --- 1) Both pigs on their sides ---------------------------------
    if side1 and side2:
        if n1 == n2:                            # same face up  →  Sider
            return f"Sider! ({n1} + {n2})", 1, None
        else:                                   # opposite faces → Pig Out
            return f"Pig Out! ({n1} + {n2})", 0, "pigout"

    # --- 2) Exactly one pig on its side ------------------------------
    if side1 ^ side2:                           # xor: only one side-pig
        if side1:
            desc = f"{n2} (other pig on side) → **{p2}** pts"
            return desc, p2, None
        else:
            desc = f"{n1} (other pig on side) → **{p1}** pts"
            return desc, p1, None

    # --- 3) Neither pig on its side ----------------------------------
    # Mixed Combo or Double
    if n1 == n2:                                # Double  (quadruple base)
        score = (p1 + p2) * 2
        return f"Double {n1}! → **{score}** pts", score, None
    else:                                       # Mixed Combo
        score = p1 + p2
        return f"{n1} + {n2} → **{score}** pts", score, None

class PigGameState:                           # ▲ NEW
    def __init__(self, ante: int):
        self.ante = ante          # cost every time you click Roll
        self.pot = 0
        self.scores: dict[int, int] = {}      # banked, per player
        self.turn_score = 0
        self.turn_order: list[int] = []
        self.turn_iter: itertools.cycle | None = None
        self.current: int | None = None
        self.message: discord.Message | None = None

    # rotation helper
    def next_player(self) -> int:
        self.current = next(self.turn_iter)
        self.turn_score = 0
        return self.current
    

async def gmb_pig_mp(interaction: discord.Interaction, ante):
    channel_id = interaction.channel.id
    if channel_id in active_pig_games:
        await interaction.response.send_message(
            "🐷 A Pass-the-Pigs game is already running in this channel!",
            ephemeral=True
        )
        return

    # set up GameState, register command author
    game = PigGameState(ante)
    active_pig_games[channel_id] = game
    game.turn_order.append(interaction.user.id)

    # show lobby view (60 s to join)
    view = PigLobbyView(game)
    await interaction.response.edit_message(
        content=(
            f"🎉 **Pass the Pigs lobby opened!**\n"
            f"Ante per roll: **{ante}** pts\n"
            f"{interaction.user.mention} is in already. "
            f"Click **Join** to enter – game starts in <t:{view.starttime}:R>."
        ),
        view=view
    )
    game.message = await interaction.original_response()





class PigRollView(discord.ui.View):   
    def __init__(self, game: PigGameState):
        super().__init__(timeout=45)
        self.game = game
        self.add_item(PigRollButton("🎲 Roll"))
        self.add_item(PigBankButton("💰 Bank"))

    async def on_timeout(self):
        self.clear_items()
        if self.game.message:
            await self.game.message.edit(
                content="⏱️ Pass-the-Pigs timed out – game over!",
                view=self
            )
        active_pig_games.pop(self.game.message.channel.id, None)

class PigRollButton(discord.ui.Button):
    def __init__(self, label): super().__init__(label=label, style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        game = self.view.game
        uid = interaction.user.id

        # Wrong player?
        if uid != game.current:
            await interaction.response.send_message("⛔ Not your turn!", ephemeral=True)
            return

        player = db.get_user(interaction.guild_id, uid)
        if player.points < game.ante:
            await interaction.response.send_message(
                f"❌ Need {game.ante} pts to roll.", ephemeral=True
            )
            return

        # Pay ante → pot
        player.points -= game.ante
        player.gambling_losses += game.ante
        db.update_user(player)
        game.pot += game.ante

        desc, pts, flag = score_roll()

        if flag == "pigout":
            game.turn_score = 0
            game.next_player()
            txt = f"🐷 **{desc}** – turn ends!\n It is now {interaction.guild.get_member(game.current).mention}'s turn"
            
        elif flag == "oinker":
            game.turn_score = 0
            game.scores[uid] = 0
            txt = f"💀 **{desc}** – you lose *all* banked points!"
            game.next_player()
        else:
            game.turn_score += pts
            txt = (
                f"{desc}\nRunning turn: **{game.turn_score}** pts\n"
                f"Pot: **{game.pot}** – (*Bank* to cash-in)"
            )

        await interaction.response.edit_message(content=txt, view=self.view)

class PigBankButton(discord.ui.Button):
    def __init__(self, label): super().__init__(label=label, style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        game = self.view.game
        uid = interaction.user.id

        if uid != game.current:
            await interaction.response.send_message("⛔ Not your turn!", ephemeral=True)
            return

        game.scores[uid] = game.scores.get(uid, 0) + game.turn_score
        total = game.scores[uid]
        game.turn_score = 0

        # Check win
        if total >= TARGET_SCORE:
            winnings = game.pot
            player = db.get_user(interaction.guild_id, uid)
            player.points += winnings
            player.gambling_winnings += winnings
            db.update_user(player)

            await interaction.response.edit_message(
                content=(
                    f"🏆 **{interaction.user.display_name}** reaches {total} pts and "
                    f"wins the pot of **{winnings}**!\nBalance: {player.points}"
                ),
                view=None
            )
            active_pig_games.pop(interaction.channel.id, None)
            return

        # Rotate to next player
        nxt_id = game.next_player()
        nxt_mention = interaction.guild.get_member(nxt_id).mention
        await interaction.response.edit_message(
            content=(
                f"💼 You banked – total **{total}** pts.\n"
                f"Pot: **{game.pot}**\n"
                f"{nxt_mention}, it’s your turn!"
            ),
            view=self.view
        )

class PigLobbyView(discord.ui.View):
    def __init__(self, game: PigGameState):
        super().__init__(timeout=60)
        self.game = game
        self.add_item(PigJoinButton())
        self.starttime = int(time.time()) + 60

    async def on_timeout(self):
        """Called automatically after 60 s."""
        msg = self.game.message

        # Not enough players?
        if len(self.game.turn_order) < 2:
            await msg.edit(
                content="👥 Not enough players joined – lobby cancelled.",
                view=None
            )
            active_pig_games.pop(msg.channel.id, None)
            return

        # Enough players – start the real game
        random.shuffle(self.game.turn_order)
        self.game.turn_iter = itertools.cycle(self.game.turn_order)
        self.game.next_player()

        player_mentions = ", ".join(
            msg.guild.get_member(uid).mention for uid in self.game.turn_order
        )
        roll_view = PigRollView(self.game)

        await msg.edit(
            content=(
                f"🐷 **Pass the Pigs begins!**\n"
                f"Players: {player_mentions}\n"
                f"{msg.guild.get_member(self.game.current).mention} rolls first. "
                f"Ante: **{self.game.ante}** pts per roll."
            ),
            view=roll_view
        )


class PigJoinButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Join", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        game = self.view.game
        uid = interaction.user.id

        # Already joined?
        if uid in game.turn_order:
            await interaction.response.send_message(
                "🖐️ You’re already in the lobby!", ephemeral=True
            )
            return

        # Must be able to afford the ante
        player = db.get_user(interaction.guild_id, uid)
        if player.points < game.ante:
            await interaction.response.send_message(
                f"❌ You need at least {game.ante} points to join.",
                ephemeral=True
            )
            return

        # Register player
        game.turn_order.append(uid)
        await interaction.response.send_message(
            f"✅ {interaction.user.display_name} joined the game!",
            ephemeral=True
        )

        # Update the lobby message so everyone sees the growing 
        print(f"current turn order {game.turn_order}")
        names = ", ".join(
            interaction.guild.get_member(pid).mention
            for pid in game.turn_order
        )
        await game.message.edit(
            content=(
                f"🎉 **Pass the Pigs lobby**\n"
                f"Players so far: {names}\n"
                f"Click **Join** to enter – game starts automatically in <t:{self.view.starttime}:R>."
            ),
            view=self.view
        )
        
