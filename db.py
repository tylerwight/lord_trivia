#create database "lord_trivia"
#CREATE TABLE user_data (id INT AUTO_INCREMENT PRIMARY KEY, guild_id BIGINT NOT NULL, user_id BIGINT NOT NULL, points BIGINT DEFAULT 0, streak INT DEFAULT 0, answers_total INT DEFAULT 0, answers_correct INT DEFAULT 0, gambling_winnings BIGINT DEFAULT 0, gambling_losses BIGINT DEFAULT 0);
#CREATE USER 'lord_trivia'@'localhost' IDENTIFIED BY 'your_secure_password';
from config import DB_CONFIG
import mysql.connector
from mysql.connector import Error
import logging


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
        logging.info("Database schema verified.")
    except Error as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        cursor.close()
        conn.close()


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
        logging.info(f"User {user_id} in guild {guild_id} added to user_data.")
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
