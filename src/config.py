free_subscription = 3
bot_name = "@Bina_az_bot"
support_name = "@nimesheiba"
price = {
    "7 дней": 5,
    "14 дней": 10,
    "30 дней": 15,
}

try:
    with open("res/important_data.key", 'r') as f:
        card_number, admin_chat_id = f.read().split(';')
except FileNotFoundError:
    raise FileNotFoundError("Can't find card number and admin chat id. It must be stored at res/important_data.key")

try:
    with open("res/telegram.key", 'r') as f:
        telegram_key = f.read()
except FileNotFoundError:
    raise FileNotFoundError("Can't find telegram token. It must be stored at res/telegram.key")

try:
    with open("res/telegram_second.key", 'r') as f:
        telegram_second_key = f.read()
except FileNotFoundError:
    raise FileNotFoundError("Can't find telegram token. It must be stored at res/telegram_second.key.key")

ERROR_LOG_FILENAME = "error.log"
LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s:%(name)s:%(process)d:%(lineno)d %(levelname)s %(module)s.%(funcName)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[%(levelname)s] in %(module)s.%(funcName)s: %(message)s",
        },
    },
    "handlers": {
        "error_logfile": {
            "formatter": "default",
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": ERROR_LOG_FILENAME,
            "backupCount": 2,
        },
        "verbose_output": {
            "formatter": "simple",
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "bot": {
            "level": "DEBUG",
            "handlers": [
                "verbose_output",
            ],
        },
        "store_keeper": {
            "level": "DEBUG",
            "handlers": [
                "verbose_output",
            ],
        },
    },
    "root": {
        "level": "INFO",
        "handlers": [
            "error_logfile"
        ]
    },
}
