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

ACTION_TYPES = {
    "start": 1,
    "help": 2,
    "choose_category": 3,
    "choose_question": 4,
    "chat_request": 5,
    "chat_start": 6,
    "ask_question": 7
}

async def create_db_pool():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE)

async def category_exists(name):
    async with db_pool.acquire() as connection:
        exists = await connection.fetchval(
            "SELECT EXISTS(SELECT 1 FROM category WHERE LOWER(name) = LOWER($1))", name
        )
        return exists
    
async def category_add(name):
    async with db_pool.acquire() as connection:
        cat_id = await connection.fetchval(
            "INSERT INTO category (name) VALUES ($1) RETURNING id", name
        )
        return cat_id
async def category_remove(category_id):
    async with db_pool.acquire() as connection:
        await connection.execute('DELETE FROM category WHERE id = $1', category_id)

async def question_add(category_id, question, answer):
    async with db_pool.acquire() as connection:
        question_id = await connection.fetchval(
            "INSERT INTO faq (category_id, question, answer) VALUES ($1, $2, $3) RETURNING id", category_id, question, answer
        )
        return question_id

async def question_remove(question_id):
    async with db_pool.acquire() as connection:
        await connection.execute('DELETE FROM faq WHERE id = $1', question_id)

async def question_exists(question_text):
    async with db_pool.acquire() as connection:
        exists = await connection.fetchval(
            "SELECT EXISTS(SELECT 1 FROM faq WHERE LOWER(question) = LOWER($1))", question_text
        )
        return exists

async def log_user_action(user_id, action_type, category_id=None, faq_id=None, another_question=None):
    action_type_id = ACTION_TYPES[action_type]
    async with db_pool.acquire() as connection:
        user_action_id = await connection.fetchval(
            """
            INSERT INTO user_action(user_id, action_time, action_type_id, category_id, faq_id, another_question)
            VALUES ($1, NOW(), $2, $3, $4, $5)
            RETURNING id
            """, user_id, action_type_id, category_id, faq_id, another_question
        )
        return user_action_id
    
async def log_chat_message(user_action_id, sender_type, message_text, operator_id):
    async with db_pool.acquire() as connection:
        await connection.execute(
            """
            INSERT INTO chat_message(user_action_id, sender_type, message_text, sent_at, operator_id)
            VALUES ($1, $2, $3, NOW(), $4)
            RETURNING id
            """, user_action_id, sender_type, message_text, operator_id
        )
    
async def get_categories():
    async with db_pool.acquire() as connection:
        return await connection.fetch("SELECT id, name FROM category ORDER BY name")

async def get_operators():
    async with db_pool.acquire() as connection:
        rows = await connection.fetch("SELECT tg_id FROM staff WHERE role = 'operator'")
        return [row['tg_id'] for row in rows]

async def get_admins():
    async with db_pool.acquire() as connection:
        rows = await connection.fetch("SELECT tg_id FROM staff WHERE role = 'admin'")
        return [row['tg_id'] for row in rows]
   
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

