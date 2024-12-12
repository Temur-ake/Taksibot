from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import Bot

from keyboards import client_button, main_button
from state import Data

inform_router = Router()


@inform_router.message(F.text == "Почта бор")
async def start_pochta(message: Message, state: FSMContext):
    await message.answer(
        "Илтимос буюртма хақида бироз малумот беринг! Мисол учун: Асакадан Яккасаройга Битта сумкада кийимлар бор, Велосипедни олиб кетиш керак, Илтимос фақат томида багажи борлар алоқага чиқсин")
    await state.set_state(Data.delivery)


@inform_router.message(Data.delivery)
async def capture_delivery_message(message: Message, state: FSMContext, bot: Bot):
    user_message = message.text

    try:
        await bot.send_message(-1002452020125, user_message)

        await message.answer("Буюртмангиз қабул қилинди! Тез орада шафёрларимиз сизга алоқага чиқишади")

        await state.clear()

    except Exception as e:
        await message.answer(f"Хатолик юз берди: {e}")


@inform_router.message(F.text == "Шофёр")
async def start_shofer(message: Message, state: FSMContext):
    await message.answer("Илтимос элон бериш учун бироз малумот беринг! Мисол учун: Мошина Жентра, 2 киши бор яна 2 киши олиб Тошкентдан Андижонга юраман")
    await state.set_state(Data.driver)


@inform_router.message(Data.driver)
async def capture_driver_message(message: Message, state: FSMContext, bot: Bot):
    user_message = message.text

    try:
        await bot.send_message(-1002487836129, user_message)

        await message.answer("Элонингиз қабул қилинди ва клиентлар гурухига юборилди!")

        await state.clear()

    except Exception as e:
        await message.answer(f"Хатолик юз берди: {e}")


@inform_router.message(F.text == "Ортга")
async def back(message: Message):
    await message.answer('Танланг :', reply_markup=main_button())


ROUTES = [
    "Андижон -> Тошкент",
    "Тошкент -> Андижон",
    "Фарғона -> Тошкент",
    "Тошкент -> Фарғона",
    "Наманган -> Тошкент",
    "Тошкент -> Наманган"
]


def format_route(route: str) -> str:
    from_city, to_city = route.split(" -> ")

    return f"{from_city}дан {to_city}га"


@inform_router.message(F.text == "Клиент")
async def start(message: Message):
    await message.answer("Танланг:", reply_markup=client_button())


@inform_router.message(F.text.in_(ROUTES))  #
async def start_route(message: Message, state: FSMContext):
    route = message.text

    formatted_route = format_route(route)

    await message.answer(
        f"Илтимос буюртма хақида бироз малумо беринг! Мисол учун: Соат 19:00 да {formatted_route} чиқиб кетишим керак 1 та катта сумкам бор")

    await state.set_state(Data.client)

# klient kanali = -1002365517010

@inform_router.message(Data.client)
async def capture_user_message(message: Message, state: FSMContext, bot: Bot):
    user_message = message.text

    try:
        await bot.send_message(-1002365517010, user_message)

        await message.answer(f"Буюртмангиз қабул қилинди! Тез орада шафёрларимиз сизга алоқага чиқишади")

        await state.clear()

    except Exception as e:
        await message.answer(f"Хатолик юз берди: {e}")
