import enum

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

