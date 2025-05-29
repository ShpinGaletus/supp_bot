import os

from aiogram import Bot
from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("API_TOKEN")

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_db = int(os.getenv("REDIS_DB", 0))

redis_client = Redis(host=redis_host, port=redis_port, db=redis_db)
bot = Bot(token=TOKEN)
storage = RedisStorage(redis=redis_client, state_ttl=3600, data_ttl=3600)

