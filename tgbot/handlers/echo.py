from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode
from tgbot.keyboards.reply import kbd_menu, kbd_inf, kbd_cinema


async def bot_echo(message: types.Message):
    if message.text == "Пошук інформації":
        await message.reply(".", reply_markup=kbd_inf)
    if message.text == "Кінотеатри":
        await message.reply(".", reply_markup=kbd_cinema)
    if message.text == "Назад":
        await message.reply(".", reply_markup=kbd_menu)
    # text = [
    #     "Ехо без стану.",
    #     "Повідомлення:",
    #     message.text
    # ]
    #
    # await message.answer('\n'.join(text))
#
#
# async def bot_echo_all(message: types.Message, state: FSMContext):
#     state_name = await state.get_state()
#     text = [
#         f'Ехо в стані {hcode(state_name)}',
#         'Вмістимість повідомлення:',
#         hcode(message.text)
#     ]
#     await message.answer('\n'.join(text))


def register_echo(dp: Dispatcher):
    dp.register_message_handler(bot_echo)
    # dp.register_message_handler(bot_echo_all, state="*", content_types=types.ContentTypes.ANY)
