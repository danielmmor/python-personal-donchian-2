import logging
import json
import configparser as cfg
import requests
import string
from functools import wraps
from telegram import (InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)
from dbhelper import DBHelper
from functs import Functions


# ------------------ Generic names for states navigation -----------------------

states_codes = [i + j for i in string.ascii_uppercase[:6] for j in string.ascii_lowercase]
num_states = 0
# Menu
x = 6
MENU_RADAR, MENU_TRACK, MENU_PORTF, MENU_INFO, \
    MENU_SET, MENU_HELP = states_codes[:num_states + x]
num_states += x
# Radar
x = 5
RADAR_SM_DAY, RADAR_SM_WEEK, RADAR_MI_DAY, RADAR_MI_WEEK, \
    RADAR_ORDER = states_codes[num_states : num_states + x]
num_states += x
# Tickers tracking
x = 3
TRACK_ADD, TRACK_REM, TRACK_WARN_REM = states_codes[num_states : num_states + x]
num_states += x
# Portfolio
x = 4
PORTF_ADD, PORTF_SUBTR, PORTF_SUBST, PORTF_CLEAR = states_codes[num_states : num_states + x]
num_states += x
# Info
x = 1
INFO = states_codes[num_states : num_states + x]
num_states += x
# Settings
x = 3
SET_TIME, SET_MODE, SET_RISK = states_codes[num_states : num_states + x]
num_states += x
# Time settings
x = 2
TIME_CHANGE, TIME_ACT_DEACT = states_codes[num_states : num_states + x]
num_states += x
# Tracker radar mode settings
x = 4 
MODE_SM_DAY, MODE_SM_WEEK, MODE_MI_DAY, MODE_MI_WEEK = states_codes[num_states : num_states + x]
num_states += x
# Risk management settings
x = 2
RISK_BLOCK, RISK_PERC = states_codes[num_states : num_states + x]
num_states += x
# Help
x = 6
HP_HDIW, HP_NUMS, HP_BUY, HP_SET, \
    HP_CONTACT, HP_SELECT = states_codes[num_states : num_states + x]
num_states += x
# Admin states and initial settings
x = 9
ADMIN_B, ADMIN_C, ADMIN_D, INIT_SET_A, INIT_SET_B, INIT_SET_C, \
    INIT_SET_D, INIT_SET_E, INIT_SET_F = states_codes[num_states : num_states + x]
num_states += x
# Meta states
x = 5
MENU, START_OVER, PREV_LEVEL, EXITING, EXIT = states_codes[num_states : num_states + x]
num_states += x
# Shortcut to ConvHandler.END
STOP = ConversationHandler.END



# ------------------ Bot initialization -----------------------

def read_token(config):
    parser = cfg.ConfigParser()
    parser.read(config)
    return parser.get('creds', 'token')

def init():
    global db, fc, rkr, ADMS_LIST, token
    db = DBHelper()
    fc = Functions()
    rkr = json.dumps({'remove_keyboard':True})
    # ADMINS: [Daniel Moreira]
    ADMS_LIST = [545699841]
    token = read_token('hidden/config.cfg')
    db.setup()

def send_msg(user, msg, msg_id='', reply_markup=''):
    url = f'https://api.telegram.org/bot{token}/sendMessage?' \
          f'chat_id={user}&text={msg}&reply_to_message_id={msg_id}&' \
          f'reply_markup={reply_markup}&parse_mode=HTML'
    requests.get(url)

def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMS_LIST:
            text = 'Unauthorized access'
            send_msg(user_id, text)
            return
        return func(update, context, *args, **kwargs)
    return wrapped


# ------------------ User start and admin control ------------------

def start(update, context):
    user_id = update.message.chat_id
    f_name = update.message.chat.first_name
    l_name = update.message.chat.last_name if update.message.chat.last_name else '-'
    name = (f_name + ' ' + l_name)
    username = update.message.chat.username if update.message.chat.username else '-'
    user_type = update.message.chat.type
    is_bot = update._effective_user.is_bot

    if user_type == 'group' or is_bot:
        context.bot.leaveChat(chat_id=user_id)
    else:
        admin_text, user_text = fc.func_user_start(user_id, name, username)
        send_msg(user_id, user_text)
        send_msg(ADMS_LIST[0], admin_text)

def admin_a(update, context):
    admin_id = update.message.chat_id
    msg_id = update.message.reply_to_message_id
    admin_text = 'Selecione uma das opções de adm ou clique em /cancelar:'
    global admin_opts
    admin_opts = [
        'Autorizar usuário', 
        'Desativar usuário', 
        'Editar usuário', 
        'Pesquisar usuário', 
        'Pesquisar por data'
    ]
    keyboard = [[x] for x in admin_opts]
    reply_markup = json.dumps({'keyboard': keyboard, 'one_time_keyboard': True})
    send_msg(admin_id, admin_text, msg_id, reply_markup)
    return ADMIN_B

def admin_b(update, context):
    admin_id = update.message.chat_id
    msg_id = update.message.reply_to_message_id
    msg = update.message.text
    if msg in admin_opts:
        choice = admin_opts.index(msg)
        context.user_data['selection'] = choice
        if choice == 0:
            admin_text = f'{admin_opts[choice]} - digite o user_id e o nome completo, separado por vírgulas ' \
                    '(se não quiser inserir o nome completo, digite "0") ou clique em /cancelar:'
        elif choice == 1:
            admin_text = f'{admin_opts[choice]} - digite o user_id:'
        elif choice == 2:
            admin_text = f'{admin_opts[choice]} - digite o user_id, o campo a editar (nome | username | email) ' \
                    'e o novo dado, separados por vírgulas (exemplo "123456, username, @Usuario") ou clique em /cancelar:'
        elif choice == 3:
            admin_text = f'{admin_opts[choice]} - digite o campo de pesquisa (user_id | nome | username) ' \
                    'e a pesquisa, separados por vírgula (exemplo "username, @Usuario") ou clique em /cancelar:'
        elif choice == 4:
            admin_text = f'{admin_opts[choice]} - digite as datas inicial e final, separadas por vírgulas ' \
                    '(exemplo "15/02/2020, 26/02/2020") ou clique em /cancelar:'
        send_msg(admin_id, admin_text, msg_id, rkr)
        return ADMIN_C

def admin_c(update, context):
    admin_id = update.messa.chat_id
    msg_id = update.message.reply_to_message_id
    msg = update.message.text
    choice = context.user_data['selection']
    admin_text, success = fc.func_admin(msg, choice)

def admin_d(update, context):
    admin_text = 'Formulário enviado!'
    update.callback_query.edit_message_text(text=admin_text)
    STOP
    configs_ini_a(update, context)

def configs_ini_a(update, context):
    user_id = context.user_data['user_id']