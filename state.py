from aiogram.fsm.state import StatesGroup, State


class Client(StatesGroup):
    town = State()
    client_count = State()
    hour = State()
    tariff = State()
    phone_number = State()


class DriverState(StatesGroup):
    full_name = State()
    age = State()
    city = State()
    town = State()
    type_of_car = State()
    tariff = State()
    phone_number = State()
    document = State()
    tex_passport = State()
    user_confirm = State()
    admin_confirm = State()


class EditDriverState(StatesGroup):
    full_name = State()
    age = State()
    city = State()
    town = State()
    type_of_car = State()
    tariff = State()
    phone_number = State()
    document = State()
    tex_passport = State()


class OrderState(StatesGroup):
    route = State()
    delivery_time = State()


class Delivery(StatesGroup):
    town = State()
    delivery = State()
    hour = State()
    phone_number = State()


class AdminState(StatesGroup):
    title = State()
    photo = State()
    end = State()
