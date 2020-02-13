

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
from utils import update_db_test_status, ask_question, write_answer
from parser_tests import load_test
from conf import TOKEN


PATH_DB = '../data/database/bot.db'


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())




#######################################################################
#################       USER COMMANDS        ##########################
#######################################################################

@dp.message_handler(commands=['help'])
async def process_help_user_command(message: types.Message):
    await message.reply(r"""
Commands:
/help - type "/help" to get the hints.
/test <test_id> - type "test" and add the code to run the test
""")


@dp.message_handler(commands=['test'])
async def process_test_command(message: types.Message):
    arguments = message.get_args().split()
    permission, answer = process_test_command_argumens(arguments, PATH_DB)
    if permission:
        # answer = filename
        test_data = load_test(answer)
        btn_begin_quiz = InlineKeyboardButton(
            f"Begin the test \"{test_data['testname']}\"",
            callback_data=f"begin_test {answer}"
        )
        kb_begin_quiz = InlineKeyboardMarkup().add(btn_begin_quiz)
        await message.answer(
            f"The test: {test_data['testname']}\n\nThe description: {test_data['description']}",
            reply_markup=kb_begin_quiz
        )
    else:
        await message.answer(answer)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('begin_test'))
async def process_callback_begin_test(callback_query: types.CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)
    await state.set_state(BotStates.STATE_TEST)
    await bot.send_message(callback_query.from_user.id, 'The test has begun')

    filename = callback_query.data[len('begin_test '):]
    test_data = load_test(filename)
    update_db_test_status(filename, test_data, callback_query, PATH_DB) # ToDo
    # First question
    text_question = ask_question(callback_query, PATH_DB) # ToDo
    await bot.send_message(callback_query.from_user.id, text_question)


@dp.message_handler(commands=['admin'])
async def process_admin_command(message: types.Message):
    if is_admin(message, PATH_DB):
        state = dp.current_state(user=message.from_user.id)
        await state.set_state(BotStates.STATE_ADMIN)
        await message.answer('You are an admin')
    else:
        await message.answer('Permission denied')


#######################################################################
#################      ADMIN COMMANDS        ##########################
#######################################################################

@dp.message_handler(state=BotStates.STATE_ADMIN, commands=['help'])
async def process_help_admin_command(message: types.Message):
    await message.reply(r"""
Commands Admin:
/help - type "/help" to get the hints.
/test <test_id> - type "test" and add the code to run the test

/admin - set role Admin
/user - set role User
/show_tests - show exists tests
""")


@dp.message_handler(state=BotStates.STATE_ADMIN, commands=['user'])
async def process_user_command(message: types.Message):
    if is_admin(message, PATH_DB):
        state = dp.current_state(user=message.from_user.id)
        await state.reset_state()
        await message.answer('You are an user')
    else:
        await message.answer('Permission denied')


@dp.message_handler(state=BotStates.STATE_ADMIN, commands=['show_tests'])
async def process_show_tests_command(message: types.Message):
    tests_info = get_info_show_tests(PATH_DB)
    await message.reply(tests_info)


#######################################################################
#################       TEST COMMANDS        ##########################
#######################################################################


@dp.message_handler(state=BotStates.STATE_TEST, commands=['help'])
async def process_help_test_command(message: types.Message):
    await message.reply(r"""
Command Test:
/help - type "/help" to get the hints.
/q - type "/q" to finish the test""")


@dp.message_handler(state=BotStates.STATE_TEST, commands=['q'])
async def process_end_test_command(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    await state.reset_state()
    await message.answer('The end')


@dp.message_handler(state=BotStates.STATE_TEST)
async def echo_message(message: types.Message):
    answer = write_answer(message, PATH_DB)
    await message.answer(answer)

    text_question = ask_question(message, PATH_DB) # ToDo
    if text_question is None:
        await bot.send_message(message.from_user.id, 'The end.')
        # update tests_status
        # change state
        state = dp.current_state(user=message.from_user.id)
        await state.reset_state()
    else:
        await bot.send_message(message.from_user.id, text_question)



if __name__ == '__main__':
    executor.start_polling(dp)

