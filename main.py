#TELEGRAM_API_TOKEN = '5628907522:AAGYSqMrZTPVaBasnCzh1wv-Gz0bWWrsMgE'
import telebot
import sqlite3
from datetime import datetime, timedelta
from telebot import types

# Токен вашего бота
TOKEN = '5628907522:AAGYSqMrZTPVaBasnCzh1wv-Gz0bWWrsMgE'

bot = telebot.TeleBot(TOKEN)

# Создание базы данных и таблицы (если не существует)
conn = sqlite3.connect('consultations.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS consultations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER, 
        user_name TEXT, 
        date TEXT, 
        time TEXT, 
        description TEXT
    )
''')
conn.commit()

def add_consultation(message, date, time, description):
    """
    Добавляет новую консультацию в базу данных.
    """
    try:
        datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M")
    except ValueError:
        bot.reply_to(message, "Некорректный формат даты или времени. Используйте ГГГГ-ММ-ДД ЧЧ:ММ")
        return

    today = datetime.now().date().strftime('%Y-%m-%d')
    if date < today:
        bot.reply_to(message, "Дата записи не может быть раньше сегодняшней.")
        return

    user_id = message.from_user.id
    user_name = message.from_user.full_name

    conn = sqlite3.connect('consultations.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO consultations (user_id, user_name, date, time, description) VALUES (?, ?, ?, ?, ?)",
                   (user_id, user_name, date, time, description))
    conn.commit()
    conn.close()
    bot.reply_to(message, f"Запись успешно добавлена на {date} в {time}: {description}")
    send_main_menu(message)

def get_all_consultations(message):
    """
    Выводит список всех консультаций пользователя.
    """
    conn = sqlite3.connect('consultations.db')
    cursor = conn.cursor()

    user_id = message.from_user.id
    cursor.execute("SELECT id, user_name, date, time, description FROM consultations WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()

    if rows:
        response = "Все записи:\n"
        for row in rows:
            response += f"№{row[0]}, {row[1]} {row[2]}: {row[3]}\n{row[4]}\n"
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Записей нет.")

    conn.close()
    send_main_menu(message)

def get_next_week_consultations(message):
    """
    Выводит список консультаций пользователя на следующую неделю.
    """
    # Создание нового соединения с базой данных
    conn = sqlite3.connect('consultations.db')
    cursor = conn.cursor()

    user_id = message.from_user.id
    today = datetime.now()
    next_week = today + timedelta(days=7)
    print(user_id, today.strftime('%Y-%m-%d'), next_week.strftime('%Y-%m-%d'))

    cursor.execute("SELECT * FROM consultations WHERE user_id=? AND date BETWEEN ? AND ?",
                   (user_id, today.strftime('%Y-%m-%d'), next_week.strftime('%Y-%m-%d')))
    rows = cursor.fetchall()

    if rows:
        response = "Ваши записи на следующую неделю:\n"
        for row in rows:
            response += f"№{row[0]} {row[3]}: {row[4]}\n{row[5]}\n "
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "У вас нет записей на следующую неделю.")

    conn.close()  # Закрытие соединения с базой данных
    send_main_menu(message)

def delete_consultation(message, consultation_id):
    """
    Удаляет консультацию по ее ID.
    """
    # Создание нового соединения с базой данных
    conn = sqlite3.connect('consultations.db')
    cursor = conn.cursor()

    user_id = message.from_user.id
    print(user_id)

    # Проверяем, что пользователь пытается удалить свою консультацию
    cursor.execute("SELECT * FROM consultations WHERE id=? AND user_id=?", (consultation_id, user_id))
    row = cursor.fetchone()
    print(row)

    if row:
        print(consultation_id)
        cursor.execute("DELETE FROM consultations WHERE id=?", (consultation_id,))
        conn.commit()
        bot.reply_to(message, "Запись успешно удалена.")
    else:
        bot.reply_to(message, "Запись не найдена или вы не являетесь ее владельцем.")

    conn.close()  # Закрытие соединения с базой данных
    send_main_menu(message)

def delete_old_consultations(message):
    """
    Удаляет консультации, которые старше месяца.
    """
    today = datetime.now()
    one_month_ago = today - timedelta(days=30)

    # Создание нового соединения с базой данных
    conn = sqlite3.connect('consultations.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM consultations WHERE date < ?", (one_month_ago.strftime('%Y-%m-%d'),))
    conn.commit()

def create_reply_keyboard(buttons):
    """
    Создает клавиатуру с кнопками.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*buttons)
    return markup

def send_main_menu(message):
    """
    Функция для отправки основного меню.
    """
    markup = create_reply_keyboard([
        types.KeyboardButton('Новая запись'),
        types.KeyboardButton('Все записи'),
        types.KeyboardButton('Неделя'),
        types.KeyboardButton('Удалить запись')
    ])
    bot.reply_to(message, "Привет! доступны такие операции:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Отправляет приветственное сообщение и клавиатуру.
    """
    delete_old_consultations(message)  # Удаляем старые консультации при запуске бота
    send_main_menu(message)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    """
    Обрабатывает текстовые сообщения от пользователя.
    """
    if message.text.lower() == 'новая запись':
        # Начало процесса записи на консультацию
        msg = bot.reply_to(message, "Введите дату записи в формате ГГГГ-ММ-ДД")
        bot.register_next_step_handler(msg, process_date_step)
    elif message.text.lower() == 'все записи':
        get_all_consultations(message)
    elif message.text.lower() == 'неделя':
        get_next_week_consultations(message)
    elif message.text.lower() == 'удалить запись':
        msg = bot.reply_to(message, "Введите № записи, которую хотите удалить:")
        bot.register_next_step_handler(msg, process_delete_step)
    else:
        bot.reply_to(message, "Я не понимаю вашу команду. Попробуйте еще раз.")

def process_date_step(message):
    """
    Обрабатывает шаг записи даты.
    """
    date = message.text
    msg = bot.reply_to(message, "Введите время записи в формате ЧЧ:ММ")
    bot.register_next_step_handler(msg, process_time_step, date)

def process_time_step(message, date):
    """
    Обрабатывает шаг записи времени.
    """
    time = message.text
    msg = bot.reply_to(message, "Введите содержание записи:")
    bot.register_next_step_handler(msg, process_description_step, date, time)

def process_description_step(message, date, time):
    """
    Обрабатывает шаг записи описания.
    """
    description = message.text
    add_consultation(message, date, time, description)

def process_delete_step(message):
    """
    Обрабатывает удаление консультации.
    """
    try:
        consultation_id = int(message.text)
        delete_consultation(message, consultation_id)
    except ValueError:
        bot.reply_to(message, "Введите правильный № записи.")

if __name__ == '__main__':
    bot.remove_webhook()  # Удаляем активный вебхук, если он был установлен
    bot.polling()  # Запускаем polling для получения обновлений

