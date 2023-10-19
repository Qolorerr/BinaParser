from typing import Dict, Any

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, ContextTypes, MessageHandler, filters, \
    CallbackQueryHandler

from src.config import telegram_key, bot_name, support_name, price, card_number, admin_chat_id
from src.dialog_lines import DialogLines, DefaultKeyboard
from src.store_keeper import StoreKeeper

MAIN_MENU, RENEW_SUB, PAYMENT = range(3)


async def send_default_message(update: Update, line: DialogLines, args: Dict[str, Any] = {}) -> None:
    reply_keyboard = [line.value.buttons[i:i + 2] for i in range(0, len(line.value.buttons), 2)]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text(line.value.text % args, reply_markup=markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        till_time = store_keeper.new_user(update.message.from_user.id)
    except KeyError:
        return await main_menu(update, context)
    await send_default_message(update, DialogLines.start, {"datetime": till_time.strftime("%d.%m.%Y %H:%M:%S")})
    return MAIN_MENU


async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await send_default_message(update, DialogLines.guide)
    return MAIN_MENU


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await send_default_message(update, DialogLines.about, {"bot_name": bot_name})
    return MAIN_MENU


async def account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    till_time = store_keeper.get_subscription_time(user_id)
    args = {
        "user_id": user_id,
        "datetime": till_time.strftime("%d.%m.%Y %H:%M:%S"),
        "tasks": len(store_keeper.get_tasks(user_id))
    }
    await send_default_message(update, DialogLines.account, args)
    return MAIN_MENU


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await send_default_message(update, DialogLines.contact, {"support_name": support_name})
    return MAIN_MENU


async def renew_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await send_default_message(update, DialogLines.renew_subscription)
    return RENEW_SUB


async def pay_window(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    day = update.message.text
    args = {
        "day": day,
        "price": price[day],
        "card": card_number
    }
    await send_default_message(update, DialogLines.pay_window, args)
    context.user_data['payment_info'] = (day, price[day])
    return PAYMENT


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await send_default_message(update, DialogLines.main_menu)
    return MAIN_MENU


async def prove_processing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['payment_prove'] = (update.message.chat_id, update.message.message_id)
    return PAYMENT


async def payment_processing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'payment_prove' in context.user_data:
        user_id = update.message.from_user.id
        chat_id, message_id = context.user_data.pop('payment_prove')
        day, price = context.user_data.pop('payment_info')
        payment_info = f"{user_id};{chat_id};{day.split()[0]}"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Approve", callback_data="pmt_apr_" + payment_info),
                                          InlineKeyboardButton("Decline", callback_data="pmt_dec_" + payment_info)]])
        await context.bot.send_message(admin_chat_id, f"User {user_id} sent {price} azn for {day} subscription",
                                       reply_markup=keyboard)
        await context.bot.forward_message(admin_chat_id, chat_id, message_id)
        await send_default_message(update, DialogLines.payment_processing)
        return MAIN_MENU
    return await pay_window(update, context)


async def callback_processing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    func, _, args = query.data.partition('_')
    if func == 'pmt':
        verdict, _, args = args.partition('_')
        user_id, chat_id, days = map(int, args.split(';'))
        if verdict == 'apr':
            store_keeper.add_subscription_time(user_id, days)
            await context.bot.send_message(chat_id, f"Перевод подтверждён. Подписка продлена на {days} дней")
        elif verdict == 'dec':
            await context.bot.send_message(chat_id, f"Перевод не подтверждён. "
                                                    f"По всем вопросам обращайтесь {support_name}")
        await query.edit_message_reply_markup(None)


async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pass


async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Your chat id: {update.message.chat_id}\nYour ID: {update.message.from_user.id}")


if __name__ == "__main__":
    application = ApplicationBuilder().token(telegram_key).build()
    store_keeper = StoreKeeper()
    application.add_handler(CommandHandler('get_chat_id', get_chat_id))
    application.add_handler(CallbackQueryHandler(callback_processing))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      MessageHandler(filters.TEXT, start)],
        states={
            MAIN_MENU: [MessageHandler(filters.Text([name]), func)
                        for func, name in zip([guide, tasks, about, account, contact, renew_subscription],
                                              DefaultKeyboard.main_menu.value)],
            RENEW_SUB: [MessageHandler(filters.Text([key for key in price.keys()]), pay_window),
                        MessageHandler(filters.Text(["Отмена"]), main_menu)],
            PAYMENT: [MessageHandler(filters.Text(DefaultKeyboard.payment_confirmation.value[0]), payment_processing),
                      MessageHandler((filters.PHOTO | filters.Document.IMAGE | filters.Document.PDF), prove_processing),
                      MessageHandler(filters.Text(["Отмена"]), main_menu)]
        },
        fallbacks=[],
        per_chat=False
    )
    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)
