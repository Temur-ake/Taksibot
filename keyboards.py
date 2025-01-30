from aiogram.enums import ChatType
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_button():
    rkb = ReplyKeyboardBuilder()
    rkb.add(
        *[
            KeyboardButton(text='Клиент'),
            KeyboardButton(text='Шофёр')
        ]
    )
    rkb.adjust(2, 2)
    return rkb.as_markup(resize_keyboard=True)


def client_button(message):
    rkb = ReplyKeyboardBuilder()
    if message.chat.type == ChatType.PRIVATE:
        rkb.add(
            *[
                KeyboardButton(text='Андижон -> Тошкент'),
                KeyboardButton(text='Тошкент -> Андижон'),
                # KeyboardButton(text="Фарғона -> Тошкент"),
                # KeyboardButton(text="Тошкент -> Фарғона"),
                # KeyboardButton(text='Наманган -> Тошкент'),
                # KeyboardButton(text="Тошкент -> Наманган"),

                KeyboardButton(text="Почта бор"),
                KeyboardButton(text="Ортга")

            ]
        )
        rkb.adjust(2, 2)
    return rkb.as_markup(resize_keyboard=True)
