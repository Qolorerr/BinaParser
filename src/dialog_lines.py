import enum
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class DialogLine:
    text: str = ""
    buttons: List[str] = None
    args: Dict[str, Any] = None


class DefaultKeyboard(enum.Enum):
    main_menu = ["Инструкция", "Задачи", "О боте", "Аккаунт", "Контакты", "Продлить подписку"]
    subscription_options = ["7 дней", "14 дней", "30 дней", "Отмена"]
    payment_confirmation = ["Средства переведены", "Отмена"]
    tasks_frequency = ["3 минуты", "5 минут", "10 минут", "Отмена"]


class DialogLines(enum.Enum):
    start = DialogLine(
        "Добро пожаловать в ...\nУважаемый(ая), Вам подключена пробная подписка до 📅%(datetime)s. "
        "Желаю полезного использования!😜. Рекомендую ознакомиться с инструкцией.",
        DefaultKeyboard.main_menu.value)
    guide = DialogLine(
        "Youtube link",
        DefaultKeyboard.main_menu.value)
    about = DialogLine(
        "Бот не собирает никакой информации о продавцах, не передает третьим лицам "
        "данные Ваших запросов и не изменяет что-либо в опубликованных объявлениях. "
        "Бот проверяет только наличие новых объявлений и, как только они появятся, "
        "%(bot_name)s даст Вам об этом знать.",
        DefaultKeyboard.main_menu.value)
    account = DialogLine(
        "Ваш ID: %(user_id)s\nПодписка активна до: %(datetime)s\nКоличество активных задач: "
        "%(tasks)s\n\n(каждому новому пользователю присваивается свой ID)",
        DefaultKeyboard.main_menu.value)
    contact = DialogLine(
        "Если у Вас возникли вопросы или есть пожелания - связь с поддержкой %(support_name)s",
        DefaultKeyboard.main_menu.value)
    renew_subscription = DialogLine(
        "Выберите время продления подписки",
        DefaultKeyboard.subscription_options.value)
    pay_window = DialogLine(
        "Продление подписки на %(day)s стоит %(price)s azn\nПереведите средства на карту: %(card)s\n"
        "После отправьте фото подтверждения и нажмите кнопку о подтверждении оплаты",
        DefaultKeyboard.payment_confirmation.value)
    main_menu = DialogLine(
        "Главное меню",
        DefaultKeyboard.main_menu.value)
    payment_processing = DialogLine(
        "Ожидайте подтверждения платежа",
        DefaultKeyboard.main_menu.value)
    set_task_frequency = DialogLine("⏳Шаг:2/3. \nВыберите частоту проверки объявлений",
                                    DefaultKeyboard.tasks_frequency.value)
    set_task_name = DialogLine("Шаг:3/3. \nВведите название задачи")
    task_created = DialogLine("👍Поздравляю! Задача успешно создана!\nДля получения объявлений начните чат с "
                              "@bina_az_notifier_bot")
