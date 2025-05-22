import discord
import db
import string
import asyncio
import ui
import time

async def mp_trivia_loop(interaction: discord.Interaction, rounds: int = 3):
    tmpq = db.get_random_question()
    view = ui.MPButtonContainer(tmpq)
    sleeptime = 15
    for round in range(rounds):
        question = db.get_random_question()
        view.question = question
        view.user_answers = {}
        view.repopulate_buttons()

        # Format the question prompt and answer choices
        letters = string.ascii_uppercase
        embed = discord.Embed(
            title=f"Trivia Time! Round {round+1}/{rounds}",
            description=question.prompt,
            color=discord.Color.blurple()
        )
        
        for i, answer in enumerate(question.answers):
            embed.add_field(name=f":regional_indicator_{letters[i].lower()}: :", value=answer, inline=False)

        current_time_unix = int(time.time())
        embed.add_field(name=f"Time Left", value = f"<t:{current_time_unix + sleeptime}:R>", inline=False)
    
        if view.message is None:
            # First round, send the message
            await interaction.response.send_message(embed=embed, view=view)
            view.message = await interaction.original_response()  
        else:
            await view.message.edit(embed=embed, view=view)

        await asyncio.sleep(sleeptime + 2)

        # Build a summary of who answered what
        summary_lines = []
        for user_id, answer_index in view.user_answers.items():
            user = db.get_user(interaction.guild_id, user_id)

            if user_id not in view.user_totals:
                view.user_totals[user_id] = {
                    "correct": 0,
                    "points": 0,
                }
            user.answers_total += 1

            if answer_index == question.correct_index:
                user.answers_correct += 1
                user.streak += 1
                user.points += 1
                result = f"✅ +1 points"
                view.user_totals[user_id]["correct"] += 1
                view.user_totals[user_id]["points"] += 1
            else:
                user.streak = 0
                result = "❌ +0 points"

            db.update_user(user)
            summary_lines.append(f"<@{user_id}> {result}")

        # Show results
        results_text = "\n".join(summary_lines) or "*No answers this round.*"
        embed.add_field(name="Results", value=results_text, inline=False)
        await view.message.edit(embed=embed, view=None)
        await asyncio.sleep(4)

    if view.user_totals:
        final_lines = []
        for user_id, stats in view.user_totals.items():
            final_lines.append(
                f"<@{user_id}> — ✅ Correct: {stats['correct']}/{rounds}, 🏅 Points: {stats['points']}"
            )

        await interaction.channel.send(
            "🏁 Trivia session ended!\n **📊 Final Results:**\n" + "\n".join(final_lines)
        )
    else:
        await interaction.channel.send("🏁 Trivia session ended!\n No one participated. 😢")
