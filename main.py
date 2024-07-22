import os, logging, telebot, time, gspread, re
from datetime import datetime, timedelta
from pprint import pprint
from threading import Thread
from telebot import types
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import telebot_calendar
from flask import Flask, request, Response

app = Flask(__name__)


def get_timestamp():
    timestamp = time.strftime("%Y-%m-%d %X")
    return timestamp


# pylint --reports=y text main.py
# https://api.telegram.org/_/setwebhook?url=https://6109-85-93-60-23.ngrok-free.app
@app.route('/', methods=['POST', 'GET'])
def index():
    try:
        if request.headers.get('Content-Type') == 'application/json':
            update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
            bot.process_new_updates([update])
            return Response('ok', status=200)
        else:
            return Response('Invalid')
    except Exception as e:
        print("[X]", get_timestamp(), "Error:\n>", e)
        return "Error", 400


API_TOKEN = "_"
logging.basicConfig(level=logging.INFO, filename="py_log.log", filemode="w")
logging.debug("A DEBUG Message")
logging.info("An INFO")
logging.warning("A WARNING")
logging.error("An ERROR")
logging.critical("A message of CRITICAL severity")
telebot.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot(API_TOKEN)

# Указываем путь к JSON
gc = gspread.service_account(filename='beautysaloon.json')
# Открываем тестовую таблицу
sh = gc.open_by_key('_')

print('start bot')


# Создаем приветствие с выбором меню
@bot.message_handler(commands=['start'])
def start(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Посмотреть работы \U0001FABD", callback_data='my_jobs'))
    keyboard.add(InlineKeyboardButton("Запись на процедуру \U0001F4C3", callback_data='CALENDAR'))
    keyboard.add(InlineKeyboardButton("Price List \U0001F4B8", callback_data='price'))
    keyboard.add(InlineKeyboardButton("Посмотреть мои записи \U0001F4D6", callback_data='my_notes'))
    keyboard.add(InlineKeyboardButton("Контакты \U0001F4F1", callback_data='contacts'))
    bot.send_message(message.chat.id,
                     'Привет , я Маша 🌷\n\nИ это мой телеграмм бот для записи ко мне на наращивание ресниц  🌿')
    bot.send_message(message.chat.id, 'Выберите действие \U0001F447', reply_markup=keyboard)


# обрабатка кнопки главное меню
@bot.callback_query_handler(func=lambda call: call.data.startswith("menu"))
def callback_inline(call: CallbackQuery):
    if call.data == "menu":
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Посмотреть работы \U0001FABD", callback_data='my_jobs'))
        keyboard.add(InlineKeyboardButton("Запись на процедуру \U0001F4C3", callback_data='CALENDAR'))
        keyboard.add(InlineKeyboardButton("Price List \U0001F4B8", callback_data='price'))
        keyboard.add(InlineKeyboardButton("Посмотреть мои записи \U0001F4D6", callback_data='my_notes'))
        keyboard.add(InlineKeyboardButton("Контакты \U0001F4F1", callback_data='contacts'))
        bot.send_message(
            chat_id=call.from_user.id,
            text=f"Вы вернулись в главное меню",
            reply_markup=keyboard,
        )


# функция перевода даты в день недели
def get_day_of_week(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
        day_of_week = date_obj.weekday()
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        return days[day_of_week]
    except ValueError:
        return "Invalid date format. Please use dd.mm.YYYY."


lst_date = []
lst = []
lst_work_date = []
# Creates a unique calendar
# calendar = Calendar(language=RUSSIAN_LANGUAGE)
calendar_1_callback = telebot_calendar.CallbackData("calendar_1", "action", "year", "month", "day")

worksheet_list = sh.worksheets()

# распарсиваем листы для проверки на записи
def parse_list_of_dicts(list_of_dicts):
    result = []
    for d in list_of_dicts:
        parsed_dict = {}
        for key, value in d.items():
            try:
                parsed_value = eval(value)  # Попытка преобразования строки валидного Python выражения в значение
            except NameError:
                parsed_value = value  # Если не получилось преобразовать значение, оставляем его как строку
            parsed_dict[key] = parsed_value
        result.append(parsed_dict)
    return result
@bot.callback_query_handler(func=lambda call: call.data.startswith("CALENDAR"))
def callback_inline(call: CallbackQuery):
    """
    Catches a message with the command "start" and sends the calendar

    :return:
    """
    if call.data == "CALENDAR":
        now = datetime.now()  # Get the current date
        count_user = 0
        pattern_search = str(call.from_user.id)

        # проверка свободных дат
        for i in worksheet_list:
            worksheet = sh.worksheet(i.title)
            list_of_dicts = worksheet.get_all_records()
            formatdate = datetime.strptime(i.title, '%d.%m.%Y').date()
            pprint(list_of_dicts)
            for l in list_of_dicts:
                print(l)
                for k, v in l.items():
                    print(v)
                    if v == pattern_search:
                        count_user += 1
                        if count_user >= 2:
                            bot.send_message(
                                        chat_id=call.from_user.id,
                                        text=f"Внимание!!! вы достигли лимита на запись (не более 2)",
                                        reply_markup=menu_and_buck())
                            break
                    if formatdate >= datetime.now().date() and v == "None":
                        lst.append(formatdate)
                        if i not in lst_work_date:
                            lst_work_date.append(i.title)

            formatdate = datetime.strptime(i.title, '%d.%m.%Y').date()
            if formatdate >= datetime.now().date():
                if i.find("None") == None:
                    lst.append(formatdate)
                    if i not in lst_work_date:
                        lst_work_date.append(i.title)

            pprint(list_of_dicts)
            print(worksheet)
            formatdate = datetime.strptime(i.title, '%d.%m.%Y').date()
            if i.find(pattern_search) == True:
                count_user += 1
                if count_user >= 2:
                    bot.send_message(
                        chat_id=call.from_user.id,
                        text=f"Внимание!!! вы достигли лимита на запись (не более 2)",
                        reply_markup=menu_and_buck())
                    break
            if formatdate >= datetime.now().date():
                if i.find("None") == None:
                    lst.append(formatdate)
                    if i not in lst_work_date:
                        lst_work_date.append(i.title)
        count_days = timedelta(days=31)
        end_date = datetime.now() + count_days
        worksheet = sh.get_worksheet(0)
        for i in range((end_date - datetime.now()).days):
            current_date = datetime.today() + timedelta(days=i)
            formatted_date = current_date.strftime('%d.%m.%Y')
            print(173, formatted_date)
            if formatted_date not in lst_work_date:
                worksheet = sh.worksheet("26.01.2024")
                worksheet.copy_to(sh.id)
                print(122, worksheet)
                start_dates = "26.01.2024" + " (копия)"
                print(124)
                worksheet = sh.worksheet(start_dates)
                print(126, worksheet)
                worksheet.update_title(formatted_date)
                if get_day_of_week(formatted_date) == 'Вс':
                    # Обновление значения ячеек H1 и I1
                    worksheet.update_cell(1, 4, '11:00')  # D1
                    worksheet.update_cell(1, 5, '14:00')  # E1
                    # Цикл для обновления значений в столбце I от строки 2 до строки 7
                    for i in range(2, 8):
                        worksheet.update_cell(i, 5, '')  # Пустое значение в столбце I
                        worksheet.update_cell(i, 4, '')
                        worksheet.update_cell(i, 8, 1)

        # Получить  значения из ячеек
        cells = [(worksheet.cell(2, i).value, worksheet.cell(1, i).value, f'time1{i}') for i in range(3, 9)]
        print(cells)
        lst_work = [cell[0] for cell in cells]
        print(189, lst_work)
        print(190, worksheet_list)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Выбери доступную дату:\n ✅ - есть свободное время',
            reply_markup=telebot_calendar.create_calendar(
                name=calendar_1_callback.prefix,
                year=now.year,
                month=now.month,
                lst_current_date=lst
                # Specify the NAME of your calendar
            )
        )


# обработка выбранной даты календаря
@bot.callback_query_handler(
    func=lambda call: call.data.startswith(calendar_1_callback.prefix)
)
def callback_inline(call: CallbackQuery):
    """
    Обработка inline callback запросов
    :param call:
    :return:
    """

    # At this point, we are sure that this calendar is ours. So we cut the line by the separator of our calendar
    name, action, year, month, day = call.data.split(calendar_1_callback.sep)
    # Processing the calendar. Get either the date or None if the buttons are of a different type
    date = telebot_calendar.calendar_query_handler(
        bot=bot, call=call, name=name, action=action, year=year, month=month, day=day, lst_currant_date=lst
    )
    # There are additional steps. Let's say if the date DAY is selected, you can execute your code. I sent a message.
    if action == "DAY":
        current_date = datetime.now()
        # Прибавляем интервал  времени
        result_date = date + timedelta(hours=current_date.hour, minutes=current_date.minute + 5,
                                       seconds=current_date.second)

        # elif result_date.date() > current_date_now and not all(lst_work):
        #     buttons = [types.InlineKeyboardButton(text=val[1], callback_data=val[2]) for val in cells if
        #                val[0] is None]
        #     buttons.extend([types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
        #                     types.InlineKeyboardButton(text="Назад", callback_data='CALENDAR')])
        #     keyboard = types.InlineKeyboardMarkup(row_width=2)
        #     keyboard.add(*buttons)
        #     bot.send_message(
        #         chat_id=call.from_user.id,
        #         text=f"Вы выбрали дату: {date.strftime('%d.%m.%Y')}, выберите время для записи \U0001F553",
        #         reply_markup=keyboard,
        #     )
        #
        # elif result_date.strftime('%d.%m.%Y') == current_date.strftime('%d.%m.%Y'):
        #     buttons = []
        #     for val in cells:
        #         date_string = val[1]
        #     date_format = "%H:%M"
        #     date_object = datetime.strptime(date_string, date_format).hour
        #     current_date_hour = datetime.now().hour
        #     if date_object > current_date_hour and date_object - current_date_hour > 2 and val[0] is None:
        #         buttons.append(types.InlineKeyboardButton(text=val[1], callback_data=val[2]))
        #         buttons.extend([types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
        #                         types.InlineKeyboardButton(text="Назад", callback_data='CALENDAR')])
        #         keyboard = types.InlineKeyboardMarkup(row_width=2)
        #         keyboard.add(*buttons)
        #         bot.send_message(
        #             chat_id=call.from_user.id,
        #             text=f"Вы выбрали дату: {date.strftime('%d.%m.%Y')}, выберите время для записи \U0001F553",
        #             reply_markup=keyboard,
        #         )
        #
        #     else:
        #         bot.send_message(
        #             chat_id=call.from_user.id,
        #             text=f"На выбранную вами дату: {date.strftime('%d.%m.%Y')}, заняты все места",
        #             reply_markup=menu_and_buck(),
        #         )
        #


# генерация клавиатуры подтверждения записи
def get_yes_no_keyboard():
    buttons = [
        types.InlineKeyboardButton(text="Да", callback_data='yes'),
        types.InlineKeyboardButton(text="Нет", callback_data='no'),
        types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
        types.InlineKeyboardButton(text="Назад", callback_data='know_')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    return keyboard


def menu_and_buck():
    buttons = [
        types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
        types.InlineKeyboardButton(text="Назад", callback_data='menu')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    return keyboard


def time_date(name):
    worksheet = sh.worksheet(lst_date[-1])
    time_lst.append(name)
    valc1 = worksheet.cell(1, 3).value
    vald1 = worksheet.cell(1, 4).value
    vale1 = worksheet.cell(1, 5).value
    valf1 = worksheet.cell(1, 6).value
    valg1 = worksheet.cell(1, 7).value
    valh1 = worksheet.cell(1, 8).value
    coord1 = {'time13': ('C2', valc1),
              'time14': ('D2', vald1),
              'time15': ('E2', vale1),
              'time16': ('F2', valf1),
              'time17': ('G2', valg1),
              'time18': ('H2', valh1)}
    return coord1[name]


# временная переменная
key_value = {'time10': ('C2', '10.00')}
name_lst = []
time_lst = []


# обрабатываем кнопки времени
@bot.callback_query_handler(func=lambda call: call.data.startswith("time"))
def callback_inline(call: CallbackQuery):
    key_value['time10'] = time_date(call.data)
    buttons = [
        types.InlineKeyboardButton(text="\U0001F4CD 1D (натуральный эффект) - 800 руб\n", callback_data='service_1d'),
        types.InlineKeyboardButton(text="\U0001F4CD️ 2D (мокрый лиса, кукла) - 950 руб\n", callback_data='service_2d'),
        types.InlineKeyboardButton(text="\U0001F4CD 3D (кайли, лиса, кукла) - 1000 руб\n", callback_data='service_3d'),
        types.InlineKeyboardButton(text="\U0001F4CD Ламинирование - 2000 руб\n", callback_data='service_lamination'),
        types.InlineKeyboardButton(text="\U0001F4CD️ Коррекция ресниц - 650 руб\n", callback_data='service_correction'),
        types.InlineKeyboardButton(text="* снятие чужой работы - 150 руб\n", callback_data='service_remove'),
        types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
        types.InlineKeyboardButton(text="Назад", callback_data='CALENDAR')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)

    bot.send_message(
        chat_id=call.from_user.id,
        text=f"Выберите услугу:",
        reply_markup=keyboard
    )
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.delete_message(call.message.chat.id, call.message.message_id)


key_service = {}


# обрабатка кнопопки услуга
@bot.callback_query_handler(func=lambda call: call.data.startswith("service_"))
def callback_inline(call: CallbackQuery):
    buttons = [
        types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
        types.InlineKeyboardButton(text="Назад", callback_data=time_lst[-1])
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    if call.data == 'service_1d':
        key_service['Услуга'] = '1D (натуральный эффект)'
    elif call.data == 'service_2d':
        key_service['Услуга'] = '2D (мокрый лиса, кукла)'
    elif call.data == 'service_3d':
        key_service['Услуга'] = '3D (кайли, лиса, кукла)'
    elif call.data == 'service_lamination':
        key_service['Услуга'] = 'ламинирование'
        key_service['Изгиб'] = ' '
        key_service['Что еще нужно'] = ' '
        buttons = [
            types.InlineKeyboardButton(text="Повышенная чувствительность глаз", callback_data='know_eye'),
            types.InlineKeyboardButton(text="Контактные линзы", callback_data='know_lenses'),
            types.InlineKeyboardButton(text="Тонкие и ломкие ресницы", callback_data='know_brittle'),
            types.InlineKeyboardButton(text="Беременность", callback_data='know_pregnancy'),
            types.InlineKeyboardButton(text="Лактация", callback_data='know_loctation'),
            types.InlineKeyboardButton(text="Аллергический ринит", callback_data='know_rhinitis'),
            types.InlineKeyboardButton(text="Конъюктивит", callback_data='know_conjunctivitis'),
            types.InlineKeyboardButton(text="Другое", callback_data='other'),
            types.InlineKeyboardButton(text="Ничего не нужно", callback_data='know_not'),
            types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
            types.InlineKeyboardButton(text="Назад", callback_data='bending_')
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*buttons)
        bot.send_message(
            chat_id=call.from_user.id,
            text=f"Выберите что важно учесть:",
            reply_markup=keyboard
        )
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif call.data == 'service_remove':
        key_service['Услуга'] = 'снятие чужой работы'
        key_service['Изгиб'] = ' '
        key_service['Что еще нужно'] = ' '
        buttons = [
            types.InlineKeyboardButton(text="Повышенная чувствительность глаз", callback_data='know_eye'),
            types.InlineKeyboardButton(text="Контактные линзы", callback_data='know_lenses'),
            types.InlineKeyboardButton(text="Тонкие и ломкие ресницы", callback_data='know_brittle'),
            types.InlineKeyboardButton(text="Беременность", callback_data='know_pregnancy'),
            types.InlineKeyboardButton(text="Лактация", callback_data='know_loctation'),
            types.InlineKeyboardButton(text="Аллергический ринит", callback_data='know_rhinitis'),
            types.InlineKeyboardButton(text="Конъюктивит", callback_data='know_conjunctivitis'),
            types.InlineKeyboardButton(text="Другое", callback_data='other'),
            types.InlineKeyboardButton(text="Ничего не нужно", callback_data='know_not'),
            types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
            types.InlineKeyboardButton(text="Назад", callback_data='bending_')
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*buttons)
        bot.send_message(
            chat_id=call.from_user.id,
            text=f"Выберите что важно учесть:",
            reply_markup=keyboard
        )
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data == 'service_correction':
        key_service['Услуга'] = 'коррекция ресниц'
        key_service['Изгиб'] = ' '
        key_service['Что еще нужно'] = ' '
        buttons = [
            types.InlineKeyboardButton(text="Повышенная чувствительность глаз", callback_data='know_eye'),
            types.InlineKeyboardButton(text="Контактные линзы", callback_data='know_lenses'),
            types.InlineKeyboardButton(text="Тонкие и ломкие ресницы", callback_data='know_brittle'),
            types.InlineKeyboardButton(text="Беременность", callback_data='know_pregnancy'),
            types.InlineKeyboardButton(text="Лактация", callback_data='know_loctation'),
            types.InlineKeyboardButton(text="Аллергический ринит", callback_data='know_rhinitis'),
            types.InlineKeyboardButton(text="Конъюктивит", callback_data='know_conjunctivitis'),
            types.InlineKeyboardButton(text="Другое", callback_data='other'),
            types.InlineKeyboardButton(text="Ничего не нужно", callback_data='know_not'),
            types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
            types.InlineKeyboardButton(text="Назад", callback_data='bending_')
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*buttons)
        bot.send_message(
            chat_id=call.from_user.id,
            text=f"Выберите что важно учесть:",
            reply_markup=keyboard
        )
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        buttons = [
            types.InlineKeyboardButton(text="D", callback_data='bending_d'),
            types.InlineKeyboardButton(text="L", callback_data='bending_l'),
            types.InlineKeyboardButton(text="C", callback_data='bending_c'),
            types.InlineKeyboardButton(text="M", callback_data='bending_m'),
            types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
            types.InlineKeyboardButton(text="Назад", callback_data=time_lst[-1])
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*buttons)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        bot.send_message(
            chat_id=call.from_user.id,
            text=f"Выберите изгиб:",
            reply_markup=keyboard
        )
        bot.delete_message(call.message.chat.id, call.message.message_id)


# обрабатка кнопопки изгиб
@bot.callback_query_handler(func=lambda call: call.data.startswith("bending_"))
def callback_inline(call: CallbackQuery):
    if call.data == 'bending_d':
        key_service['Изгиб'] = 'D'
    elif call.data == 'bending_l':
        key_service['Изгиб'] = 'L'
    elif call.data == 'bending_c':
        key_service['Изгиб'] = 'M'
    elif call.data == 'bending_m':
        key_service['Изгиб'] = 'C'
    buttons = [
        types.InlineKeyboardButton(text="Добавление цветных ресниц", callback_data='need_сolor'),
        types.InlineKeyboardButton(text="Не нужно", callback_data='need_other'),
        types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
        types.InlineKeyboardButton(text="Назад", callback_data='service_')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.send_message(
        chat_id=call.from_user.id,
        text=f"Выберите что необходимо:",
        reply_markup=keyboard
    )
    bot.delete_message(call.message.chat.id, call.message.message_id)


# обрабатка кнопопки доп. услуги
@bot.callback_query_handler(func=lambda call: call.data.startswith("need_"))
def callback_inline(call: CallbackQuery):
    if call.data == 'need_сolor':
        key_service['Что еще нужно'] = 'Добавление цветных ресниц'
    elif call.data == 'need_other':
        key_service['Что еще нужно'] = 'Не нужно'
    buttons = [
        types.InlineKeyboardButton(text="Повышенная чувствительность глаз", callback_data='know_eye'),
        types.InlineKeyboardButton(text="Контактные линзы", callback_data='know_lenses'),
        types.InlineKeyboardButton(text="Тонкие и ломкие ресницы", callback_data='know_brittle'),
        types.InlineKeyboardButton(text="Беременность", callback_data='know_pregnancy'),
        types.InlineKeyboardButton(text="Лактация", callback_data='know_loctation'),
        types.InlineKeyboardButton(text="Аллергический ринит", callback_data='know_rhinitis'),
        types.InlineKeyboardButton(text="Конъюктивит", callback_data='know_conjunctivitis'),
        types.InlineKeyboardButton(text="Другое", callback_data='other'),
        types.InlineKeyboardButton(text="Ничего не нужно", callback_data='know_not'),
        types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
        types.InlineKeyboardButton(text="Назад", callback_data='bending_')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    bot.send_message(
        chat_id=call.from_user.id,
        text=f"Выберите что важно учесть:",
        reply_markup=keyboard
    )
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.delete_message(call.message.chat.id, call.message.message_id)


# обрабатываем кнопки что важно учесть
@bot.callback_query_handler(func=lambda call: call.data.startswith("know_"))
def callback_inline(call: CallbackQuery):
    buttons = [
        types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
        types.InlineKeyboardButton(text="Назад", callback_data='need_')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    if call.data == 'know_eye':
        key_service['Что важно учесть'] = 'Повышенная чувствительность глаз'
    elif call.data == 'know_lenses':
        key_service['Что важно учесть'] = 'Контактные линзы'
    elif call.data == 'know_brittle':
        key_service['Что важно учесть'] = 'Тонкие и ломкие ресницы'
    elif call.data == 'know_pregnancy':
        key_service['Что важно учесть'] = 'Беременность'
    elif call.data == 'know_loctation':
        key_service['Что важно учесть'] = 'Лактация'
    elif call.data == 'know_rhinitis':
        key_service['Что важно учесть'] = 'Аллергический ринит'
    elif call.data == 'know_conjunctivitis':
        key_service['Что важно учесть'] = 'Конъюктивит'
    elif call.data == 'know_not':
        key_service['Что важно учесть'] = 'Не нужно'
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    if key_service['Услуга'] != 'снятие чужой работы':
        bot.send_message(
            chat_id=call.from_user.id,
            text=f"Вы выбрали время: {key_value['time10'][1]}\n"
                 f"Услуга - {key_service['Услуга']}\n"
                 f"Изгиб - {key_service['Изгиб']}\n"
                 f"Что еще нужно - {key_service['Что еще нужно']}\n"
                 f"Что важно учесть - {key_service['Что важно учесть']}\n"
                 f"Если все верно введите ваше имя и номер телефона:\n"
                 f"Например: Алиса 89199559993",
            reply_markup=keyboard

        )
    else:
        bot.send_message(
            chat_id=call.from_user.id,
            text=f"Вы выбрали время: {key_value['time10'][1]}\n"
                 f"Услуга - {key_service['Услуга']}\n"
                 f"Что важно учесть - {key_service['Что важно учесть']}\n"
                 f"Если все верно введите ваше имя и номер телефона:\n"
                 f"Например: Алиса 89199559993",
            reply_markup=keyboard

        )

    bot.register_next_step_handler(call.message, valid_name_and_number)


@bot.callback_query_handler(func=lambda call: call.data == 'other')
def callback_inline(call: CallbackQuery):
    if call.data == 'other':
        buttons = [
            types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
            types.InlineKeyboardButton(text="Назад", callback_data='know_')
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*buttons)
        bot.send_message(
            chat_id=call.from_user.id,
            text=f"Введите что важно учесть:",
            reply_markup=keyboard
        )
        bot.register_next_step_handler(call.message, save_name)


def save_name(message):
    key_service['Что важно учесть'] = message.text
    bot.reply_to(message, f"Вы выбрали время: {key_value['time10'][1]}\n"
                          f"Услуга - {key_service['Услуга']}\n"
                          f"Изгиб - {key_service['Изгиб']}\n"
                          f"Что еще нужно - {key_service['Что еще нужно']}\n"
                          f"Что важно учесть - {key_service['Что важно учесть']}\n"
                          f"Если все верно введите ваше имя и номер телефона:\n"
                          f"Например: Алиса 89199559993")
    bot.register_next_step_handler(message, valid_name_and_number)


# проверка текста на соответствие имени и даты
def valid_name_and_number(message_any):
    regex = r'^[А-ЯЁа-яё]+\s(8|\+7)\d{10}$'
    result = re.findall(regex, message_any.text)
    if len(lst_date) > 0:
        if result:
            name_lst.append(message_any.text)
            bot.send_message(
                chat_id=message_any.from_user.id,
                text=f'Вы хотите записаться {lst_date[-1]}, на вышеуказанное время?',
                reply_markup=get_yes_no_keyboard(),
            )
            bot.delete_message(chat_id=message_any.from_user.chat.id, message_id=message_any.message.message_id)

        else:
            bot.send_message(
                chat_id=message_any.from_user.id,
                text=f'Вы ввели не верный номер телефона, введите повторно в соответствии с примером "Алиса 89199559993"',
                reply_markup=get_yes_no_keyboard(),
            )


# подтверждение записи в google sheets
@bot.callback_query_handler(func=lambda call: call.data == 'yes')
def callback_inline(call: CallbackQuery):
    if call.data == "yes":
        worksheet = sh.worksheet(lst_date[-1])
        user_id = call.from_user.id
        alphabet_key = key_value['time10'][0][0]
        val_user = alphabet_key + '2'
        worksheet.update(val_user, name_lst[-1])
        val_user_id = alphabet_key + '3'
        worksheet.update(val_user_id, user_id)
        val_service = alphabet_key + '4'
        worksheet.update(val_service, key_service['Услуга'])
        val_bending = alphabet_key + '5'
        val = worksheet.acell(key_value['time10'][0]).value
        try:
            worksheet.update(val_bending, key_service['Изгиб'])
            val_need = alphabet_key + '6'
            worksheet.update(val_need, key_service['Что еще нужно'])
            val_take = alphabet_key + '7'
            worksheet.update(val_take, key_service['Что важно учесть'])
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
            # bot.send_message(
            #     chat_id=6074853744,
            #     text=f"К тебе записалась {call.from_user.id}, {lst_date[-1]}, в {key_value['time10'][1]}, {val}, услуга: {key_service['Услуга']} не забудь посмотреть свой график \U0001F63D",
            #     reply_markup=menu_and_buck()
            # )
            # bot.send_message(
            #     chat_id=call.from_user.id,
            #     text=f"Запись, {lst_date[-1]}, в {key_value['time10'][1]}, {val}\n\nЖду тебя ❤️\n\nПо адресу : ул.Зеленая 12 Г ( ТЦ Рубин 💎) \n* 2 этаж , направо , самый последний кабинет с левой стороны.",
            # )
            # bot.send_photo(call.message.chat.id, photo=open(f"trends_photo/image2.jpg", 'rb'),
            #                reply_markup=menu_and_buck())

        except Exception as e:
            pass
            # bot.send_message(
            #     chat_id=6074853744,
            #     text=f"К тебе записалась {call.from_user.id}, {lst_date[-1]}, в {key_value['time10'][1]}, {val}, услуга: {key_service['Услуга']} не забудь посмотреть свой график \U0001F63D",
            #     reply_markup=menu_and_buck()
            # )
            # bot.send_message(
            #     chat_id=call.from_user.id,
            #     text=f"Запись, {lst_date[-1]}, в {key_value['time10'][1]}, {val}\n\nЖду тебя ❤️\n\nПо адресу : ул.Зеленая 12 Г ( ТЦ Рубин 💎) \n* 2 этаж , направо , самый последний кабинет с левой стороны.",
            #     reply_markup=menu_and_buck(),
            # )
            # bot.send_photo(call.message.chat.id, photo=open(f"trends_photo/image2.jpg", 'rb'),
            #                reply_markup=menu_and_buck())


# отмена записи в google sheets
@bot.callback_query_handler(func=lambda call: call.data == 'no')
def callback_inline(call: CallbackQuery):
    try:
        if call.data == "no":
            worksheet = sh.worksheet(lst_date[-1])
            worksheet.update(values=key_value['time10'][0], range_name='')
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
            bot.send_message(
                chat_id=call.from_user.id,
                text=f"Запись отменена",
                reply_markup=menu_and_buck(),
            )
            bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        bot.send_message(
            chat_id=call.from_user.id,
            text='Хотите вернуться в главное меню?',
            reply_markup=menu_and_buck(),
        )


alphabet = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J', 10: 'K', 11: 'L'}

dct_val = {}


# получение всех своих записей по id
@bot.callback_query_handler(func=lambda call: call.data == 'my_notes')
def callback_inline(call: CallbackQuery):
    if call.data == "my_notes":
        worksheets = sh.worksheets()
        datetime_object_now = datetime.now()
        user_id = call.from_user.id
        for worksheet in worksheets:
            date_obj = datetime.strptime(worksheet.title, '%d.%m.%Y')
            if date_obj >= datetime_object_now:
                values_list = worksheet.row_values(3)
                if len(values_list) > 0:
                    for val in enumerate(values_list):
                        if val[1] == str(user_id):
                            coordinate_alphabet = alphabet[val[0]] + '1'
                            val_time = worksheet.acell(coordinate_alphabet).value
                            dct_val.setdefault(date_obj.strftime('%d.%m.%Y'), []).append(val_time)

        if dct_val:
            lst_button = []
            markup = types.InlineKeyboardMarkup(row_width=2)
            for date, times in dct_val.items():
                # Create a callback query button for each date
                lst_button.append(types.InlineKeyboardButton(date, callback_data='date_' + date))
            lst_button.extend([
                types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
                types.InlineKeyboardButton(text="Назад", callback_data='menu')
            ])
            markup.add(*lst_button)
            bot.send_message(
                chat_id=call.from_user.id,
                text=f"Вы записаны на следующие даты: \U0001F4D6",
                reply_markup=markup,
            )
        else:
            bot.send_message(
                chat_id=call.from_user.id,
                text=f"У вас нет записей \U0001F4D6",
                reply_markup=menu_and_buck(),
            )


@bot.callback_query_handler(func=lambda call: call.data.startswith('date_'))
def handle_date_callback(call):
    date = call.data.split('_')[1]
    times = dct_val[date]
    lst_button = []
    for t in times:
        lst_button.append(types.InlineKeyboardButton(t, callback_data='vrem_' + t))
    lst_button.append(types.InlineKeyboardButton(text="В главное меню", callback_data='menu'))
    lst_button.append(types.InlineKeyboardButton(text="Назад", callback_data='my_notes'))
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(*lst_button)
    bot.edit_message_text(f"На дату {date} у вас есть следющие записи", call.message.chat.id, call.message.message_id,
                          reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('vrem'))
def handle_time_callback(call):
    times = call.data.split('_')[1]
    # Send a message with the selected time
    bot.send_message(
        chat_id=call.from_user.id,
        text=f'Вы записаны на: {times}',
        reply_markup=menu_and_buck(),
    )


@bot.callback_query_handler(func=lambda call: call.data == 'my_jobs')
def handle_time_callback(call):
    buttons = [
        types.InlineKeyboardButton(text="В главное меню", callback_data='menu'),
        types.InlineKeyboardButton(text="Назад", callback_data='menu')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    bot.send_message(chat_id=call.from_user.id,
                     text=f"Инстаграм : https://instagram.com/lashmaker_mary_19\n"
                          f"VK : https://vk.com/club224237512",
                     reply_markup=keyboard)


# обработка кнопки контакты
@bot.callback_query_handler(func=lambda call: call.data == 'contacts')
def handle_time_callback(call):
    bot.send_message(
        chat_id=call.from_user.id,
        text=f"📞 Мой номер телефона: 8-912-365-31-24\n"
             f"📷 Подписывайся на мой Instagram: https://instagram.com/lashmaker_mary_19\n"
             f"🌐 Мой ВКонтакте: https://vk.com/id500472844\n",
        reply_markup=menu_and_buck()
    )


# обработка кноки цен
@bot.callback_query_handler(func=lambda call: call.data == 'price')
def handle_time_callback(call):
    markup = telebot.types.InlineKeyboardMarkup()
    back = telebot.types.InlineKeyboardButton('Назад', callback_data='buck')
    menu = types.InlineKeyboardButton(text="В главное меню", callback_data='menu')
    trends = types.InlineKeyboardButton(text="Тренды 2024", callback_data='trends')
    markup.row(trends, back, menu)
    bot.send_message(
        chat_id=call.from_user.id,
        text=f"\U0001F4CD 1D (натуральный эффект) - 1000 руб\n\n"
             f"\U0001F4CD️ 2D (мокрый лиса, кукла) - 1200 руб\n\n"
             f"\U0001F4CD 3D (кайли, лиса, кукла) - 1400 руб\n\n"
             f"\U0001F4CD️ лучи  + 500 руб\n\n"
             f"\U0001F4CD️ Коррекция ресниц - 700 руб\n\n"
             f" * снятие чужой работы - 300 руб\n\n",
        reply_markup=markup
    )


# Путь к папке с картинками
photo_path_trends = 'trends_photo'

# Получение списка файлов с картинками
images_trends = [file for file in os.listdir(photo_path_trends) if file.endswith('.jpg')]

current_index_trends = 0


@bot.callback_query_handler(func=lambda call: call.data == 'trends')
def handle_time_callback(call):
    show_image_trends(call.message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data in ['first', 'two'])
def change_image(callback_query):
    global current_index_trends
    if callback_query.data == 'prev':
        current_index_trends = (current_index_trends - 1) % len(images_trends)
    else:
        current_index_trends = (current_index_trends + 1) % len(images_trends)
    show_image_trends(callback_query.message.chat.id)
    bot.answer_callback_query(callback_query.id)


def show_image_trends(chat_id):
    image = images_trends[current_index_trends]
    markup = telebot.types.InlineKeyboardMarkup()
    prev_button = telebot.types.InlineKeyboardButton('Назад', callback_data='first')
    next_button = telebot.types.InlineKeyboardButton('Вперед', callback_data='two')
    menu = types.InlineKeyboardButton(text="В главное меню", callback_data='menu')
    markup.row(prev_button, next_button, menu)
    bot.send_photo(chat_id, photo=open(f"trends_photo/{image}", 'rb'), reply_markup=markup)


# создаем напоминание пользователям о записи
def obnulenie():
    while True:
        time.sleep(24 * 60 * 60)
        # выбираем следующий день
        worksheet_list = sh.worksheets()
        lst_work = [i.title for i in worksheet_list]
        date_now = datetime.now()
        new_date = date_now + timedelta(days=1)
        next_day = new_date.strftime('%d.%m.%Y')
        if next_day in lst_work:
            worksheet = sh.worksheet(next_day)
            values_list = worksheet.row_values(3)  # выбираем третью строку в дате
            for val in enumerate(values_list):
                if val[1] != '' and val[1] != '   id_пользователя':
                    chat_id = int(val[1])
                    coordinate_alphabet = alphabet[val[0]] + '1'
                    val_time = worksheet.acell(coordinate_alphabet).value
                    bot.send_message(
                        chat_id=chat_id,
                        text=f"Вы записаны в {val_time}"
                    )


thread1 = Thread(target=obnulenie, args=())  # создаём поток
thread1.start()  # запускаем поток

if __name__ == '__main__':
    app.run(debug=True)
    # bot.remove_webhook()
    # bot.set_webhook(url='194.87.199.180:8443', certificate=open('url_cert.pem', 'rb'))
    # app.run(host='0.0.0.0', port=8443, ssl_context=('url_cert.pem', 'usrl_private.key'))
