from datetime import datetime

from aiogram import Bot, Router, F
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton,  InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy import update, select, func

from keyboards import main_button, cancel_button, delivery_button, driver_button, confirm_button, \
    cancel_button1, client_button, admin_button, tariff_button, quantity_button
from models import session, Driver
from state import Delivery, Client, DriverState, EditDriverState, OrderState

inform_router = Router()

# 📌 Define groups
GROUP_ANDIJON = -1002560104017  # Buyurtma A -> T gruppa
GROUP_TASHKENT = -1002462270850  # Buyurtma T -> A gruppa
# shopirlar = -1002630555042 #shopurlar
# GROUP_ID = -1002673628832  # toshkent shopirlar
# GROUP_ID1 = -1002540963651 #adnijon shopirlar
admin_chat_id = [7914466408]
pending_drivers = {}

ROUTES = ["Андижон -> Тошкент", "Тошкент -> Андижон"]
ROUTES1 = ["Андижон => Тошкент", "Тошкент => Андижон"]

ANDIJON_TOWNS = [
    "Андижон шаҳар", "Олтинкўл", "Асака", "Балиқчи", "Булоқбоши", "Куйганёр",
    "Бўстон", "Избоскан", "Жалақудуқ", "Марҳамат", "Пахтаобод", "Пойтуғ",
    "Хўжаобод", "Шаҳрихон", "Улуғнор", "Хонобод", "Қорасув", "Қўрғонтепа"
]

TASHKENT_TOWNS = [
    "Бектемир", "Чилонзор", "Миробод", "Мирзо Улуғбек", "Олмазор",
    "Сергели", "Шайхонтохур", "Учтепа", "Яккасарой", "Яшнаобод", "Юнусобод"
]


def confirm_button1(message_id: int):
    """Админ учун тасдиқлаш тугмалари"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ҳа", callback_data=f"admin_yes_{message_id}"),
                InlineKeyboardButton(text="❌ Йўқ", callback_data=f"admin_no_{message_id}"),
            ]
        ]
    )
    return keyboard


def get_route_keyboard():
    """🚗 Haydovchi yo‘nalishini tanlash uchun tugmalar"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=route, callback_data=f"route_{route}")] for route in ROUTES
        ]
    )
    return keyboard


class IsAdmin(Filter):
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __call__(self, message: Message, bot: Bot) -> bool:
        return message.from_user.id in admin_chat_id


def format_route(route: str) -> str:
    from_city, to_city = route.split(" -> ")
    return f"{from_city}дан {to_city}га"


@inform_router.message(F.text == "Ортга")
async def back(message: Message):
    await message.answer('Танланг :', reply_markup=main_button())


@inform_router.message(F.text == "Бекор килиш")
async def back(message: Message, state: FSMContext):
    if state:
        await state.clear()
    await message.answer('Бекор килинди ✅', reply_markup=main_button())


# 📌 **Dynamic town selection based on route**
def town_button(route: str):
    """Generate dynamic town selection buttons based on the chosen route."""
    rkb = ReplyKeyboardBuilder()
    if "-> Тошкент" in route or "=> Тошкент" in route:
        towns = ANDIJON_TOWNS
    if "-> Андижон" in route or "=> Андижон" in route:
        towns = TASHKENT_TOWNS

    for town in towns:
        rkb.add(KeyboardButton(text=town))
    rkb.add(KeyboardButton(text="Бекор килиш"))  # Back button
    rkb.adjust(3, 3)
    return rkb.as_markup(resize_keyboard=True)


async def process_order(message: Message, state: FSMContext, bot: Bot, is_pochta=False):
    """📦 Почта ёки клиент буюртмаларини ҳайдовчиларга тақсимлаш"""
    data = await state.get_data()
    route = data.get("route")
    town = data.get("town")
    user_count = data.get("client_count")
    user_message = data.get("user_message")
    delivery_time = str(data.get("hour"))
    phone_number = message.text if "phone_number" not in data else data.get("phone_number")
    username = message.from_user.username or "-"
    tariff = data.get("tariff", "Почта")

    # order_type = "📦 Почта" if is_pochta else "🧍 Клиент"
    if is_pochta:
        client_info = (
            f"🛣 Йўналиш: {route}\n🏙 Туман: {town}\n📋 Малумот: {user_message}\n"
            f"⏰ Вақт: {delivery_time}\n📞 Телефон: {phone_number}\n"
            f"👤 Телеграм: @{username}\n"
        )
    if not is_pochta:
        client_info = (
            f"🛣 Йўналиш: {route}\n🏙 Туман: {town}\n📋 Одам сони: {user_count}\n"
            f"⏰ Вақт: {delivery_time}\n📞 Телефон: {phone_number}\n"
            f"👤 Телеграм: @{username}\n"
        )

    # 📌 Send to the correct group based on the **route**
    if route in ["Андижон -> Тошкент", "Андижон => Тошкент"]:
        await bot.send_message(GROUP_ANDIJON, f"🚕 {tariff}  буюртма!\n{client_info}")

    elif route in ["Тошкент -> Андижон", "Тошкент => Андижон"]:
        await bot.send_message(GROUP_TASHKENT, f"🚕 {tariff}  буюртма!\n{client_info}")

    await message.answer("✅ Cизнинг буюртмангиз қабул қилинди. Тез орада сиз билан боғланамиз!",
                         reply_markup=main_button())
    await state.clear()


# 📦 **Pochta buyurtmalari**
@inform_router.message(F.text == "Почта бор")
async def start_pochta(message: Message):
    await message.answer("🚖 Йўналишни танланг:", reply_markup=delivery_button(message))


@inform_router.message(F.text.in_(ROUTES1))
async def route_pochta(message: Message, state: FSMContext):
    await state.update_data(route=message.text)
    await message.answer("🚖 Почтани қаердан оламиз:\n\n Туманни танланг йоки киритинг:",
                         reply_markup=town_button(message.text))
    await state.set_state(Delivery.town)


@inform_router.message(Delivery.town)
async def capture_pochta_town(message: Message, state: FSMContext):
    await state.update_data(town=message.text)
    await message.answer("✉️ Илтимос буюртма хақида бироз малумот беринг!\n\n"

                         "Мисол учун: Андижондан Яккасаройга Битта сумкада кийимлар бор,\nВелосипедни олиб кетиш керак, Илтимос фақат томида \nбагажи борлар алоқага чиқсин",
                         reply_markup=cancel_button(message))
    await state.set_state(Delivery.delivery)


@inform_router.message(Delivery.delivery)
async def capture_pochta_message(message: Message, state: FSMContext):
    await state.update_data(user_message=message.text)
    await message.answer("⏰ Нечида чикариб юбориш керак? Масалан: 19:00", reply_markup=cancel_button(message))
    await state.set_state(Delivery.hour)


@inform_router.message(Delivery.hour)
async def capture_pochta_hour(message: Message, state: FSMContext):
    try:
        delivery_time = datetime.strptime(message.text.strip(), "%H:%M").time()
        await state.update_data(hour=delivery_time)
    except ValueError:
        await message.answer("⚠️ Илтимос, тўғри форматда ёзинг! Масалан: 15:30", reply_markup=cancel_button(message))
        return

    await message.answer("📞 Телефон рақамингизни киритинг: Масалан: 970501655", reply_markup=cancel_button(message))
    await state.set_state(Delivery.phone_number)


@inform_router.message(Delivery.phone_number)
async def capture_pochta_phone(message: Message, state: FSMContext, bot: Bot):
    if not message.text.isdigit():
        await message.answer("⚠️ Телефон рақами фақат рақамлардан иборат бўлиши керак!",
                             reply_markup=cancel_button(message))
        return

    await state.update_data(phone_number=message.text)
    await process_order(message, state, bot, is_pochta=True)


# 🧍 **Klient buyurtmalari**
@inform_router.message(F.text == "Клиент")
async def start_client(message: Message):
    await message.answer("🚖 Йўналишни танланг:", reply_markup=client_button(message))


@inform_router.message(F.text.in_(ROUTES))
async def start_client_route(message: Message, state: FSMContext):
    await state.update_data(route=message.text)
    await message.answer("🚖 Сизни қаердан оламиз:\n\n Туманни танланг йоки киритинг:",
                         reply_markup=town_button(message.text))
    await state.set_state(Client.town)


@inform_router.message(Client.town)
async def capture_client_town(message: Message, state: FSMContext):
    await state.update_data(town=message.text)
    await message.answer("👥 Одам сонини танланг йоки киритинг:", reply_markup=quantity_button())
    await state.set_state(Client.client_count)  # ✅ State to'g'rilandi


@inform_router.message(Client.client_count)
async def capture_client_count(message: Message, state: FSMContext):
    await state.update_data(client_count=int(message.text))

    await message.answer("⏰ Нечида йолга чикишингиз керак? Масалан: 19:00", reply_markup=cancel_button(message))
    await state.set_state(Client.hour)


@inform_router.message(Client.hour)
async def capture_client_hour(message: Message, state: FSMContext):
    try:
        delivery_time = datetime.strptime(message.text.strip(), "%H:%M").time()
        await state.update_data(hour=delivery_time)
    except ValueError:
        await message.answer("⚠️ Илтимос, тўғри форматда ёзинг! Масалан: 15:30", reply_markup=cancel_button(message))
        return

    # 🔹 TARIF tanlash tugmalari
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
    await state.set_state(Client.tariff)


@inform_router.message(Client.tariff)
async def client_tariff(message: Message, state: FSMContext):
    if message.text not in ["Стандарт", "Комфорт"]:
        await message.answer("⚠️ Илтимос, тарифни тўғри танланг!", reply_markup=tariff_button())
        return

    await state.update_data(tariff=message.text)
    await message.answer("📞 Телефон рақамингизни киритинг: Масалан: 970501655", reply_markup=cancel_button(message))
    await state.set_state(Client.phone_number)


@inform_router.message(Client.phone_number)
async def client_phone(message: Message, state: FSMContext, bot: Bot):
    if not message.text.isdigit():
        await message.answer("⚠️ Телефон рақами фақат рақамлардан иборат бўлиши керак!",
                             reply_markup=cancel_button(message))
        return

    await state.update_data(phone_number=message.text)
    await process_order(message, state, bot, is_pochta=False)


@inform_router.message(F.text == "Оператор билан боғланиш")
async def call_center(message: Message):
    await message.answer("Биз билан богланиш учун:\n\n+998552010255\n\n@VPEXadmin")


# @inform_router.message(F.text == "Шофёр")
# async def start_shofer(message: Message, state: FSMContext):
#     """Агар ҳайдовчи базада мавжуд бўлса, менюни кўрсатади. Акс ҳолда, рўйхатдан ўтказиш бошланади."""
#     query = select(Driver).where(Driver.telegram_id == str(message.from_user.id))
#     driver = session.execute(query).scalars().first()
#
#     if driver:
#         await message.answer("Танланг:", reply_markup=driver_button())
#
#     else:
#         await message.answer(
#             "📝 Исм-шарифингизни киритинг \n\nМасалан: Ботир Кодиров :", reply_markup=cancel_button(message)
#         )
#         await state.set_state(DriverState.full_name)
#
#
# @inform_router.message(DriverState.full_name)
# async def capture_driver_fullname(message: Message, state: FSMContext):
#     """Исм-шарифини сақлайди ва кейинги қадамга ўтади."""
#     await state.update_data(full_name=message.text)
#     await message.answer("📆 Ёшингизни киритинг \n\nМасалан: 25 :", reply_markup=cancel_button(message))
#     await state.set_state(DriverState.age)
#
#
# @inform_router.message(DriverState.age)
# async def capture_driver_age(message: Message, state: FSMContext):
#     """Ёшни сақлайди ва фақат рақам киритилганини текширади."""
#     if not message.text.isdigit():  # 🔍 Фақат сон киритилганлигини текшириш
#         await message.answer("⚠️ Илтимос, ёшингизни фақат рақам сифатида киритинг! (Масалан: 25)",
#                              reply_markup=cancel_button(message))
#         return  # ❌ Агар нотўғри бўлса, функцияни тугатамиз
#
#     await state.update_data(age=int(message.text))  # ✅ Тўғри ёшни сақлаш
#     await message.answer("📍 Вилоятингизни киритинг \n\nМасалан: Андижон tyoki :", reply_markup=cancel_button(message))
#     await state.set_state(DriverState.city)
#
#
# # registratsiyadan keyin malumoti rasmsiz va andijondan yoki toshkentdaman deb tugmani ezishiga grurhga tashab qoyadi
# # tarifni tanlaydi nomerdan oldin
# @inform_router.message(DriverState.city)
# async def capture_driver_city(message: Message, state: FSMContext):
#     """Шаҳарни сақлайди ва кейинги қадамга ўтади."""
#     await state.update_data(city=message.text)
#     await message.answer("🏢 Туманни киритинг \n\nМасалан: Хожаобод :", reply_markup=cancel_button(message))
#     await state.set_state(DriverState.town)
#
#
# @inform_router.message(DriverState.town)
# async def capture_driver_town(message: Message, state: FSMContext):
#     """Туман номини сақлайди ва кейинги қадамга ўтади."""
#     await state.update_data(town=message.text)
#     await message.answer("🚗 Машина турини киритинг \n\nМасалан: Кобалт :", reply_markup=cancel_button(message))
#     await state.set_state(DriverState.type_of_car)
#
#
# @inform_router.message(DriverState.type_of_car)
# async def capture_driver_car_type(message: Message, state: FSMContext):
#     """Машина турини сақлайди ва кейинги қадамга ўтади."""
#     await state.update_data(type_of_car=message.text)
#     await message.answer("📞 Телефон рақамингизни киритинг \n\nМасалан: 970501655 :",
#                          reply_markup=cancel_button(message))
#     await state.set_state(DriverState.phone_number)
#
#
# @inform_router.message(DriverState.phone_number)
# async def capture_driver_phone_number(message: Message, state: FSMContext):
#     if not message.text.isdigit():  # 🔍 Фақат сон киритилганлигини текшириш
#         await message.answer("⚠️ Илтимос, телефон номери фақат рақам сифатида киритинг! (Масалан: 970501655)",
#                              reply_markup=cancel_button(message))
#         return  # ❌ Агар нотўғри бўлса, функцияни тугатамиз
#     """Телефон рақамини сақлайди ва кейинги қадамга ўтади."""
#     await state.update_data(phone_number=int(message.text))
#     await message.answer("📄 Правангизни расмини юборинг :", reply_markup=cancel_button(message))
#     await state.set_state(DriverState.document)
#
#
# @inform_router.message(DriverState.document)
# async def capture_driver_document(message: Message, state: FSMContext):
#     """Ҳужжат расмини сақлайди ва кейинги қадамга ўтади."""
#     if message.photo:
#         await state.update_data(document=message.photo[-1].file_id)
#         await message.answer("📃 Техпаспорт расмини юборинг :", reply_markup=cancel_button(message))
#         await state.set_state(DriverState.tex_passport)
#     else:
#         await message.answer("⚠️ Илтимос, ҳужжат расмини юборинг!")
#
#
# @inform_router.message(DriverState.tex_passport)
# async def capture_driver_tex_passport(message: Message, state: FSMContext):
#     """Техпаспорт расмини сақлайди, барча маълумотларни чиқаради ва тасдиқлаш сўрайди."""
#
#     if not message.photo:
#         await message.answer("⚠️ Илтимос, техпаспорт расмини юборинг!", reply_markup=cancel_button(message))
#         return
#
#     # ✅ **Техпаспорт расмини сақлаш**
#     await state.update_data(tex_passport=message.photo[-1].file_id)
#
#     # 🔍 **State даги барча маълумотларни олиш**
#     data = await state.get_data()
#
#     # 📋 **Ҳайдовчининг киритган маълумотларини чиқариш**
#     caption = (
#         f"📋 *Сиз киритган маълумотлар:*\n\n"
#         f"👤 *Исм:* {data.get('full_name', 'Номаълум')}\n"
#         f"🗓 *Ёш:* {data.get('age', 'Номаълум')}\n"
#         f"🏙 *Шаҳар:* {data.get('city', 'Номаълум')}\n"
#         f"📍 *Туман:* {data.get('town', 'Номаълум')}\n"
#         f"🚗 *Машина тури:* {data.get('type_of_car', 'Номаълум')}\n"
#         f"📞 *Тел:* {data.get('phone_number', 'Номаълум')}\n"
#     )
#
#     # ✅ **Ҳужжат ва техпаспортни юбориш**
#     if data.get("document"):
#         await message.answer_photo(photo=data["document"], caption="📄 *Сизнинг Правангиз *", parse_mode="Markdown")
#
#     if data.get("tex_passport"):
#         await message.answer_photo(photo=data["tex_passport"], caption="📄 *Сизнинг техпаспортингиз*",
#                                    parse_mode="Markdown")
#
#     # ✅ **Маълумотларни тасдиқлаш учун юбориш**
#     await message.answer(caption, parse_mode="Markdown")
#     await message.answer("📋 *Маълумотларни тасдиқлайсизми?*", reply_markup=confirm_button(), parse_mode="Markdown")
#
#     await state.set_state(DriverState.user_confirm)
#
#
# @inform_router.callback_query(DriverState.user_confirm, F.data == "confirm_yes")
# async def process_confirm_yes(callback_query: CallbackQuery, state: FSMContext, bot):
#     """Фойдаланувчи (шофёр) маълумотларини админга юбориш."""
#     data = await state.get_data()
#     telegram_id = str(callback_query.from_user.id)
#
#     if not data:
#         await callback_query.message.answer("⚠️ Хатолик: Маълумотлар йўқолди! Илтимос, қайта уриниб кўринг.")
#         return
#
#     # ✅ **Фойдаланувчи ID ни маълумотларга қўшиш**
#     data["telegram_id"] = telegram_id
#
#     print(f"✅ Админ тасдиқлаш учун маълумотлар: {data}")  # DEBUG
#
#     caption = (
#         f"📋 Янги Шофёр:\n"
#         f"👤 Исми: {data.get('full_name', 'Номаълум')}\n"
#         f"🗓 Ёши: {data.get('age', 'Номаълум')}\n"
#         f"🏙 Шаҳар: {data.get('city', 'Номаълум')}\n"
#         f"📍 Туман: {data.get('town', 'Номаълум')}\n"
#         f"🚗 Машина тури: {data.get('type_of_car', 'Номаълум')}\n"
#         f"📞 Тел: {data.get('phone_number', 'Номаълум')}\n\n\n"
#         "Маълумотларни тасдиклайсизми?"
#     )
#
#     msg = None  # ✅ Ensure msg is always defined
#
#     for admin in admin_chat_id:
#         if data.get("document"):
#             await bot.send_photo(admin, photo=data["document"], caption="📄 Ҳужжат (Права)")
#
#         if data.get("tex_passport"):
#             try:
#                 msg = await bot.send_photo(admin, photo=data["tex_passport"], caption=caption)
#             except:
#                 msg = await bot.send_document(admin, document=data["tex_passport"], caption=caption)
#
#     if msg:
#         message_id = msg.message_id  # ✅ Админга юборилган хабар ID сини сақлаш
#         pending_drivers[message_id] = data  # ✅ **telegram_id билан бирга сақлаймиз!**
#         print(f"✅ Маълумот сақланди: {message_id} -> {data}")  # ✅ Debug
#
#         await bot.edit_message_reply_markup(
#             chat_id=msg.chat.id,
#             message_id=message_id,
#             reply_markup=confirm_button1(message_id)  # ✅ Хабар ID билан тугмалар яратиш
#         )
#
#     await callback_query.message.delete()
#     await callback_query.message.answer("✅ Маълумотлар админга юборилди, илтимос кутиб туринг.",
#                                         reply_markup=main_button())
#
#
# @inform_router.callback_query(F.data.startswith("admin_yes_"))
# async def admin_approve_driver(callback_query: CallbackQuery, bot: Bot):
#     """Админ тасдиқласа, шофёр базага сақланади."""
#     message_id = int(callback_query.data.split("_")[-1])  # ✅ Хабар ID ни олиш
#
#     print(f"🔍 Админ тасдиқлаган хабар ID: {message_id}")  # ✅ DEBUG
#
#     if message_id not in pending_drivers:
#         await callback_query.message.answer("⚠️ Хатолик: Маълумотлар топилмади! Илтимос, қайта уриниб кўринг.")
#         return
#
#     шофёр_data = pending_drivers.pop(message_id)  # ✅ Маълумотларни олиш ва cachedan ўчириш
#     user_id = шофёр_data.get("telegram_id")  # ✅ Фойдаланувчининг Telegram ID сини олиш
#
#     await save_driver_to_db(шофёр_data, callback_query)
#
#     await callback_query.message.edit_reply_markup(reply_markup=None)
#     await callback_query.message.answer("✅ Шофёр базага сақланди!", reply_markup=admin_button())
#
#     if user_id:
#         await bot.send_message(user_id, "✅ *Админ маълумотларингизни қабул қилди!*", parse_mode="Markdown",
#                                reply_markup=driver_button())
#
#
# @inform_router.callback_query(DriverState.user_confirm, F.data == "confirm_no")
# async def process_confirm_no(callback_query: CallbackQuery, state: FSMContext):
#     """Фойдаланувчи шофёр бўлишдан воз кечди."""
#     await state.clear()
#     await callback_query.message.answer("❌ Маълумотлар бекор қилинди.", reply_markup=main_button())
#
#
# @inform_router.callback_query(F.data.startswith("admin_no_"))
# async def admin_reject_driver(callback_query: CallbackQuery, bot: Bot):
#     """Админ шофёрни рад этса, фойдаланувчига хабар боради."""
#     message_id = int(callback_query.data.split("_")[-1])  # ✅ Хабар ID ни олиш
#
#     print(f"🔍 Админ рад этган хабар ID: {message_id}")  # ✅ DEBUG
#
#     if message_id not in pending_drivers:
#         await callback_query.message.answer("⚠️ Хатолик: Маълумотлар топилмади! Илтимос, қайта уриниб кўринг.")
#         return
#
#     шофёр_data = pending_drivers.pop(message_id)  # ✅ Маълумотларни олиш ва cachedan ўчириш
#     user_id = шофёр_data.get("telegram_id")  # ✅ Фойдаланувчининг Telegram ID сини олиш
#
#     await callback_query.message.edit_reply_markup(reply_markup=None)  # ✅ Инлайн тугмаларни ўчириш
#     await callback_query.message.answer("❌ Шофёр аризаси рад этилди!")
#     await callback_query.message.delete()
#     if user_id:
#         await bot.send_message(user_id, "❌ *Админ маълумотларингизни рад этди.*", parse_mode="Markdown",
#                                reply_markup=main_button())
#
#
# async def save_driver_to_db(data: dict, callback: CallbackQuery):
#     """Шофёрни базага сақлаш функцияси"""
#
#     telegram_id = data.get("telegram_id")  # ✅ Telegram ID ни олиш
#
#     if not telegram_id:
#         print("❌ Хатолик: Telegram ID топилмади!")
#         return
#
#     existing_driver = session.execute(
#         select(Driver).where(Driver.telegram_id == telegram_id)
#     ).scalars().first()
#
#     if existing_driver:
#         print(f"❌ Хатолик: Бу шофёр ({telegram_id}) аллақачон рўйхатдан ўтган!")
#         return
#
#     print(f"✅ Базага сақланаётган маълумотлар: {data}")
#
#     driver = Driver(
#         telegram_id=telegram_id,
#         full_name=data.get('full_name', 'No Name'),
#         age=int(data.get('age', 0)),
#         city=data.get('city', 'No City'),
#         town=data.get('town', 'No Town'),
#         type_of_car=data.get('type_of_car', 'No Car'),
#         phone_number=data.get('phone_number', 'No Number'),
#         document=data.get('document', 'No Document'),
#         tex_passport=data.get('tex_passport', 'No Tex Passport'),
#     )
#
#     session.add(driver)
#     session.commit()
#     print(f"✅ Шофёр ({telegram_id}) муваффақиятли қўшилди!")
#
#
# """
# Шофёр
# """
#
# """Маълумотларни янгилаш қисми"""
#
#
# def get_edit_driver_keyboard():
#     ikb = InlineKeyboardBuilder()
#     ikb.button(text="Исмини ўзгартириш", callback_data="edit_full_name")
#     ikb.button(text="Ёшни ўзгартириш", callback_data="edit_age")
#     ikb.button(text="Шаҳарни ўзгартириш", callback_data="edit_city")
#     ikb.button(text="Туманни ўзгартириш", callback_data="edit_town")
#     ikb.button(text="Машина турини ўзгартириш", callback_data="edit_type_of_car")
#     ikb.button(text="Телефон рақамни ўзгартириш", callback_data="edit_phone_number")
#     ikb.button(text="Ҳужжатни ўзгартириш", callback_data="edit_document")
#     ikb.button(text="Тех паспортни ўзгартириш", callback_data="edit_tex_passport")
#     ikb.adjust(1)
#     return ikb.as_markup()
#
#
# async def update_driver_field(user_id: int, field_name: str, value: str):
#     query = update(Driver).where(Driver.telegram_id == user_id).values({field_name: value})
#     session.execute(query)
#     session.commit()
#
#
# @inform_router.message(F.text == "💼 Маълумотларни янгилаш")
# async def change_datas(message: Message):
#     await message.answer("Қайси маълумотингизни алмаштирмоқчисиз?", reply_markup=get_edit_driver_keyboard())
#
#
# @inform_router.callback_query(F.data == "edit_full_name")
# async def edit_full_name(callback: CallbackQuery, state: FSMContext):
#     await callback.message.answer("Янги исмингизни киритинг (Масалан: Али):", reply_markup=cancel_button1(callback))
#     await state.set_state(EditDriverState.full_name)
#     await callback.answer()
#
#
# @inform_router.message(EditDriverState.full_name)
# async def save_full_name(message: Message, state: FSMContext):
#     full_name = message.text
#     await update_driver_field(message.from_user.id, "full_name", full_name)
#
#     await message.answer(f"Исмингиз янгиланди: {full_name}", reply_markup=driver_button())
#     await state.clear()
#
#
# @inform_router.callback_query(F.data == "edit_age")
# async def edit_age(callback: CallbackQuery, state: FSMContext):
#     await callback.message.answer("Янги ёшингизни киритинг (Масалан: 21):", reply_markup=cancel_button1(callback))
#     await state.set_state(EditDriverState.age)
#     await callback.answer()
#
#
# @inform_router.message(EditDriverState.age)
# async def save_age(message: Message, state: FSMContext):
#     if not message.text.isdigit():
#         await message.answer("⚠️ Илтимос, ёшингизни фақат рақам сифатида киритинг! (Масалан: 25)",
#                              reply_markup=cancel_button(message))
#         return
#     age = int(message.text)
#     await update_driver_field(message.from_user.id, "age", age)
#
#     await message.answer(f"Ёшингиз янгиланди: {age}", reply_markup=driver_button())
#     await state.clear()
#
#
# @inform_router.callback_query(F.data == "edit_city")
# async def edit_city(callback: CallbackQuery, state: FSMContext):
#     await callback.message.answer("Янги шаҳарни киритинг (Масалан: Андижон):", reply_markup=cancel_button1(callback))
#     await state.set_state(EditDriverState.city)
#     await callback.answer()
#
#
# @inform_router.message(EditDriverState.city)
# async def save_city(message: Message, state: FSMContext):
#     city = message.text
#     await update_driver_field(message.from_user.id, "city", city)
#
#     await message.answer(f"Шаҳар янгиланди: {city}", reply_markup=driver_button())
#     await state.clear()
#
#
# @inform_router.callback_query(F.data == "edit_town")
# async def edit_town(callback: CallbackQuery, state: FSMContext):
#     await callback.message.answer("Янги туманни киритинг (Масалан: Жалакудук):", reply_markup=cancel_button1(callback))
#     await state.set_state(EditDriverState.town)
#     await callback.answer()
#
#
# @inform_router.message(EditDriverState.town)
# async def save_town(message: Message, state: FSMContext):
#     town = message.text
#     await update_driver_field(message.from_user.id, "town", town)
#
#     await message.answer(f"Туман янгиланди: {town}", reply_markup=driver_button())
#     await state.clear()
#
#
# @inform_router.callback_query(F.data == "edit_type_of_car")
# async def edit_type_of_car(callback: CallbackQuery, state: FSMContext):
#     await callback.message.answer("Янги машина турини киритинг (Масалан: Жентра):",
#                                   reply_markup=cancel_button1(callback))
#     await state.set_state(EditDriverState.type_of_car)
#     await callback.answer()
#
#
# @inform_router.message(EditDriverState.type_of_car)
# async def save_type_of_car(message: Message, state: FSMContext):
#     type_of_car = message.text
#     await update_driver_field(message.from_user.id, "type_of_car", type_of_car)
#
#     await message.answer(f"Машина тури янгиланди: {type_of_car}", reply_markup=driver_button())
#     await state.clear()
#
#
# @inform_router.callback_query(F.data == "edit_phone_number")
# async def edit_phone_number(callback: CallbackQuery, state: FSMContext):
#     await callback.message.answer("Янги телефон рақамингизни киритинг (Масалан: 970501655):",
#                                   reply_markup=cancel_button1(callback))
#     await state.set_state(EditDriverState.phone_number)
#     await callback.answer()
#
#
# @inform_router.message(EditDriverState.phone_number)
# async def save_phone_number(message: Message, state: FSMContext):
#     if not message.text.isdigit():
#         await message.answer(
#             "⚠️ Илтимос, телефон рақамни фақат рақамлардан иборат қилиб киритинг! (Масалан: 970501655)",
#             reply_markup=cancel_button(message))
#         return
#     phone_number = int(message.text)
#     await update_driver_field(message.from_user.id, "phone_number", phone_number)
#
#     await message.answer(f"Телефон рақам янгиланди: {phone_number}", reply_markup=driver_button())
#     await state.clear()
#
#
# @inform_router.callback_query(F.data == "edit_document")
# async def edit_document(callback: CallbackQuery, state: FSMContext):
#     await callback.message.answer("📄 Янги ҳужжат расмини юборинг:", reply_markup=cancel_button1(callback))
#     await state.set_state(EditDriverState.document)
#     await callback.answer()
#
#
# @inform_router.message(EditDriverState.document)
# async def save_document(message: Message, state: FSMContext):
#     if message.photo:
#         document = message.photo[-1].file_id
#     elif message.document:
#         document = message.document.file_id
#     else:
#         await message.answer("⚠️ Илтимос, расм ёки PDF ҳужжат юборинг!", reply_markup=cancel_button(message))
#         return
#
#     await update_driver_field(message.from_user.id, "document", document)
#     await message.answer("✅ Ҳужжат янгиланди!", reply_markup=driver_button())
#
#
# @inform_router.callback_query(F.data == "edit_tex_passport")
# async def edit_tex_passport(callback: CallbackQuery, state: FSMContext):
#     await callback.message.answer("📃 Янги тех паспорт расмини юборинг:", reply_markup=cancel_button1(callback))
#     await state.set_state(EditDriverState.tex_passport)
#     await callback.answer()
#
#
# @inform_router.message(EditDriverState.tex_passport)
# async def save_tex_passport(message: Message, state: FSMContext):
#     if message.photo:
#         tex_passport = message.photo[-1].file_id
#     elif message.document:
#         tex_passport = message.document.file_id
#     else:
#         await message.answer("⚠️ Илтимос, расм ёки PDF ҳужжат юборинг!", reply_markup=cancel_button(message))
#         return
#
#     await update_driver_field(message.from_user.id, "tex_passport", tex_passport)
#     await message.answer("✅ Тех паспорт янгиланди!", reply_markup=driver_button())
#     await state.clear()


# '''
# Навбатга туриш қисми
# '''
# from datetime import datetime, timedelta, time
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
#
# queue_counter = 0  # Навбатга турганлар учун глобал ҳисоблагич
#
# # **🔹 НАВБАТГА ТУРИШ БОШЛАНИШ ВАҚТИ**
# NAVBAT_START_TIME = time(9, 0)  # 21:00 да бошланади
# NAVBAT_END_TIME = (
#         datetime.combine(datetime.today(), NAVBAT_START_TIME) + timedelta(hours=2)).time()  # 2 соат давом этади
#
# # **🔹 ЙЎНАЛИШЛАР**
# ROUTES = [
#     "Андижон -> Тошкент",
#     "Тошкент -> Андижон"
# ]
#
#
# @inform_router.message(F.text == "🔉 Навбатга туриш")
# async def to_queue_start(message: Message, state: FSMContext):
#     """🚀 НАВБАТГА ТУРИШНИ БОШЛАШ"""
#     now = datetime.now().time()
#
#     # ✅ НАВБАТГА ТУРИШ ВАҚТИ ТЕКШИРИЛАДИ
#     if not (NAVBAT_START_TIME <= now <= NAVBAT_END_TIME):
#         await message.answer(f"⛔️ Кечирасиз, навбатга туриш вақти тугаган.\n\n"
#                              f"🕒 Навбатга туриш {NAVBAT_START_TIME.strftime('%H:%M')} дан "
#                              f"{NAVBAT_END_TIME.strftime('%H:%M')} гача давом этган.")
#         return
#
#     # ✅ Ҳайдовчини базадан топамиз
#     driver = session.execute(
#         select(Driver).where(Driver.telegram_id == str(message.from_user.id))
#     ).scalars().first()
#
#     if not driver:
#         await message.answer("⚠️ Сиз ҳали рўйхатдан ўтмагансиз! Аввал маълумотларингизни тўлдиринг.", main_button())
#         return
#
#     # ✅ Агар ҳайдовчи аллақачон бугун навбатга турган бўлса, унга яна рухсат бермаймиз
#     today = datetime.today().date()
#     if driver.queue and driver.date_added and driver.date_added.date() == today:
#         await message.answer(f"⏳ Сиз бугун аллақачон навбатга тургансиз! Тартиб рақамингиз: {driver.queue}")
#         return
#
#     # ✅ Энг катта навбат рақамини олиб, кейингисини белгилаймиз
#     max_queue = session.execute(select(func.max(Driver.queue))).scalar() or 0
#     new_queue = max_queue + 1
#
#     await state.update_data(queue=new_queue)
#     await message.answer("📍 Қаерга кетмоқчисиз?\n\n\n  Танланг 👇", reply_markup=get_route_keyboard())
#     await state.set_state(OrderState.route)
#
#
# @inform_router.callback_query(F.data.startswith("route_"))
# async def to_queue_route(callback: CallbackQuery, state: FSMContext):
#     """🚗 ҲАЙДОВЧИНИНГ ЙЎНАЛИШИНИ ҚАБУЛ ҚИЛИШ"""
#     route = callback.data.split("_", 1)[1]  # route_Андижон -> Тошкент => "Андижон -> Тошкент"
#
#     await state.update_data(route=route)
#     await callback.message.answer("⏳ Нечида йолга чикишингиз керак? \n\n(Масалан: 19:00)",
#                                   reply_markup=cancel_button1(callback))
#     await state.set_state(OrderState.delivery_time)
#     await callback.answer()
#
#
# @inform_router.message(OrderState.delivery_time)
# async def to_queue_delivery_time(message: Message, state: FSMContext):
#     """🕒 ҲАЙДОВЧИНИНГ БОРИШ ВАҚТИНИ ҚАБУЛ ҚИЛИШ"""
#     try:
#         delivery_time = datetime.strptime(message.text.strip(), "%H:%M").time()
#     except ValueError:
#         await message.answer("⚠️ Илтимос, тўғри форматда ёзинг! Масалан: 15:30", reply_markup=cancel_button(message))
#         return
#
#     # ✅ Янги маълумотларни сақлаймиз
#     data = await state.get_data()
#     driver = session.execute(select(Driver).where(Driver.telegram_id == str(message.from_user.id))).scalars().first()
#     driver.queue = data['queue']
#     driver.route = data['route']
#     driver.delivery_time = datetime.combine(datetime.today(), delivery_time)
#     driver.date_added = datetime.now()
#     session.commit()
#
#     await message.answer(f"✅ Сиз навбатга турганингиз тасдиқланди! 🚖\n"
#                          f"🔢 Тартиб рақамингиз: {data['queue']}\n"
#                          f"📍 Йўналиш: {data['route']}\n"
#                          f"🕒 Етиб бориш вақти: {delivery_time.strftime('%H:%M')}")
#     await message.answer(f"Илтимос, клиент бўлишини кутинг. Клиент бўлиши биланоқ сиз билан богланамиз 😊",
#                          reply_markup=driver_button())
#     await state.clear()


@inform_router.message(F.text == "📊 Менинг маълумотларим")
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
        f"📞 *Тел:* {driver.phone_number}\n"
        f"🔢 *Навбат рақами:* {driver.queue if driver.queue else 'Йўқ'}\n"
    )

    await message.answer(caption, parse_mode="Markdown")

    # 4️⃣ Агар ҳайдовчининг ҳужжатлари бўлса, расм сифатида юборамиз
    if driver.document:
        await message.answer_photo(driver.document, caption="📄 *Сизнинг ҳужжатингиз (Права)*",
                                   parse_mode="Markdown")

    if driver.tex_passport:
        await message.answer_photo(driver.tex_passport, caption="📃 *Сизнинг техпаспортингиз*",
                                   parse_mode="Markdown")


@inform_router.message(F.text == "📞 Админ билан боғланиш")
async def contact_with_admin(message: Message):
    await message.answer("Илтимос шу одамга Телеграмдан ёзинг @Mirzajonow_21")


# 🔹 **Admin Paneli**
# KeyboardButton(text="А -> Т Шопирлар"),
# KeyboardButton(text="Т -> А Шопирлар"),
@inform_router.message(F.text == "🔅 А -> Т Шопирлар", IsAdmin())
async def admin_panel1(message: Message):
    """Бугунги Андижондан Тошкентга кетаётган шоферларни чиқаради"""
    drivers = session.query(Driver).filter(
        Driver.route == "Андижон -> Тошкент",
        Driver.date_added >= datetime.now().date()
    ).order_by(Driver.queue).all()

    if not drivers:
        await message.answer("🚖 Бугун Андижондан Тошкентга кетаётган шофёрлар мавжуд эмас.")
        return

    response = "🚖 *Андижон -> Тошкент шофёрлари*\n\n"
    for driver in drivers:
        response += f"🏙 *Тартиб раками:* {driver.queue}\n"
        response += f"🏙 *Исми:* {driver.full_name}\n"
        response += f"🏙 *Туман:* {driver.town}\n"
        response += f"⏰ *Кетиш вақти:* {driver.delivery_time}\n"
        response += f"📞 *Телефон:* {driver.phone_number}\n"
        response += "---------------------\n"

    await message.answer(response, parse_mode="Markdown")


@inform_router.message(F.text == "🔅 Т -> А Шопирлар", IsAdmin())
async def admin_panel(message: Message):
    """Бугунги Тошкентдан Андижонга кетаётган шоферларни чиқаради"""
    drivers = session.query(Driver).filter(
        Driver.route == "Тошкент -> Андижон",
        Driver.date_added >= datetime.now().date()
    ).order_by(Driver.queue).all()

    if not drivers:
        await message.answer("🚖 Бугун Тошкентдан Андижонга кетаётган шофёрлар мавжуд эмас.")
        return

    response = "🚖 *Тошкент -> Андижон шофёрлари*\n\n"
    for driver in drivers:
        response += f"🏙 *Тартиб раками:* {driver.queue}\n"
        response += f"🏙 *Исми:* {driver.full_name}\n"
        response += f"🏙 *Туман:* {driver.town}\n"
        response += f"⏰ *Кетиш вақти:* {driver.delivery_time}\n"
        response += f"📞 *Телефон:* {driver.phone_number}\n"
        response += "---------------------\n"

    await message.answer(response, parse_mode="Markdown")
# @inform_router.message(F.text == "🔄 Буюртмаларни Тозалаш", IsAdmin())
# async def clear_orders(message: Message):
#     """📌 Админ буюртмаларни ўчириш"""
#     global PENDING_ORDERS
#     PENDING_ORDERS = []
#     await message.answer("✅ Барча навбатдаги буюртмалар ўчирилди!")


# from sqlalchemy.sql import text
#
# # 📋 **Buyurtmalar ro‘yxati**
# PENDING_ORDERS = []
#
#
# async def get_ready_driver(session, route: str, delivery_time: str, bot: Bot):
#     """🛣 Yo‘nalish, yetib borish vaqti va bo‘sh joy borligini tekshirib haydovchini topish"""
#     today = datetime.now().date()
#
#     # **🚀 1. Barcha haydovchilarni olish (queue ASC bo‘yicha)**
#     query = text("""
#         SELECT id, telegram_id, full_name, phone_number,delivery_time,client_count, route, TIME(delivery_time) as time_only, date_added, queue
#         FROM drivers
#         WHERE route = :route
#         AND TIME(delivery_time) = TIME(:delivery_time)
#         AND DATE(date_added) = :today
#         AND COALESCE(client_count, 0) < 4
#         ORDER BY queue ASC
#     """)
#
#     all_drivers = session.execute(query, {
#         "route": route,
#         "delivery_time": delivery_time,
#         "today": today
#     }).fetchall()
#
#     print(f"🟢 {route} bo‘yicha {delivery_time} uchun mos haydovchilar: {all_drivers}")  # DEBUG LOG
#
#     for driver in all_drivers:
#         driver_id = driver.id
#         driver_name = driver.full_name
#         driver_queue = driver.queue
#         driver_clients = driver.client_count if driver.client_count is not None else 0
#         driver_telegram_id = driver.telegram_id
#
#         print(f"🔍 Tekshirilayotgan haydovchi: {driver_name}, Queue: {driver_queue}, Client Count: {driver_clients}")
#
#         # **📌 4 ta mijoz olgan haydovchini o'tkazib yuboramiz**
#         if driver_clients >= 4:
#             print(f"⏩ {driver_name} ({driver_queue}) haydovchining `client_count = 4`, keyingisiga o‘tamiz...")
#             continue
#
#             # **✅ 4. Mijoz biriktiramiz**
#         update_query = text("""
#             UPDATE drivers
#             SET client_count = COALESCE(client_count, 0) + 1
#             WHERE id = :driver_id
#         """)
#         session.execute(update_query, {"driver_id": driver_id})
#         session.commit()
#
#         print(f"✅ {driver_name} ({driver_queue}) haydovchiga mijoz biriktirildi!")
#
#         # **🚖 Agar bu haydovchining 4-mijoz bo‘lsa, unga maxsus xabar yuboramiz**
#         if driver_clients + 1 == 4:
#             await bot.send_message(
#                 driver_telegram_id,
#                 "✅ Сизда 4 та мижоз йиғилди!\nЙўлингиз бехатар бўлсин! 🚖"
#             )
#         return driver
#
#     print("🚫 Tayyor shofyor topilmadi!")
#     return None
