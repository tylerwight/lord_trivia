import discord
import db
import string
import asyncio
import ui

async def mp_trivia_loop(interaction: discord.Interaction, rounds: int = 3):
    tmpq = db.get_random_question()
    view = ui.MPButtonContainer(tmpq)
    for _ in range(rounds):
        question = db.get_random_question()
        view.question = question
        view.user_answers = {}
        view.repopulate_buttons()

        # Format the question prompt and answer choices
        letters = string.ascii_uppercase
        answer_lines = "\n".join(
            f"{letters[i]}: {answer}" for i, answer in enumerate(question.answers)
        )
        content = f"**Trivia Time!**\n{question.prompt}\n{answer_lines}"

        if view.message is None:
            # First round, send the message
            await interaction.response.send_message(content, view=view)
            view.message = await interaction.original_response()  
        else:
            await view.message.edit(content=content, view=view)

        await asyncio.sleep(15)

        # Build a summary of who answered what
        summary_lines = []
        for user_id, answer_index in view.user_answers.items():
            user = db.get_user(interaction.guild_id, user_id)
            user.answers_total += 1

            if answer_index == question.correct_index:
                user.answers_correct += 1
                user.streak += 1
                user.points += 1
                result = "✅"
            else:
                user.streak = 0
                result = "❌"

            db.update_user(user)
            summary_lines.append(f"<@{user_id}> {result}")

        # Show results
        results_text = "\n".join(summary_lines) or "*No answers this round.*"
        await view.message.edit(content=content + "\n\n**Results:**\n" + results_text, view=None)

        await asyncio.sleep(3)

    await interaction.channel.send("🏁 Trivia session ended!")
