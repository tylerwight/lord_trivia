import discord
import db
import string
import asyncio
import ui

async def gmb_game_loop(interaction: discord.Interaction):
    view = ui.WagerSelectView()
    await interaction.response.send_message(
        content="💰 Choose your wager amount:",
        view=view
    )
    view.message = await interaction.original_response()
