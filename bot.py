# -*- coding: utf-8 -*-

import logging
import json
import configparser as cfg
import requests

from functools import wraps
from telegram import (InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)

from dbhelper import DBHelper
from functs import Functions

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# ------------------ Generic names for states navigation -----------------------


states_letters = [
    'Aa', 'Ab', 'Ac', 'Ad', 'Ae', 'Af', 'Ag', 'Ah', 'Ai', 'Aj', 'Ak', 'Al', 'Am', 
    'An', 'Ao', 'Ap', 'Aq', 'Ar', 'As', 'At', 'Au', 'Av', 'Aw', 'Ax', 'Ay', 'Az', 
    'Ba', 'Bb', 'Bc', 'Bd', 'Be', 'Bf', 'Bg', 'Bh', 'Bi', 'Bj', 'Bk', 'Bl', 'Bm', 
    'Bn', 'Bo', 'Bp', 'Bq', 'Br', 'Bs', 'Bt', 'Bu', 'Bv', 'Bw', 'Bx', 'By', 'Bz', 
    'Ca', 'Cb', 'Cc', 'Cd', 'Ce', 'Cf', 'Cg', 'Ch', 'Ci', 'Cj', 'Ck', 'Cl', 'Cm', 
    'Cn', 'Co', 'Cp', 'Cq', 'Cr', 'Cs', 'Ct', 'Cu', 'Cv', 'Cw', 'Cx', 'Cy', 'Cz', 
    'Da', 'Db', 'Dc', 'Dd', 'De', 'Df', 'Dg', 'Dh', 'Di', 'Dj', 'Dk', 'Dl', 'Dm', 
    'Dn', 'Do', 'Dp', 'Dq', 'Dr', 'Ds', 'Dt', 'Du', 'Dv', 'Dw', 'Dx', 'Dy', 'Dz', 
    'Ea', 'Eb', 'Ec', 'Ed', 'Ee', 'Ef', 'Eg', 'Eh', 'Ei', 'Ej', 'Ek', 'El', 'Em', 
    'En', 'Eo', 'Ep', 'Eq', 'Er', 'Es', 'Et', 'Eu', 'Ev', 'Ew', 'Ex', 'Ey', 'Ez', 
    'Fa', 'Fb', 'Fc', 'Fd', 'Fe', 'Ff', 'Fg', 'Fh', 'Fi', 'Fj', 'Fk', 'Fl', 'Fm', 
    'Fn', 'Fo', 'Fp', 'Fq', 'Fr', 'Fs', 'Ft', 'Fu', 'Fv', 'Fw', 'Fx', 'Fy', 'Fz'
]

num_states = 0
# Menu
x = 6
MENU_RADAR, MENU_TRACK, MENU_PORTF, MENU_INFO, \
    MENU_SET, MENU_HELP = states_letters[:num_states + x]
num_states += x
# Radar
x = 5
RADAR_SM_DAY, RADAR_SM_WEEK, RADAR_MI_DAY, RADAR_MI_WEEK, \
    RADAR_ORDER = states_letters[num_states : num_states + x]
num_states += x
# Tickers tracking
x = 3
TRACK_ADD, TRACK_REM, TRACK_WARN_REM = states_letters[num_states : num_states + x]
num_states += x
# Portfolio
x = 4
PORTF_ADD, PORTF_SUBTR, PORTF_SUBST, PORTF_CLEAR = states_letters[num_states : num_states + x]
num_states += x
# Info
x = 1
INFO = states_letters[num_states : num_states + x]
num_states += x
# Settings
x = 3
SET_TIME, SET_MODE, SET_RISK = states_letters[num_states : num_states + x]
num_states += x
# Time settings
x = 2
TIME_CHANGE, TIME_ACT_DEACT = states_letters[num_states : num_states + x]
num_states += x
# Tracker radar mode settings
x = 4 
MODE_SM_DAY, MODE_SM_WEEK, MODE_MI_DAY, MODE_MI_WEEK = states_letters[num_states : num_states + x]
num_states += x
# Risk management settings
x = 2
RISK_BLOCK, RISK_PERC = states_letters[num_states : num_states + x]
num_states += x
# Help
x = 6
HP_HDIW, HP_NUMS, HP_BUY, HP_SET, \
    HP_CONTACT, HP_SELECT = states_letters[num_states : num_states + x]
num_states += x
# Admin states and initial settings
x = 9
ADMIN_B, ADMIN_C, ADMIN_D, INIT_SET_A, INIT_SET_B, INIT_SET_C, \
    INIT_SET_D, INIT_SET_E, INIT_SET_F = states_letters[num_states : num_states + x]
num_states += x
# Meta states
x = 5
MENU, START_OVER, PREV_LEVEL, EXITING, EXIT = states_letters[num_states : num_states + x]
num_states += x
# Shortcut to ConvHandler.END
STOP = ConversationHandler.END


# ------------------ Bot initialization -----------------------

db = DBHelper()
fc = Functions()
db.setup()
# ADMINS: [Daniel Moreira]
ADMS_LIST = [545699841]


def read_token(config):
    parser = cfg.ConfigParser()
    parser.read(config)
    return parser.get('creds', 'token')


TOKEN = read_token('hidden/config.cfg')
remove_keyboard = {'remove_keyboard':True}
RKR = json.dumps(remove_keyboard)
def send_msg(user, msg, msg_id='', reply_markup=''):
    token = TOKEN
    url = (f'https://api.telegram.org/bot{token}/sendMessage?chat_id={user}&text={msg}&reply_to_message_id={msg_id}&reply_markup={reply_markup}&parse_mode=HTML')
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


def start(update, context):
    user_id = update.message.chat_id
    f_name = update.message.chat.first_name
    l_name = update.message.chat.last_name if update.message.chat.last_name else '-'
    name = f'{f_name} {l_name}'
    username = update.message.chat.username if update.message.chat.username else '-'
    user_type = update.message.chat.type
    is_bot = update._effective_user.is_bot

    if user_type == 'group' or is_bot:
        context.bot.leaveChat(chat_id=user_id)
    else:
        text = fc.func_user_start(user_id, name, username)
        if text:
            send_msg(user_id, text)
        else:
            admin_text = f'Novo usuário:\nuser_id: {user_id}\nname: {name}\nusername: @{username}\n'
            send_msg(ADMS_LIST[0], admin_text)

            user_text = 'Bem-vindo, investidor! Por favor, aguarde enquanto preparamos tudo.'
            send_msg(user_id, user_text)

# função inútil até agora
def enviar_id(update, context):
    user_id = update.message.chat_id
    f_name = update.message.chat.first_name
    l_name = update.message.chat.last_name if update.message.chat.last_name else ''
    name = f'{f_name} {l_name}'
    username = update.message.chat.username

    admin_text = f'Usuário mandou:\nuser_id: {user_id}\nname: {name}\nusername: @{username}\n'
    send_msg(ADMS_LIST[0], admin_text)


@restricted
def admin_a(update, context):
    global curr_admin_id
    curr_admin_id = update.message.chat_id
    msg_id = update.message.message_id

    text = 'Selecione uma das opções de adm ou clique em /cancelar:'
    opts = [
        ['Autorizar usuário'], 
        ['Desativar usuário'], 
        ['Editar usuário'], 
        ['Pesquisar usuário'], 
        ['Pesquisar por data']
    ]
    reply_markup = {'keyboard': opts, 'one_time_keyboard': True}
    k = json.dumps(reply_markup)

    send_msg(curr_admin_id, text, msg_id, k)
    # Configurações rápidas:
    # Qual classe de ações você irá utilizar com mais frequência? Small/Mid
    # Qual escala temporal você prefere? Diário/Semanal
    # Qual gerenciamento de risco acha mais adequado? Bloq/Porc Stop
        # Quantos bloq/Quantos %
    # Qual é o seu capital total para investir pelo método? Envie "0" (zero) se não quiser responder.
    # Tudo pronto! Você pode mudar essas configurações através do /menu.
    return ADMIN_B


def admin_b(update, context):
    msg_id = update.message.message_id
    msg = update.message.text

    opts = ['Autorizar usuário', 
            'Desativar usuário', 
            'Editar usuário', 
            'Pesquisar usuário',
            'Pesquisar por data'
    ]
    
    if msg in opts:
        choice = opts.index(msg)
        context.user_data['selection'] = choice
        if choice == 0:
            text = f'{opts[choice]} - digite o user_id e o nome completo, separado por vírgulas ' \
                    '(se não quiser inserir o nome completo, digite "0") ou clique em /cancelar:'
        elif choice == 1:
            text = f'{opts[choice]} - digite o user_id:'
        elif choice == 2:
            text = f'{opts[choice]} - digite o user_id, o campo a editar (nome | username | email) ' \
                    'e o novo dado, separados por vírgulas (exemplo "123456, username, @Usuario") ou clique em /cancelar:'
        elif choice == 3:
            text = f'{opts[choice]} - digite o campo de pesquisa (user_id | nome | username) ' \
                    'e a pesquisa, separados por vírgula (exemplo "username, @Usuario") ou clique em /cancelar:'
        elif choice == 4:
            text = f'{opts[choice]} - digite as datas inicial e final, separadas por vírgulas ' \
                    '(exemplo "15/02/2020, 26/02/2020") ou clique em /cancelar:'
        send_msg(curr_admin_id, text, msg_id, RKR)
        return ADMIN_C


def admin_c(update, context):
    msg_id = update.message.message_id
    msg = update.message.text
    choice = context.user_data['selection']

    text, success = fc.func_admin(msg, choice)
    if success and choice == 1:
        text += ' Sessão encerrada.'
    send_msg(curr_admin_id, text, msg_id)
    if success:
        if choice == 0:
            msg = msg.split(', ')
            context.user_data['user_id'] = msg[0]
            buttons = [[
                InlineKeyboardButton(text='Enviar formulário', callback_data=str(ADMIN_D)),
                InlineKeyboardButton(text='Sair', callback_data=str(STOP))
            ]]
            keyboard = InlineKeyboardMarkup(buttons)
            text = 'Deseja enviar o formulário de configs iniciais para o usuário?'
            update.message.reply_text(text=text, reply_markup=keyboard)
            return ADMIN_D
        else:
            return STOP
    else:
        return ADMIN_C


def admin_d(update, context):
    text = 'Formulário enviado!'
    update.callback_query.edit_message_text(text=text)
    cancel(update, context)
    configs_ini_a(update, context)


def configs_ini_a(update, context):
    user_id = context.user_data['user_id']
    text = 'funcionou, sim ou não?'
    buttons = [[
        InlineKeyboardButton(text='Vai pro B', callback_data=str(INIT_SET_B)),
        InlineKeyboardButton(text='Sair', callback_data=str(STOP))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)
    context.bot.sendMessage(chat_id=user_id, text=text, reply_markup=keyboard)

def configs_ini_b(update, context):
    text = 'funcionou de novo, sim ou não?'
    buttons = [[
        InlineKeyboardButton(text='Vai pro C', callback_data=str(INIT_SET_C)),
        InlineKeyboardButton(text='Sair', callback_data=str(STOP))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return INIT_SET_C

def configs_ini_c(update, context):
    text = 'chega'
    buttons = [[
        InlineKeyboardButton(text='Sair', callback_data=str(STOP))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return INIT_SET_D

def configs_ini_d(update, context):
    return INIT_SET_E

def configs_ini_e(update, context):
    return INIT_SET_F

def configs_ini_f(update, context):
    return STOP


# ------------------ Menu Principal -----------------------


def menu(update, context):
    if not context.user_data.get(START_OVER):
        user_id = update.message.chat_id
        user_allowed = db.user_check(user_id, 1)
    else:
        user_allowed = True

    if user_allowed:
        text = 'MENU PRINCIPAL - Selecione uma das opções.'
        buttons = [[
            InlineKeyboardButton(text='Radar!', callback_data=str(MENU_RADAR)),
        ], [
            InlineKeyboardButton(text='Carteira', callback_data=str(MENU_TRACK)),
            InlineKeyboardButton(text='Capital', callback_data=str(MENU_PORTF)),
        ], [
            InlineKeyboardButton(text='Meu status', callback_data=str(MENU_INFO)),
            InlineKeyboardButton(text='Configurações', callback_data=str(MENU_SET)),
            InlineKeyboardButton(text='Ajuda', callback_data=str(MENU_HELP))
        ], [
            InlineKeyboardButton(text='Fechar', callback_data=str(STOP))
        ]]
        keyboard = InlineKeyboardMarkup(buttons)

        if context.user_data.get(START_OVER):
            update.callback_query.answer()
            update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        else:
            update.message.reply_text('Olá! A qualquer momento você '
                                    'pode clicar em /ajuda.')
            update.message.reply_text(text=text, reply_markup=keyboard)

        context.user_data[START_OVER] = True
        return MENU
    else:
        text = 'Você ainda não está autorizado. Fale com o administrador!'
        update.message.reply_text(text=text)


# Radar
def menu_radar(update, context):
    context.user_data[PREV_LEVEL] = menu
    #ordem = fc.func_ordem (?) db.get_ordem [ordenação, ordenar por]
    text = 'RADAR - Selecione o modo de análise ou modifique a ordenação dos resultados. ' \
           'Atual: ordenar por ''''+ordem'''
    buttons = [[
        InlineKeyboardButton(text='Small Caps/Diário', callback_data=str(RADAR_SM_DAY)),
        InlineKeyboardButton(text='Mid Caps/Diário', callback_data=str(RADAR_MI_DAY))
    ], [
        InlineKeyboardButton(text='Small Caps/Semanal', callback_data=str(RADAR_SM_WEEK)),
        InlineKeyboardButton(text='Mid Caps/Semanal', callback_data=str(RADAR_MI_WEEK))
    ], [
        InlineKeyboardButton(text='Ordenar resultados por...', callback_data=str(RADAR_ORDER))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(STOP)),
        InlineKeyboardButton(text='Fechar', callback_data=str(EXIT))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[START_OVER] = True
    return MENU_RADAR


def radar_activate(update, context):
    text = 'Aguarde um momento, por favor.'
    mode = update.callback_query.data
    #donchian_principal


def radar_order(update, context):
    context.user_data[PREV_LEVEL] = menu_radar
    text = 'ORDENAR POR - Selecione qual dado será utilizado para ordenar os resultados:'
    buttons = [[
        InlineKeyboardButton(text='Nome do ativo (Stock)', callback_data='1')
    ], [
        InlineKeyboardButton(text='Canal superior (DUp)', callback_data='2')
    ], [
        InlineKeyboardButton(text='Último fechamento (Close)', callback_data='3')
    ], [
        InlineKeyboardButton(text='Canal inferior (DDown)', callback_data='4')
    ], [
        InlineKeyboardButton(text='Distância (Dist)', callback_data='5')
    ], [
        InlineKeyboardButton(text='"Trendabilidade" (Trend)', callback_data='6')
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(STOP)),
        InlineKeyboardButton(text='Fechar', callback_data=str(EXIT))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return RADAR_ORDER


def ordenacao(update, context):
    return 'abc'


# Carteira
def menu_carteira(update, context):
    context.user_data[PREV_LEVEL] = menu
    #carteira = fc.func_get_carteira (?)
    text = 'CARTEIRA - Selecione uma das opções. ' \
           'Composição atual da carteira: ''''+carteira'''
    buttons = [[
        InlineKeyboardButton(text='Adicionar ativo', callback_data=str(TRACK_ADD)),
        InlineKeyboardButton(text='Remover ativo', callback_data=str(TRACK_REM))
    ], [
        InlineKeyboardButton(text='Desativar último(s) alerta(s)', callback_data=str(TRACK_WARN_REM))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(STOP)),
        InlineKeyboardButton(text='Fechar', callback_data=str(EXIT))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[START_OVER] = True
    return MENU_TRACK


#def carteira_upd(update, context):
    #if add
    #text = ADD+'Digite o índice a ser adicionado:'
    #elif rem
    #text = REM+'Escolha o índice a ser removido:'
    #keyboard com os índices
    #elif retirar alerta
    #text = RETI+'Os alertas da carteira foram removidos até o preço mudar novamente.'


#def carteira_finalizar(update, context):
    #confirmar sucesso da alteração


# Capital
def menu_capital(update, context):
    context.user_data[PREV_LEVEL] = menu
    #portfolio = db.get_portfolio (?)
    text = 'CAPITAL - Selecione uma das opções. ' \
           'Valor atual de carteira: ''''+portfolio'''
    buttons = [[
        InlineKeyboardButton(text='Adicionar ao valor', callback_data=str(PORTF_ADD)),
        InlineKeyboardButton(text='Subtrair do valor', callback_data=str(PORTF_SUBTR))
    ], [
        InlineKeyboardButton(text='Substituir o valor', callback_data=str(PORTF_SUBST)),
        InlineKeyboardButton(text='Zerar', callback_data=str(PORTF_CLEAR))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(STOP)),
        InlineKeyboardButton(text='Fechar', callback_data=str(EXIT))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[START_OVER] = True
    return MENU_PORTF


#def capital_upd(update, context):
    #if add/subtrair/subst
    #text = '''ADD/SUBTRAIR/SUBST'''+'Digite o valor:'
    #elif zerar
    #text = 'Tem certeza que deseja zerar?'


def capital_finalizar(update, context):
    return 'confirmado ou rejeitado'


# Info
def menu_info(update, context):
    context.user_data[PREV_LEVEL] = menu
    text = 'MEU STATUS:'
    context.user_data[START_OVER] = False
    #blabla reply_text
    return STOP


# Configurações
def menu_config(update, context):
    context.user_data[PREV_LEVEL] = menu
    text = 'CONFIGURAÇÕES - Selecione uma das opções.'
    buttons = [[
        InlineKeyboardButton(text='Configs de hora', callback_data=str(SET_TIME))
    ], [
        InlineKeyboardButton(text='Modo a ser usado automaticamente', callback_data=str(SET_MODE))
    ], [
        InlineKeyboardButton(text='Gerenciamento de risco', callback_data=str(SET_RISK)),
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(STOP)),
        InlineKeyboardButton(text='Fechar', callback_data=str(EXIT))
    ]]

    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[START_OVER] = True
    return MENU_SET


# Hora
def config_hora(update, context):
    context.user_data[PREV_LEVEL] = menu_config
    text = 'CONFIGURAÇÕES DE HORA - Selecione uma das opções.'
    buttons = [[
        InlineKeyboardButton(text='Mudar a hora dos alertas automáticos', callback_data=str(TIME_CHANGE))
    ], [
        InlineKeyboardButton(text='Ativar/Desativar alertas automáticos', callback_data=str(TIME_ACT_DEACT))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(STOP)),
        InlineKeyboardButton(text='Fechar', callback_data=str(EXIT))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return SET_TIME


def hora_upd(update, context):
    return 'abc'


def hora_finalizar(update, context):
    return 'confirmar sucesso da alteração'


# Classe/escala temporal
def config_mode(update, context):
    context.user_data[PREV_LEVEL] = menu_config
    text = 'CONFIGURAÇÕES DE MODO - Selecione a classe de ativos e a escala temporal a serem ' \
           'usados no alerta automático.'
    buttons = [[
        InlineKeyboardButton(text='Small Caps/Diário', callback_data=str(RADAR_SM_DAY)),
        InlineKeyboardButton(text='Mid Caps/Diário', callback_data=str(RADAR_MI_DAY))
    ], [
        InlineKeyboardButton(text='Small Caps/Semanal', callback_data=str(RADAR_SM_WEEK)),
        InlineKeyboardButton(text='Mid Caps/Semanal', callback_data=str(RADAR_MI_WEEK))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(STOP)),
        InlineKeyboardButton(text='Fechar', callback_data=str(EXIT))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return SET_MODE


def mode_upd(update, context):
    return 'atualizar e confirmar sucesso'


# Gerenciamento de risco
def config_risco(update, context):
    context.user_data[PREV_LEVEL] = menu_config
    text = 'CONFIGURAÇÕES DE RISCO - Selecione o gerenciamento de risco a ser utilizado no cálculo do volume: '
    buttons = [[
        InlineKeyboardButton(text='Bloquinho por operação', callback_data=str(RISK_BLOCK)),
    ], [
        InlineKeyboardButton(text='Porcentagem relativa ao stop', callback_data=str(RISK_PERC))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(STOP)),
        InlineKeyboardButton(text='Fechar', callback_data=str(EXIT))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return SET_RISK


# Bloquinhos/ porc
def risco_upd(update, context):
    #perguntar o número de bloquinhos/ porc
    return 'abc'


# Porcentagem relativa ao stop
def risco_finalizar(update, context):
    #confirmar sucesso
    return 'abc'


# Ajuda
def menu_ajuda(update, context):
    context.user_data[PREV_LEVEL] = menu
    text = 'AJUDA - Selecione um tópico: '
    buttons = [[
        InlineKeyboardButton(text='Como o bot funciona?', callback_data=str(HP_HDIW)),
    ], [
        InlineKeyboardButton(text='O que são os números no radar?', callback_data=str(HP_NUMS))
    ], [
        InlineKeyboardButton(text='Qual ação do radar eu devo comprar?', callback_data=str(HP_BUY))
    ], [
        InlineKeyboardButton(text='Quais e o que são as configurações?', callback_data=str(HP_SET))
    ], [
        InlineKeyboardButton(text='Outras dúvidas e sugestões', callback_data=str(HP_CONTACT))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(STOP)),
        InlineKeyboardButton(text='Fechar', callback_data=str(EXIT))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[START_OVER] = True
    return MENU_HELP


def ajuda_finalizar(update, context):
    context.user_data[PREV_LEVEL] = menu_ajuda
    text = 'AJUDA - TITULO QUALQUER'
    buttons = [[
        InlineKeyboardButton(text='Voltar', callback_data=str(STOP)),
        InlineKeyboardButton(text='Fechar', callback_data=str(EXIT))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[START_OVER] = True
    return MENU_HELP


# Voltar
def voltar(update, context):
    update.callback_query.answer()
    context.user_data[START_OVER] = True
    context.user_data[PREV_LEVEL](update, context)
    return STOP


# Finalizar a conversa
def stop(update, context):
    context.user_data[START_OVER] = False
    update.callback_query.answer()
    text = 'Até mais!'
    update.callback_query.edit_message_text(text=text)
    return EXITING


def end(update, context):
    print('entrei no end')
    context.user_data[START_OVER] = False
    update.callback_query.answer()
    text = 'Até mais!'
    update.callback_query.edit_message_text(text=text)
    return STOP


@restricted
def cancel(update, context):
    print('entrei no cancel')
    text = 'Sessão de adm encerrada.'
    send_msg(curr_admin_id, text, '', RKR)
    return STOP


# Error handler
def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    
    
    # Ajuda
    ajuda_finalizar_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            ajuda_finalizar, 
            pattern='^{0}$|^{1}$|^{2}$|^{3}$|^{4}$'.format(str(HP_HDIW),
                                                           str(HP_NUMS),
                                                           str(HP_BUY),
                                                           str(HP_SET),
                                                           str(HP_CONTACT))
        )],
        states={
            HP_SELECT: []
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(EXIT)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU_HELP,
            EXITING: EXITING
        }
    )
    
    menu_ajuda_handlers = [
        ajuda_finalizar_conv
    ]
    menu_ajuda_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_ajuda, pattern='^'+str(MENU_HELP)+'$')],
        states={
            MENU_HELP: menu_ajuda_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(EXIT)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU,
            EXITING: STOP
        }
    )


    # Configurações
    config_risco_handlers = [
        CallbackQueryHandler(risco_upd, pattern='^{0}$|^{1}$'.format(str(RISK_BLOCK),
                                                                     str(RISK_PERC)))
    ]
    config_risco_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(config_risco, pattern='^'+str(SET_RISK)+'$')],
        states={
            SET_RISK: config_risco_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(EXIT)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU_SET,
            EXITING: EXITING
        }
    )

    config_mode_handlers = [
        #CallbackQueryHandler(
        #   mode_upd, 
        #   pattern='^{0}$|^{1}$|^{2}$|^{3}$'.format(str(RADAR_SM_DAY),
        #                                            str(RADAR_MI_DAY),
        #                                            str(RADAR_SM_WEEK),
        #                                            str(RADAR_MI_WEEK))
        #)
    ]
    config_mode_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(config_mode, pattern='^'+str(SET_MODE)+'$')],
        states={
            SET_MODE: config_mode_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(EXIT)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU_SET,
            EXITING: EXITING
        }
    )

    config_hora_handlers = [
        CallbackQueryHandler(hora_upd, pattern='^{0}$|^{1}$'.format(str(TIME_CHANGE),
                                                                    str(TIME_ACT_DEACT)))
    ]
    config_hora_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(config_hora, pattern='^'+str(SET_TIME)+'$')],
        states={
            SET_TIME: config_hora_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(EXIT)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU_SET,
            EXITING: EXITING
        }
    )

    menu_config_handlers = [
        config_hora_conv,
        config_mode_conv,
        config_risco_conv
    ]
    menu_config_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_config, pattern='^'+str(MENU_SET)+'$')],
        states={
            MENU_SET: menu_config_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(EXIT)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU,
            EXITING: STOP
        }
    )


    # Capital
    menu_capital_handlers = [
        #CallbackQueryHandler(
        #   capital_upd, 
        #   pattern='^{0}$|^{1}$|^{2}$|^{3}$'.format(str(PORTF_ADD),
        #                                            str(PORTF_SUBTR),
        #                                            str(PORTF_SUBST),
        #                                            str(PORTF_CLEAR))
        #)
    ]
    menu_capital_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_capital, pattern='^'+str(MENU_PORTF)+'$')],
        states={
            MENU_PORTF: menu_capital_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(EXIT)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU,
            EXITING: STOP
        }
    )


    # Carteira
    menu_carteira_handlers = [
        #CallbackQueryHandler(
        #   carteira_upd, 
        #   pattern='^{0}$|^{1}$|^{2}$'.format(str(TRACK_ADD),
        #                                      str(TRACK_REM),
        #                                      str(TRACK_WARN_REM))
        #)
    ]
    menu_carteira_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_carteira, pattern='^'+str(MENU_TRACK)+'$')],
        states={
            MENU_TRACK: menu_carteira_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(EXIT)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU,
            EXITING: STOP
        }
    )


    # Radar
    radar_order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(radar_order, pattern='^'+str(RADAR_ORDER)+'$')],
        states={
            RADAR_ORDER: [CallbackQueryHandler(ordenacao, pattern=r'^\d$')],
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(EXIT)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU_RADAR,
            EXITING: EXITING
        }
    )

    menu_radar_handlers = [
        CallbackQueryHandler(radar_activate, pattern='^'+str(RADAR_SM_DAY)+'$'),
        radar_order_conv
    ]
    menu_radar_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_radar, pattern='^'+str(MENU_RADAR)+'$')],
        states={
            MENU_RADAR: menu_radar_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(EXIT)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU,
            EXITING: STOP
        }
    )


    # Menu Principal
    menu_handlers = [
        menu_radar_conv,
        menu_carteira_conv,
        menu_capital_conv,
        CallbackQueryHandler(menu_info, pattern='^'+str(MENU_INFO)+'$'),
        menu_config_conv,
        menu_ajuda_conv,
    ]
    menu_conv = ConversationHandler(
        entry_points=[CommandHandler('menu', menu)],
        states={
            MENU: menu_handlers,
            STOP: [CallbackQueryHandler(end, pattern='^'+str(STOP)+'$')]
        },
        fallbacks=[CallbackQueryHandler(end, pattern='^'+str(STOP)+'$')]
    )


    # Configs Iniciais
    configs_ini_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(configs_ini_b, pattern='^'+str(INIT_SET_B)+'$')],
        states={
            INIT_SET_C: [CallbackQueryHandler(configs_ini_c, pattern='^'+str(INIT_SET_C)+'$'),
                MessageHandler(Filters.text, configs_ini_c)],
            INIT_SET_D: [MessageHandler(Filters.text, configs_ini_d)],
            INIT_SET_E: [MessageHandler(Filters.text, configs_ini_e)],
            INIT_SET_F: [MessageHandler(Filters.text, configs_ini_f)]
        },
        fallbacks=[MessageHandler(Filters.regex('^(terminar)$'), end)]
    )


    # Admin
    admin_conv = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_a)],
        states={
            ADMIN_B: [CommandHandler('admin', admin_a),
                      MessageHandler(Filters.regex('^(Autorizar usuário|' \
                                                   'Desativar usuário|' \
                                                   'Editar usuário|' \
                                                   'Pesquisar usuário|' \
                                                   'Pesquisar por data)$'), admin_b)],

            ADMIN_C: [CommandHandler('admin', admin_a),
                      MessageHandler(~Filters.command, admin_c)],
                      
            ADMIN_D: [CallbackQueryHandler(admin_d, pattern='^'+str(ADMIN_D)+'$')]
        },
        fallbacks=[
            CommandHandler('cancelar', cancel), 
            CallbackQueryHandler(cancel, pattern='^'+str(STOP)+'$')
        ]
    )


    start_comm = CommandHandler('start', start)


    dp.add_handler(menu_conv)
    dp.add_handler(admin_conv)
    dp.add_handler(configs_ini_conv)

    dp.add_handler(start_comm)

    # log all errors
    dp.add_error_handler(error)

    updater.start_polling()

if __name__ == '__main__':
    main()