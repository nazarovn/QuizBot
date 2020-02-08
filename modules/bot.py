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


from bot_states import BotStates
from utils import is_admin, get_info_show_tests, process_test_command_argumens
from conf import TOKEN


PATH_DB = '../data/database/bot.db'



bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())



inline_btn_1 = InlineKeyboardButton('Teacher', callback_data='button1')
inline_btn_2 = InlineKeyboardButton('Student', callback_data='button2')

inline_kb_full = InlineKeyboardMarkup(row_width=2).add(inline_btn_1, inline_btn_2)

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


#######################################################################
#################       USER COMMANDS        ##########################
#######################################################################


@dp.message_handler(commands=['help'])
async def process_help_user_command(message: types.Message):
    await message.reply(r"""
Commands:
/help - help
/test <test_id> - run test
""")


@dp.message_handler(commands=['test'])
async def process_test_command(message: types.Message):
    arguments = message.get_args().split()
    permission, answer = process_test_command_argumens(arguments)
    if permission:
        # state to Test
        # load quiz data
        # print describe
        # button: start quiz
        # run questions
        run_quiz(arguments)
    else:
        await message.answer(answer)



#######################################################################
#################      ADMIN COMMANDS        ##########################
#######################################################################


@dp.message_handler(state=BotStates.STATE_ADMIN, commands=['help'])
async def process_help_admin_command(message: types.Message):
    await message.reply(r"""
Commands Admin:
/help - help
/test <test_id> - run test

/admin - set role Admin
/user - set role User
/show_tests - show exists tests
""")


@dp.message_handler(state='*', commands=['admin'])
async def process_admin_command(message: types.Message):
    if is_admin(message, PATH_DB):
        state = dp.current_state(user=message.from_user.id)
        await state.set_state(BotStates.STATE_ADMIN)
        await message.reply('You are admin')
    else:
        await message.reply('Permission denied')


@dp.message_handler(state='*', commands=['user'])
async def process_user_command(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    await state.reset_state()
    await message.reply('You are user')


@dp.message_handler(state=BotStates.STATE_ADMIN, commands=['show_tests'])
async def process_show_tests_command(message: types.Message):
    tests_info = get_info_show_tests(PATH_DB)
    await message.reply(tests_info)


#######################################################################
#################       TEST COMMANDS        ##########################
#######################################################################









@dp.message_handler()
async def echo_message(message: types.Message):
    #print(dir(msg))
    msg = message
    print(msg.from_user)
    print(msg.from_user.id)
    print()
    print(msg.chat)
    print(msg.conf)
    
    state = dp.current_state(user=message.from_user.id)
    await bot.send_message(msg.from_user.id, 'Answer recorded')
    await bot.send_message(msg.from_user.id, state)


if __name__ == '__main__':
    executor.start_polling(dp)

