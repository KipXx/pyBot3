import asyncio
import datetime
import json
import sqlite3

import requests
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

import keyboards as kb

bot = Bot(token='5946513884:AAGkl2MPaJ5sK0BRYsbWkY6PV23JJBF1-aU')
API = '709e3cbe105d05f7bfdb27403929d3bc'
dp = Dispatcher()


last_city = None
is_subscribed = False
# Переводчик
file_name = 'weather_data.json'
with open(file_name, 'r', encoding='utf-8') as json_file:
    weather_mapping = json.load(json_file)


conn = sqlite3.connect('subscriptions.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id INTEGER PRIMARY KEY,
        city TEXT,
        is_subscribed INTEGER
    )
''')
conn.commit()


@dp.message(F.text == '/start')
async def cmd_start(message: Message):
    await message.answer(
        f'Здравствуйте, {message.from_user.first_name}! Я бот погоды. Чтобы узнать погоду, просто напиши название города.')


@dp.message(F.text.lower() == 'завтра')
async def cmd_weather_tomorrow(message: Message):
    global last_city
    if last_city:
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        res = requests.get(f'https://api.openweathermap.org/data/2.5/forecast?q={last_city}&appid={API}&units=metric')
        if res.status_code == 200:
            data = json.loads(res.text)
            tomorrow_data = None
            for forecast in data['list']:
                if forecast['dt_txt'].split()[0] == tomorrow:
                    tomorrow_data = forecast
                    break
            if tomorrow_data:
                temp = tomorrow_data['main']['temp']
                temp_like = tomorrow_data['main']['feels_like']
                pressure = tomorrow_data["main"]["pressure"]
                wind_speed = tomorrow_data["wind"]["speed"]
                humidity = tomorrow_data["main"]["humidity"]
                weather_trans_en = tomorrow_data['weather'][0]['description']
                weather_trans_ru = weather_mapping.get(weather_trans_en, weather_trans_en)
                weather_info = (f'🌤️Завтра: {weather_trans_ru}\n'
                                f'🌡️Температура: {temp}°C\n'
                                f'🤲Ощущается как: {temp_like}°C\n'
                                f'💧Влажность: {humidity}%\n'
                                f'🎈Давление: {pressure} мбар\n'
                                f'🍃Скорость ветра: {wind_speed} м/с')
                await message.answer(text=weather_info, reply_markup=kb.main)
    else:
        await message.reply(f'Пожалуйста, сначала укажите город.')


@dp.message(F.text.lower() == 'погода на 3 дня')
async def cmd_weather_3_days(message: Message):
    global last_city
    if last_city:
        today = datetime.datetime.now()
        dates_to_check = ["📅Завтра", "📅Послезавтра", "📅Через три дня"]
        weather_info = ""

        res = requests.get(f'https://api.openweathermap.org/data/2.5/forecast?q={last_city}&appid={API}&units=metric')
        if res.status_code == 200:
            data = json.loads(res.text)

            for i, date_to_check in enumerate(dates_to_check):
                date_weather = None
                for forecast in data['list']:
                    date_str = forecast['dt_txt'].split()[0]
                    if date_str == (today + datetime.timedelta(days=i + 1)).strftime('%Y-%m-%d'):
                        date_weather = forecast
                        break
                if date_weather:
                    temp = date_weather['main']['temp']
                    temp_like = date_weather['main']['feels_like']
                    pressure = date_weather["main"]["pressure"]
                    wind_speed = date_weather["wind"]["speed"]
                    humidity = date_weather["main"]["humidity"]
                    weather_trans_en = date_weather['weather'][0]['description']
                    weather_trans_ru = weather_mapping.get(weather_trans_en, weather_trans_en)

                    weather_info += f'{date_to_check}: \n🌤️{weather_trans_ru}\n' \
                                    f'🌡️Температура: {temp}°C\n' \
                                    f'🤲Ощущается как: {temp_like}°C\n' \
                                    f'💧Влажность: {humidity}%\n' \
                                    f'🎈Давление: {pressure} мбар\n' \
                                    f'🍃Скорость ветра: {wind_speed} м/с\n\n'

            await message.answer(text=weather_info, reply_markup=kb.main)
    else:
        await message.reply(f'Пожалуйста, сначала укажите город.')


@dp.message()
async def cmd_weather(message: Message):
    global last_city, is_subscribed
    print(last_city)

    if message.text.lower() == 'каждый час':
        is_subscribed = True
        cursor.execute('INSERT OR REPLACE INTO subscriptions (user_id, city, is_subscribed) VALUES (?, ?, ?)',
                       (message.from_user.id, last_city, 1))
        conn.commit()
        await message.answer('Рассылка активирована. Буду присылать погоду каждый час.')
        asyncio.create_task(send_weather_periodically(message.from_user.id))

    elif message.text.lower() == 'стоп':
        is_subscribed = False
        cursor.execute('INSERT OR REPLACE INTO subscriptions (user_id, city, is_subscribed) VALUES (?, ?, ?)',
                       (message.from_user.id, last_city, 0))
        conn.commit()
        await message.answer('Рассылка отключена.')

    else:
        # Текущая погода
        last_city = message.text
        res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={last_city}&appid={API}&units=metric')

        if res.status_code == 200:
            data = json.loads(res.text)
            if "main" in data:
                temp = data["main"]["temp"]
                temp_like = data["main"]["feels_like"]
                pressure = data["main"]["pressure"]
                wind_speed = data["wind"]["speed"]
                humidity = data["main"]["humidity"]
                weather_trans_en = data["weather"][0]["description"]
                weather_trans_ru = weather_mapping.get(weather_trans_en, weather_trans_en)
                weather_info = (f'🌤️Сейчас погода: {weather_trans_ru}\n'
                                f'🌡️Температура: {temp}°C\n'
                                f'🤲Ощущается как: {temp_like}°C\n'
                                f'💧Влажность: {humidity}%\n'
                                f'🎈Давление: {pressure} мбар\n'
                                f'🍃Скорость ветра: {wind_speed} м/с')

                await message.answer(weather_info, reply_markup=kb.main)
                # Проверка на активную рассылку
                if is_subscribed:
                    await send_weather_periodically(message.from_user.id)

        else:
            await message.reply('Город указан неверно или не найден.')


async def send_weather_periodically(user_id):
    while True:
        # Проверка на активную рассылку
        cursor.execute('SELECT is_subscribed, city FROM subscriptions WHERE user_id = ?', (user_id,))
        is_subscribed_db, city = cursor.fetchone()
        if not is_subscribed_db:
            break
        last_city = city
        res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={last_city}&appid={API}&units=metric')

        if res.status_code == 200:
            data = json.loads(res.text)
            if "main" in data:
                temp = data["main"]["temp"]
                temp_like = data["main"]["feels_like"]
                pressure = data["main"]["pressure"]
                wind_speed = data["wind"]["speed"]
                humidity = data["main"]["humidity"]
                weather_trans_en = data["weather"][0]["description"]
                weather_trans_ru = weather_mapping.get(weather_trans_en, weather_trans_en)
                weather_info = (f'🌤️Сейчас погода: {weather_trans_ru}\n'
                                f'🌡️Температура: {temp}°C\n'
                                f'🤲Ощущается как: {temp_like}°C\n'
                                f'💧Влажность: {humidity}%\n'
                                f'🎈Давление: {pressure} мбар\n'
                                f'🍃Скорость ветра: {wind_speed} м/с')

                await bot.send_message(user_id, weather_info)
        await asyncio.sleep(3600)  # Таймер


async def check_and_resume_subscriptions():
    cursor.execute('SELECT user_id, city FROM subscriptions WHERE is_subscribed = 1')
    subscribed_users = cursor.fetchall()
    for user in subscribed_users:
        user_id, city = user
        last_city = city
        asyncio.create_task(send_weather_periodically(user_id))


async def main():
    await check_and_resume_subscriptions()  # Проверка рассылки на актуальность при запуке
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Выход')
