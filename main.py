from datetime import datetime
import telebot
from telebot import types
import psycopg2

bot = telebot.TeleBot('8859793608:AAE66WHIKeRf5FtkBapGN9718oAz9LG28OI')

start_end = {
    1: ("09:30", "11:00"),
    2: ("11:00", "12:45"),
    3: ("12:45", "14:30"),
    4: ("14:30", "16:40"),
    5: ("16:55", "18:25"),
    6: ("18:25", "20:10"),
    7: ("20:10", "21:55")}

user_sessions = {}


@bot.message_handler(commands=['start'])
def start_search(message):
    chat_id = message.chat.id
    user_sessions[chat_id] = {}

    building_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    building_markup.add(types.KeyboardButton('Авиамоторная'),types.KeyboardButton('Народное ополчение'))

    bot.send_message(chat_id, f'Здравствуйте, {message.from_user.first_name}! Выберете корпус:', reply_markup=building_markup)
    bot.register_next_step_handler(message, building)


def building(message):
    chat_id = message.chat.id
    user_input = message.text.strip() if message.content_type == 'text' else ''
    user_building ={
        'Авиамоторная': 'А',
        'Народное ополчение': 'Н'
    }

    if user_input in user_building:
        user_sessions[chat_id]['building'] = user_building[user_input]

        date_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        date_markup.add(types.KeyboardButton("Сегодня"))

        bot.send_message(chat_id,f'Нажмите кнопку "Сегодня" или введите дату в формате: ЧЧ.ММ.ГГГГ:',reply_markup=date_markup)
        bot.register_next_step_handler(message, date)

    else:
        bot.send_message(chat_id, 'Ошибка, используйте кнопки!')
        bot.register_next_step_handler(message, building)


def date(message):
    chat_id = message.chat.id
    user_input = message.text.strip() if message.content_type == 'text' else ''

    if user_input.lower() == 'сегодня':
        current_date = datetime.now().strftime("%d.%m.%Y")
        user_sessions[chat_id]['date'] = current_date

    elif user_input:
        try:
            valid_date = datetime.strptime(user_input, "%d.%m.%Y")
            current_date = valid_date.strftime("%d.%m.%Y")
            user_sessions[chat_id]['date'] = current_date
        except ValueError:
            bot.send_message(chat_id, 'Неверный формат даты!')
            bot.register_next_step_handler(message, date)
            return

    else:
         bot.send_message(chat_id, 'Ошибка! Нажмите кнопку "Сегодня" или введите дату в формате: ЧЧ.ММ.ГГГГ:')
         bot.register_next_step_handler(message, date)
         return

    time_type_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    time_type_button = [types.KeyboardButton('По парам'), types.KeyboardButton('Свой промежуток')]
    time_type_markup.add(*time_type_button)
    bot.register_next_step_handler(message, time_type)
    bot.send_message(chat_id, 'Как вам удобно ввести время?', reply_markup=time_type_markup)


def time_type(message):
    chat_id = message.chat.id
    user_input = message.text.strip() if message.content_type == 'text' else ''

    valid_types = ['По парам', 'Свой промежуток']

    if user_input in valid_types:
        if user_input == 'По парам':
            lesson_markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
            lesson_buttons = [types.KeyboardButton(str(lesson)) for lesson in start_end.keys()]
            lesson_markup.add(*lesson_buttons)

            bot.send_message(chat_id, 'Выберите пару:', reply_markup=lesson_markup)
            bot.register_next_step_handler(message, time_lesson)

        elif user_input == 'Свой промежуток':
            bot.send_message(chat_id, 'Введите время в формате ЧЧ:ММ-ЧЧ:ММ', reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, time_user)

    else:
        bot.send_message(chat_id, 'Ошибка, используйте кнопки!')
        bot.register_next_step_handler(message, time_type)


def time_lesson(message):
    chat_id = message.chat.id
    user_input = message.text.strip() if message.content_type == 'text' else ''

    if user_input.isdigit() and int(user_input) in start_end.keys():
        user_sessions[chat_id]['lessons'] = [int(user_input)]

        floor_markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        floor_buttons = [types.KeyboardButton(str(i)) for i in range(1, 6)]
        floor_markup.add(*floor_buttons)
        bot.send_message(chat_id, 'Выберите этаж:', reply_markup=floor_markup)
        bot.register_next_step_handler(message, floor)

    else:
        bot.send_message(chat_id, 'Ошибка, используйте кнопки!')
        bot.register_next_step_handler(message, time_lesson)


def time_to_minutes(time_str):
    parts = time_str.strip().split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    return hours * 60 + minutes


def time_user(message):
    chat_id = message.chat.id
    user_input = message.text.strip() if message.content_type == 'text' else ''
    time_parts = user_input.split('-')

    if len(time_parts) == 2:
        try:
            user_start = time_to_minutes(time_parts[0])
            user_end = time_to_minutes(time_parts[1])

            matched_lessons = []
            for lesson_num, lesson_times in start_end.items():
                lesson_start = time_to_minutes(lesson_times[0])
                lesson_end = time_to_minutes(lesson_times[1])

                if lesson_start < user_end and lesson_end > user_start:
                    matched_lessons.append(lesson_num)

                    user_sessions[chat_id]['lessons'] = matched_lessons

                    floor_markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
                    floor_buttons = [types.KeyboardButton(str(floor_num)) for floor_num in range(1, 6)]
                    floor_markup.add(*floor_buttons)

            bot.send_message(chat_id, 'Выберите этаж:', reply_markup=floor_markup)
            bot.register_next_step_handler(message, floor)

        except Exception:
            bot.send_message(chat_id, 'Ошибка! Проверьте формат (например, 12:00-15:00)')
            bot.register_next_step_handler(message, time_user)

    else:
        bot.send_message(chat_id, 'Ошибка! Проверьте формат (например, 12:00-15:00)')
        bot.register_next_step_handler(message, time_user)


def floor(message):
    chat_id = message.chat.id
    user_input = message.text.strip() if  message.content_type == 'text' else ''

    if user_input in [str(x) for x in range(1, 6)]:
        user_sessions[chat_id]['floor'] = int(user_input)

        size_markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        size_markup.add(types.KeyboardButton('S'), types.KeyboardButton('M'), types.KeyboardButton('L'))
        bot.send_message(chat_id, 'Выберите размер аудитории (S, M, L):', reply_markup=size_markup)
        bot.register_next_step_handler(message, size)

    else:
        bot.send_message(chat_id, 'Ошибка, используйте кнопки!')
        bot.register_next_step_handler(message, floor)


def size(message):
    chat_id = message.chat.id
    user_size = message.text.strip() if message.content_type == 'text' else ''

    if user_size in ['S', 'M', 'L']:
        user_sessions[chat_id]['size'] = user_size
        result(message)

    else:
        bot.send_message(chat_id, 'Ошибка, используйте кнопки!')
        bot.register_next_step_handler(message, size)


def found_free(user_data):
    connection = psycopg2.connect("dbname=visi_db user=semenbarinov password=semenbarinov host=localhost")
    cursor = connection.cursor()

    query = """
        SELECT r.room_id 
        FROM rooms r
        WHERE r.building = %s 
          AND r.floor = %s 
          AND r.size = %s
          AND NOT EXISTS (
              SELECT 1 
              FROM timetable t 
              WHERE t.date = %s 
              AND t.lesson_number = ANY(%s)
              AND r.room_id = ANY(t.busy_rooms)
          );
    """

    cursor.execute(query, (
        user_data['building'],
        user_data['floor'],
        user_data['size'],
        user_data['date'],
        user_data['lessons']))

    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    return [row[0] for row in rows]


def result(message):
    chat_id = message.chat.id
    user_map = {
        'А': 'https://mtuci.ru/map/',
        'Н': 'https://mtuci.ru/map/narod'}
    current_map = user_map[user_sessions[chat_id]['building']]

    free_rooms = found_free(user_sessions[chat_id])
    if free_rooms:
        result_text = 'Свободные аудитории:\n' + '\n'.join(free_rooms)
    else:
        result_text = 'По вашим параметрам свободных аудиторий не найдено.'

    bot.send_message(chat_id, result_text, reply_markup=types.ReplyKeyboardRemove())
    bot.send_message(chat_id, f'Для нового поиска введите /start\nКарта МТУСИ: {current_map}')


@bot.message_handler(commands=['get_map'])
def site (message):
    bot.send_message(message.chat.id, 'Карта МТУСИ:\n' 'Народное ополчение: https://mtuci.ru/map/narod\n' 'Авиамоторная: https://mtuci.ru/map/')


bot.polling(none_stop=True)