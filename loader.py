import os

from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=TOKEN)
storage = MemoryStorage()