from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
from config import TOKEN
from gpt import GPT

bot = TeleBot(TOKEN)
gpt = GPT()


def create_keyboard(buttons_list):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard


@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id,
                     text=f"Привет, {user_name}! Я бот-помощник для решения разных задач!\n"
                          f"Ты можешь прислать условие задачи, а я постараюсь её решить.\n"
                          "/solve_task - для вопросов, /help - для более подробной информации",
                     reply_markup=create_keyboard(["/solve_task", '/help']))


@bot.message_handler(commands=['help'])
def support(message):
    bot.send_message(message.from_user.id,
                     text=f"""Бот-философ поможет решить вам насущные задачи, доступные команды:
/start - запуск бота(единожды)
/solve_task - начать решение задачи вместе с нейросетью
/continue - продолжение ответа от нейросети(используется после solve_task)""",
                     reply_markup=create_keyboard(["/solve_task"]))


@bot.message_handler(commands=['solve_task'])
def solve_task(message):
    global users_history
    users_history = {}
    gpt.full_response = []
    bot.send_message(message.chat.id, "Напиши запрос:")
    bot.register_next_step_handler(message, get_promt)


@bot.message_handler(commands=['continue'])
def continue_solve_task(message):
    user_id = message.from_user.id
    if user_id not in users_history or not users_history[user_id]['user_request']:
        bot.send_message(user_id, "Нет предыдущего запроса для продолжения.")
        return

    user_request = users_history[user_id]['user_request']
    json = gpt.make_promt(user_request)
    resp = gpt.send_request(json)
    response = gpt.process_resp(resp)

    if not response[0]:
        bot.send_message(user_id, "Не удалось выполнить запрос...")
    else:
        bot.send_message(user_id, continuue+response[1])
        bot.send_message(user_id, text="Для продолжения нажмите кнопку /continue, для нового запроса /solve_task",
                         reply_markup=create_keyboard(["/continue", "/solve_task"]))


@bot.message_handler(commands=['debug'])
def send_debug_info(message):
    user_id = message.from_user.id
    try:
        with open('gpt_errors.log', 'rb') as file:
            bot.send_document(user_id, file)
    except FileNotFoundError:
        bot.send_message(user_id, "Файл логов не найден.")


@bot.message_handler(func=lambda message: True)
def get_promt(message):
    user_id = message.from_user.id
    user_request = message.text
    # Сохраняем запрос пользователя для последующего использования
    if user_id not in users_history:
        users_history[user_id] = {'user_request': user_request}
    else:
        users_history[user_id]['user_request'] = user_request
        return
    user_request = users_history[user_id]['user_request']
    json = gpt.make_promt(user_request)
    resp = gpt.send_request(json)
    response = gpt.process_resp(resp)

    if not response[0]:
        bot.send_message(user_id, "Не удалось выполнить запрос...")
    else:
        global continuue
        continuue = response[1]
        bot.send_message(user_id, response[1])
        bot.send_message(user_id, text="Для продолжения нажмите кнопку /continue, для нового запроса /solve_task",
                         reply_markup=create_keyboard(["/continue", "/solve_task"]))


bot.polling()
