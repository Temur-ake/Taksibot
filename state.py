from aiogram.fsm.state import StatesGroup, State


class Data(StatesGroup):
    client = State()
    driver = State()
    delivery = State()



class AdminState(StatesGroup):
    title = State()
    photo = State()
    end = State()
