from dataclasses import dataclass
from typing import List

@dataclass
class Question:
    prompt: str
    answers: List[str]
    correct_index: int
    difficulty: str
    category: str

    def is_correct(self, user_choice: str) -> bool:
        # Normalize input and map letters to indices
        user_choice = user_choice.strip().upper()
        letter_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        return letter_to_index.get(user_choice) == self.correct_index
    
@dataclass
class User:
    guild_id: int
    user_id: int
    points: int
    streak: int
    answers_total: int
    answers_correct: int
    gambling_winnings: int
    gambling_losses: int


if __name__ == "__main__":
    q1 = Question(
        prompt="What is 2 + 2?",
        answers=["3", "4", "5", "6"],
        correct_index=1
    )

    # Print the question and answer choices
    print(q1.prompt)
    for idx, answer in enumerate(q1.answers):
        print(f" {chr(65 + idx)}: {answer}")  # chr(65) is 'A'

    answer = input("Your answer (A, B, C, D): ")
    if q1.is_correct(answer):
        print("Right!")
    else:
        print("Wrong!")