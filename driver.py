import asyncio
import logging
import os
import sys
from datetime import datetime
from os import getenv
import aiogram.exceptions
from aiogram import Router, F, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from sqlalchemy import update, select

from handlers.inform import IsAdmin, admin_chat_id, pending_drivers, confirm_button1
from keyboards import driver_button, cancel_button, confirm_button, main_button, admin_button, cancel_button1, \
    register_button, tariff_button, driver_location_button
from models import Driver, session, User
from state import DriverState, EditDriverState, AdminState
from aiogram import html

dp = Dispatcher()

driver_router = Router()
dp.include_routers(driver_router)

load_dotenv()
TOKEN = getenv("TOKEND")


@driver_router.message(CommandStart())
async def start_bot(message: Message, state: FSMContext):
    user_id = message.from_user.id
    full_name = html.bold(message.from_user.full_name)
    username = message.from_user.username
    await state.clear()

    # User bazada bor yoki yo‘qligini tekshirish
    existing_user = session.query(User).filter_by(user_id=user_id).first()
    if not existing_user:
        new_user = User(user_id=user_id, username=username)
        session.add(new_user)
        session.commit()

    # Haydovchi bazada bor yoki yo‘qligini tekshirish
    query = select(Driver).where(Driver.telegram_id == str(user_id))
    driver = session.execute(query).scalars().first()

    if driver:
        markup = driver_button()
    else:
        markup = register_button()

    # Xabarni bir marta yuborish
    await message.answer(
        f'Ассалому алайкум, {full_name}\n\nБизнинг ботга хуш келибсиз',
        reply_markup=markup
    )

    # Admin uchun tugmalar
    if str(user_id) == os.getenv('ADMIN_ID'):
        await message.answer(
            f'Салом админ {full_name}',
            reply_markup=admin_button()
        )


@driver_router.message(F.text == "📞 Админ билан боғланиш")
async def contact_with_admin(message: Message):
    await message.answer("Илтимос шу одамга Телеграмдан ёзинг @VPEXadmin")


@driver_router.message(F.text == "Ортга")
async def back(message: Message):
    user_id = message.from_user.id
    query = select(Driver).where(Driver.telegram_id == str(user_id))
    driver = session.execute(query).scalars().first()

    if driver:
        await message.answer('Танланг :', reply_markup=driver_button())


@driver_router.message(F.text == "Бекор килиш")
async def back(message: Message, state: FSMContext):
    user_id = message.from_user.id
    query = select(Driver).where(Driver.telegram_id == str(user_id))
    driver = session.execute(query).scalars().first()
    if state:
        await state.clear()
    if driver:
        await message.answer('Бекор килинди ✅', reply_markup=driver_button())
    await message.answer('Бекор килинди ✅')


@driver_router.message(F.text.func(lambda text: text and text.strip().lower() == "рўйхатдан ўтиш"))
async def start_shofer(message: Message, state: FSMContext):
    """Агар ҳайдовчи базада мавжуд бўлса, менюни кўрсатади. Акс ҳолда, рўйхатдан ўтказиш бошланади."""
    query = select(Driver).where(Driver.telegram_id == str(message.from_user.id))
    driver = session.execute(query).scalars().first()

    if driver:
        await message.answer("Танланг:", reply_markup=driver_button())

    else:
        await message.answer(
            "📝 Исм-шарифингизни киритинг \n\nМасалан: Ботир Кодиров :", reply_markup=cancel_button(message)
        )
        await state.set_state(DriverState.full_name)


@driver_router.message(DriverState.full_name)
async def capture_driver_fullname(message: Message, state: FSMContext):
    """Исм-шарифини сақлайди ва кейинги қадамга ўтади."""
    await state.update_data(full_name=message.text)
    await message.answer("📆 Ёшингизни киритинг \n\nМасалан: 25 :", reply_markup=cancel_button(message))
    await state.set_state(DriverState.age)


@driver_router.message(DriverState.age)
async def capture_driver_age(message: Message, state: FSMContext):
    """Ёшни сақлайди ва фақат рақам киритилганини текширади."""
    if not message.text.isdigit():  # 🔍 Фақат сон киритилганлигини текшириш
        await message.answer("⚠️ Илтимос, ёшингизни фақат рақам сифатида киритинг! (Масалан: 25)",
                             reply_markup=cancel_button(message))
        return  # ❌ Агар нотўғри бўлса, функцияни тугатамиз

    await state.update_data(age=int(message.text))  # ✅ Тўғри ёшни сақлаш
    await message.answer("📍 Вилоятингизни киритинг \n\nМасалан: Андижон йоки Тошкент:",
                         reply_markup=cancel_button(message))
    await state.set_state(DriverState.city)


# registratsiyadan keyin malumoti rasmsiz va andijondan yoki toshkentdaman deb tugmani ezishiga grurhga tashab qoyadi
# tarifni tanlaydi nomerdan oldin
@driver_router.message(DriverState.city)
async def capture_driver_city(message: Message, state: FSMContext):
    """Шаҳарни сақлайди ва кейинги қадамга ўтади."""
    await state.update_data(city=message.text)
    await message.answer("🏢 Туманни киритинг \n\nМасалан: Хожаобод :", reply_markup=cancel_button(message))
    await state.set_state(DriverState.town)


@driver_router.message(DriverState.town)
async def capture_driver_town(message: Message, state: FSMContext):
    """Туман номини сақлайди ва кейинги қадамга ўтади."""
    await state.update_data(town=message.text)
    await message.answer("🚗 Машина турини киритинг \n\nМасалан: Кобалт :", reply_markup=cancel_button(message))
    await state.set_state(DriverState.type_of_car)


@driver_router.message(DriverState.type_of_car)
async def capture_driver_car_type(message: Message, state: FSMContext):
    """Машина турини сақлайди ва кейинги қадамга ўтади."""
    await state.update_data(type_of_car=message.text)
    await message.answer("🚖 Тарифни танланг:\n"
                         '''
Стандарт тариф :

Автомобил салонига 4 та 
йуловчи олинади 

Манзилга йетгунга кадар тухташлар сони 3 тадан ошмайди

Автомобиллари 1 ва 2 позиция булади

Нархлар уртача ва ундан арзонрок.

🚖 🚖 🚖 🚖 🚖 🚖 🚖 🚖 🚖 

Комфорт тариф :

Автомобил салонига 3 та 
йуловчи олинади 

Манзилга йетгунга кадар тухташлар сони 1 тадан ошмайди (йуловчи эхтийожи бундан мустасно)

Автомобиллари  3 позиция ва ундан юкори булади

Нархлар уртача ва ундан сал киммат

Автомобиллари дейарли хаммасида танирофка мавжуд, кондиционер доимий об хавога караб, салонда без газ сув доимий тоза салон.
                         ''', reply_markup=tariff_button())
    await state.set_state(DriverState.tariff)


@driver_router.message(DriverState.tariff)
async def capture_driver_car_type(message: Message, state: FSMContext):
    """Машина турини сақлайди ва кейинги қадамга ўтади."""
    if message.text not in ["Стандарт", "Комфорт"]:
        await message.answer("⚠️ Илтимос, тарифни тўғри танланг!", reply_markup=tariff_button())
        return
    await state.update_data(tariff=message.text)
    await message.answer("📞 Телефон рақамингизни киритинг \n\nМасалан: 970501655 :",
                         reply_markup=cancel_button(message))
    await state.set_state(DriverState.phone_number)


@driver_router.message(DriverState.phone_number)
async def capture_driver_phone_number(message: Message, state: FSMContext):
    if not message.text.isdigit():  # 🔍 Фақат сон киритилганлигини текшириш
        await message.answer("⚠️ Илтимос, телефон номери фақат рақам сифатида киритинг! (Масалан: 970501655)",
                             reply_markup=cancel_button(message))
        return  # ❌ Агар нотўғри бўлса, функцияни тугатамиз
    """Телефон рақамини сақлайди ва кейинги қадамга ўтади."""
    await state.update_data(phone_number=int(message.text))
    await message.answer("📄 Правангизни расмини юборинг :", reply_markup=cancel_button(message))
    await state.set_state(DriverState.document)


@driver_router.message(DriverState.document)
async def capture_driver_document(message: Message, state: FSMContext):
    """Ҳужжат расмини сақлайди ва кейинги қадамга ўтади."""
    if message.photo:
        await state.update_data(document=message.photo[-1].file_id)
        await message.answer("📃 Техпаспорт расмини юборинг :", reply_markup=cancel_button(message))
        await state.set_state(DriverState.tex_passport)
    else:
        await message.answer("⚠️ Илтимос, ҳужжат расмини юборинг!")


@driver_router.message(DriverState.tex_passport)
async def capture_driver_tex_passport(message: Message, state: FSMContext):
    """Техпаспорт расмини сақлайди, барча маълумотларни чиқаради ва тасдиқлаш сўрайди."""

    if not message.photo:
        await message.answer("⚠️ Илтимос, техпаспорт расмини юборинг!", reply_markup=cancel_button(message))
        return

    # ✅ **Техпаспорт расмини сақлаш**
    await state.update_data(tex_passport=message.photo[-1].file_id)

    # 🔍 **State даги барча маълумотларни олиш**
    data = await state.get_data()

    # 📋 **Ҳайдовчининг киритган маълумотларини чиқариш**
    caption = (
        f"📋 *Сиз киритган маълумотлар:*\n\n"
        f"👤 *Исм:* {data.get('full_name', 'Номаълум')}\n"
        f"🗓 *Ёш:* {data.get('age', 'Номаълум')}\n"
        f"🏙 *Шаҳар:* {data.get('city', 'Номаълум')}\n"
        f"📍 *Туман:* {data.get('town', 'Номаълум')}\n"
        f"🚗 *Машина тури:* {data.get('type_of_car', 'Номаълум')}\n"
        f"😎 *Тариф тури:* {data.get('tariff', 'Номаълум')}\n"
        f"📞 *Тел:* {data.get('phone_number', 'Номаълум')}\n"
    )

    # ✅ **Ҳужжат ва техпаспортни юбориш**
    if data.get("document"):
        await message.answer_photo(photo=data["document"], caption="📄 *Сизнинг Правангиз *", parse_mode="Markdown")

    if data.get("tex_passport"):
        await message.answer_photo(photo=data["tex_passport"], caption="📄 *Сизнинг техпаспортингиз*",
                                   parse_mode="Markdown")

    # ✅ **Маълумотларни тасдиқлаш учун юбориш**
    await message.answer(caption, parse_mode="Markdown")
    await message.answer("📋 *Маълумотларни тасдиқлайсизми?*", reply_markup=confirm_button(), parse_mode="Markdown")

    await state.set_state(DriverState.user_confirm)


@driver_router.callback_query(DriverState.user_confirm, F.data == "confirm_yes")
async def process_confirm_yes(callback_query: CallbackQuery, state: FSMContext, bot):
    """Фойдаланувчи (шофёр) маълумотларини админга юбориш."""
    data = await state.get_data()
    telegram_id = str(callback_query.from_user.id)

    if not data:
        await callback_query.message.answer("⚠️ Хатолик: Маълумотлар йўқолди! Илтимос, қайта уриниб кўринг.")
        return

    # ✅ **Фойдаланувчи ID ни маълумотларга қўшиш**
    data["telegram_id"] = telegram_id

    print(f"✅ Админ тасдиқлаш учун маълумотлар: {data}")  # DEBUG

    caption = (
        f"📋 Янги Шофёр:\n"
        f"👤 Исми: {data.get('full_name', 'Номаълум')}\n"
        f"🗓 Ёши: {data.get('age', 'Номаълум')}\n"
        f"🏙 Шаҳар: {data.get('city', 'Номаълум')}\n"
        f"📍 Туман: {data.get('town', 'Номаълум')}\n"
        f"🚗 Машина тури: {data.get('type_of_car', 'Номаълум')}\n"
        f"😎 *Тариф тури:* {data.get('tariff', 'Номаълум')}\n"
        f"📞 Тел: {data.get('phone_number', 'Номаълум')}\n\n\n"
        "Маълумотларни тасдиклайсизми?"
    )

    msg = None  # ✅ Ensure msg is always defined

    for admin in admin_chat_id:
        if data.get("document"):
            await bot.send_photo(admin, photo=data["document"], caption="📄 Ҳужжат (Права)")

        if data.get("tex_passport"):
            try:
                msg = await bot.send_photo(admin, photo=data["tex_passport"], caption=caption)
            except:
                msg = await bot.send_document(admin, document=data["tex_passport"], caption=caption)

    if msg:
        message_id = msg.message_id  # ✅ Админга юборилган хабар ID сини сақлаш
        pending_drivers[message_id] = data  # ✅ **telegram_id билан бирга сақлаймиз!**
        print(f"✅ Маълумот сақланди: {message_id} -> {data}")  # ✅ Debug

        await bot.edit_message_reply_markup(
            chat_id=msg.chat.id,
            message_id=message_id,
            reply_markup=confirm_button1(message_id)  # ✅ Хабар ID билан тугмалар яратиш
        )

    await callback_query.message.delete()
    await callback_query.message.answer("✅ Маълумотлар админга юборилди, илтимос кутиб туринг.",
                                        reply_markup=main_button())


@driver_router.callback_query(F.data.startswith("admin_yes_"))
async def admin_approve_driver(callback_query: CallbackQuery, bot: Bot):
    """Админ тасдиқласа, шофёр базага сақланади."""
    message_id = int(callback_query.data.split("_")[-1])  # ✅ Хабар ID ни олиш

    print(f"🔍 Админ тасдиқлаган хабар ID: {message_id}")  # ✅ DEBUG

    if message_id not in pending_drivers:
        await callback_query.message.answer("⚠️ Хатолик: Маълумотлар топилмади! Илтимос, қайта уриниб кўринг.")
        return

    шофёр_data = pending_drivers.pop(message_id)  # ✅ Маълумотларни олиш ва cachedan ўчириш
    user_id = шофёр_data.get("telegram_id")  # ✅ Фойдаланувчининг Telegram ID сини олиш
    drivergroup = -1002630555042

    await save_driver_to_db(шофёр_data, callback_query)

    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer("✅ Шофёр базага сақланди!", reply_markup=admin_button())

    if user_id:
        await bot.send_message(user_id, "✅ *Админ маълумотларингизни қабул қилди!*", parse_mode="Markdown",
                               reply_markup=driver_button())
        await bot.send_message(drivergroup, шофёр_data)


@driver_router.callback_query(DriverState.user_confirm, F.data == "confirm_no")
async def process_confirm_no(callback_query: CallbackQuery, state: FSMContext):
    """Фойдаланувчи шофёр бўлишдан воз кечди."""
    await state.clear()
    await callback_query.message.answer("❌ Маълумотлар бекор қилинди.", reply_markup=main_button())


@driver_router.callback_query(F.data.startswith("admin_no_"))
async def admin_reject_driver(callback_query: CallbackQuery, bot: Bot):
    """Админ шофёрни рад этса, фойдаланувчига хабар боради."""
    message_id = int(callback_query.data.split("_")[-1])  # ✅ Хабар ID ни олиш

    print(f"🔍 Админ рад этган хабар ID: {message_id}")  # ✅ DEBUG

    if message_id not in pending_drivers:
        await callback_query.message.answer("⚠️ Хатолик: Маълумотлар топилмади! Илтимос, қайта уриниб кўринг.")
        return

    шофёр_data = pending_drivers.pop(message_id)  # ✅ Маълумотларни олиш ва cachedan ўчириш
    user_id = шофёр_data.get("telegram_id")  # ✅ Фойдаланувчининг Telegram ID сини олиш

    await callback_query.message.edit_reply_markup(reply_markup=None)  # ✅ Инлайн тугмаларни ўчириш
    await callback_query.message.answer("❌ Шофёр аризаси рад этилди!")
    await callback_query.message.delete()
    if user_id:
        await bot.send_message(user_id, "❌ *Админ маълумотларингизни рад этди.*", parse_mode="Markdown",
                               reply_markup=main_button())


async def save_driver_to_db(data: dict, callback: CallbackQuery):
    """Шофёрни базага сақлаш функцияси"""

    telegram_id = data.get("telegram_id")  # ✅ Telegram ID ни олиш

    if not telegram_id:
        print("❌ Хатолик: Telegram ID топилмади!")
        return

    existing_driver = session.execute(
        select(Driver).where(Driver.telegram_id == telegram_id)
    ).scalars().first()

    if existing_driver:
        print(f"❌ Хатолик: Бу шофёр ({telegram_id}) аллақачон рўйхатдан ўтган!")
        return

    print(f"✅ Базага сақланаётган маълумотлар: {data}")

    driver = Driver(
        telegram_id=telegram_id,
        full_name=data.get('full_name', 'No Name'),
        age=int(data.get('age', 0)),
        city=data.get('city', 'No City'),
        town=data.get('town', 'No Town'),
        type_of_car=data.get('type_of_car', 'No Car'),
        tariff=data.get('tariff', 'No Tarif'),
        phone_number=data.get('phone_number', 'No Number'),
        document=data.get('document', 'No Document'),
        tex_passport=data.get('tex_passport', 'No Tex Passport'),
    )

    session.add(driver)
    session.commit()
    print(f"✅ Шофёр ({telegram_id}) муваффақиятли қўшилди!")


"""
Шофёр
"""

"""Маълумотларни янгилаш қисми"""


def get_edit_driver_keyboard():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Исмини ўзгартириш", callback_data="edit_full_name")
    ikb.button(text="Ёшни ўзгартириш", callback_data="edit_age")
    ikb.button(text="Шаҳарни ўзгартириш", callback_data="edit_city")
    ikb.button(text="Туманни ўзгартириш", callback_data="edit_town")
    ikb.button(text="Машина турини ўзгартириш", callback_data="edit_type_of_car")
    ikb.button(text="Машина тарифини ўзгартириш", callback_data="edit_type_of_tariff")
    ikb.button(text="Телефон рақамни ўзгартириш", callback_data="edit_phone_number")
    ikb.button(text="Ҳужжатни ўзгартириш", callback_data="edit_document")
    ikb.button(text="Тех паспортни ўзгартириш", callback_data="edit_tex_passport")
    ikb.adjust(1)
    return ikb.as_markup()


async def update_driver_field(user_id: int, field_name: str, value: str):
    # Ensure user_id is a string for comparison
    user_id_str = str(user_id)
    query = update(Driver).where(Driver.telegram_id == user_id_str).values({field_name: value})
    session.execute(query)
    session.commit()


@driver_router.message(F.text == "💼 Маълумотларни янгилаш")
async def change_datas(message: Message):
    await message.answer("Қайси маълумотингизни алмаштирмоқчисиз?", reply_markup=get_edit_driver_keyboard())


@driver_router.callback_query(F.data == "edit_full_name")
async def edit_full_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Янги исмингизни киритинг (Масалан: Али):", reply_markup=cancel_button1(callback))
    await state.set_state(EditDriverState.full_name)
    await callback.answer()


@driver_router.message(EditDriverState.full_name)
async def save_full_name(message: Message, state: FSMContext):
    full_name = message.text
    await update_driver_field(message.from_user.id, "full_name", full_name)

    await message.answer(f"Исмингиз янгиланди: {full_name}", reply_markup=driver_button())
    await state.clear()


@driver_router.callback_query(F.data == "edit_age")
async def edit_age(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Янги ёшингизни киритинг (Масалан: 21):", reply_markup=cancel_button1(callback))
    await state.set_state(EditDriverState.age)
    await callback.answer()


@driver_router.message(EditDriverState.age)
async def save_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Илтимос, ёшингизни фақат рақам сифатида киритинг! (Масалан: 25)",
                             reply_markup=cancel_button(message))
        return
    age = int(message.text)
    await update_driver_field(message.from_user.id, "age", age)

    await message.answer(f"Ёшингиз янгиланди: {age}", reply_markup=driver_button())
    await state.clear()


@driver_router.callback_query(F.data == "edit_city")
async def edit_city(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Янги шаҳарни киритинг (Масалан: Андижон):", reply_markup=cancel_button1(callback))
    await state.set_state(EditDriverState.city)
    await callback.answer()


@driver_router.message(EditDriverState.city)
async def save_city(message: Message, state: FSMContext):
    city = message.text
    await update_driver_field(message.from_user.id, "city", city)

    await message.answer(f"Шаҳар янгиланди: {city}", reply_markup=driver_button())
    await state.clear()


@driver_router.callback_query(F.data == "edit_town")
async def edit_town(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Янги туманни киритинг (Масалан: Жалакудук):", reply_markup=cancel_button1(callback))
    await state.set_state(EditDriverState.town)
    await callback.answer()


@driver_router.message(EditDriverState.town)
async def save_town(message: Message, state: FSMContext):
    town = message.text
    await update_driver_field(message.from_user.id, "town", town)

    await message.answer(f"Туман янгиланди: {town}", reply_markup=driver_button())
    await state.clear()


@driver_router.callback_query(F.data == "edit_type_of_car")
async def edit_type_of_car(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Янги машина турини киритинг (Масалан: Жентра):",
                                  reply_markup=cancel_button1(callback))
    await state.set_state(EditDriverState.type_of_car)
    await callback.answer()


@driver_router.message(EditDriverState.type_of_car)
async def save_type_of_car(message: Message, state: FSMContext):
    type_of_car = message.text
    await update_driver_field(message.from_user.id, "type_of_car", type_of_car)

    await message.answer(f"Машина тури янгиланди: {type_of_car}", reply_markup=driver_button())
    await state.clear()


@driver_router.callback_query(F.data == "edit_type_of_tariff")
async def edit_type_of_car(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🚖 Тарифни танланг:\n"
                                  '''
         Стандарт тариф :
         
         Автомобил салонига 4 та 
         йуловчи олинади 
         
         Манзилга йетгунга кадар тухташлар сони 3 тадан ошмайди
         
         Автомобиллари 1 ва 2 позиция булади
         
         Нархлар уртача ва ундан арзонрок.
         
         🚖 🚖 🚖 🚖 🚖 🚖 🚖 🚖 🚖 
         
         Комфорт тариф :
         
         Автомобил салонига 3 та 
         йуловчи олинади 
         
         Манзилга йетгунга кадар тухташлар сони 1 тадан ошмайди (йуловчи эхтийожи бундан мустасно)
         
         Автомобиллари  3 позиция ва ундан юкори булади
         
         Нархлар уртача ва ундан сал киммат
         
         Автомобиллари дейарли хаммасида танирофка мавжуд, кондиционер доимий об хавога караб, салонда без газ сув доимий тоза салон.
                                  ''', reply_markup=tariff_button())
    await state.set_state(EditDriverState.tariff)
    await callback.answer()


@driver_router.message(EditDriverState.tariff)
async def save_type_of_car(message: Message, state: FSMContext):
    type_of_tariff = message.text
    await update_driver_field(message.from_user.id, "tariff", type_of_tariff)

    await message.answer(f"Машина тарифи янгиланди: {type_of_tariff}", reply_markup=driver_button())
    await state.clear()


@driver_router.callback_query(F.data == "edit_phone_number")
async def edit_phone_number(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Янги телефон рақамингизни киритинг (Масалан: 970501655):",
                                  reply_markup=cancel_button1(callback))
    await state.set_state(EditDriverState.phone_number)
    await callback.answer()


@driver_router.message(EditDriverState.phone_number)
async def save_phone_number(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            "⚠️ Илтимос, телефон рақамни фақат рақамлардан иборат қилиб киритинг! (Масалан: 970501655)",
            reply_markup=cancel_button(message))
        return
    phone_number = int(message.text)
    await update_driver_field(message.from_user.id, "phone_number", phone_number)

    await message.answer(f"Телефон рақам янгиланди: {phone_number}", reply_markup=driver_button())
    await state.clear()


@driver_router.callback_query(F.data == "edit_document")
async def edit_document(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📄 Янги ҳужжат расмини юборинг:", reply_markup=cancel_button1(callback))
    await state.set_state(EditDriverState.document)
    await callback.answer()


@driver_router.message(EditDriverState.document)
async def save_document(message: Message, state: FSMContext):
    if message.photo:
        document = message.photo[-1].file_id
    # elif message.document:
    #     document = message.document.file_id
    else:
        await message.answer("⚠️ Илтимос, расм юборинг!", reply_markup=cancel_button(message))
        return

    await update_driver_field(message.from_user.id, "document", document)
    await message.answer("✅ Ҳужжат янгиланди!", reply_markup=driver_button())


@driver_router.callback_query(F.data == "edit_tex_passport")
async def edit_tex_passport(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📃 Янги тех паспорт расмини юборинг:", reply_markup=cancel_button1(callback))
    await state.set_state(EditDriverState.tex_passport)
    await callback.answer()


@driver_router.message(EditDriverState.tex_passport)
async def save_tex_passport(message: Message, state: FSMContext):
    if message.photo:
        tex_passport = message.photo[-1].file_id
    # elif message.document:
    #     tex_passport = message.document.file_id
    else:
        await message.answer("⚠️ Илтимос, расм юборинг!", reply_markup=cancel_button(message))
        return

    await update_driver_field(message.from_user.id, "tex_passport", tex_passport)
    await message.answer("✅ Тех паспорт янгиланди!", reply_markup=driver_button())
    await state.clear()


@driver_router.message(F.text == "📊 Менинг маълумотларим")
async def show_driver_info(message: Message):
    """Ҳайдовчининг барча маълумотларини чиқаради."""

    # 1️⃣ Ҳайдовчини базадан топамиз
    driver = session.execute(
        select(Driver).where(Driver.telegram_id == str(message.from_user.id))
    ).scalars().first()

    # 2️⃣ Агар ҳайдовчи базада бўлмаса, хабар чиқарамиз
    if not driver:
        await message.answer("⚠️ Сиз ҳали рўйхатдан ўтмагансиз! Аввал маълумотларингизни тўлдиринг.")
        return

    # 3️⃣ Ҳайдовчининг барча маълумотларини чиқарамиз
    caption = (
        f"📋 *Сизнинг маълумотларингиз:*\n\n"
        f"👤 *Исм:* {driver.full_name}\n"
        f"🗓 *Ёш:* {driver.age}\n"
        f"🏙 *Шаҳар:* {driver.city}\n"
        f"📍 *Туман:* {driver.town}\n"
        f"🚗 *Машина тури:* {driver.type_of_car}\n"
        f"😎 *Тариф тури:* {driver.tariff}\n"
        f"📞 *Тел:* {driver.phone_number}\n"
        # f"🔢 *Навбат рақами:* {driver.queue if driver.queue else 'Йўқ'}\n"
    )

    await message.answer(caption, parse_mode="Markdown")

    # 4️⃣ Агар ҳайдовчининг ҳужжатлари бўлса, расм сифатида юборамиз
    if driver.document:
        await message.answer_photo(driver.document, caption="📄 *Сизнинг ҳужжатингиз (Права)*",
                                   parse_mode="Markdown")

    if driver.tex_passport:
        await message.answer_photo(driver.tex_passport, caption="📃 *Сизнинг техпаспортингиз*",
                                   parse_mode="Markdown")


from datetime import datetime

from datetime import datetime


# Tugma yaratish funksiyasi

# "🔉 Жойни белгилаш" bosilganda tugmalar chiqadi
@driver_router.message(F.text == "🔉 Жойни белгилаш")
async def contact_with_admin(message: Message):
    await message.answer("📍 Ҳозирги жойлашувингизни танланг:", reply_markup=driver_location_button())


# Tugmalardan birini bosganda ma’lumotlar guruhga yuboriladi
@driver_router.message(F.text.in_(["Андижондаман", "Тошкентдаман"]))
async def send_driver_info(message: Message, bot: Bot):
    # Foydalanuvchi ma'lumotlarini bazadan olish
    query = select(Driver).where(Driver.telegram_id == str(message.from_user.id))
    driver = session.execute(query).scalars().first()

    if not driver:
        await message.answer("❌ Сиз рўйхатдан ўтмагансиз!")
        return

    # Hozirgi vaqtni olish
    now = datetime.now().strftime("%H:%M:%S")

    # Haydovchi ma'lumotlari
    location = message.text  # Foydalanuvchi tanlagan joy
    text = (
        f"🚖 Янги локатсия\n\n"
        f"👤 Ҳайдовчи: {driver.full_name}\n"
        f"🕒 Вақт: {now}\n"
        f"🚘 Машина: {driver.type_of_car} \n"
        f"📞 Номери:({driver.phone_number})\n"
        f"📍 Жойлашув: {location}"
    )

    # Haydovchiga javob yuborish
    # shopirlar = -1002630555042 #shopurlar

    if location == "Андижондаман":
        GROUP_ID = -1002540963651  # toshkent shopirlar
        await bot.send_message(GROUP_ID, text)
        await message.answer("✅ Локатсия юборилди!")
    if location == "Тошкентдаман":
        GROUP_ID1 = -1002673628832  # adnijon shopirlar

        await bot.send_message(GROUP_ID1, text)
        await message.answer("✅ Локатсия юборилди!")


@driver_router.message(F.text == 'Реклама 🔊', IsAdmin())
async def start_advertisement(message: Message, state: FSMContext):
    await message.answer("📸 Реклама расмини юборинг!")
    await state.set_state(AdminState.photo)


# 📌 **Реклама учун расм юклаш**
@driver_router.message(AdminState.photo, IsAdmin(), F.photo)
async def capture_ad_photo(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await state.update_data(photo=photo)
    await state.set_state(AdminState.title)
    await message.answer("📝 Реклама ҳақида тўлиқ маълумот киритинг!")


# 📌 **Реклама матнини қабул қилиш ва фойдаланувчиларга юбориш**
@driver_router.message(AdminState.title, IsAdmin(), ~F.photo)
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


# 🔹 **Admin Paneli**
# KeyboardButton(text="А -> Т Шопирлар"),
# KeyboardButton(text="Т -> А Шопирлар"),
# tarif qoshib , Joylashuvni guruhga yuborib turish
# @driver_router.message(F.text == "🔅 А -> Т Шопирлар", IsAdmin())
# async def admin_panel1(message: Message):
#     """Бугунги Андижондан Тошкентга кетаётган шоферларни чиқаради"""
#     drivers = session.query(Driver).filter(
#         Driver.route == "Андижон -> Тошкент",
#         Driver.date_added >= datetime.now().date()
#     ).order_by(Driver.queue).all()
#
#     if not drivers:
#         await message.answer("🚖 Бугун Андижондан Тошкентга кетаётган шофёрлар мавжуд эмас.")
#         return
#
#     response = "🚖 *Андижон -> Тошкент шофёрлари*\n\n"
#     for driver in drivers:
#         response += f"🏙 *Тартиб раками:* {driver.queue}\n"
#         response += f"🏙 *Исми:* {driver.full_name}\n"
#         response += f"🏙 *Туман:* {driver.town}\n"
#         response += f"⏰ *Кетиш вақти:* {driver.delivery_time}\n"
#         response += f"📞 *Телефон:* {driver.phone_number}\n"
#         response += "---------------------\n"
#
#     await message.answer(response, parse_mode="Markdown")
#
#
# @driver_router.message(F.text == "🔅 Т -> А Шопирлар", IsAdmin())
# async def admin_panel(message: Message):
#     """Бугунги Тошкентдан Андижонга кетаётган шоферларни чиқаради"""
#     drivers = session.query(Driver).filter(
#         Driver.route == "Тошкент -> Андижон",
#         Driver.date_added >= datetime.now().date()
#     ).order_by(Driver.queue).all()
#
#     if not drivers:
#         await message.answer("🚖 Бугун Тошкентдан Андижонга кетаётган шофёрлар мавжуд эмас.")
#         return
#
#     response = "🚖 *Тошкент -> Андижон шофёрлари*\n\n"
#     for driver in drivers:
#         response += f"🏙 *Тартиб раками:* {driver.queue}\n"
#         response += f"🏙 *Исми:* {driver.full_name}\n"
#         response += f"🏙 *Туман:* {driver.town}\n"
#         response += f"⏰ *Кетиш вақти:* {driver.delivery_time}\n"
#         response += f"📞 *Телефон:* {driver.phone_number}\n"
#         response += "---------------------\n"
#
#     await message.answer(response, parse_mode="Markdown")


@driver_router.message(F.text == "Админ Бўлими")
async def admin_panel(message: Message):
    link = 'http://localhost:8050'
    await message.answer(text=f'🔗 Админ Бўлимига ўтиш: {link}')


async def driver() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    asyncio.run(driver())
