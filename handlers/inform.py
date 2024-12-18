from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import Bot

from checkings import check_user_permission, restrict_user
from keyboards import client_button, main_button
from state import Delivery, Driver, Client

inform_router = Router()

ROUTES = [
    "Андижон -> Тошкент",
    "Тошкент -> Андижон"
]


def format_route(route: str) -> str:
    from_city, to_city = route.split(" -> ")

    return f"{from_city}дан {to_city}га"


@inform_router.message(F.text == "Почта бор")
async def start_pochta(message: Message, state: FSMContext):
    await message.answer(
        "Илтимос буюртма хақида бироз малумот беринг! Мисол учун: Асакадан Яккасаройга Битта сумкада кийимлар бор, Велосипедни олиб кетиш керак, Илтимос фақат томида багажи борлар алоқага чиқсин")
    await state.set_state(Delivery.delivery)


@inform_router.message(Delivery.delivery)
async def capture_delivery_message(message: Message, state: FSMContext):
    await state.update_data(user_message=message.text)
    await message.answer("Илтимос телефон рақамингизни киритинг:")
    await state.set_state(Delivery.phone_number)


@inform_router.message(Delivery.phone_number)
async def capture_phone_number(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_message = data.get("user_message")
    phone_number = message.text
    user_fullname = message.from_user.username or " - "

    try:
        await bot.send_message(-1001898131334,
                               f"Телеграми: @{user_fullname}\n\n{user_message}\n\nТелефон рақами: {phone_number}")
        await bot.send_message(-1002376904373,
                               f"Телеграми: @{user_fullname}\n\n{formatted_route}\n{user_message}\n\nТелефон рақами: {phone_number}")
        await message.answer("Буюртмангиз қабул қилинди! Тез орада шафёрларимиз сизга алоқага чиқишади")
        await state.clear()

    except Exception as e:
        await message.answer(f"Хатолик юз берди: {e}")


@inform_router.message(F.text == "Шофёр")
async def start_shofer(message: Message, state: FSMContext, bot: Bot):
    await message.answer(
        "Илтимос элон бериш учун бироз малумот беринг! Мисол учун: Мошина Жентра, 2 киши бор яна 2 киши олиб Тошкентдан Андижонга юраман "
        "+998970501655")

    # Set the user's state to "driver"
    await state.set_state(Driver.driver)


@inform_router.message(Driver.driver)
async def capture_driver_message(message: Message, state: FSMContext, bot: Bot):
    try:
        # Capture the message and store it in the FSM state
        await state.update_data(user_message=message.text)

        # Get the stored data
        data = await state.get_data()
        user_message = data.get("user_message")

        # Send the message to the specified Telegram group/channel
        await bot.send_message(-1001898131334, f"{user_message}")
        await message.answer("Элонингиз қабул қилинди ва клиентлар гурухига юборилди!")
        await state.clear()

    except Exception as e:
        # Handle any errors, such as network issues or permission problems
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")
        print(f"Error: {e}")



# @inform_router.message(Driver.phone_number)
# async def capture_driver_phone_number(message: Message, state: FSMContext, bot: Bot):
#     data = await state.get_data()
#     user_message = data.get("user_message")
#     phone_number = message.text
#     user_id = message.from_user.id
#     user_fullname = message.from_user.username or " - "
#
#     try:
#         await bot.send_message(-1001898131334,
#                                f"{user_message}")
#         # if await check_user_permission(user_id):
#         #     await bot.send_message(-1002487836129, f"{message.text}")
#         #     await message.answer("Элонингиз қабул қилинди ва клиентлар гурухига юборилди!")
#         #     await state.clear()
#         # else:
#         #     await message.answer(
#         #         f"Хурматли {user_fullname}, ушбу гуруҳга елон бериш учун бизнинг шофёрлар гуруҳимизга қўшилишингиз керак! "
#         #         f"Қўшилиш учун {C_W24} админ билан боғланинг!")
#         #     return
#
#     except Exception as e:
#         await message.answer(f"Хатолик юз берди: {e}")


@inform_router.message(F.text == "Клиент")
async def start(message: Message):
    await message.answer("Танланг:", reply_markup=client_button())


@inform_router.message(F.text.in_(ROUTES))
async def start_route(message: Message, state: FSMContext):
    route = message.text
    formatted_route = format_route(route)
    await state.update_data(route=formatted_route)
    await message.answer(
        f"Илтимос буюртма хақида бироз малумот беринг! Мисол учун: Соат 19:00 да {formatted_route} чиқиб кетишим керак 1 та катта сумкам бор")
    await state.set_state(Client.client)


@inform_router.message(Client.client)
async def capture_user_message(message: Message, state: FSMContext):
    await state.update_data(user_message=message.text)
    await message.answer("Илтимос телефон рақамингизни киритинг:")
    await state.set_state(Client.phone_number)


@inform_router.message(Client.phone_number)
async def capture_phone_number_with_route(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_message = data.get("user_message")
    formatted_route = data.get("route", "")
    phone_number = message.text
    user_fullname = message.from_user.username or " - "

    try:
        await bot.send_message(-1001898131334,
                               f"Телеграми: @{user_fullname}\n\n{formatted_route}\n{user_message}\n\nТелефон рақами: {phone_number}")
        await bot.send_message(-1002376904373,
                               f"Телеграми: @{user_fullname}\n\n{formatted_route}\n{user_message}\n\nТелефон рақами: {phone_number}")
        await message.answer("Буюртмангиз қабул қилинди! Тез орада шафёрларимиз сизга алоқага чиқишади")
        await state.clear()

    except Exception as e:
        await message.answer(f"Хатолик юз берди: {e}")


@inform_router.message(F.text == "Ортга")
async def back(message: Message):
    await message.answer('Танланг :', reply_markup=main_button())
