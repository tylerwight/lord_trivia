from config import DB_CONFIG
import mysql.connector
from mysql.connector import Error
import logging
import models
import json


def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None
    

def initialize():
    conn = get_connection()
    if not conn:
        print("Failed to initialize database: No connection.")
        return

    cursor = conn.cursor()
    try:
        # Create user_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                points BIGINT DEFAULT 0,
                streak INT DEFAULT 0,
                answers_total INT DEFAULT 0,
                answers_correct INT DEFAULT 0,
                gambling_winnings BIGINT DEFAULT 0,
                gambling_losses BIGINT DEFAULT 0,
                UNIQUE (guild_id, user_id)
            );
        """)

        # Create questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                prompt VARCHAR(1024),
                answers JSON,
                correct_index INT,
                enabled BOOLEAN NOT NULL DEFAULT TRUE
            );
        """)

        logging.info("Database schema verified.")
    except Error as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        cursor.close()
        conn.close()


#################
######USERS######
#################

def add_user(guild_id: int, user_id: int):
    conn = get_connection()
    if not conn:
        logging.info("Unable to connect to database.")
        return

    cursor = conn.cursor()
    try:
        query = """
        INSERT IGNORE INTO user_data (guild_id, user_id)
        VALUES (%s, %s)
        """
        cursor.execute(query, (guild_id, user_id))
        conn.commit()
        logging.info(f"DB.ADDUSER: User {user_id} in guild {guild_id} added to user_data.")
    except Error as e:
        logging.error(f"Error adding user: {e}")
    finally:
        cursor.close()
        conn.close()

def user_exists(guild_id: int, user_id: int) -> bool:
    conn = get_connection()
    if not conn:
        print("Unable to connect to database.")
        return False

    cursor = conn.cursor()
    try:
        query = """
        SELECT 1 FROM user_data
        WHERE guild_id = %s AND user_id = %s
        LIMIT 1
        """
        cursor.execute(query, (guild_id, user_id))
        result = cursor.fetchone()
        return result is not None
    except Error as e:
        print(f"Error checking if user exists: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_user(guild_id: int, user_id: int) -> models.User | None:
    conn = get_connection()
    if not conn:
        logging.info("DB.GETUSER: unable to connect to DB")
        return None
    
    cursor = conn.cursor()
    try:
        query = "SELECT guild_id, user_id, points, streak, answers_total, answers_correct, gambling_winnings, gambling_losses FROM user_data WHERE guild_id=%s AND user_id=%s"
        cursor.execute(query, (guild_id, user_id))
        row = cursor.fetchone()
        if row:
            return models.User(
                guild_id=row[0],
                user_id=row[1],
                points=row[2],
                streak=row[3],
                answers_total=row[4],
                answers_correct=row[5],
                gambling_winnings=row[6],
                gambling_losses=row[7],
            )
        else:
            logging.info(f"DB.GETUSER: No user found with guild_id {guild_id} and user_id {user_id}")
            return None
    except Error as e:
        logging.error(f"DB.GETUSER: Error Retrieving User: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


#################
####QUESTIONS####
#################

def add_question(question: models.Question):
    conn = get_connection()
    if not conn:
        logging.info("Unable to connect to database.")
        return

    cursor = conn.cursor()
    try:
        query = "INSERT INTO questions (prompt, answers, correct_index) VALUES (%s, %s, %s)"
        cursor.execute(query, (question.prompt, json.dumps(question.answers), question.correct_index))
        conn.commit()
        logging.info(f"DB.ADDQUESTION: Question added to table Questions: {question.prompt}.")

    except Error as e:
        logging.error(f"Error adding question: {e}")
    finally:
        cursor.close()
        conn.close()


def get_question(question_id: int) -> models.Question | None:
    conn = get_connection()
    if not conn:
        logging.error("DB.GETQUESTION: unable to connect to DB")
        return None
    
    cursor = conn.cursor()
    try:
        query = "SELECT prompt, answers, correct_index FROM questions WHERE id = %s"
        cursor.execute(query, (question_id,))
        row = cursor.fetchone()
        if row:
            return models.Question(prompt=row[0], answers=json.loads(row[1]), correct_index=row[2])
        else:
            logging.info(f"DB.GETQUESTION: No question found with id {question_id}")
            return None
    except Error as e:
        logging.error(f"DB.GETQUESTION: Error Retrieving QUESTION: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_random_question() -> models.Question | None:
    conn = get_connection()
    if not conn:
        logging.warning("DB.GET_RANDOM_QUESTION: Unable to connect to DB.")
        return None

    cursor = conn.cursor()
    try:
        query = """
            SELECT prompt, answers, correct_index
            FROM questions
            WHERE enabled = TRUE
            ORDER BY RAND()
            LIMIT 1
        """
        cursor.execute(query)
        row = cursor.fetchone()
        if row:
            return models.Question(
                prompt=row[0],
                answers=json.loads(row[1]),
                correct_index=row[2]
            )
        else:
            logging.info("DB.GET_RANDOM_QUESTION: No enabled questions found.")
            return None
    except Error as e:
        logging.error(f"DB.GET_RANDOM_QUESTION: Error retrieving question: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


#create database "lord_trivia"
#CREATE TABLE user_data (id INT AUTO_INCREMENT PRIMARY KEY, guild_id BIGINT NOT NULL, user_id BIGINT NOT NULL, points BIGINT DEFAULT 0, streak INT DEFAULT 0, answers_total INT DEFAULT 0, answers_correct INT DEFAULT 0, gambling_winnings BIGINT DEFAULT 0, gambling_losses BIGINT DEFAULT 0);
#CREATE USER 'lord_trivia'@'localhost' IDENTIFIED BY 'your_secure_password';

# CREATE TABLE questions (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     prompt VARCHAR(1024),
#     answers JSON,
#     correct_index INT,
#     enabled BOOLEAN
# );

# Insert into MySQL
# cursor.execute(
#     "INSERT INTO questions (prompt, answers, correct_index) VALUES (%s, %s, %s)",
#     (q.prompt, json.dumps(q.answers), q.correct_index)
# )


# cursor.execute("SELECT prompt, answers, correct_index FROM questions WHERE id = %s", (question_id,))
# row = cursor.fetchone()
# q = Question(prompt=row[0], answers=json.loads(row[1]), correct_index=row[2])

# if __name__ == "__main__":
#     q1 = models.Question(
#         prompt="What is 2 + 2?",
#         answers=["3", "4", "5", "6"],
#         correct_index=1
#     )
#     add_question(q1)