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
'''
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
'''
# ------------------ Generic names for states navigation -----------------------
s = string.ascii_uppercase
states_codes = [i + j for i in s[:6] for j in s]
(
    # Menu
    MENU_RADAR, MENU_TRACK, 
    MENU_PORTF, MENU_INFO, MENU_SET, MENU_HELP,
    # Radar
    RADAR_BUY, RADAR_TRACK, RADAR_A, RADAR_B, RADAR_ORDER,
    # Ticker tracker
    TRACK_UPD, TRACK_EXIT, TRACK_WARN_REM,
    # Portfolio
    PORTF_ADD, PORTF_SUBTR, PORTF_SUBST, PORTF_CLEAR,
    PORTF_CHANGE, PORTF_UPD,
    # Info
    INFO, INFO_DUMMY,
    # Settings
    SET_TIME, SET_MODE, SET_RISK,
    # Time settings
    TIME_UPD, TIME_EXIT, TIME_ACT_DEACT,
    # Tracker radar mode settings
    MODE_UPD, MODE_DUMMY,
    # Risk management settings
    RISK_UPD, RISK_EXIT,
    # Help
    HP_HDIW, HP_NUMS, HP_BUY, HP_SET,
    HP_CONTACT, HP_SELECT, HP_EXIT,
    # Admin states and initial settings
    ADMIN_B, ADMIN_C, ADMIN_D, INIT_SET_A, 
    INIT_SET_B, INIT_SET_C, INIT_SET_D, INIT_SET_E, 
    INIT_SET_F,
    # Meta states
    MENU, START_OVER, PREV_LEVEL,
    EXITING, EXIT,
    # remaining codes
    *_
) = states_codes
# Shortcut to ConvHandler.END
STOP = ConversationHandler.END

# ------------------ Bot initialization -----------------------
def read_token(config):
    parser = cfg.ConfigParser()
    parser.read(config)
    return parser.get('creds', 'token')

def init():
    global db, fc, bt, RKR, ADMS_LIST, TOKEN, ADMIN_OPTS, INIT
    TOKEN = read_token('hidden/config.cfg')
    db = DBHelper()
    db.setup()
    fc = Functions(TOKEN)
    bt = Buttons()
    RKR = json.dumps({'remove_keyboard':True})
    # ADMINS: [Daniel Moreira]
    ADMS_LIST = [545699841]
    fc.schedule()
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
    def wrapped(upd, context, *args, **kwargs):
        user_id = upd.effective_user.id
        if user_id not in ADMS_LIST:
            text = 'Unauthorized access'
            fc.func_send_msg(chat_id=user_id, text=text)
            return
        else:
            return func(upd, context, *args, **kwargs)
    return wrapped
'''
def catch_error(f):
    @wraps(f)
    def wrap(upd, context):
        logging.info("User {user} sent {message}".format(user=upd.message.from_user.username, message=upd.message.text))
        try:
            return f(upd, context)
        except Exception as e:
            # Add info to error tracking
            logging.error('Erro: '+str(e))
    return wrap
'''

# ------------------ User start and admin control ------------------
def start(upd, context):
    user_id = upd.message.chat_id
    f_name = upd.message.chat.first_name
    l_name = upd.message.chat.last_name if upd.message.chat.last_name else '-'
    name = (f_name + ' ' + l_name)
    username = upd.message.chat.username if upd.message.chat.username else '-'
    user_type = upd.message.chat.type
    is_bot = upd._effective_user.is_bot

    if user_type == 'group' or is_bot:
        context.bot.leaveChat(chat_id=user_id)
    else:
        admin_text, user_text = fc.func_user_start(user_id, name, username)
        fc.func_send_msg(chat_id=user_id, text=user_text)
        fc.func_send_msg(chat_id=ADMS_LIST[0], text=admin_text)

@restricted
def admin_a(upd, context):
    global curr_admin_id, ADMIN_OPTS
    curr_admin_id = upd.message.chat_id
    msg_id = upd.message.message_id
    admin_text = 'Selecione uma das opções de adm ou clique em /cancelar:'
    keyboard = [[x] for x in ADMIN_OPTS]
    reply_markup = json.dumps({'keyboard': keyboard, 'one_time_keyboard': True})
    fc.func_send_msg(
        chat_id=curr_admin_id, 
        text=admin_text, 
        reply_to_message_id=msg_id, 
        reply_markup=reply_markup
    )
    return ADMIN_B

def admin_b(upd, context):
    global curr_admin_id, ADMIN_OPTS
    msg_id = upd.message.message_id
    msg = upd.message.text
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
        fc.func_send_msg(
            chat_id=curr_admin_id, 
            text=admin_text, 
            reply_to_message_id=msg_id, 
            reply_markup=RKR
        )
        return ADMIN_C

def admin_c(upd, context):
    msg_id = upd.message.message_id
    msg = upd.message.text
    choice = context.user_data['selection']
    admin_text, success = fc.func_admin(msg, choice)
    fc.func_send_msg(
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
            upd.message.reply_text(text=admin_text, reply_markup=IKM(buttons))
            return ADMIN_D
        else:
            return -1
    else:
        return ADMIN_C

def admin_d(upd, context):
    admin_text = 'Formulário enviado!'
    upd.callback_query.edit_message_text(text=admin_text)
    cancel(upd, context)
    init_set_a(context)

def init_set_a(context):
    global INIT
    INIT = True
    user_id = context.user_data['user_id']
    text = 'Você foi autorizado. Agora, uma etapa muito importante: vamos ' \
           'configurar o seu perfil em poucos passos. Você vai poder modificar depois se quiser.'
    fc.func_send_msg(chat_id=user_id, text=text)
    text = 'Primeiro, qual classe de ações você irá utilizar com mais frequência?'
    keyboard = [['Small Caps'], ['Mid Large Caps']]
    reply_markup = json.dumps({'keyboard': keyboard, 'one_time_keyboard': True})
    fc.func_send_msg(chat_id=user_id, text=text, reply_markup=reply_markup)
    return INIT_SET_B

def init_set_b(upd, context):
    global INIT
    if not INIT: return STOP
    INIT = False
    user_id = upd.message.chat_id
    msg_id = upd.message.message_id
    msg = upd.message.text
    A, B = 'Small Caps', 'Mid Large Caps'
    if msg not in [A, B]:
        text = 'Resposta inválida. Tente novamente:'
        reply_markup = json.dumps({'keyboard': [[A], [B]], 'one_time_keyboard': True})
        fc.func_send_msg(
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
        fc.func_send_msg(chat_id=user_id, text=text, reply_markup=reply_markup)
        return INIT_SET_C

def init_set_c(upd, context):
    user_id = upd.message.chat_id
    msg_id = upd.message.message_id
    msg = upd.message.text
    A, B = 'Diário', 'Semanal'
    if msg not in [A, B]:
        text = 'Resposta inválida. Tente novamente:'
        reply_markup = json.dumps({'keyboard': [[A], [B]], 'one_time_keyboard': True})
        fc.func_send_msg(
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
        fc.func_send_msg(chat_id=user_id, text=text, reply_markup=reply_markup)
        return INIT_SET_D

def init_set_d(upd, context):
    user_id = upd.message.chat_id
    msg_id = upd.message.message_id
    msg = upd.message.text
    A, B = 'Bloquinho por operação', 'Porcentagem relativa ao stop'
    if msg not in [A, B]:
        text = 'Resposta inválida. Tente novamente:'
        reply_markup = json.dumps({'keyboard': [[A], [B]], 'one_time_keyboard': True})
        fc.func_send_msg(
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
        fc.func_send_msg(chat_id=user_id, text=text)
        return INIT_SET_E

def init_set_e(upd, context):
    msg = upd.message.text
    text, success = fc.func_init_check(context.user_data['init_set'][2], msg)
    upd.message.reply_text(text)
    if success:
        context.user_data['init_set'].append(msg)
        return INIT_SET_F
    else:
        return INIT_SET_E

def init_set_f(upd, context):
    user_id = upd.effective_user.id
    all_data = context.user_data['init_set']
    msg = upd.message.text
    text, success = fc.func_init_check('p', msg, user_id, all_data)
    upd.message.reply_text(text)
    if success:
        all_data.append(msg)
        db.user_init(user_id, all_data)
        return -1
    else:
        return INIT_SET_F

# ------------------ Main menu ------------------
# @catch_error
def menu(upd, context):
    print('entrei no menu')
    text = 'MENU PRINCIPAL - Selecione uma das opções:\n\r'
    buttons = bt.buttons(MENU)
    if context.user_data.get(START_OVER):
        upd.callback_query.answer()
        upd.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
        return MENU
    else:
        user_id = upd.message.chat_id
        query = db.get_info(user_id)
        print(query)
        user_allowed = int(query[0][4])
        if user_allowed:
            upd.message.reply_text('Olá! Se precisar de ajuda, '
                'contate o @DanMoreira.')
            upd.message.reply_text(text=text, reply_markup=IKM(buttons))
            context.user_data[START_OVER] = True
            return MENU
        else:
            text = 'Você ainda não está autorizado. Fale com o administrador!'
            upd.message.reply_text(text=text)

# Radar
def menu_radar(upd, context):
    print('entrei no menu_radar')
    context.user_data[PREV_LEVEL] = menu
    #ordem = fc.func_ordem (?) db.get_ordem [ordenação, ordenar por]
    text = 'RELATÓRIOS - Selecione a análise:' 
        #'ou modifique a ordenação dos resultados.\n\r' \
        #   'Atual: ordenar por +ordem
    buttons = bt.buttons(MENU_RADAR)
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data['choice'] = 'track'
    context.user_data[START_OVER] = True
    return RADAR_A

def radar_a(upd, context):
    print('entrei no radar_a')
    choice = upd.callback_query.data
    context.user_data['choice'] = 'buy'
    if choice == 'buy':
        text = 'Selecione o modo:'
        buttons = bt.buttons(RADAR_BUY)
    # elif choice == RADAR_ORDER:
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return RADAR_B

def radar_b(upd, context):
    print('entrei no radar_b')
    choice = context.user_data['choice']
    user_id = upd.effective_user.id
    mode = upd.callback_query.data if choice == 'buy' else None
    text = 'Gerando relatório, aguarde um momento.'
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text)
    context.bot.sendChatAction(chat_id=user_id, action='typing')
    context.user_data[START_OVER] = False
    report = fc.func_radar(choice, user_id, mode)
    fc.func_send_msg(chat_id=user_id, text=report)
    return EXITING

# Tracker
def menu_track(upd, context):
    print('entrei no menu_track')
    context.user_data[PREV_LEVEL] = menu
    user_id = upd.effective_user.id
    text = 'CARTEIRA - Selecione uma das opções.\n\r' \
           'Composição atual da carteira:\n\r'+fc.func_get_tickers_user(user_id)
    buttons = bt.buttons(MENU_TRACK)
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return TRACK_UPD

def track_upd(upd, context):
    print('entrei no track_upd')
    context.user_data[PREV_LEVEL] = menu_track
    user_id = upd.effective_user.id
    choice = int(upd.callback_query.data)
    context.user_data['choice'] = choice
    if choice < 4:
        text = 'Digite o índice a ser adicionado para monitorar seu preço de venda ' \
            'ou selecione uma das opções ' \
            '(para adicionar vários, digite os índices separados por vírgula):'
    else:
        t_list = fc.func_get_tickers_user(user_id, False)
        reply_markup = json.dumps({'keyboard': [[x] for x in t_list], 'one_time_keyboard': True})
        text = 'Escolha o índice a ser removido ou selecione uma das opções:'
        fc.func_send_msg(
            
            chat_id=user_id, 
            text='Carteira:', 
            reply_markup=reply_markup
        )
    #keyboard com os índices
    #elif retirar alerta
    #text = RETI+'Os alertas da carteira foram removidos até o preço mudar novamente.'
    buttons = bt.buttons(EXIT)
    upd.callback_query.answer()
    send = upd.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data['msg_id'] = send.message_id
    return TRACK_EXIT

def track_exit(upd, context):
    print('entrei no track_exit')
    user_id = upd.message.chat_id
    msg = upd.message.text
    choice = context.user_data['choice']
    text, success = fc.func_tickers_upd_user(user_id, msg, choice)
    try:
        context.bot.deleteMessage(chat_id=user_id, message_id=context.user_data['msg_id'])
    except:
        pass
    fc.func_send_msg(chat_id=user_id, text=text)
    if not success: return TRACK_EXIT
    context.user_data[START_OVER] = False
    return EXITING

# Portfolio
def menu_portf(upd, context):
    print('entrei no menu_portf')
    context.user_data[PREV_LEVEL] = menu
    user_id = upd.effective_user.id
    portf = db.get_info(user_id)[0][6]
    text = 'CAPITAL - Selecione uma das opções.\n\r' \
           'Valor atual de carteira: R$'+portf+''
    buttons = bt.buttons(MENU_PORTF)
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return PORTF_UPD

def portf_upd(upd, context):
    print('entrei no portf_upd')
    context.user_data[PREV_LEVEL] = menu_portf
    user_id = upd.effective_user.id
    choice = int(upd.callback_query.data)
    context.user_data['choice'] = choice
    if choice == 3:
        text = 'Tem certeza que deseja zerar o valor do capital?'
        keyboard = [['Sim'], ['Cancelar']]
        reply_markup = json.dumps({'keyboard': keyboard, 'one_time_keyboard': True})
        query_markup = ''
        forward = PORTF_CLEAR
        fc.func_send_msg(chat_id=user_id, text='Escolha abaixo:', reply_markup=reply_markup)
    else:
        opts = ['adicionar', 'subtrair', 'substituir']
        text = 'CAPITAL - Digite o valor a '+opts[choice]+' ' \
            '(somente números) ou selecione uma das opções:'
        buttons = bt.buttons(EXIT)
        query_markup = IKM(buttons)
        forward = PORTF_CHANGE
    upd.callback_query.answer()
    send = upd.callback_query.edit_message_text(text=text, reply_markup=query_markup)
    context.user_data['msg_id'] = send.message_id
    return forward

def portf_change(upd, context):
    print('entrei no portf_change')
    context.user_data[PREV_LEVEL] = portf_upd
    user_id = upd.message.chat_id
    msg = upd.message.text
    choice = context.user_data['choice']
    text, success = fc.func_portf_upd(user_id, msg, choice)
    try:
        context.bot.deleteMessage(chat_id=user_id, message_id=context.user_data['msg_id'])
    except:
        pass
    fc.func_send_msg(chat_id=user_id, text=text)
    if not success: return PORTF_CHANGE
    context.user_data[START_OVER] = False
    return EXITING

def portf_clear(upd, context):
    print('entrei no portf_clear')
    user_id = upd.message.chat_id
    msg = upd.message.text
    if msg == 'Cancelar':
        text = 'Operação cancelada.\n\rAté mais!'
    else:
        choice = context.user_data['choice']
        text = fc.func_portf_upd(user_id, msg, choice)
    upd.message.reply_text(text=text)
    context.user_data[START_OVER] = False
    return EXITING

# Info
def menu_info(upd, context):
    print('entrei no menu_info')
    context.user_data[PREV_LEVEL] = menu
    user_id = upd.effective_user.id
    text = fc.func_get_info(user_id)
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text)#, reply_markup=IKM(buttons))
    fc.func_send_msg(chat_id=user_id, text='Até mais!')
    context.user_data[START_OVER] = False
    return STOP

# Settings
def menu_set(upd, context):
    print('entrei no menu_set')
    context.user_data[PREV_LEVEL] = menu
    text = 'CONFIGURAÇÕES - Selecione uma das opções.'
    buttons = bt.buttons(MENU_SET)
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return SET_TIME

# Time settings
def set_time(upd, context):
    print('entrei no set_time')
    context.user_data[PREV_LEVEL] = menu_set
    text = 'MUDAR HORA/DIA - Selecione uma das opções.'
    buttons = bt.buttons(SET_TIME)
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return TIME_UPD

def time_upd(upd, context):
    print('entrei no time_upd')
    context.user_data[PREV_LEVEL] = set_time
    user_id = upd.effective_user.id
    choice = int(upd.callback_query.data)
    context.user_data['choice'] = choice
    cb_text, text, keyboard = fc.func_time_upd(user_id, int(choice))
    buttons = bt.buttons(EXIT)
    upd.callback_query.answer()
    send = upd.callback_query.edit_message_text(text=cb_text, reply_markup=IKM(buttons))
    context.user_data['msg_id'] = send.message_id
    if keyboard: 
        reply_markup = json.dumps({'keyboard': keyboard, 'one_time_keyboard': True})
        fc.func_send_msg(chat_id=user_id, text=text, reply_markup=reply_markup)
    return TIME_EXIT

def time_exit(upd, context):
    print('entrei no time_exit')
    user_id = upd.message.chat_id
    msg = upd.message.text
    choice = context.user_data['choice']
    text, success = fc.func_time_exit(user_id, choice, msg)
    try:
        context.bot.deleteMessage(chat_id=user_id, message_id=context.user_data['msg_id'])
    except:
        pass
    fc.func_send_msg(chat_id=user_id, text=text)
    if not success: return TIME_EXIT
    context.user_data[START_OVER] = False
    return EXITING

# Radar mode settings
def set_mode(upd, context):
    print('entrei no set_mode')
    context.user_data[PREV_LEVEL] = menu_set
    text = 'CONFIGURAÇÕES DE MODO - Selecione a classe de ativos ' \
           'e a escala temporal a serem usados no alerta automático.'
    buttons = bt.buttons(SET_MODE)
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return MODE_UPD

def mode_upd(upd, context):
    print('entrei no mode_upd')
    user_id = upd.effective_user.id
    choice = upd.callback_query.data
    text = fc.func_mode_upd(user_id, choice)
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text)
    context.user_data[START_OVER] = False
    return EXITING

# Risk mngmt settings
def set_risk(upd, context):
    print('entrei no set_risk')
    context.user_data[PREV_LEVEL] = menu_set
    text = 'CONFIGURAÇÕES DE RISCO - Selecione o gerenciamento de risco a ' \
           'ser utilizado no cálculo do volume:'
    buttons = bt.buttons(SET_RISK)
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return RISK_UPD

def risk_upd(upd, context):
    print('entrei no risk_upd')
    user_id = upd.effective_user.id
    choice = upd.callback_query.data
    context.user_data['choice'] = choice
    text = fc.func_risk_upd(user_id, choice)
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text)
    return RISK_EXIT

def risk_exit(upd, context):
    print('entrei no risk_exit')
    user_id = upd.message.chat_id
    msg = upd.message.text
    choice = context.user_data['choice']
    text, success = fc.func_risk_exit(user_id, choice, msg)
    try:
        context.bot.deleteMessage(chat_id=user_id, message_id=context.user_data['msg_id'])
    except:
        pass
    fc.func_send_msg(chat_id=user_id, text=text)
    if not success: return RISK_EXIT
    context.user_data[START_OVER] = False
    return EXITING

# Help
def menu_help(upd, context):
    print('entrei no menu_help')
    context.user_data[PREV_LEVEL] = menu
    text = 'AJUDA - Selecione um tópico:'
    buttons = bt.buttons(MENU_HELP)
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return MENU_HELP

def help_exit(upd, context):
    print('entrei no help_exit')
    context.user_data[PREV_LEVEL] = menu_help
    text = 'AJUDA - TITULO QUALQUER'
    buttons = bt.buttons(EXIT)
    upd.callback_query.answer()
    upd.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return MENU_HELP

# Go back
def back(upd, context):
    upd.callback_query.answer()
    context.user_data[START_OVER] = True
    context.user_data[PREV_LEVEL](upd, context)
    return STOP

# End conversation
def stop(upd, context):
    print('entrei no stop')
    context.user_data[START_OVER] = False
    upd.callback_query.answer()
    text = 'Até mais!'
    upd.callback_query.edit_message_text(text=text)
    return EXITING

def end(upd, context):
    print('entrei no end')
    context.user_data[START_OVER] = False
    text = 'Até mais!'
    if upd.callback_query:
        upd.callback_query.answer()
        upd.callback_query.edit_message_text(text=text)
    else:
        fc.func_send_msg(
            chat_id=upd.effective_user.id, 
            text=text, 
            reply_markup=RKR
        )
    return STOP

@restricted
def cancel(upd, context):
    global curr_admin_id
    print('entrei no cancel')
    text = 'Sessão de adm encerrada.'
    if upd.callback_query:
        upd.callback_query.answer()
        upd.callback_query.edit_message_text(text=text)
    else:
        fc.func_send_msg(
            chat_id=curr_admin_id, 
            text=text, 
            reply_markup=RKR
        )
    return STOP

'''
# Error handler
def error(upd, context):
    logger.warning('Update "%s" caused error "%s"', upd, context.error)
'''
def main():
    global ADMIN_OPTS
    updr = Updater(TOKEN, use_context=True)
    dp = updr.dispatcher
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
    track_upd_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(track_upd, pattern=r'^\d$')],
        states={TRACK_EXIT: [MessageHandler(Filters.text, track_exit)]},
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: TRACK_UPD,
            EXITING: EXITING
        }
    )
    menu_track_handlers = [track_upd_conv]
    menu_track_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_track, pattern='^'+MENU_TRACK+'$')],
        states={TRACK_UPD: menu_track_handlers},
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
    menu_radar_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_radar, pattern='^'+MENU_RADAR+'$')],
        states={
            RADAR_A: [
                CallbackQueryHandler(radar_a, pattern='^buy$'),
                CallbackQueryHandler(radar_b, pattern='^track$')
            ],
            RADAR_B: [CallbackQueryHandler(radar_b, pattern=r'^\d$')]
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
    #dp.add_error_handler(error)
    updr.start_polling()

    print('Bot initialized successfuly.')
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    print('Initializing bot...')
    init()
    main()
    '''
    while True:
        try:
            print('Initializing bot...')
            init()
            main()
        except Exception as e:
            ex_text = 'Deu ruim:\n'+ str(e)
            fc.func_send_msg(chat_id='545699841', text=ex_text)
            print('\r\n\r\nBot Error:\r\n\r\n')
            print(ex_text)
            print('\r\n\r\nRestarting...\r\n\r\n')
    '''