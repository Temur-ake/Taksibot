from datetime import datetime, timedelta
from aiogram import Bot, Router
from aiogram.types import ChatPermissions, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from models import session, User

checking_router = Router()

KEYWORDS_C = [
    'кетаман',
    'ketaman',

    'бораман',
    'boraman',

    'чиқиб кетишим керак',
    'chiqib ketishim kerak'
]

KEYWORDS_D = [
    'кам',
    'kam',

    'камдамиз',
    'kamdamiz',

    'ТОМ БАГАЖ БОР',
    'TOM BAGAJ BOR',

    'тўлдик',
    "to'ldik",

    'почта оламиз',
    'pochta olamiz',

    'камда',
    'kamda',

    'каммиз',
    'kammiz',

]


# klientlar_kanali = -1002477688128
# shopirlar_kanali = -1001898131334


async def check_user_permission(user_id: int) -> bool:
    """Check if the user has permission based on a database timestamp."""
    user = session.query(User).filter(User.user_id == user_id).first()
    if user and user.last_permission_granted:
        return datetime.now() < user.last_permission_granted
    return False


async def check_for_keywords(message_text: str, keywords: list) -> bool:
    """Check if the message contains any of the specified keywords."""
    if message_text:
        return any(keyword in message_text.lower() for keyword in keywords)
    return False


async def not_restrict_user(bot: Bot, chat_id: int, user_id: int):
    """Restore the user's permission to send messages."""
    await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=ChatPermissions(can_send_messages=True)
    )


async def restrict_user(bot: Bot, chat_id: int, user_id: int, duration_minutes: int):
    """Temporarily restrict the user's permission to send messages."""
    until_date = datetime.now() + timedelta(minutes=duration_minutes)
    await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until_date
    )


@checking_router.message()
async def check(message: Message, bot: Bot):
    """Main handler to check message content and apply restrictions."""
    if message.chat.type not in ['group', 'supergroup'] and message.chat.id == -1002477688128:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    print(f"guruxning chat id  {chat_id}")

    user = session.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id, username=message.from_user.username, chat_id=chat_id)
        session.add(user)
        session.commit()

    if await check_for_keywords(message.text, KEYWORDS_C):
        try:
            await bot.send_message(-1002477688128, f"{message.text}")
            await message.delete()

            ikb = InlineKeyboardBuilder()
            ikb.add(InlineKeyboardButton(text='Заказ бериш', url='https://t.me/ToshkentAndijonTaksi_Bot'))

            await message.answer(
                f"❗❗️ХУРМАТЛИ {message.from_user.full_name} СИЗНИНГ ЗАКАЗИНГИЗ ШОФЁРЛАР 🚖 ГРУППАСИГА ТУШДИ ❗️ "
                f"ЛИЧКАНГИЗДА ИШОНЧЛИК ШОФЁРЛАРИМИЗ 🚖 КУТМОКДА ⏱ КУЛАЙЛИК УЧУН БОТ ОРКАЛИ ЗАКАЗ БЕРИНГ  ⬇️ 👇⬇️ 👇 ⬇️ 👇 ⬇️👇 ⬇️",
                reply_markup=ikb.as_markup()
            )
        except Exception as e:
            print(f"Error sending group message: {e}")
        return

    # if await check_for_keywords(message.text, KEYWORDS_D) and not check_user_permission(user_id): # and not checking
    #     C_W24 = "@C_W24"
    #     try:
    #         await message.answer(
    #             f"Хурматли {message.from_user.full_name}, ушбу гуруҳда ишлашингиз учун бизнинг шофёрлар гуруҳимизга қўшилишингиз керак! "
    #             f"Қўшилиш учун {C_W24} админ билан боғланинг!")
    #         # await message.delete()
    #         # await restrict_user(bot, chat_id, user_id, duration_minutes=0)
    #     except Exception as e:
    #         print(f"Error sending group message: {e}")
    #     return


    # if message.text:
    #     await bot.send_message(-1002477688128, f"{message.text}")
    #     return

    #Guruh id sini tekshirish kerak
    # if await check_user_permission(user_id):
    #     await bot.send_message(-1002487836129, f"{message.text}")
    #     return
    #
    # if not await check_user_permission(user_id):
    #     C_W24 = "@C_W24"
    #     await message.answer(
    #         f"Хурматли {message.from_user.full_name}, ушбу гуруҳда ишлашингиз учун бизнинг шофёрлар гуруҳимизга қўшилишингиз керак! "
    #         f"Қўшилиш учун {C_W24} админ билан боғланинг!")
        # await message.delete()
        # await restrict_user(bot, chat_id, user_id, duration_minutes=0)
