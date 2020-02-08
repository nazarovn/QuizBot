import requests
import re

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

from conf import TOKEN


button_hi = KeyboardButton('Начать тест! 👋')

greet_kb = ReplyKeyboardMarkup(resize_keyboard=True)
greet_kb.add(button_hi)

inline_btn_1 = InlineKeyboardButton('Teacher', callback_data='button1')
inline_btn_2 = InlineKeyboardButton('Student', callback_data='button2')

inline_kb_full = InlineKeyboardMarkup(row_width=2).add(inline_btn_1, inline_btn_2)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())



def get_url():
    contents = requests.get('https://random.dog/woof.json').json()    
    url = contents['url']
    return url


def get_image_url():
    allowed_extension = ['jpg','jpeg','png']
    file_extension = ''
    while file_extension not in allowed_extension:
        url = get_url()
        file_extension = re.search("([^.]*)$",url).group(1).lower()
    return url


@dp.message_handler(commands=['bop'])
async def process_photo_command(message: types.Message):
    caption = 'Ути-пути'
    image = get_image_url()
    await bot.send_photo(message.from_user.id, image,
                         caption=caption,
                         reply_to_message_id=message.message_id)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('button'))
async def process_callback_kb1btn1(callback_query: types.CallbackQuery):
    code = callback_query.data[-1]
    if code == '1':
        await bot.answer_callback_query(callback_query.id, text='You are teacher')
        await bot.send_message(callback_query.from_user.id, f'You are teacher')
    if code == '2':
        await bot.answer_callback_query(callback_query.id, text='You are student')
        await bot.send_message(callback_query.from_user.id, f'You are student')
    else:
        await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f'Write you name:')



@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Hi!\nWhat are you?", reply_markup=inline_kb_full)


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply(r"""
Commands:
/help - help
/start - start work with tests
/bop - get dog
""")


@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, 'Answer recorded')


if __name__ == '__main__':
    executor.start_polling(dp)

