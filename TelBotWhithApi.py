import telebot
import sqlite3
import datetime
import time
import threading
import requests

TOKEN = ''
bot = telebot.TeleBot(TOKEN)
RusArr= {1:2, 2:3, 3:4 , 4:5 , 5:6 ,6:7, 7:1}
today = datetime.datetime.today().weekday()


def user_chat_id_try(message):
    conn = sqlite3.connect('scheduledb.db')
    cursor = conn.cursor()
    user_chat_id = message.chat.id

    chat_id_try = cursor.execute("SELECT * FROM `users` WHERE user_chat_id =(?)", (user_chat_id,)).fetchone()
    if chat_id_try == None:
        cursor.execute("INSERT INTO users (user_chat_id,username) VALUES ('%s','%s')" % (user_chat_id, message.chat.username))

    notification_try = cursor.execute("SELECT * FROM `notification` WHERE user_chat_id =(?)", (user_chat_id,)).fetchone()
    if notification_try == None:
        cursor.execute("INSERT INTO notification (user_chat_id) VALUES ('%s')" % (user_chat_id,))

    conn.commit()
    conn.close()
    return user_chat_id


#########################################################################################################################
#########################################################################################################################
# Ф-я авто-уведомлений

def timeCheck ():
    conn = sqlite3.connect('scheduledb.db')
    cursor = conn.cursor()
    while True:
        currtime = datetime.time( datetime.datetime.now().time().hour,  datetime.datetime.now().time().minute)
        user_chat_ids =  cursor.execute('SELECT user_chat_id FROM `notification` WHERE time_n=(?)',(str(currtime),))
        user_chat_ids = user_chat_ids.fetchall()
        for user_chat_id in user_chat_ids :
                if user_chat_id != None and user_chat_id != '':
                    txt = showDay(RusArr[today+1], user_chat_id)
                    bot.send_message(user_chat_id, '<b>Авто-нагадування</b>\n\n' +txt, parse_mode="HTML")
        time.sleep(60)
    conn.close()
tChThr = threading.Thread(target=timeCheck, name='tchThr')
tChThr.start()
#
# #
# # ##########################################################################################################################################
# # ##########################################################################################################################################
# # # Ф-я для вывода пар на определенный день


def showDay(day, user_chat_id) :
    if day >6 :
        day=1
    conn = sqlite3.connect('scheduledb.db')
    cursor = conn.cursor()
    user_group = ((cursor.execute("SELECT user_group  FROM `users` WHERE user_chat_id =(?)", (user_chat_id,))).fetchone())[0]
    user_group_lessons = requests.get('https://api.rozklad.org.ua/v2/groups/{0}/timetable'.format(user_group)).json()
    if (user_group_lessons["statusCode"] == 200):
        week = requests.get('http://api.rozklad.org.ua/v2/weeks').json()
        lessons_day = user_group_lessons["data"]["weeks"][str(week['data'])]["days"][str(day)]
        text_for_send = "<b> - {0} - </b>\n".format(lessons_day["day_name"])
        for lesson in lessons_day["lessons"]:
            text_for_send += "{0}) {1}  \n".format(lesson["lesson_number"], lesson["lesson_name"])
            text_for_send += "<code>{0} {1} </code>".format(lesson["lesson_type"], lesson["lesson_room"])
            if len(lesson["teachers"]) != 0:
                teacher = lesson["teachers"][0]
                text_for_send += "<code>{0}</code>\n".format(teacher["teacher_name"])
    else:
        text_for_send = 'Визначте свою групу за домомогою команди -<code> /set БС-62 </code>.'
    conn.close()
    return text_for_send

# # ##########################################################################################################################################
# # ##########################################################################################################################################
#
# # # ф-я позволяет принимает желаемый день и отсылает результат (в командной форме)
@bot.message_handler(commands=['monday','tuesday','wednesday','thursday','friday','saturday'])
def handle_monday(message):
    user_chat_id = user_chat_id_try(message)
    dictOfDays = {'monday':1,'tuesday':2 ,'wednesday':3,'thursday':4,'friday':5 ,'saturday':6 }
    bot.send_message(message.chat.id, showDay(dictOfDays[message.text[1:]], user_chat_id), parse_mode="HTML")

# # # ф-я позволяет принимает команду отсылает рассписание на неделю (в командной форме)
@bot.message_handler(commands=['all'])
def handle_all(message):
    user_chat_id = user_chat_id_try(message)
    conn = sqlite3.connect('scheduledb.db')
    cursor = conn.cursor()
    user_group = ((cursor.execute("SELECT user_group  FROM `users` WHERE user_chat_id =(?)", (user_chat_id,))).fetchone())[0]
    user_group_lessons = requests.get('https://api.rozklad.org.ua/v2/groups/{0}/timetable'.format(user_group))
    user_group_lessons = user_group_lessons.json()
    if( user_group_lessons['statusCode'] == 200):
        for week in range(1,3):
            text = '<b>Розклад групи - {0} -</b>\n\n'.format(user_group_lessons['data']['group']['group_full_name'], )
            text +='<b>Неділя - {0}</b>'.format(week) +'\n'
            lessons_days = user_group_lessons['data']['weeks'][str(week)]['days']
            for day in range(1,7):
                lessons_day = lessons_days[str(day)]
                lessons = lessons_day['lessons']
                if len(lessons)== 0 :
                    continue
                text += lessons_day['day_name'] + '\n'
                for lesson in lessons:
                    text += "{0}) {1}  \n".format(lesson["lesson_number"],lesson["lesson_name"])
                    text += "- <code>{0} {1} </code>".format(lesson["lesson_type"],lesson["lesson_room"])
                    if len(lesson["teachers"])!=0:
                       teacher = lesson["teachers"][0]
                       text += "<code>{0}</code> -\n".format(teacher["teacher_name"])

            text += '\n'
            bot.send_message(user_chat_id, text, parse_mode="HTML")
            text = ''
    else:
        text = 'Визначте свою групу за домомогою команди -<code> /set </code> \nФормат  -<code> /set БС-62 </code>'
        bot.send_message(user_chat_id, text, parse_mode="HTML")
    conn.close()

# # # ф-я позволяет принимает команду отсылает рассписание сегодня  (в командной форме)
@bot.message_handler(commands=['today'])
def handle_all(message):
    user_chat_id  = user_chat_id_try(message)
    text =showDay(RusArr[today] , user_chat_id )
    bot.send_message(user_chat_id ,text, parse_mode= "HTML")
#
# # # ф-я позволяет принимает команду отсылает рассписание завтра (в командной форме)
@bot.message_handler(commands=['tomorrow'])
def handle_all(message):
    user_chat_id = user_chat_id_try(message)
    text =showDay(RusArr[today+1] ,  user_chat_id)
    bot.send_message( user_chat_id,text, parse_mode= "HTML")
#
# # # ф-я позволяет установить время автоуведомлений   (в командной форме)
@bot.message_handler(commands=['settime'])
def handle_all(message):
    txt= message.text[9:14]
    try:
        time = datetime.time(int(txt[0:2]), int(txt[3:5]))
    except ValueError:
        bot.send_message(message.chat.id, '<b>Некоректні дані.</b>\n\nВведіть час у форматі - <code>/settime 21:30</code> . ', parse_mode="HTML")
        return 0
    conn = sqlite3.connect('scheduledb.db')
    cursor = conn.cursor()
    user_chat_id = user_chat_id_try(message)
    cursor.execute("UPDATE notification SET time_n ='{0}' WHERE user_chat_id='{1}'".format(time, user_chat_id))
    conn.commit()
    txt = 'Розклад буде відправлятися щоденно о - <code>{0}:{1}</code>'.format(time.hour,time.minute)
    conn.close()
    bot.send_message(message.chat.id, txt, parse_mode="HTML")

# # # ф-я позволяет увидеть все доступные команды  (в командной форме)
@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id, '/monday - Понеділок \n/tuesday - Вівторок \n/wednesday - Середа \n/thursday  - Четвер \n/friday - П\'ятниця \n/saturday - Субота')

# # ф-я позволяет принимает выбрать группу  (в командной форме)
@bot.message_handler(commands=['set'])
def handle_sunday(message):
    user_chat_id = user_chat_id_try(message)
    group_name = message.text[5:]
    if group_name == '' or None :
        bot.send_message(user_chat_id,'Група не введена\n Формат -<code> /set БС-62 </code>',parse_mode= "HTML")
    else:
        group_inf = requests.get('http://api.rozklad.org.ua/v2/groups/{0}'.format(group_name))
        group_inf = group_inf.json()
        if group_inf['statusCode'] == 200 :
            conn = sqlite3.connect('scheduledb.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET user_group ='{0}' WHERE user_chat_id='{1}'".format(group_inf['data']['group_id'],user_chat_id))
            bot.send_message(user_chat_id,'Вибрана група -<code> {0} </code>\nДля зміни застосуй команду -<code> /set </code> \nУ форматі -<code> /set БС-62 </code>'.format(group_inf['data']['group_full_name'].upper(), ),parse_mode="HTML")
            conn.commit()
            conn.close()
        else:
            bot.send_message(user_chat_id,'Групу <code>"{0}"</code> не знайдено. \nПеревірте введені дані.'.format(group_name, ), parse_mode="HTML")



##########################################################################################################################################
##  Ф-Я ДЛЯ СТАРТА , ПЕРЕДАЕТ КЛАВИАТУРУ И ДАЕТ ПОНЯТЬ ЕСТЬ ЛИ ТЫ В РЕГИСТРЕ  ######################################################################################################################################

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
    user_markup.row('Понеділок', 'Вівторок')
    user_markup.row('Середа', 'Четвер')
    user_markup.row('П\'ятниця', 'Субота ')

    conn = sqlite3.connect('scheduledb.db')
    cursor = conn.cursor()
    user_chat_id = user_chat_id_try(message)

    user_inf = cursor.execute("SELECT *  FROM `users` WHERE user_chat_id =(?)",(user_chat_id,))
    group_id = user_inf.fetchone()[2]
    if group_id == None or group_id=='' :
        group_name = 'Група не обрана'
    else :
        group_inf = requests.get('http://api.rozklad.org.ua/v2/groups/{0}'.format(group_id))
        group_inf = group_inf.json()
        if group_inf['statusCode'] == 200 :
            group_name = group_inf["data"]["group_full_name"]
            group_name = 'Ваша група -<code> {0} </code>'.format(group_name.upper(),)
        else:
            group_name= 'Група не обрана'
    txt = '<b>Вітаю </b>, <code>{0}</code><b> !</b> \n{1} \nДля зміни застосуй команду -<code> /set </code> \nУ форматі -<code> /set БС-62 </code>'.format(message.chat.username, group_name )
    txt = txt +'\n\nФункція автоповідомлення -<code> /settime</code>\nФормат  -<code> /settime 21:30</code>'
    bot.send_message(user_chat_id,txt,reply_markup=user_markup ,parse_mode= "HTML")
    conn.close()

##########################################################################################################################################
##########################################################################################################################################
#
# # # ф-я позволяет принимает команду отсылает рассписание на выбраный день , отправляет ошибку если команда не определена (в текстовой форме)
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_chat_id = user_chat_id_try(message)
    RusArr= {'Понеділок':1, 'Вівторок': 2, 'Середа':3 ,'Четвер': 4, 'П\'ятниця' :5, 'Субота':6}
    if (message.text in RusArr.keys()) :
        bot.send_message(user_chat_id, showDay(RusArr[message.text], user_chat_id), parse_mode="HTML")
    else:
        bot.send_message(user_chat_id, 'Я не знаю що означає <code> "{0}" </code>'.format(message.text, ),parse_mode="HTML")


# ##########################################################################################################################################
# ##########################################################################################################################################

# s = input('-')
# bot.send_message(399127688,'<i>Амин</i> : <code>{0}</code>'.format(s,), parse_mode= "HTML")
bot.polling(none_stop=True)