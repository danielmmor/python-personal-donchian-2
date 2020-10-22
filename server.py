'''
def constructor(word, forward):
    def function(x):
        print(word)
        x += 2
        return forward, x
    return function

set_mode = constructor('alo', 123)

A, B = set_mode(4)
print(A, B)
'''
import logging
import json
import configparser as cfg
import string
import schedule
import time
from functools import wraps
from telegram import (InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)
from buttons import Buttons
from dbhelper import DBHelper
from functs import Functions
from radar import Radar

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

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
RADAR_SM_DAY, RADAR_SM_WEEK, RADAR_ML_DAY, RADAR_ML_WEEK, \
    RADAR_ORDER = states_codes[num_states : num_states + x]
num_states += x
# Ticker tracker
x = 3
TRACK_UPD, TRACK_EXIT, TRACK_WARN_REM = states_codes[num_states : num_states + x]
num_states += x
# Portfolio
x = 6
PORTF_ADD, PORTF_SUBTR, PORTF_SUBST, PORTF_CLEAR, \
    PORTF_CHANGE, PORTF_UPD = states_codes[num_states : num_states + x]
num_states += x
# Info
x = 2
INFO, INFO_DUMMY = states_codes[num_states : num_states + x]
num_states += x
# Settings
x = 3
SET_TIME, SET_MODE, SET_RISK = states_codes[num_states : num_states + x]
num_states += x
# Time settings
x = 3
TIME_UPD, TIME_EXIT, TIME_ACT_DEACT = states_codes[num_states : num_states + x]
num_states += x
# Tracker radar mode settings
x = 2
MODE_UPD, MODE_DUMMY = states_codes[num_states : num_states + x]
num_states += x
# Risk management settings
x = 2
RISK_UPD, RISK_EXIT = states_codes[num_states : num_states + x]
num_states += x
# Help
x = 7
HP_HDIW, HP_NUMS, HP_BUY, HP_SET, \
    HP_CONTACT, HP_SELECT, HP_EXIT = states_codes[num_states : num_states + x]
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
    global db, fc, bt, rd, RKR, ADMS_LIST, TOKEN, ADMIN_OPTS, INIT
    db = DBHelper()
    db.setup()
    fc = Functions()
    bt = Buttons()
    rd = Radar()
    RKR = json.dumps({'remove_keyboard':True})
    # ADMINS: [Daniel Moreira]
    ADMS_LIST = [545699841]
    TOKEN = read_token('hidden/config.cfg')
    ADMIN_OPTS = [
        'Autorizar usuário', 
        'Desativar usuário', 
        'Editar usuário', 
        'Pesquisar usuário', 
        'Pesquisar por data'
    ]
    INIT = False

def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMS_LIST:
            text = 'Unauthorized access'
            context.bot.sendMessage(chat_id=user_id, text=text)
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
        context.bot.sendMessage(chat_id=user_id, text=user_text)
        context.bot.sendMessage(chat_id=ADMS_LIST[0], text=admin_text)

@restricted
def admin_a(update, context):
    global curr_admin_id, ADMIN_OPTS
    curr_admin_id = update.message.chat_id
    msg_id = update.message.message_id
    admin_text = 'Selecione uma das opções de adm ou clique em /cancelar:'
    keyboard = [[x] for x in ADMIN_OPTS]
    reply_markup = json.dumps({'keyboard': keyboard, 'one_time_keyboard': True})
    context.bot.sendMessage(
        chat_id=curr_admin_id, 
        text=admin_text, 
        reply_to_message_id=msg_id, 
        reply_markup=reply_markup
    )
    return ADMIN_B

def admin_b(update, context):
    global curr_admin_id, ADMIN_OPTS
    msg_id = update.message.message_id
    msg = update.message.text
    if msg in ADMIN_OPTS:
        choice = ADMIN_OPTS.index(msg)
        context.user_data['selection'] = choice
        if choice == 0:
            admin_text = f'{ADMIN_OPTS[choice]} - digite o user_id e o nome completo, separado por vírgulas ' \
                    '(se não quiser inserir o nome completo, digite "0") ou clique em /cancelar:'
        elif choice == 1:
            admin_text = f'{ADMIN_OPTS[choice]} - digite o user_id:'
        elif choice == 2:
            admin_text = f'{ADMIN_OPTS[choice]} - digite o user_id, o campo a editar (nome | username | email) ' \
                    'e o novo dado, separados por vírgulas (exemplo "123456, username, @Usuario") ou clique em /cancelar:'
        elif choice == 3:
            admin_text = f'{ADMIN_OPTS[choice]} - digite o campo de pesquisa (user_id | nome | username) ' \
                    'e a pesquisa, separados por vírgula (exemplo "username, @Usuario") ou clique em /cancelar:'
        elif choice == 4:
            admin_text = f'{ADMIN_OPTS[choice]} - digite as datas inicial e final, separadas por vírgulas ' \
                    '(exemplo "15/02/2020, 26/02/2020") ou clique em /cancelar:'
        context.bot.sendMessage(
            chat_id=curr_admin_id, 
            text=admin_text, 
            reply_to_message_id=msg_id, 
            reply_markup=RKR
        )
        return ADMIN_C

def admin_c(update, context):
    msg_id = update.message.message_id
    msg = update.message.text
    choice = context.user_data['selection']
    admin_text, success = fc.func_admin(msg, choice)
    context.bot.sendMessage(
        chat_id=curr_admin_id, 
        text=admin_text, 
        reply_to_message_id=msg_id
    )
    if success:
        if choice == 0:
            msg = msg.split(', ')
            context.user_data['user_id'] = msg[0]
            buttons = bt.buttons(ADMIN_C)
            admin_text = 'Deseja enviar o formulário de configs iniciais para o usuário?'
            update.message.reply_text(text=admin_text, reply_markup=IKM(buttons))
            return ADMIN_D
        else:
            return -1
    else:
        return ADMIN_C

def admin_d(update, context):
    admin_text = 'Formulário enviado!'
    update.callback_query.edit_message_text(text=admin_text)
    cancel(update, context)
    init_set_a(context)

def init_set_a(context):
    global INIT
    INIT = True
    user_id = context.user_data['user_id']
    text = 'Você foi autorizado. Agora, uma etapa muito importante: vamos ' \
           'configurar o seu perfil em poucos passos. Você vai poder modificar depois se quiser.'
    context.bot.sendMessage(chat_id=user_id, text=text)
    text = 'Primeiro, qual classe de ações você irá utilizar com mais frequência?'
    keyboard = [['Small Caps'], ['Mid Large Caps']]
    reply_markup = json.dumps({'keyboard': keyboard, 'one_time_keyboard': True})
    context.bot.sendMessage(chat_id=user_id, text=text, reply_markup=reply_markup)
    return INIT_SET_B

def init_set_b(update, context):
    global INIT
    if not INIT: return STOP
    INIT = False
    user_id = update.message.chat_id
    msg_id = update.message.message_id
    msg = update.message.text
    A, B = 'Small Caps', 'Mid Large Caps'
    if msg not in [A, B]:
        text = 'Resposta inválida. Tente novamente:'
        reply_markup = json.dumps({'keyboard': [[A], [B]], 'one_time_keyboard': True})
        context.bot.sendMessage(
            chat_id=user_id, 
            text=text, 
            reply_to_message_id=msg_id, 
            reply_markup=reply_markup
        )
        return INIT_SET_B
    else:
        context.user_data['init_set'] = []
        x = 'S' if msg == A else 'M'
        context.user_data['init_set'].append(x)
        text = 'Certo. Agora, qual escala temporal você prefere?'
        keyboard = [['Diário'], ['Semanal']]
        reply_markup = json.dumps({'keyboard': keyboard, 'one_time_keyboard': True})
        context.bot.sendMessage(chat_id=user_id, text=text, reply_markup=reply_markup)
        return INIT_SET_C

def init_set_c(update, context):
    user_id = update.message.chat_id
    msg_id = update.message.message_id
    msg = update.message.text
    A, B = 'Diário', 'Semanal'
    if msg not in [A, B]:
        text = 'Resposta inválida. Tente novamente:'
        reply_markup = json.dumps({'keyboard': [[A], [B]], 'one_time_keyboard': True})
        context.bot.sendMessage(
            chat_id=user_id, 
            text=text, 
            reply_to_message_id=msg_id, 
            reply_markup=reply_markup
        )
        return INIT_SET_C
    else:
        x = 'D' if msg == A else 'W'
        context.user_data['init_set'].append(x)
        text = 'Ok. Qual gerenciamento de risco é mais adequado para você?'
        keyboard = [['Bloquinho por operação'], ['Porcentagem relativa ao stop']]
        reply_markup = json.dumps({'keyboard': keyboard, 'one_time_keyboard': True})
        context.bot.sendMessage(chat_id=user_id, text=text, reply_markup=reply_markup)
        return INIT_SET_D

def init_set_d(update, context):
    user_id = update.message.chat_id
    msg_id = update.message.message_id
    msg = update.message.text
    A, B = 'Bloquinho por operação', 'Porcentagem relativa ao stop'
    if msg not in [A, B]:
        text = 'Resposta inválida. Tente novamente:'
        reply_markup = json.dumps({'keyboard': [[A], [B]], 'one_time_keyboard': True})
        context.bot.sendMessage(
            chat_id=user_id, 
            text=text, 
            reply_to_message_id=msg_id, 
            reply_markup=reply_markup
        )
        return INIT_SET_D
    else:
        if msg == A:
            x = 'B'
            text = 'Agora, digite o número de bloquinhos que serão utilizados (ex.: "8", sem as aspas):'
        else:
            x = 'P'
            text = 'Agora, digite o porcentual de risco (ex.: "1,5", sem as aspas):'
        context.user_data['init_set'].append(x)
        context.bot.sendMessage(chat_id=user_id, text=text)
        return INIT_SET_E

def init_set_e(update, context):
    msg = update.message.text
    text, success = fc.func_init_check(context.user_data['init_set'][2], msg)
    update.message.reply_text(text)
    if success:
        context.user_data['init_set'].append(msg)
        return INIT_SET_F
    else:
        return INIT_SET_E

def init_set_f(update, context):
    msg = update.message.text
    text, success = fc.func_init_check('p', msg)
    update.message.reply_text(text)
    if success:
        context.user_data['init_set'].append(msg)
        db.user_init(update.effective_user.id, context.user_data['init_set'])
        return -1
    else:
        return INIT_SET_F


# ------------------ Main menu ------------------

def menu(update, context):
    print('entrei no menu')
    text = 'MENU PRINCIPAL - Selecione uma das opções.\n\r'
    buttons = bt.buttons(MENU)
    if context.user_data.get(START_OVER):
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
        return MENU
    else:
        user_id = update.message.chat_id
        query = db.get_info(user_id)
        print(query)
        user_allowed = int(query[0][4])
        if user_allowed:
            update.message.reply_text('Olá! A qualquer momento você '
                                    'pode clicar em /ajuda.')
            update.message.reply_text(text=text, reply_markup=IKM(buttons))
            context.user_data[START_OVER] = True
            return MENU
        else:
            text = 'Você ainda não está autorizado. Fale com o administrador!'
            update.message.reply_text(text=text)

# Radar
def menu_radar(update, context):
    print('entrei no menu_radar')
    context.user_data[PREV_LEVEL] = menu
    #ordem = fc.func_ordem (?) db.get_ordem [ordenação, ordenar por]
    text = 'RADAR - Selecione o modo de análise ou modifique a ordenação dos resultados.\n\r' \
           'Atual: ordenar por ''''+ordem'''
    buttons = bt.buttons(MENU_RADAR)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return MENU_RADAR

def radar_activate(update, context):
    print('entrei no radar_activate')
    user_id = update.effective_user.id
    text = 'Aguarde um momento, por favor.'
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)
    choice = update.callback_query.data
    report = fc.func_radar(user_id, choice)
    context.bot.sendMessage(chat_id=user_id, text=report)
    context.user_data[START_OVER] = False
    return EXITING

def radar_order(update, context):
    context.user_data[PREV_LEVEL] = menu_radar
    text = 'ORDENAR POR - Selecione qual dado será utilizado para ordenar os resultados:'
    buttons = bt.buttons(RADAR_ORDER)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return RADAR_ORDER

def order(update, context):
    return 'abc'

# Tracker
def menu_track(update, context):
    print('entrei no menu_track')
    context.user_data[PREV_LEVEL] = menu
    user_id = update.effective_user.id
    text = 'CARTEIRA - Selecione uma das opções.\n\r' \
           'Composição atual da carteira:\n\r'+fc.func_get_tickers_user(user_id)
    buttons = bt.buttons(MENU_TRACK)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return TRACK_UPD

def track_upd(update, context):
    print('entrei no track_upd')
    context.user_data[PREV_LEVEL] = menu_track
    user_id = update.effective_user.id
    choice = int(update.callback_query.data)
    context.user_data['choice'] = choice
    if choice == 0:
        text = 'Digite o índice a ser adicionado ou selecione uma das opções ' \
            '(para adicionar vários, digite os índices separados por vírgula):'
    else:
        t_list = fc.func_get_tickers_user(user_id).split('\n')
        reply_markup = json.dumps({'keyboard': [[x] for x in t_list], 'one_time_keyboard': True})
        text = 'Escolha o índice a ser removido ou selecione uma das opções:'
        context.bot.sendMessage(chat_id=user_id, text='Carteira:', reply_markup=reply_markup)
    #keyboard com os índices
    #elif retirar alerta
    #text = RETI+'Os alertas da carteira foram removidos até o preço mudar novamente.'
    buttons = bt.buttons(EXIT)
    update.callback_query.answer()
    send = update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data['msg_id'] = send.message_id
    return TRACK_EXIT

def track_exit(update, context):
    print('entrei no track_exit')
    user_id = update.message.chat_id
    msg = update.message.text
    choice = context.user_data['choice']
    text, success = fc.func_tickers_upd_user(user_id, msg, choice)
    try:
        context.bot.deleteMessage(chat_id=user_id, message_id=context.user_data['msg_id'])
    except:
        pass
    context.bot.sendMessage(chat_id=user_id, text=text)
    if not success: return TRACK_EXIT
    context.user_data[START_OVER] = False
    return EXITING

# Portfolio
def menu_portf(update, context):
    print('entrei no menu_portf')
    context.user_data[PREV_LEVEL] = menu
    user_id = update.effective_user.id
    portf = db.get_info(user_id)[0][6]
    text = 'CAPITAL - Selecione uma das opções.\n\r' \
           'Valor atual de carteira: R$'+portf+''
    buttons = bt.buttons(MENU_PORTF)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return PORTF_UPD

def portf_upd(update, context):
    print('entrei no portf_upd')
    context.user_data[PREV_LEVEL] = menu_portf
    user_id = update.effective_user.id
    choice = int(update.callback_query.data)
    context.user_data['choice'] = choice
    if choice == 3:
        text = 'Tem certeza que deseja zerar o valor do capital?'
        keyboard = [['Sim'], ['Cancelar']]
        reply_markup = json.dumps({'keyboard': keyboard, 'one_time_keyboard': True})
        query_markup = ''
        forward = PORTF_CLEAR
        context.bot.sendMessage(chat_id=user_id, text='Escolha abaixo:', reply_markup=reply_markup)
    else:
        opts = ['adicionar', 'subtrair', 'substituir']
        text = 'CAPITAL - Digite o valor a '+opts[choice]+' ' \
            '(somente números) ou selecione uma das opções:'
        buttons = bt.buttons(EXIT)
        query_markup = IKM(buttons)
        forward = PORTF_CHANGE
    update.callback_query.answer()
    send = update.callback_query.edit_message_text(text=text, reply_markup=query_markup)
    context.user_data['msg_id'] = send.message_id
    return forward

def portf_change(update, context):
    print('entrei no portf_change')
    context.user_data[PREV_LEVEL] = portf_upd
    user_id = update.message.chat_id
    msg = update.message.text
    choice = context.user_data['choice']
    text, success = fc.func_portf_upd(user_id, msg, choice)
    try:
        context.bot.deleteMessage(chat_id=user_id, message_id=context.user_data['msg_id'])
    except:
        pass
    context.bot.sendMessage(chat_id=user_id, text=text)
    if not success: return PORTF_CHANGE
    context.user_data[START_OVER] = False
    return EXITING

def portf_clear(update, context):
    print('entrei no portf_clear')
    user_id = update.message.chat_id
    msg = update.message.text
    if msg == 'Cancelar':
        text = 'Operação cancelada.\n\rAté mais!'
    else:
        choice = context.user_data['choice']
        text = fc.func_portf_upd(user_id, msg, choice)
    update.message.reply_text(text=text)
    context.user_data[START_OVER] = False
    return EXITING

# Info
def menu_info(update, context):
    print('entrei no menu_info')
    context.user_data[PREV_LEVEL] = menu
    user_id = update.effective_user.id
    text = fc.func_get_info(user_id)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)#, reply_markup=IKM(buttons))
    context.bot.sendMessage(chat_id=user_id, text='Até mais!')
    context.user_data[START_OVER] = False
    return STOP

# Settings
def menu_set(update, context):
    print('entrei no menu_set')
    context.user_data[PREV_LEVEL] = menu
    text = 'CONFIGURAÇÕES - Selecione uma das opções.'
    buttons = bt.buttons(MENU_SET)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return SET_TIME

# Time settings
def set_time(update, context):
    print('entrei no set_time')
    context.user_data[PREV_LEVEL] = menu_set
    text = 'MUDAR HORA/DIA - Selecione uma das opções.'
    buttons = bt.buttons(SET_TIME)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return TIME_UPD

def time_upd(update, context):
    print('entrei no time_upd')
    context.user_data[PREV_LEVEL] = set_time
    user_id = update.effective_user.id
    choice = int(update.callback_query.data)
    context.user_data['choice'] = choice
    cb_text, text, keyboard = fc.func_time_upd(user_id, 'A', choice)
    buttons = bt.buttons(EXIT)
    update.callback_query.answer()
    send = update.callback_query.edit_message_text(text=cb_text, reply_markup=IKM(buttons))
    context.user_data['msg_id'] = send.message_id
    if keyboard: 
        reply_markup = json.dumps({'keyboard': keyboard, 'one_time_keyboard': True})
        context.bot.sendMessage(chat_id=user_id, text=text, reply_markup=reply_markup)
    return TIME_EXIT

def time_exit(update, context):
    print('entrei no time_exit')
    user_id = update.message.chat_id
    msg = update.message.text
    choice = context.user_data['choice']
    text, success = fc.func_time_exit(user_id, choice, msg)
    try:
        context.bot.deleteMessage(chat_id=user_id, message_id=context.user_data['msg_id'])
    except:
        pass
    context.bot.sendMessage(chat_id=user_id, text=text)
    if not success: return TIME_EXIT
    context.user_data[START_OVER] = False
    return EXITING

# Radar mode settings
def set_mode(update, context):
    print('entrei no set_mode')
    context.user_data[PREV_LEVEL] = menu_set
    text = 'CONFIGURAÇÕES DE MODO - Selecione a classe de ativos ' \
           'e a escala temporal a serem usados no alerta automático.'
    buttons = bt.buttons(SET_MODE)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return MODE_UPD

def mode_upd(update, context):
    print('entrei no mode_upd')
    user_id = update.effective_user.id
    choice = update.callback_query.data
    text = fc.func_mode_upd(user_id, choice)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)
    context.user_data[START_OVER] = False
    return EXITING

# Risk mngmt settings
def set_risk(update, context):
    print('entrei no set_risk')
    context.user_data[PREV_LEVEL] = menu_set
    text = 'CONFIGURAÇÕES DE RISCO - Selecione o gerenciamento de risco a ' \
           'ser utilizado no cálculo do volume:'
    buttons = bt.buttons(SET_RISK)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return RISK_UPD

def risk_upd(update, context):
    print('entrei no risk_upd')
    user_id = update.effective_user.id
    choice = update.callback_query.data
    context.user_data['choice'] = choice
    text = fc.func_risk_upd(user_id, choice)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)
    return RISK_EXIT

def risk_exit(update, context):
    print('entrei no risk_exit')
    user_id = update.message.chat_id
    msg = update.message.text
    choice = context.user_data['choice']
    text, success = fc.func_risk_exit(user_id, choice, msg)
    try:
        context.bot.deleteMessage(chat_id=user_id, message_id=context.user_data['msg_id'])
    except:
        pass
    context.bot.sendMessage(chat_id=user_id, text=text)
    if not success: return RISK_EXIT
    context.user_data[START_OVER] = False
    return EXITING

# Help
def menu_help(update, context):
    print('entrei no menu_help')
    context.user_data[PREV_LEVEL] = menu
    text = 'AJUDA - Selecione um tópico:'
    buttons = bt.buttons(MENU_HELP)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return MENU_HELP

def help_exit(update, context):
    print('entrei no help_exit')
    context.user_data[PREV_LEVEL] = menu_help
    text = 'AJUDA - TITULO QUALQUER'
    buttons = bt.buttons(EXIT)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return MENU_HELP

# Go back
def back(update, context):
    update.callback_query.answer()
    context.user_data[START_OVER] = True
    context.user_data[PREV_LEVEL](update, context)
    return STOP

# End conversation
def stop(update, context):
    print('entrei no stop')
    context.user_data[START_OVER] = False
    update.callback_query.answer()
    text = 'Até mais!'
    update.callback_query.edit_message_text(text=text)
    return EXITING

def end(update, context):
    print('entrei no end')
    context.user_data[START_OVER] = False
    text = 'Até mais!'
    if update.callback_query:
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text)
    else:
        context.bot.sendMessage(
            chat_id=update.effective_user.id, 
            text=text, 
            reply_markup=RKR
        )
    return STOP

@restricted
def cancel(update, context):
    global curr_admin_id
    print('entrei no cancel')
    text = 'Sessão de adm encerrada.'
    if update.callback_query:
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text)
    else:
        context.bot.sendMessage(
            chat_id=curr_admin_id, 
            text=text, 
            reply_markup=RKR
        )
    return STOP

# Error handler
def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    global ADMIN_OPTS
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    # Help
    help_exit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            help_exit, 
            pattern='^{0}$|^{1}$|^{2}$|^{3}$|^{4}$'.format(HP_HDIW,
                                                           HP_NUMS,
                                                           HP_BUY,
                                                           HP_SET,
                                                           HP_CONTACT)
        )],
        states={HP_SELECT: []},
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU_HELP,
            EXITING: EXITING
        }
    )
    menu_help_handlers = [help_exit_conv]
    menu_help_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_help, pattern='^'+MENU_HELP+'$')],
        states={
            MENU_HELP: menu_help_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU,
            EXITING: STOP
        }
    )
    # Settings
    set_risk_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_risk, pattern='^'+str(SET_RISK)+'$')],
        states={
            RISK_UPD: [CallbackQueryHandler(risk_upd, pattern='^(B|P)$')],
            RISK_EXIT: [MessageHandler(Filters.text, risk_exit)]
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU_SET,
            EXITING: EXITING
        }
    )
    set_mode_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_mode, pattern='^'+SET_MODE+'$')],
        states={MODE_UPD: [CallbackQueryHandler(mode_upd, pattern='^(S|M),(D|W)$')]},
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU_SET,
            EXITING: EXITING
        }
    )
    time_upd_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(time_upd, pattern=r'^\d$')],
        states={TIME_EXIT: [MessageHandler(Filters.text, time_exit)]},
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: TIME_UPD,
            EXITING: EXITING
        }
    )
    set_time_handlers = [time_upd_conv]
    set_time_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_time, pattern='^'+SET_TIME+'$')],
        states={TIME_UPD: set_time_handlers,},
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: SET_TIME,
            EXITING: EXITING
        }
    )
    menu_set_handlers = [
        set_time_conv,
        set_mode_conv,
        set_risk_conv
    ]
    menu_set_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_set, pattern='^'+MENU_SET+'$')],
        states={SET_TIME: menu_set_handlers,},
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU,
            EXITING: STOP
        }
    )
    # Portfolio
    portf_upd_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(portf_upd, pattern=r'^\d$')],
        states={
            PORTF_CHANGE: [MessageHandler(Filters.text, portf_change)],
            PORTF_CLEAR: [MessageHandler(Filters.text, portf_clear)]
        },
        fallbacks=[
            MessageHandler(Filters.regex('^admin_exit$'), end),
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: PORTF_UPD,
            EXITING: EXITING,
        }
    )
    menu_portf_handlers = [portf_upd_conv]
    menu_portf_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_portf, pattern='^'+MENU_PORTF+'$')],
        states={PORTF_UPD: menu_portf_handlers},
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU,
            EXITING: STOP
        }
    )
    # Ticker track
    menu_track_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_track, pattern='^'+MENU_TRACK+'$')],
        states={
            TRACK_UPD: [CallbackQueryHandler(track_upd, pattern=r'^\d$')],
            TRACK_EXIT: [MessageHandler(Filters.text, track_exit)]
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU,
            EXITING: STOP
        }
    )
    # Radar
    radar_order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(radar_order, pattern='^'+RADAR_ORDER+'$')],
        states={RADAR_ORDER: [CallbackQueryHandler(order, pattern=r'^\d$')]},
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU_RADAR,
            EXITING: EXITING
        }
    )
    menu_radar_handlers = [
        CallbackQueryHandler(radar_activate, pattern=r'^\d$'),
        radar_order_conv,
    ]
    menu_radar_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_radar, pattern='^'+MENU_RADAR+'$')],
        states={MENU_RADAR: menu_radar_handlers},
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU,
            EXITING: STOP
        }
    )
    # Main menu
    menu_handlers = [
        menu_radar_conv,
        menu_track_conv,
        menu_portf_conv,
        CallbackQueryHandler(menu_info, pattern='^'+MENU_INFO+'$'),
        menu_set_conv,
        menu_help_conv,
    ]
    menu_conv = ConversationHandler(
        entry_points=[CommandHandler('menu', menu)],
        states={
            MENU: menu_handlers,
            STOP: [CallbackQueryHandler(end, pattern='^'+str(STOP)+'$')]
        },
        fallbacks=[CallbackQueryHandler(end, pattern='^'+str(STOP)+'$')]
    )
    # Initial settings
    init_set_conv = ConversationHandler(
        entry_points=[MessageHandler(Filters.text, init_set_b)],
        states={
            INIT_SET_C: [MessageHandler(Filters.text, init_set_c)],
            INIT_SET_D: [MessageHandler(Filters.text, init_set_d)],
            INIT_SET_E: [MessageHandler(Filters.text, init_set_e)],
            INIT_SET_F: [MessageHandler(Filters.text, init_set_f)],
            STOP: [CallbackQueryHandler(end, pattern='^'+str(STOP)+'$')]
        },
        fallbacks=[CallbackQueryHandler(end, pattern='^'+str(STOP)+'$')]
    )
    # Admin
    admin_conv = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_a)],
        states={
            ADMIN_B: [MessageHandler(Filters.regex('^('+ADMIN_OPTS[0]+'|' \
                                                   +ADMIN_OPTS[1]+'|' \
                                                   +ADMIN_OPTS[2]+'|' \
                                                   +ADMIN_OPTS[3]+'|' \
                                                   +ADMIN_OPTS[4]+')$'), admin_b)],
            ADMIN_C: [MessageHandler(~Filters.command, admin_c)],
            ADMIN_D: [CallbackQueryHandler(admin_d, pattern='^'+ADMIN_D+'$')]
        },
        fallbacks=[
            CommandHandler('cancelar', cancel), 
            CallbackQueryHandler(cancel, pattern='^'+str(STOP)+'$')
        ],
        conversation_timeout=30,
    )

    start_comm = CommandHandler('start', start)
    dp.add_handler(menu_conv)
    dp.add_handler(admin_conv)
    dp.add_handler(init_set_conv, 1)
    dp.add_handler(start_comm)
    # log all errors
    dp.add_error_handler(error)
    updater.start_polling()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    init()
    main()