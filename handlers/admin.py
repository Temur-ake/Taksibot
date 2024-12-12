import asyncio
import os

import aiogram
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv

from state import AdminState
from models import session, User


def admin_button():
    rkb = ReplyKeyboardBuilder()
    rkb.add(
        KeyboardButton(text='Reklama 🔊'),
        KeyboardButton(text="Admin Bo'limi")
    )
    return rkb.as_markup(resize_keyboard=True)


load_dotenv()
admin_router = Router()


@admin_router.message(F.text == "Admin Bo'limi")
async def admin(message: Message):
    link = 'http://k.temur.life:8030'
    await message.answer(text=f'Admin Bolimi ga otish {link}')


@admin_router.message(F.text == 'Reklama 🔊', F.from_user.id == int(os.getenv('ADMIN_ID')))
async def admin(message: Message, state: FSMContext):
    await message.answer("Reklama rasmini kiriting !")
    await state.set_state(AdminState.photo)


# Handle photo upload for the ad
@admin_router.message(AdminState.photo, F.from_user.id == int(os.getenv('ADMIN_ID')), ~F.text, F.photo)
async def admin(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await state.update_data({"photo": photo})
    await state.set_state(AdminState.title)
    await message.answer("Reklama haqida to'liq malumot bering !")


@admin_router.message(AdminState.title, F.from_user.id == int(os.getenv('ADMIN_ID')), ~F.photo)
async def admin(message: Message, state: FSMContext):
    title = message.text
    await state.update_data({"title": title})

    data = await state.get_data()
    await state.clear()

    users = session.query(User).filter(User.user_id.isnot(None)).all()

    if not users:
        await message.answer("Hech kimga reklama yuborilmadi. Foydalanuvchilar mavjud emas.")
        return

    tasks = []
    for user in users:
        if user.user_id:
            try:

                chat_member = await message.bot.get_chat_member(user.user_id, user.user_id)

                if chat_member.status == 'left' or chat_member.status == 'kicked':
                    print(f'User {user.user_id} has blocked the bot or left the chat. Skipping.')
                    continue

                tasks.append(message.bot.send_photo(
                    chat_id=user.user_id,
                    photo=data['photo'],
                    caption=data['title']
                ))

            except aiogram.exceptions.TelegramForbiddenError:

                print(f'User {user.user_id} has blocked the bot. Skipping this user.')
                continue

            except aiogram.exceptions.TelegramBadRequest as e:

                if "chat not found" in str(e):
                    print(f'User {user.user_id} not found. Skipping.')
                else:
                    print(f'Failed to send to user {user.user_id}: {e}')
                continue
    await message.answer("Reklama yuborildi !")
    if tasks:
        await asyncio.gather(*tasks)
