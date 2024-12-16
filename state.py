from aiogram.fsm.state import StatesGroup, State


class Client(StatesGroup):
    client = State()
    phone_number = State()


class Driver(StatesGroup):
    driver = State()

class Delivery(StatesGroup):
    delivery = State()
    phone_number = State()


class AdminState(StatesGroup):
    title = State()
    photo = State()
    end = State()
