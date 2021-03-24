import logging

import coloredlogs
from aiogram import executor

from application import utils
from application.config import config

if __name__ == '__main__':
    log_level = logging.getLevelName(config.log_level)
    coloredlogs.install(level=log_level)
    logging.basicConfig(level=log_level)

    bot, dp = utils.get_bot()
    executor.start_polling(dp)
