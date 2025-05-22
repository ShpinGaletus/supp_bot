import asyncpg

DATABASE = 'postgresql://postgres:123456@localhost:5432/support_bot'

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