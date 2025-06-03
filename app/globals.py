from .database import get_operators, get_admins
from collections import deque
OPERATORS = []
ADMINS = []
operator_queue = deque()

async def load_roles():
    global OPERATORS, ADMINS, operator_queue
    OPERATORS = await get_operators()
    operator_queue = deque(OPERATORS)
    ADMINS = await get_admins()