from keep_alive import keep_alive
import telebot
from telebot import types
import random
import time
from threading import Thread

TOKEN = "8161107014:AAH1I0srDbneOppDw4AsE2kEYtNtk7CRjOw"
bot = telebot.TeleBot(TOKEN)

user_balances = {}
user_games = {}
aviator_games = {}  # Aviator o'yinlar
ADMIN_ID = 5815294733
withdraw_sessions = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_balances.setdefault(user_id, 1000)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Balance', 'Play Mines')
    if user_id == ADMIN_ID:
        markup.add('Hisob to‘ldirish', 'Mablag‘ chiqarish')
    else:
        markup.add('Hisob to‘ldirish', 'Hisob yechish')
    markup.add('Aviator')
    bot.send_message(message.chat.id, "Xush kelibsiz! O‘yinlarni boshlang!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Balance")
def balance(message):
    user_id = message.from_user.id
    bal = user_balances.get(user_id, 0)
    bot.send_message(message.chat.id, f"Balansingiz: {bal} so‘m")

@bot.message_handler(func=lambda m: m.text == "Aviator")
def aviator_start(message):
    user_id = message.from_user.id
    if user_id in aviator_games:
        bot.send_message(message.chat.id, "Oldingi Aviator hali tugamadi.")
        return
    msg = bot.send_message(message.chat.id, "Tikish miqdorini kiriting:")
    bot.register_next_step_handler(msg, lambda m: aviator_bet(m, user_id))

def aviator_bet(message, user_id):
    try:
        bet = int(message.text)
        if bet < 1000:
            bot.send_message(message.chat.id, "Minimal tikish 1000 so‘m.")
            return
        if user_balances.get(user_id, 0) < bet:
            bot.send_message(message.chat.id, "Balansda yetarli mablag‘ yo‘q.")
            return

        user_balances[user_id] -= bet

        if random.random() < 0.1:  # 10% katta crash
            crash = round(random.uniform(3.0, 8.0), 2)
        else:
            crash = round(random.uniform(1.05, 1.7), 2)  # past yutish ehtimoli

        aviator_games[user_id] = {
            'stake': bet,
            'crash': crash,
            'x': 1.0,
            'active': True,
            'msg_id': None
        }
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(" Cash Out", callback_data="aviator_cashout"))
        msg = bot.send_message(message.chat.id, f" Aviator boshlandi!\nMultiplikator: x1.00", reply_markup=markup)
        aviator_games[user_id]['msg_id'] = msg.message_id
        Thread(target=run_aviator, args=(message.chat.id, user_id)).start()

    except ValueError:
        bot.send_message(message.chat.id, "Faqat raqam kiriting.")

def run_aviator(chat_id, user_id):
    game = aviator_games[user_id]
    x = 1.0
    while x < game['crash'] and game['active']:
        x = round(x + 0.1, 2)
        game['x'] = x
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(" Cash Out", callback_data="aviator_cashout"))
            bot.edit_message_text(f" Multiplikator: x{x}", chat_id, game['msg_id'], reply_markup=markup)
        except:
            pass
        time.sleep(0.5)

    if game['active']:
        game['active'] = False
        bot.edit_message_text(f" BORTLANDI!\nMultiplikator: x{game['crash']}\nSiz yutqazdingiz.", chat_id, game['msg_id'])
        del aviator_games[user_id]

@bot.callback_query_handler(func=lambda call: call.data == "aviator_cashout")
def aviator_cashout(call):
    user_id = call.from_user.id
    if user_id not in aviator_games:
        bot.answer_callback_query(call.id, "O‘yin topilmadi.")
        return

    game = aviator_games[user_id]
    if not game['active']:
        bot.answer_callback_query(call.id, "Juda kech.")
        return

    game['active'] = False
    win = int(game['stake'] * game['x'])
    user_balances[user_id] += win
    bot.edit_message_text(
        f"Cash Out!\nMultiplikator: x{game['x']}\nYutuq: {win} so‘m",
        call.message.chat.id,
        game['msg_id']
    )
    del aviator_games[user_id]

print("Bot ishga tushdi...")
keep_alive()
bot.polling(none_stop=True)

