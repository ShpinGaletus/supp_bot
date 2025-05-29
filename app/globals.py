from .database import get_operators, get_admins

OPERATORS = []
ADMINS = []

async def load_roles():
    global OPERATORS, ADMINS
    OPERATORS = await get_operators()
    ADMINS = await get_admins()
    print(f"Loaded operators: {OPERATORS}")