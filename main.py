import logging.config
from typing import Dict, Any

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, Bot, \
    CallbackQuery
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, ContextTypes, MessageHandler, filters, \
    CallbackQueryHandler

from src.config import telegram_key, bot_name, support_name, price, card_number, admin_chat_id, telegram_second_key, \
    LOGGER_CONFIG
from src.dialog_lines import DialogLines, DefaultKeyboard
from src.store_keeper import StoreKeeper

MAIN_MENU, RENEW_SUB, PAYMENT, SET_TASK_FREQUENCY, SET_TASK_NAME = range(5)

logging.config.dictConfig(LOGGER_CONFIG)
logger = logging.getLogger("bot")


async def send_default_message(update: Update, line: DialogLines, args: Dict[str, Any] = {}) -> None:
    if line.value.buttons:
        reply_keyboard = [line.value.buttons[i:i + 2] for i in range(0, len(line.value.buttons), 2)]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    else:
        markup = None
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


async def list_tasks(user_id: int, query: CallbackQuery, func: str, page: int = 0) -> None:
    tasks = store_keeper.get_tasks(user_id)
    if len(tasks) > 5:
        keyboard = [[InlineKeyboardButton(f"<{task.name}>", callback_data=f"tsk_{func}_{task.id}")]
                    for task in tasks[page * 5: (page + 1) * 5]]
        page_nav = []
        if page > 0:
            page_nav.append(InlineKeyboardButton("<<", callback_data=f"tsk_{func}_p{page - 1}"))
        if page < (len(tasks) - 1) // 5:
            page_nav.append(InlineKeyboardButton(">>", callback_data=f"tsk_{func}_p{page + 1}"))
        keyboard = InlineKeyboardMarkup(keyboard + [page_nav])
        await query.edit_message_text(f"Список задач\nСтраница {page + 1} из {(len(tasks) - 1) // 5 + 1}")
    else:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(f"<{task.name}>",
                                                               callback_data=f"tsk_{func}_{task.id}")]
                                         for task in tasks])
        await query.edit_message_text("Список задач")
    await query.edit_message_reply_markup(keyboard)


async def callback_processing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    logger.debug(query.data)
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
    elif func == 'tsk':
        if args == 'crt':
            logger.debug("Creating task")
            await context.bot.send_message(update.effective_chat.id,
                                           "Шаг:1/3.\nПришлите ссылку категории с сайта bina.az")
            await query.edit_message_reply_markup(None)
            context.user_data['tsk_crt'] = None
            return
        func, _, args = args.partition('_')
        if func in ['del', 'inf'] and args and args[0] == 'p':
            page = int(args[1:])
            await list_tasks(update.effective_user.id, query, func, page)
        elif func in ['del', 'inf'] and not args:
            await list_tasks(update.effective_user.id, query, func)
        elif func == 'del':
            task_id = int(args)
            store_keeper.remove_task(task_id)
            context.job_queue.get_jobs_by_name(str(task_id))[0].schedule_removal()
            await list_tasks(update.effective_user.id, query, func)
            logger.debug(f"Removed task: {task_id}")
        elif func == 'inf':
            task_id = int(args)
            task = store_keeper.get_task(task_id)
            await context.bot.send_message(update.effective_chat.id, f"Имя задачи <{task.name}>\nURL: {task.url}")


async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Создать задачу", callback_data="tsk_crt")],
                                     [InlineKeyboardButton("Удалить задачу", callback_data="tsk_del")],
                                     [InlineKeyboardButton("Информация о задаче", callback_data="tsk_inf")]])
    await update.message.reply_text("Выберите пункт меню", reply_markup=keyboard)
    return MAIN_MENU


async def set_task_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.debug("Setting task url")
    if 'tsk_crt' not in context.user_data:
        return MAIN_MENU
    offset, length = update.message.entities[0].offset, update.message.entities[0].length
    url = update.message.text[offset:offset + length]
    try:
        items = store_keeper.get_last_k_items(url, 1)
    except KeyError:
        await update.message.reply_text("Ссылка должна быть категорией с bina.az")
        return MAIN_MENU
    except Exception as e:
        await update.message.reply_text("Не найдены объявления на этой странице")
        logger.error("Get items error", exc_info=e)
        return MAIN_MENU
    if not items:
        await update.message.reply_text("Не найдены объявления на этой странице")
        return MAIN_MENU
    context.user_data['tsk_crt'] = [url]
    await send_default_message(update, DialogLines.set_task_frequency)
    return SET_TASK_FREQUENCY


async def set_task_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.debug("Setting task frequency")
    minutes = update.message.text
    frequency = int(minutes.split()[0])
    context.user_data['tsk_crt'].append(frequency)
    await send_default_message(update, DialogLines.set_task_name)
    return SET_TASK_NAME


async def set_task_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.debug("Setting task name")
    name = update.message.text
    url, frequency = context.user_data.pop('tsk_crt')
    task_id = store_keeper.add_task(update.message.from_user.id, name, url, frequency)
    context.job_queue.run_repeating(notification, frequency * 60,
                                    name=str(task_id), user_id=update.message.from_user.id)
    logger.info(f"Created task: {task_id}")
    await send_default_message(update, DialogLines.main_menu)
    return MAIN_MENU


async def notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.debug("New notification")
    task_id = int(context.job.name)
    user_id = context.job.user_id
    items = store_keeper.get_new_items(task_id)
    logger.debug(f"Find {len(items)} notifications")
    for item in items:
        message = f"Найдено новое объявление:\nЦена: {item.price}\nМесто: {item.location}\nПодробнее: " \
                  f"https://ru.bina.az/item/{item.id}"
        await notifier.send_message(user_id, message)


async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Your chat id: {update.message.chat_id}\nYour ID: {update.message.from_user.id}")


if __name__ == "__main__":
    application = ApplicationBuilder().token(telegram_key).build()
    notifier = Bot(telegram_second_key)
    store_keeper = StoreKeeper(application.job_queue, notification)
    application.add_handler(CommandHandler('get_chat_id', get_chat_id))
    application.add_handler(CallbackQueryHandler(callback_processing))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      MessageHandler(filters.TEXT, start)],
        states={
            MAIN_MENU: [MessageHandler(filters.Text([name]), func)
                        for func, name in zip([guide, tasks, about, account, contact, renew_subscription],
                                              DefaultKeyboard.main_menu.value)] +
                       [MessageHandler(filters.Entity(MessageEntity.URL), set_task_url)],
            RENEW_SUB: [MessageHandler(filters.Text([key for key in price.keys()]), pay_window),
                        MessageHandler(filters.Text(["Отмена"]), main_menu)],
            PAYMENT: [MessageHandler(filters.Text(DefaultKeyboard.payment_confirmation.value[0]), payment_processing),
                      MessageHandler((filters.PHOTO | filters.Document.IMAGE | filters.Document.PDF), prove_processing),
                      MessageHandler(filters.Text(["Отмена"]), main_menu)],
            SET_TASK_FREQUENCY: [MessageHandler(filters.Text([value
                                                              for value in DefaultKeyboard.tasks_frequency.value[:-1]]),
                                                set_task_frequency),
                                 MessageHandler(filters.Text(["Отмена"]), main_menu)],
            SET_TASK_NAME: [MessageHandler(filters.TEXT, set_task_name)]
        },
        fallbacks=[],
        per_chat=False
    )
    application.add_handler(conv_handler)
    logger.info("Application started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
