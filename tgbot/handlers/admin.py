from aiogram import Dispatcher
from aiogram.types import Message


async def admin_start(message: Message):
    await message.reply("Hello, admin!")


def register_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, commands=["start_ad"], state="*", is_admin=True)
