import requests
import html
import random
import json
import models
import db
"""
Pulls random trivia questions from opentdb and adds them to the lord_trivia database.
This assumes the database has already been created, run lord_trivia once to ensure the DB connectoin is working
run with `python3 get_quetsions.py`
"""
url = "https://opentdb.com/api.php?amount=50"
data = requests.get(url)

if not data:
    print("request failed, exiting")
    exit

json_data = json.loads(data.text)


print(f"number of results: {len(json_data['results'])}")

for question in json_data['results']:
    print(f"working on: {question['question']}\n====================================")
    if len(question['incorrect_answers']) > 3:
        raise ValueError("expected ≤ 3 answers") 
    
    prompt = html.unescape(question['question'])
    difficulty = html.unescape(question['difficulty'])
    category = html.unescape(question['category'])
    correct = html.unescape(question['correct_answer'])
    answers = [html.unescape(a) for a in question['incorrect_answers']]
    answers.append(correct)
    
    random.shuffle(answers)
    correct_index = answers.index(correct)


    input_q = models.Question(               
        prompt = prompt,
        answers = answers,
        correct_index = correct_index,
        category = category,
        difficulty = difficulty
    )

    
    db.add_question(input_q)
    print("\n")




