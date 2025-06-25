import discord
import db
import string
import asyncio
import time
import logging
import models


async def submit_question_loop(interaction: discord.Interaction, client: discord.Client):
    await interaction.response.send_message("Starting thread to submit question...", ephemeral=False)
    inital_message = await interaction.original_response()

    thread = await inital_message.create_thread(name=f"Submit Trivia Question with {interaction.user}")

    def check(m):
        return m.author == interaction.user and m.channel == thread
    
    await thread.send("Please type the prompt for your trivia question (ex: what is the capital of Bolivia?)")
    try:
        prompt_msg = await client.wait_for("message", timeout=60.0, check=check)
        logging.info(f"Raw message object: {prompt_msg}") 
        prompt = prompt_msg.content
        logging.info(f"Got prompt from user: {prompt}")
    except asyncio.TimeoutError:
        await thread.send("You took too long to respond. Bye!")
        return
    

    await thread.send("Please type the correct answer (ex: Sucre)")
    try:
        correct_msg = await client.wait_for("message", timeout=60.0, check=check)
        correct_ans = correct_msg.content
        logging.info(f"Got correct answer from user: {correct_ans}")
    except asyncio.TimeoutError:
        await thread.send("You took too long to respond. Bye!")
        return
    
    await thread.send("Please type an incorrect answer (1/3) (ex: Alabama)")
    try:
        incorrect_1_msg = await client.wait_for("message", timeout=60.0, check=check)
        incorrect_1_ans = incorrect_1_msg.content
    except asyncio.TimeoutError:
        await thread.send("You took too long to respond. Bye!")
        return
    
    await thread.send("Please type an incorrect answer (2/3) (ex: Bogota)")
    try:
        incorrect_2_msg = await client.wait_for("message", timeout=60.0, check=check)
        incorrect_2_ans = incorrect_2_msg.content
    except asyncio.TimeoutError:
        await thread.send("You took too long to respond. Bye!")
        return
    
    await thread.send("Please type an incorrect answer (3/3) (ex: Buenos Aires)")
    try:
        incorrect_3_msg = await client.wait_for("message", timeout=60.0, check=check)
        incorrect_3_ans = incorrect_3_msg.content
    except asyncio.TimeoutError:
        await thread.send("You took too long to respond. Bye!")
        return
    

    await thread.send(f"you gave me: {prompt}, Correct: {correct_ans}, 1: {incorrect_1_ans}, 2: {incorrect_2_ans}, 3: {incorrect_3_ans}\n\n Is that correct? yes/no")

    try:
        finished_msg = await client.wait_for("message", timeout=60.0, check=check)
        finished = finished_msg.content
    except asyncio.TimeoutError:
        await thread.send("You took too long to respond. Bye!")
        return
    
    if 'no' in finished.lower():
        await thread.send("okay bye.")
        return
    

    if 'yes' in finished.lower():
        await thread.send("Great, adding question to the database!")
        input_question = models.Question(
            prompt = prompt,
            answers = [correct_ans, incorrect_1_ans, incorrect_2_ans, incorrect_3_ans],
            correct_index = 0,
            difficulty = "Medium",
            category="General"
        )
        if db.add_question(input_question):
            await thread.send("Quesiton added successfully")
        else:
            await thread.send("Error adding question to database")

