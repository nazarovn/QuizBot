
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
from utils import update_db_test_status_begin, update_db_test_status_end, ask_question, write_answer
from utils import generate_new_password, get_password
from parser_tests import load_test, upload_file, check_file, update_db_tests
from conf import TOKEN


PATH_DB = '../data/database/bot.db'
PATH_TESTS = '../data/tests'


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())





#######################################################################
#################       USER COMMANDS        ##########################
#######################################################################

@dp.message_handler(commands=['help'])
async def process_help_user_command(message: types.Message):
    await message.answer(r"""
Commands:
/help - type "/help" to get the hints.
/test <test_id> - type "test" and add the code to run the test
""")


@dp.message_handler(commands=['test'])
async def process_test_command(message: types.Message):
    arguments = message.get_args().split()
    permission, answer = process_test_command_argumens(arguments, message, PATH_DB)
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
    update_db_test_status_begin(filename, test_data, callback_query, PATH_DB)
    # First question
    text_question = ask_question(callback_query, PATH_DB)
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


@dp.message_handler(state=BotStates.STATE_ADMIN, commands=['new_passwd'])
async def process_new_passwd_command(message: types.Message):
    """Generate new password."""
    passwd = generate_new_password(PATH_DB)
    await message.reply(f"new password: {passwd}")


@dp.message_handler(state=BotStates.STATE_ADMIN, commands=['show_passwd'])
async def process_show_passwd_command(message: types.Message):
    """Generate new password."""
    passwd = get_password(PATH_DB)
    await message.reply(f"new password: {passwd}")


@dp.message_handler(state=BotStates.STATE_ADMIN, content_types=types.ContentType.DOCUMENT)
async def process_callback_begin_test(message: types.Message):
    max_file_size = 10_000

    filename = message.document.file_name
    filesize = message.document.file_size
    fileid = message.document.file_id

    # checks:
    # 1) file type
    file_type_ = '.yaml'
    if filename[-len(file_type_):] != file_type_:
        await message.answer('File format should be ".yaml"')
        return
    # 2) size
    if filesize > max_file_size:
        await message.answer(f'Size error. File size is {filesize}. Max file size is {max_file_size}')
        return

    await upload_file(bot, fileid, filename, PATH_TESTS)
    correct_flg, error_messages = check_file(filename)
    update_db_tests(correct_flg, filename, PATH_DB, PATH_TESTS)
    if correct_flg:
        answer = get_info_show_tests(PATH_DB, filename)
    else:
        answer = error_messages
    await message.answer(answer)


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
    update_db_test_status_end(message, PATH_DB)


@dp.message_handler(state=BotStates.STATE_TEST)
async def process_answer(message: types.Message):

    success, answer = write_answer(message, PATH_DB)
    await message.answer(answer)

    text_question = ask_question(message, PATH_DB)
    if (text_question is None) or (not success):
        await bot.send_message(message.from_user.id, 'The end.')
        # update tests_status
        update_db_test_status_end(message, PATH_DB)
        state = dp.current_state(user=message.from_user.id)
        await state.reset_state()
    else:
        await bot.send_message(message.from_user.id, text_question)



if __name__ == '__main__':
    executor.start_polling(dp)

