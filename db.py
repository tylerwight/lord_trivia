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
        # Create table if it doesn't exist
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
        print("Database schema verified.")
    except Error as e:
        print(f"Error initializing database: {e}")
    finally:
        cursor.close()
        conn.close()