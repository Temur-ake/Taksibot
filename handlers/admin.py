import os
import asyncio
import aiogram.exceptions
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv

from handlers.inform import IsAdmin
from keyboards import admin_button
from state import AdminState
from models import session, User

# 🔹 **Админ тугмалари**


load_dotenv()
ADMIN_ID = int(os.getenv('ADMIN_ID'))
admin_router = Router()


# 📌 **Админ бўлимига ўтиш ҳаволаси**
@admin_router.message(F.text == "Админ Бўлими")
async def admin_panel(message: Message):
    link = 'http://localhost:8050'
    await message.answer(text=f'🔗 Админ Бўлимига ўтиш: {link}')


# 📌 **Реклама жараёнини бошлаш**
@admin_router.message(F.text == 'Реклама 🔊', IsAdmin())
async def start_advertisement(message: Message, state: FSMContext):
    await message.answer("📸 Реклама расмини юборинг!")
    await state.set_state(AdminState.photo)


# 📌 **Реклама учун расм юклаш**
@admin_router.message(AdminState.photo, IsAdmin(), F.photo)
async def capture_ad_photo(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await state.update_data(photo=photo)
    await state.set_state(AdminState.title)
    await message.answer("📝 Реклама ҳақида тўлиқ маълумот киритинг!")


# 📌 **Реклама матнини қабул қилиш ва фойдаланувчиларга юбориш**
@admin_router.message(AdminState.title, IsAdmin(), ~F.photo)
async def send_advertisement(message: Message, state: FSMContext):
    title = message.text
    data = await state.get_data()
    await state.clear()

    users = session.query(User).filter(User.user_id.isnot(None)).all()

    if not users:
        await message.answer("🚫 Ҳеч кимга реклама юборилмади. Фойдаланувчилар мавжуд эмас.")
        return

    tasks = []
    deleted_users = []

    for user in users:
        if user.user_id:
            try:
                # ✅ **Реклама юбориш**
                tasks.append(message.bot.send_photo(
                    chat_id=user.user_id,
                    photo=data['photo'],
                    caption=title
                ))

            except aiogram.exceptions.TelegramForbiddenError:
                print(f'🚫 Фойдаланувчи {user.user_id} ботни блоклаган ёки гуруҳдан чиқиб кетган.')
                deleted_users.append(user.user_id)

            except aiogram.exceptions.TelegramBadRequest as e:
                if "chat not found" in str(e):
                    print(f'🚫 Фойдаланувчи {user.user_id} топилмади. Ўчиришга тайёрланмоқда.')
                    deleted_users.append(user.user_id)
                else:
                    print(f'❌ {user.user_id} га юборишда хатолик: {e}')

    # ✅ **Блоклаган ёки топилмаган фойдаланувчиларни базадан ўчириш**
    if deleted_users:
        session.query(User).filter(User.user_id.in_(deleted_users)).delete(synchronize_session=False)
        session.commit()
        print(f"🗑️ {len(deleted_users)} та фойдаланувчи базадан ўчирилди.")

    if tasks:
        await asyncio.gather(*tasks)

    await message.answer("✅ Реклама барча актив фойдаланувчиларга юборилди!", reply_markup=admin_button())

# 📌 **Буюртмаларни тозалаш**
# @admin_router.message(F.text == "🔄 Буюртмаларни Тозалаш", F.from_user.id == ADMIN_ID)
# async def clear_orders(message: Message):
#     global PENDING_ORDERS
#     PENDING_ORDERS = []
#     await message.answer("✅ Барча навбатдаги буюртмалар ўчирилди!")
