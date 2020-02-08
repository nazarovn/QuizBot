from aiogram.utils.helper import Helper, HelperMode, ListItem, Item


class BotStates(Helper):
    mode = HelperMode.snake_case
    STATE_ADMIN = Item()
    STATE_TEST = Item()

