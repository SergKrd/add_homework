import logging
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, \
    ConversationHandler

from func import select_all_lessons, select_all_admins, select_all_main_admins, add_new_admin, add_new_homework, \
    bot_token

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Stages
START, CHOOSE_SUBJECT, CHOOSE_DATE, ENTER_TASK, CONFIRMATION, REQUEST_ACCESS = range(6)

temp_user_data = {}


def is_admin(user_id):
    if str(user_id) in [el[0] for el in select_all_admins()]:
        return True
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton(text="Добавить ДЗ", callback_data="add_homework")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(text="Запросить доступ", callback_data="request_access")],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    return START


async def add_homework(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    buttons = [[InlineKeyboardButton(f'{el[2]}   {el[1]}', callback_data=str(el[:2]))] for el in
               sorted(select_all_lessons(), key=lambda x: x[1])]
    print(buttons)
    query = update.callback_query
    await query.answer()
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(text="Выберите предмет:", reply_markup=reply_markup)
    return CHOOSE_SUBJECT


async def choose_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    # Получаем кортеж из строки callback_data
    print('eval(query.data)', eval(query.data))
    subject_id, subject_name = eval(
        query.data)  # Используем eval для преобразования строки обратно в кортеж
    # Сохраняем id предмета
    context.user_data['subject_id'] = subject_id
    context.user_data['subject_name'] = subject_name
    #context.user_data['lesson_ico'] = lesson_ico
    await query.edit_message_text(text="Введите дату выполнения (ДД.ММ.ГГГГ):")
    return CHOOSE_DATE


def validate_date(date_str):
    try:
        # Попытка преобразования даты, игнорируя разделители
        date_obj = datetime.strptime(date_str.replace(".", "").replace("-", ""), "%d%m%Y")
        # Форматирование даты в нужный формат
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return None


async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    date_str = update.message.text
    valid_date = validate_date(date_str)
    if valid_date:
        context.user_data['date'] = valid_date
        await update.message.reply_text("Введите текст задания:")
        return ENTER_TASK
    else:
        await update.message.reply_text("Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:")
        return CHOOSE_DATE


async def enter_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    task = update.message.text
    context.user_data['task'] = task
    data = f"Предмет: {context.user_data['subject_name']}\nДата выполнения: {context.user_data['date']}\nЗадание: {task}"
    keyboard = [
        [
            InlineKeyboardButton(text="Подтвердить", callback_data="confirm"),
            InlineKeyboardButton(text="Исправить", callback_data="edit"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Пожалуйста, проверьте данные:\n\n{data}", reply_markup=reply_markup)
    return CONFIRMATION


async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "confirm":
        # Get current date
        date_on = datetime.now().strftime("%Y-%m-%d")
        # Get author's username
        author = update.effective_user.username
        # Save homework with additional data
        data = {
            "lessons": context.user_data['subject_name'],
            "lessons_id": context.user_data['subject_id'],
            "date_off": context.user_data['date'],
            "homework": context.user_data['task'],
            "date_on": date_on,
            "author": author,
        }

        if add_new_homework(date_on, data["date_off"], data["lessons_id"], data["homework"], author):
            await query.edit_message_text(text="Задание успешно добавлено!")
            return ConversationHandler.END
        else:
            await query.edit_message_text(text="Что-то пошло не так! Попробуйте позже.")
            return ConversationHandler.END
    else:
        # Start over from choosing subject
        return await add_homework(update, context)


async def request_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    keyboard = [
        [
            KeyboardButton(
                text="Поделиться контактом",
                request_contact=True,
            )
        ]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await context.bot.send_message(  # Отправка нового сообщения
        chat_id=user_id,
        text="Для запроса доступа нажмите на кнопку 'Поделиться контактом':",
        reply_markup=reply_markup,
    )

    return REQUEST_ACCESS


async def send_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global temp_user_data  # Переменная для хранения данных
    contact = update.effective_message.contact  # Получаем контакт
    user = update.effective_user  # Получаем пользователя

    user_id = contact.user_id
    first_name = contact.first_name
    last_name = contact.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = user.username or "не указан"  # Получаем username из user
    phone_number = contact.phone_number or "не указан"

    # Сохраняем данные в context.user_data
    context.user_data['user_id'] = user_id
    context.user_data['full_name'] = full_name
    context.user_data['username'] = username
    context.user_data['phone_number'] = phone_number

    print(context.user_data)
    temp_user_data = context.user_data

    # Отправляем сообщение администраторам
    keyboard = [
        [
            InlineKeyboardButton("✅ Добавить пользователя", callback_data=f"approve_admin:{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{user_id}"),
        ],
        [InlineKeyboardButton("👑 Добавить админа", callback_data=f"approve_main_admin:{user_id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for admin_id in [int(el[0]) for el in select_all_main_admins()]:
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"Пользователь {full_name} (ID: {user_id}) запрашивает доступ. Username: @{username}, {full_name} Телефон: {phone_number}",
            reply_markup=reply_markup,
        )
    # Удаляем кнопку "Поделиться контактом"
    # await update.effective_message.edit_reply_markup(reply_markup=None)

    await update.effective_message.reply_text("Ваш запрос отправлен администраторам.")
    return ConversationHandler.END


async def handle_admin_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global temp_user_data  # Переменная для хранения данных
    query = update.callback_query
    await query.answer()
    action, user_id = query.data.split(":")
    user_data = temp_user_data
    user_id = user_data['user_id']
    user_name = user_data['full_name']
    username = user_data['username']
    phone_number = user_data['phone_number']

    if action == "approve_admin":
        if add_new_admin(user_id, 0, phone_number, username, user_name):
            await query.edit_message_text(
                text=f"Пользователь добавлен:\nNick: @{username}\nФИО: {user_name}\nтел.: {phone_number}")
            await context.bot.send_message(chat_id=user_id,
                                           text="Ваш запрос одобрен! Теперь вы можете добавлять домашнее задание.")
        else:
            await query.edit_message_text(
                text=f"Не удалось добавить пользователя. Что-то с БД.:\nNick: @{username}\nФИО: {user_name}\nтел.: {phone_number}")
            await context.bot.send_message(chat_id=user_id, text="Что-то пошло не так. Попробуйте ещё раз позже.")
    elif action == "reject":
        keyboard = [
            [
                InlineKeyboardButton("Да", callback_data=f"notify_reject:{user_id}"),
                InlineKeyboardButton("Нет", callback_data="do_not_notify"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"Отклонить запрос от {user_name}? Оповестить пользователя?", reply_markup=reply_markup
        )
    elif action == "approve_main_admin":
        keyboard = [
            [
                InlineKeyboardButton("Да", callback_data=f"confirm_main_admin:{user_id}"),
                InlineKeyboardButton("Нет", callback_data="cancel_main_admin"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=f"Вы уверены, что хотите сделать {user_name} админом?",
                                      reply_markup=reply_markup)
    elif action == "notify_reject":
        await query.edit_message_text(text=f"Запрос от {user_name} отклонен.")
        await context.bot.send_message(chat_id=user_id, text="Ваш запрос на доступ был отклонен.")
    elif action == "confirm_main_admin":
        if add_new_admin(user_id, 1, phone_number, username, user_name):
            await query.edit_message_text(text=f"Пользователь {user_name} добавлен как админ.")
            await context.bot.send_message(chat_id=user_id, text="Ваш запрос одобрен! Теперь вы админ.")
        else:
            await query.edit_message_text(text=f" Не удалось добавить пользователя {user_name}\nЧто-то с БД.")
            await context.bot.send_message(chat_id=user_id, text="Что-то пошло не так. Попробуйте ещё раз позже.")
    else:
        await query.edit_message_text(text="Действие отменено.")


def main() -> None:
    application = Application.builder().token(bot_token()).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [
                CallbackQueryHandler(add_homework, pattern="^add_homework$"),
                CallbackQueryHandler(request_access, pattern="^request_access$"),
            ],
            CHOOSE_SUBJECT: [
                CallbackQueryHandler(choose_subject),
            ],
            CHOOSE_DATE: [
                MessageHandler(filters=filters.TEXT, callback=choose_date),
            ],
            ENTER_TASK: [
                MessageHandler(filters=filters.TEXT, callback=enter_task),
            ],
            CONFIRMATION: [
                CallbackQueryHandler(confirmation, pattern="^(confirm|edit)$"),
            ],
            REQUEST_ACCESS: [
                CallbackQueryHandler(send_contact, pattern="^send_contact$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler),
    application.add_handler(MessageHandler(filters=filters.CONTACT, callback=send_contact)),
    application.add_handler(CallbackQueryHandler(handle_admin_request,
                                                 pattern="^(approve_admin|reject|approve_main_admin|notify_reject|confirm_main_admin).*"))
    application.run_polling()


if __name__ == "__main__":
    main()
