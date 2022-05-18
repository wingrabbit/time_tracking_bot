import base64
import io

import requests
import telebot
from telebot import types
import datetime
import sqlite3

from telebot.types import InputMediaPhoto

from params import *
from dao import *
from util import *
from PIL import Image

bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start_message(message):
    if user_exists(message.from_user.id):
        bot.send_message(message.chat.id, "Welcome back!")
    else:
        insert_new_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name,
                        message.from_user.username)
        bot.send_message(message.chat.id, "Welcome!")


@bot.message_handler(commands=['buttons'])
def button_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    test_item = types.KeyboardButton("Show controls")
    markup.add(test_item)
    bot.send_message(message.chat.id, "What's up?", reply_markup=markup)


@bot.message_handler(commands=['control'])
def control_message(message):
    text_to_send = "\U0001F984 What's up?"
    if user_has_active_record(message.from_user.id):
        text_to_send += "\nYou have an active task started at "
        text_to_send += get_active_task_start_time(message.from_user.id)
    keyboard = types.InlineKeyboardMarkup()
    btn_start = types.InlineKeyboardButton(text='Start a record', callback_data='newtask')
    btn_end = types.InlineKeyboardButton(text='End a record', callback_data='endtask')
    btn_select_active_project = types.InlineKeyboardButton(text='Select active project', callback_data='selectactiveproject')
    btn_add_project = types.InlineKeyboardButton(text='Add a project', callback_data='addproject')
    btn_add_customer = types.InlineKeyboardButton(text='Add a customer', callback_data='addcustomer')
    btn_get_monthly_task = types.InlineKeyboardButton(text='Get tasks for a month', callback_data='getstats')
    btn_get_monthly_task_with_pictures = types.InlineKeyboardButton(text='Get tasks for a month (pictures)', callback_data='getpicturestats')
    keyboard.row(btn_start, btn_end)
    keyboard.row(btn_select_active_project)
    keyboard.row(btn_add_customer)
    keyboard.row(btn_add_project)
    keyboard.row(btn_get_monthly_task)
    keyboard.row(btn_get_monthly_task_with_pictures)
    bot.send_message(message.chat.id, text_to_send, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: 'newtask' in call.data)
def call_back_newtask(call):
    if not user_has_active_project(call.from_user.id):
        bot.send_message(call.message.chat.id, "No active projects, please create one and try again")
        call_back_addproject(call)
    else:
        if not user_has_active_record(call.from_user.id):
            add_record(call.from_user.id, get_active_project(call.from_user.id))
            bot.send_message(call.message.chat.id, "The record has started!")
        else:
            bot.send_message(call.message.chat.id, "You already have an active record")


@bot.callback_query_handler(func=lambda call: 'endtask' in call.data)
def call_back_endtask(call):
    if not user_has_active_record(call.from_user.id):
        bot.send_message(call.message.chat.id, "You have no active records")
    else:
        bot.send_message(call.message.chat.id, "Please enter the description of your activity")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, finish_task)


def finish_task(call):
    if call.content_type == 'text':
        finish_active_task(call.from_user.id, call.text)
        bot.send_message(call.chat.id, "The record has been stopped")
    elif call.content_type == 'photo':
        finish_active_task(call.from_user.id, call.caption)
        file_id = call.photo[-1].file_id
        file = bot.get_file(file_id)
        photo_url = "https://api.telegram.org/file/bot"+token+"/"+file.file_path
        data = requests.get(photo_url)
        encoded = base64.b64encode(data.content)
        save_photo(call.from_user.id, encoded)
        bot.send_message(call.chat.id, "The record has been stopped (image added to the database)")


@bot.callback_query_handler(func=lambda call: 'addcustomer' in call.data)
def call_back_addcustomer(call):
    bot.send_message(call.message.chat.id, "Please, enter the name of the customer!")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, add_customer)


def add_customer(message):
    insert_new_customer(message.from_user.id, message.text)
    bot.send_message(message.chat.id, "The customer {} has been added".format(message.text))


@bot.callback_query_handler(func=lambda call: 'addproject' in call.data)
def call_back_addproject(call):
    bot.send_message(call.message.chat.id, "Please, enter the name of the project")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, add_project)


def add_project(message):
    new_project_id = insert_new_project(message.from_user.id, message.text)
    set_active_project(message.from_user.id, new_project_id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='No customer', callback_data='assigntocustomer_{}_0'.format(new_project_id)))
    for row in get_customers(message.from_user.id):
        customer_id = row[0]
        customer_name = row[1]
        keyboard.add(types.InlineKeyboardButton(
            text=customer_name, callback_data='assigntocustomer_{}_{}'.format(new_project_id, customer_id)))
    bot.send_message(message.chat.id,
                     "The project {} has been added and selected as active"
                     "\n Pick up the customer for it".format(message.text),
                     reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: 'assigntocustomer_' in call.data)
def call_back_assign_project(call):
    if int(call.data.split('_')[2])==0:
        bot.send_message(call.message.chat.id, "The project has been created without a customer")
    else:
        update_project_with_customer(call.data.split('_')[1], call.data.split('_')[2])
        bot.send_message(call.message.chat.id, "The project has been successfully assigned")


@bot.callback_query_handler(func=lambda call: 'selectactiveproject' in call.data)
def call_back_select_active_project(call):
    keyboard = types.InlineKeyboardMarkup()
    for row in get_projects(call.from_user.id):
        project_id = row[0]
        project_name = row[1]
        keyboard.add(types.InlineKeyboardButton(
            text=project_name, callback_data='activeproject_{}_{}'.format(call.from_user.id, project_id)))
    bot.send_message(call.message.chat.id, "Please select the active project", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: 'activeproject_' in call.data)
def call_back_active_project(call):
    set_active_project(call.data.split('_')[1], call.data.split('_')[2])
    bot.send_message(call.message.chat.id, "The project has been set as active")


@bot.callback_query_handler(func=lambda call: 'getstats' in call.data)
def getmonthlytasks(call):
    months = get_six_months()
    keyboard = types.InlineKeyboardMarkup()
    for row in months:
        month = row[0]
        year = row[1]
        button_text = year + ', '+month
        keyboard.add(types.InlineKeyboardButton(
            text=button_text, callback_data='getmonthlytasksresults_{}_{}_{}'.format(call.from_user.id, month, year)))
    bot.send_message(call.message.chat.id,
                     "Please select a month to check the stats",
                     reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: 'getmonthlytasksresults_' in call.data)
def getmonthlytasksresults(call):
    tasks = get_monthly_projects(call.data.split('_')[1], call.data.split('_')[2], call.data.split('_')[3])
    result = ''
    total_time_spent = 0
    for task in tasks:
        #result = result + 'Task: '+ str(task[4]) +', date: '+ str(task[2])[:10] + ', time spent: ' +str(task[6])
        result = result + "\U0001F984 "+ str(task[4])+"\n"+"\U0001F31C " + str(task[2])[8:10] + "."+ str(task[2])[5:7] +"\n"+"\U000023F1 " #+ str(task[6])

        if task[6] is not None:
            total_time_spent+=int(task[6])
            result+=seconds_to_hours(int(task[6]))
        else:
            result+= ' (still in progress)'
        result+='\n \n'
    result+='\U0001F3DE '+seconds_to_hours(total_time_spent)
    bot.send_message(call.message.chat.id, result)


@bot.callback_query_handler(func=lambda call: 'getpicturestats' in call.data)
def getmonthlytaskswithpictures(call):
    months = get_six_months()
    keyboard = types.InlineKeyboardMarkup()
    for row in months:
        month = row[0]
        year = row[1]
        button_text = year + ', '+month
        keyboard.add(types.InlineKeyboardButton(
            text=button_text, callback_data='getmonthlytasksresultswithpictures_{}_{}_{}'.format(call.from_user.id, month, year)))
    bot.send_message(call.message.chat.id,
                     "Please select a month to check the stats",
                     reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: 'getmonthlytasksresultswithpictures_' in call.data)
def getmonthlytasksresultswithpictures(call):
    tasks = get_monthly_projects_with_images(call.data.split('_')[1], call.data.split('_')[2], call.data.split('_')[3])
    keyboard = types.InlineKeyboardMarkup()
    for task in tasks:
        #result = result + 'Task: '+ str(task[4]) +', date: '+ str(task[2])[:10] + ', time spent: ' +str(task[6])
        task_id = str(task[0])
        description = str(task[1])
        keyboard.add(types.InlineKeyboardButton(
            text=description,
            callback_data='showpicture_{}'.format(task_id)))
    keyboard.add(types.InlineKeyboardButton(
        text='Show all',
        callback_data='showallpictures_{}_{}_{}'.format(call.data.split('_')[1], call.data.split('_')[2], call.data.split('_')[3])))
    bot.send_message(call.message.chat.id,
                     "Please select a task to see the picture",
                     reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: 'showpicture_' in call.data)
def getpicture(call):
    record_id = call.data.split('_')[1]
    img = get_task_image(int(record_id))
    mediagroup = []
    capt = ''
    for data in img:
        mediagroup.append(InputMediaPhoto(base64.b64decode(data[0])))
        #bot.send_photo(call.message.chat.id, base64.b64decode(data[0]))
    bot.send_media_group(call.message.chat.id, mediagroup)

@bot.callback_query_handler(func=lambda call: 'showallpictures_' in call.data)
def getallpictures(call):
    pictures = get_all_monthly_images(call.data.split('_')[1], call.data.split('_')[2], call.data.split('_')[3])
    for pic in pictures:
        bot.send_photo(call.message.chat.id, base64.b64decode(pic[2]), caption=pic[1])


@bot.message_handler(content_types=['photo'])
def add_another_picture(message):
    file_id = message.photo[-1].file_id
    file = bot.get_file(file_id)
    photo_url = "https://api.telegram.org/file/bot" + token + "/" + file.file_path
    data = requests.get(photo_url)
    encoded = base64.b64encode(data.content)
    save_photo(message.from_user.id, encoded)
    bot.send_message(message.chat.id, "Another picture has been added to the recent task")

@bot.message_handler(content_types=['text'])
def get_text_message(message):
    insert_new_message(message.from_user.id, message.text)
    if message.text=="Show controls":
        control_message(message)


bot.infinity_polling()
