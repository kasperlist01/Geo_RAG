from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    """Состояния пользователя для FSM"""
    IDLE = State()            # Ожидание команды
    WAITING_FOR_FILE = State() # Ожидание загрузки файла
    WAITING_FOR_QUERY = State() # Ожидание запроса