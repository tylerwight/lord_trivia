import os
from dotenv import load_dotenv
import logging
from logging.handlers import TimedRotatingFileHandler
import colorlog


dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(dotenv_path)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'database': os.getenv('DB_DATABASE')
}



#Logging config
os.makedirs("./logs", exist_ok=True)

console_handler = colorlog.StreamHandler()
console_handler.setFormatter(colorlog.ColoredFormatter(
    fmt='[%(asctime)s] [lord_trivia] [%(log_color)s%(levelname)s%(reset)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    }
))



file_handler = TimedRotatingFileHandler(
    "./logs/CommunityPlaylistWeb.log",
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)

file_formatter = logging.Formatter(
    fmt='[%(asctime)s] [lord_trivia] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S' 
)

file_handler.setFormatter(file_formatter)



logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)