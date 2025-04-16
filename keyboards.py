from aiogram.enums import ChatType
from aiogram.types import KeyboardButton, CallbackQuery, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_button():
    rkb = ReplyKeyboardBuilder()
    rkb.add(
        *[
            KeyboardButton(text='Клиент'),
            # KeyboardButton(text='Шофёр'),
            KeyboardButton(text="Почта бор"),
            KeyboardButton(text="Оператор билан боғланиш"),
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

                KeyboardButton(text="Ортга")

            ]
        )
        rkb.adjust(2, 2)
    return rkb.as_markup(resize_keyboard=True)


def delivery_button(message):
    rkb = ReplyKeyboardBuilder()
    if message.chat.type == ChatType.PRIVATE:
        rkb.add(
            *[
                KeyboardButton(text='Андижон => Тошкент'),
                KeyboardButton(text='Тошкент => Андижон'),
                # KeyboardButton(text="Фарғона -> Тошкент"),
                # KeyboardButton(text="Тошкент -> Фарғона"),
                # KeyboardButton(text='Наманган -> Тошкент'),
                # KeyboardButton(text="Тошкент -> Наманган"),

                KeyboardButton(text="Ортга")

            ]
        )
        rkb.adjust(2, 2)
    return rkb.as_markup(resize_keyboard=True)


def cancel_button(message):
    rkb = ReplyKeyboardBuilder()
    if message.chat.type == ChatType.PRIVATE:
        rkb.add(
            *[
                KeyboardButton(text="Бекор килиш")

            ]
        )
        rkb.adjust(2, 2)

    return rkb.as_markup(resize_keyboard=True)


def cancel_button1(callback: CallbackQuery):
    rkb = ReplyKeyboardBuilder()
    if callback.message.chat.type == ChatType.PRIVATE:
        rkb.add(
            *[
                KeyboardButton(text="Бекор килиш")

            ]
        )
        rkb.adjust(2, 2)

    return rkb.as_markup(resize_keyboard=True)


def confirm_button():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ҳа", callback_data="confirm_yes"),
                InlineKeyboardButton(text="❌ Йўқ", callback_data="confirm_no"),
            ]
        ]
    )
    return keyboard


def driver_button():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(
        KeyboardButton(text='🔉 Жойни белгилаш'),
        KeyboardButton(text=' 💼 Маълумотларни янгилаш'),
        KeyboardButton(text='📞 Админ билан боғланиш'),
        KeyboardButton(text='📊 Менинг маълумотларим')
    )
    keyboard.adjust(2, 2)
    return keyboard.as_markup(resize_keyboard=True)


def admin_button():
    rkb = ReplyKeyboardBuilder()
    rkb.add(
        KeyboardButton(text='Реклама 🔊'),
        KeyboardButton(text="Админ Бўлими"),
        # KeyboardButton(text="🔅 А -> Т Шопирлар"),
        # KeyboardButton(text="🔅 Т -> А Шопирлар"),
    )
    rkb.adjust(2, 2)
    return rkb.as_markup(resize_keyboard=True)


# 🔹 Tugmalar yaratish funksiyalari
def tariff_button():
    """ Тариф танлаш тугмалари """
    buttons = [
        [KeyboardButton(text="Стандарт"), KeyboardButton(text="Комфорт")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def quantity_button():
    """ Одам сонини танлаш тугмалари """
    buttons = [
        [KeyboardButton(text="1"), KeyboardButton(text="2")],
        [KeyboardButton(text="3"), KeyboardButton(text="4")],
        # [KeyboardButton(text="Бошқа")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def register_button():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="Рўйхатдан ўтиш"))
    return keyboard.as_markup(resize_keyboard=True)


def driver_location_button():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="Андижондаман"))
    keyboard.add(KeyboardButton(text="Тошкентдаман"))
    keyboard.add(KeyboardButton(text="Ортга"))
    keyboard.adjust(2, 2)
    return keyboard.as_markup(resize_keyboard=True)
