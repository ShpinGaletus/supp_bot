import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DBNAME = os.getenv("PG_DBNAME")
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", 5432))

DATABASE = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"

db_pool: asyncpg.pool.Pool = None

async def create_db_pool():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE)

async def get_categories():
    async with db_pool.acquire() as connection:
        return await connection.fetch("SELECT id, name FROM category ORDER BY name")
    
async def get_category_name_by_id(category_id):
    async with db_pool.acquire() as connection:
        result = await connection.fetchrow(
            "SELECT name FROM category WHERE id = $1", category_id
        )
        return result['name'] if result else "Неизвестная категория"    
    
async def get_questions_by_category(category_id):
    async with db_pool.acquire() as connection:
        return await connection.fetch(
            "SELECT id, question FROM faq WHERE category_id = $1 ORDER BY id",
            category_id
        )   

async def get_answer(question_id):
    async with db_pool.acquire() as connection:
        result = await connection.fetchrow(
            "SELECT answer FROM faq WHERE id = $1", question_id
        )
        return result['answer'] if result else "Ответ не найден."
    
async def get_question_by_id(question_id):
    async with db_pool.acquire() as connection:
        result = await connection.fetchrow(
            "SELECT question FROM faq WHERE id = $1", question_id
        )
        return result['question'] if result else "Вопрос не найден."    