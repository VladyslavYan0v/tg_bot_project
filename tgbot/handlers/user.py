from aiogram import Dispatcher
from aiogram.types import Message, ContentTypes
from aiogram.dispatcher.filters import Text

from tgbot.keyboards.reply import kbd


async def user_start(message: Message):
    await message.reply("Hello, user!")


async def test_message(message: Message):
    await message.answer("Test message", reply_markup=kbd)


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_message_handler(test_message, Text(equals=["Test", "Program"]))
