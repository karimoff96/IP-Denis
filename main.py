from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from environs import Env
import requests
import datetime
import logging
import random

# Set up logging
env = Env()
env.read_env()
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
# Create .env file and put your bot token inside the file or just put your token here
BOT_TOKEN = env.str("BOT_TOKEN")

# In order not to take testers additional time and efford, I am leaving these API_TOKENs open.
weather_token = (
    "22c3404f1e8a2de09be11fefcf2a15b9"  # The source "https://openweathermap.org/"
)
exchangerate_token = (
    "DzBwQounUnjGrNUacQWDDQmpJ49pfWEP"  # The source "https://apilayer.com/"
)
random_images_token = "T8fZ8selYoqCnCQdrhDYlGP89EjN1TpOw54MonjcM06LKRpNoY4ZmZSj"  # the source is "https://api.pexels.com"
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
user_inputs = {"TO": "", "FROM": ""}


# Start command handler
@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    but1 = types.KeyboardButton(text="Прогноз погоды", request_location=True)
    but2 = types.KeyboardButton(text="Конвертация валют")
    but3 = types.KeyboardButton(text="Рандом фото")
    but4 = types.KeyboardButton(text="Создать опрос")
    button = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button.add(but1, but2, but3, but4)
    await message.answer(
        f"Привет {message.from_user.first_name}! Как я могу вам помочь?",
        reply_markup=button,
    )


# Создать опрос commanda handler
@dp.message_handler(lambda message: message.text == "Создать опрос")
async def create_poll_handler(message: types.Message):
    but1 = types.KeyboardButton(text="Назад")
    button = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button.add(but1)
    # Ask for the poll question and options
    await bot.send_message(
        chat_id=message.chat.id,
        text="Введите вопрос для опроса и варианты ответов через запятую: ",
        reply_markup=button,
    )

    # Define a message handler to handle the user's response to the question prompt
    async def handle_question(message: types.Message):
        options = message.text.split(",")
        question = options[0]
        # Create the poll and send it to the chat
        poll = types.Poll(
            question=question,
            options=options[1:],
            is_anonymous=False,
            allows_multiple_answers=True,
        )
        message_with_poll = await bot.send_poll(
            chat_id=message.chat.id,
            question=poll.question,
            options=poll.options,
            is_anonymous=False,
            allows_multiple_answers=True,
            explanation="Ответьте на вопрос, чтобы участвовать в опросе",
        )

        # Enable poll sharing in groups and channels
        await bot.set_chat_permissions(
            chat_id=message.chat.id,
            permissions=types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True,
            ),
        )
        # Get the bot's username
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        # Send a message with a link to the poll
        poll_link = f"https://t.me/{bot_username}?start=poll{message_with_poll.poll.id}"
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"Опрос '{poll.question}' создан! Линк: {poll_link}",
        )

    # Register the question message handler
    dp.register_message_handler(handle_question, chat_id=message.chat.id)


# Location handler
@dp.message_handler(content_types=types.ContentType.LOCATION)
async def handle_location(message: types.Message):
    lat = message.location.latitude
    long = message.location.longitude
    res = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={long}&lang=ru&appid={weather_token}&units=metric"
    ).json()
    await message.answer(
        f"""Погода на сегодня:\n\nПогода: {res["weather"][0]["description"]}\nТемпература: {str(res["main"]["temp"])}°\nОщущается как: {str(res["main"]["feels_like"])}°\nВлажность: {str(res["main"]["humidity"])}%\nВосход: {datetime.datetime.fromtimestamp(res["sys"]["sunrise"]).strftime("%H:%M:%S")}\nЗакат: {datetime.datetime.fromtimestamp(res["sys"]["sunset"]).strftime("%H:%M:%S")}\nГород: {res["name"]}\nВремя обновнении: {datetime.datetime.fromtimestamp(res["timezone"]).strftime("%H:%M")}"""
    )


# Convertation command handler
@dp.message_handler(lambda message: message.text == "Конвертация валют")
async def convertation(message: types.Message):
    but1 = types.KeyboardButton("RUB>USD")
    but2 = types.KeyboardButton("USD>RUB")
    but3 = types.KeyboardButton("RUB>CNY")
    but4 = types.KeyboardButton("RUB>KRW")
    but5 = types.KeyboardButton("Назад")
    button = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button.add(but1, but2, but3, but4, but5)
    await message.answer("Выберите вариант конвертации!", reply_markup=button)


# Convertation types reciever handler
@dp.message_handler(
    lambda message: message.text in ["RUB>USD", "USD>RUB", "RUB>CNY", "RUB>KRW"]
)
async def currency_handeler(message: types.Message):
    currency = message.text.split(">")
    global user_inputs
    user_inputs["TO"] = currency[1]
    user_inputs["FROM"] = currency[0]
    await message.answer("Ведиде сумму:")


# Hanlder for handling only inputted digits from user and colculating the convertation result
@dp.message_handler(lambda message: message.text.isdigit())
async def sum_handler(message: types.Message):
    global user_inputs
    url = f"https://api.apilayer.com/exchangerates_data/convert?to={user_inputs['TO']}&from={user_inputs['FROM']}&amount={message.text}"
    payload = {}
    headers = {"apikey": exchangerate_token}
    response = requests.request("GET", url, headers=headers, data=payload).json()
    data = f"""Время : {datetime.datetime.fromtimestamp(response['info']['timestamp']).strftime("%H:%M:%S")}\nДата: {response['date']}\nРезультат: {user_inputs['FROM']} {message.text}  = {user_inputs['TO']} {round(response['result'], 1)} """
    await message.answer(data)


# Random image send command handler
@dp.message_handler(lambda message: message.text in ["Рандом фото", "Другой фото"])
async def random_photo_sender(message: types.Message):
    await message.answer("Работаю...")
    headers = {
        "Authorization": random_images_token,
    }
    params = {"query": "animals", "per_page": 1}  # Only retrieve one photo at a time
    response = requests.get(
        "https://api.pexels.com/v1/search", headers=headers, params=params
    )
    data = response.json()
    total_pages = data["total_results"]
    random_page = random.randint(1, total_pages)
    params["page"] = random_page

    response = requests.get(
        "https://api.pexels.com/v1/search", headers=headers, params=params
    )
    data = response.json()
    photo_url = data["photos"][0]["src"]["large"]
    but = types.KeyboardButton(text="Другой фото")
    but1 = types.KeyboardButton(text="Назад")
    button = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button.add(but, but1)
    await message.answer_photo(
        photo_url, caption="Линк фотки: {}".format(photo_url), reply_markup=button
    )


# Back button handlar
@dp.message_handler(lambda message: message.text == "Назад")
async def send_welcome(message: types.Message):
    but1 = types.KeyboardButton(text="Прогноз погоды", request_location=True)
    but2 = types.KeyboardButton(text="Конвертация валют")
    but3 = types.KeyboardButton(text="Рандом фото")
    but4 = types.KeyboardButton(text="Создать опрос")
    button = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button.add(but1, but2, but3, but4)

    await message.answer(
        f"Выберите способ подачи",
        reply_markup=button,
    )


# Start the bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)


# The code can be modified and simplified and devided into more modules/files but because of some reasons I couldn`t spend much time on this project sorry for that
