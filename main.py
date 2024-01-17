import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import os
import random
import time
#dsdadssdsa
API_TOKEN = '6496305390:AAHsGWlf0J4qGK7zk13MzWPVkjREYLolFoE'

bot = telebot.TeleBot(API_TOKEN)

file_path = os.path.dirname(os.path.realpath(__file__))


keyboard = InlineKeyboardMarkup()
approve_button = InlineKeyboardButton("Заработать🤑", callback_data="click")
cancel_button = InlineKeyboardButton("Баланс💲", callback_data="balance")
keyboard.row(approve_button, cancel_button)

emojis = ["🤑", "💲", "💵", "💴", "💶", "💷", "💸", "🍉"]

# Добавляем словарь для отслеживания времени последнего нажатия для каждого пользователя
last_click_time = {}


isClear = False

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    global msg, isClear
    if isClear:
        isClear = False
        try:
            with sqlite3.connect(file_path + "/database.db") as con_click:
                cur_click = con_click.cursor()

                # Получение идентификаторов сообщений из базы данных
                cur_click.execute("SELECT message_id FROM messages_id WHERE id = ?", (message.chat.id,))
                result = cur_click.fetchall()

                # Удаление сообщений из базы данных и из телеграм-бота
                for row in result:
                    for message_id in row:
                        # Удаление из базы данных
                        cur_click.execute("DELETE FROM messages_id WHERE message_id = ?", (message_id,))

                        # Удаление из телеграм-бота
                        try:
                            bot.delete_message(message.chat.id, message_id)
                        except Exception as e:
                            print(f"Error deleting message {message_id} in Telegram: {e}")

                # Применение изменений в базе данных
                con_click.commit()
                cur_click.close()
                print(result)
        except Exception as e:
            print(f"Error deleting messages: {e}")
        isClear = True

    # Добавляем сообщение в базу данных
    
    msg = bot.send_message(message.chat.id, f"""Привет! Добро пожаловать в крипто бот.
                    \nВот список доступных команд:
                    \n1. /help /start - вызывает кнопку и это сообщение
                    \n2. /balance - текущий баланс

                    \nНажимайте кнопку чтобы зарабатывать криптовалюту(вывод невозможен, фан разработка)
                    """, reply_markup=keyboard)
    with sqlite3.connect(file_path + "/database.db") as con:
        cur = con.cursor()
        cur.execute("INSERT INTO messages_id (id, message_id) VALUES (?, ?)", (message.chat.id, message.message_id))
        cur.execute("INSERT INTO messages_id (id, message_id) VALUES (?, ?)", (message.chat.id, msg.message_id))
        con.commit()
    isClear = True


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Error handling message: {e}")


def click(message):
    balance_id = 0.01
    user_id = message.chat.id
    username = message.chat.username
    try:
        current_time = time.time()

        # Проверяем, прошла ли 1 секунда с момента последнего нажатия
        if user_id in last_click_time and current_time - last_click_time[user_id] < 0.5:
            return 0  # Возвращаем 0, чтобы не было ошибки при округлении

        with sqlite3.connect(file_path + "/database.db", check_same_thread=False) as con_click:
            cur_click = con_click.cursor()

            # Обновляем время последнего нажатия
            last_click_time[user_id] = current_time

            # Проверяем, существует ли запись для данного user_id в таблице
            cur_click.execute(f"SELECT * FROM crypto_keynet_bot WHERE user_id = ?", (user_id,))
            existing_record = cur_click.fetchone()

            if existing_record:
                # Если запись существует, обновляем баланс
                cur_click.execute("UPDATE crypto_keynet_bot SET balance = balance + ? WHERE user_id = ?", (balance_id, user_id))
            else:
                # Если записи нет, создаем новую запись с нулевым балансом
                cur_click.execute(f"INSERT INTO crypto_keynet_bot (balance, user_id) VALUES (?, ?)", (balance_id, user_id))

            con_click.commit()

        # Получаем обновленное значение balance_value
        cur_click.execute("SELECT balance FROM crypto_keynet_bot WHERE user_id = ?", (user_id,))
        result = cur_click.fetchone()

        if result:
            # Если результат не None, возвращаем новое значение balance_value
            return result[0]
        else:
            # Если результат None, возвращаем 0
            return 0

    except Exception as e:
        print(f"SQLite error: {e}")
        return 0



@bot.message_handler(commands=["balance"])
def balance(message, balance_value):
    try:
        with sqlite3.connect(file_path + "/database.db") as con_balance:
            cur_balance = con_balance.cursor()
            username1 = str(message.chat.first_name)
            cur_balance.execute("SELECT balance FROM crypto_keynet_bot WHERE user_id = ?", (message.chat.id,))

            result = cur_balance.fetchone()
            if result:
                balance_value = result[0]
                rounded_balance = round(balance_value, 2)
                
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=f'{username1}, Ваш баланс: {rounded_balance} ARBUZ!', reply_markup=keyboard)
            else:
                print("User not found in the database.")
    except Exception as e:
        print(f"2 error: {e}")

def balance_out():
    global balance_value
    return balance_value

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    global user, keyboard, balance_value, emojis
    username1 = str(call.message.chat.first_name)
    if call.data == "click":
        try:
            # Вызываем функцию click и обновляем значение balance_value
            balance_value = click(call.message)
            rounded_balance = round(balance_value, 2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'Вы заработали 0.01 ARBUZ!{random.choice(emojis)}', reply_markup=keyboard)
        except Exception:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'Вы заработали 0.01 ARBUZ!🥱', reply_markup=keyboard)
    elif call.data == "balance":
        try:
            # Просто выводим баланс без обновления
            rounded_balance = round(balance_value, 2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'{username1}, Ваш баланс: {rounded_balance} ARBUZ!', reply_markup=keyboard)
        except Exception:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'{username1}. Ваш баланс: {rounded_balance} ARBUZ!', reply_markup=keyboard)



bot.infinity_polling(timeout=10, long_polling_timeout = 5)