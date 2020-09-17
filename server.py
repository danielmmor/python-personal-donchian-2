import logging
import json
import configparser as cfg
import requests
import string
from functools import wraps
from telegram import (InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)
from buttons import Buttons
from dbhelper import DBHelper
from functs import Functions

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
RADAR_SM_DAY, RADAR_SM_WEEK, RADAR_MI_DAY, RADAR_MI_WEEK, \
    RADAR_ORDER = states_codes[num_states : num_states + x]
num_states += x
# Ticker tracker
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
    global db, fc, bt, rkr, ADMS_LIST, token, curr_admin_id, admin_opts
    db = DBHelper()
    fc = Functions()
    bt = Buttons()
    rkr = json.dumps({'remove_keyboard':True})
    # ADMINS: [Daniel Moreira]
    ADMS_LIST = [545699841]
    token = read_token('hidden/config.cfg')
    admin_opts = [
        'Autorizar usuário', 
        'Desativar usuário', 
        'Editar usuário', 
        'Pesquisar usuário', 
        'Pesquisar por data'
    ]
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

@restricted
def admin_a(update, context):
    curr_admin_id = update.message.chat_id
    msg_id = update.message.message_id
    admin_text = 'Selecione uma das opções de adm ou clique em /cancelar:'
    keyboard = [[x] for x in admin_opts]
    reply_markup = json.dumps({'keyboard': keyboard, 'one_time_keyboard': True})
    send_msg(curr_admin_id, admin_text, msg_id, reply_markup)
    return ADMIN_B

def admin_b(update, context):
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
        send_msg(curr_admin_id, admin_text, msg_id, rkr)
        return ADMIN_C

def admin_c(update, context):
    msg_id = update.message.reply_to_message_id
    msg = update.message.text
    choice = context.user_data['selection']
    admin_text, success = fc.func_admin(msg, choice)
    update.message.reply_text(text=admin_text)
    return STOP
    #continuar depois, revisar toda a parte de admin

def admin_d(update, context):
    admin_text = 'Formulário enviado!'
    update.callback_query.edit_message_text(text=admin_text)
    #cancel(update, context)
    init_set_a(update, context)

def init_set_a(update, context):
    user_id = context.user_data['user_id']
    text = 'funcionou, sim ou não?'
    buttons = bt.buttons(INIT_SET_A)
    context.bot.sendMessage(chat_id=user_id, text=text, reply_markup=IKM(buttons))

def init_set_b(update, context):
    text = 'funcionou de novo, sim ou não?'
    buttons = bt.buttons(INIT_SET_B)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return INIT_SET_C

def init_set_c(update, context):
    text = 'chega'
    buttons = [[
        IKB(text='Sair', callback_data=str(STOP))
    ]]
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return INIT_SET_D

def init_set_d(update, context):
    return INIT_SET_E

def init_set_e(update, context):
    return INIT_SET_F

def init_set_f(update, context):
    return STOP


# ------------------ Main menu ------------------

def menu(update, context):
    text = 'MENU PRINCIPAL - Selecione uma das opções.'
    buttons = bt.buttons(MENU)
    if context.user_data.get(START_OVER):
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
        return MENU
    else:
        user_id = update.message.chat_id
        user_allowed = db.user_check(user_id, 1)
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
    context.user_data[PREV_LEVEL] = menu
    #ordem = fc.func_ordem (?) db.get_ordem [ordenação, ordenar por]
    text = 'RADAR - Selecione o modo de análise ou modifique a ordenação dos resultados. ' \
           'Atual: ordenar por ''''+ordem'''
    buttons = bt.buttons(MENU_RADAR)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return MENU_RADAR

def radar_activate(update, context):
    text = 'Aguarde um momento, por favor.'
    mode = update.callback_query.data
    #donchian_principal

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
    context.user_data[PREV_LEVEL] = menu
    #carteira = fc.func_get_carteira (?)
    text = 'CARTEIRA - Selecione uma das opções. ' \
           'Composição atual da carteira: ''''+carteira'''
    buttons = bt.buttons(MENU_TRACK)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return MENU_TRACK

#def track_upd(update, context):
    #if add
    #text = ADD+'Digite o índice a ser adicionado:'
    #elif rem
    #text = REM+'Escolha o índice a ser removido:'
    #keyboard com os índices
    #elif retirar alerta
    #text = RETI+'Os alertas da carteira foram removidos até o preço mudar novamente.'

#def track_exit(update, context):
    #confirmar sucesso da alteração

# Portfolio
def menu_portf(update, context):
    context.user_data[PREV_LEVEL] = menu
    #portfolio = db.get_portfolio (?)
    text = 'CAPITAL - Selecione uma das opções. ' \
           'Valor atual de carteira: ''''+portfolio'''
    buttons = bt.buttons(MENU_PORTF)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return MENU_PORTF

#def portf_upd(update, context):
    #if add/subtrair/subst
    #text = '''ADD/SUBTRAIR/SUBST'''+'Digite o valor:'
    #elif zerar
    #text = 'Tem certeza que deseja zerar?'

def portf_exit(update, context):
    return 'confirmado ou rejeitado'

# Info
def menu_info(update, context):
    context.user_data[PREV_LEVEL] = menu
    text = 'MEU STATUS:'
    context.user_data[START_OVER] = False
    #blabla reply_text
    return STOP

# Settings
def menu_set(update, context):
    context.user_data[PREV_LEVEL] = menu
    text = 'CONFIGURAÇÕES - Selecione uma das opções.'
    buttons = bt.buttons(MENU_SET)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return MENU_SET

# Time settings
def set_time(update, context):
    context.user_data[PREV_LEVEL] = menu_set
    text = 'CONFIGURAÇÕES DE HORA - Selecione uma das opções.'
    buttons = bt.buttons(SET_TIME)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return SET_TIME

def time_upd(update, context):
    return 'abc'

def time_exit(update, context):
    return 'confirmar sucesso da alteração'

# Radar mode settings
def set_mode(update, context):
    context.user_data[PREV_LEVEL] = menu_set
    text = 'CONFIGURAÇÕES DE MODO - Selecione a classe de ativos e a escala temporal a serem ' \
           'usados no alerta automático.'
    buttons = bt.buttons(SET_MODE)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return SET_MODE

def mode_upd(update, context):
    return 'atualizar e confirmar sucesso'

# Risk mngmt settings
def set_risk(update, context):
    context.user_data[PREV_LEVEL] = menu_set
    text = 'CONFIGURAÇÕES DE RISCO - Selecione o gerenciamento de risco a ser utilizado no cálculo do volume: '
    buttons = bt.buttons(SET_RISK)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    return SET_RISK

def risk_upd(update, context):
    #perguntar o número de bloquinhos/ porc após ter escolhido no anterior
    return 'abc'

def risk_exit(update, context):
    #confirmar sucesso
    return 'abc'

# Help
def menu_help(update, context):
    context.user_data[PREV_LEVEL] = menu
    text = 'AJUDA - Selecione um tópico: '
    buttons = bt.buttons(MENU_HELP)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=IKM(buttons))
    context.user_data[START_OVER] = True
    return MENU_HELP

def help_exit(update, context):
    context.user_data[PREV_LEVEL] = menu_help
    text = 'AJUDA - TITULO QUALQUER'
    buttons = bt.buttons(HP_EXIT)
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
    update.callback_query.answer()
    text = 'Até mais!'
    update.callback_query.edit_message_text(text=text)
    return STOP

@restricted
def cancel(update, context):
    print('entrei no cancel')
    text = 'Sessão de adm encerrada.'
    send_msg(curr_admin_id, text, '', rkr)
    return STOP

# Error handler
def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(token, use_context=True)
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
    set_risk_handlers = [
        CallbackQueryHandler(risk_upd, pattern='^{0}$|^{1}$'.format(RISK_BLOCK,
                                                                    RISK_PERC))
    ]
    set_risk_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_risk, pattern='^'+str(SET_RISK)+'$')],
        states={SET_RISK: set_risk_handlers,},
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU_SET,
            EXITING: EXITING
        }
    )
    set_mode_handlers = [
        #CallbackQueryHandler(
        #   mode_upd, 
        #   pattern='^{0}$|^{1}$|^{2}$|^{3}$'.format(str(RADAR_SM_DAY),
        #                                            str(RADAR_MI_DAY),
        #                                            str(RADAR_SM_WEEK),
        #                                            str(RADAR_MI_WEEK))
        #)
    ]
    set_mode_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_mode, pattern='^'+SET_MODE+'$')],
        states={SET_MODE: set_mode_handlers,},
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU_SET,
            EXITING: EXITING
        }
    )
    set_time_handlers = [
        CallbackQueryHandler(time_upd, pattern='^{0}$|^{1}$'.format(TIME_CHANGE,
                                                                    TIME_ACT_DEACT))
    ]
    set_time_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_time, pattern='^'+SET_TIME+'$')],
        states={SET_TIME: set_time_handlers,},
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+EXIT+'$'),
            CallbackQueryHandler(back, pattern='^'+str(STOP)+'$')
        ],
        map_to_parent={
            STOP: MENU_SET,
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
        states={MENU_SET: menu_set_handlers,},
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
    menu_portf_handlers = [
        #CallbackQueryHandler(
        #   capital_upd, 
        #   pattern='^{0}$|^{1}$|^{2}$|^{3}$'.format(str(PORTF_ADD),
        #                                            str(PORTF_SUBTR),
        #                                            str(PORTF_SUBST),
        #                                            str(PORTF_CLEAR))
        #)
    ]
    menu_portf_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_portf, pattern='^'+MENU_PORTF+'$')],
        states={MENU_PORTF: menu_portf_handlers,},
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
    menu_track_handlers = [
        #CallbackQueryHandler(
        #   carteira_upd, 
        #   pattern='^{0}$|^{1}$|^{2}$'.format(str(TRACK_ADD),
        #                                      str(TRACK_REM),
        #                                      str(TRACK_WARN_REM))
        #)
    ]
    menu_track_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_track, pattern='^'+MENU_TRACK+'$')],
        states={MENU_TRACK: menu_track_handlers,},
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
        states={RADAR_ORDER: [CallbackQueryHandler(order, pattern=r'^\d$')],},
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
        CallbackQueryHandler(radar_activate, pattern='^'+RADAR_SM_DAY+'$'),
        radar_order_conv
    ]
    menu_radar_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_radar, pattern='^'+MENU_RADAR+'$')],
        states={MENU_RADAR: menu_radar_handlers,},
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
        entry_points=[CallbackQueryHandler(init_set_b, pattern='^'+INIT_SET_B+'$')],
        states={
            INIT_SET_C: [CallbackQueryHandler(init_set_c, pattern='^'+INIT_SET_C+'$'),
                MessageHandler(Filters.text, init_set_c)],
            INIT_SET_D: [MessageHandler(Filters.text, init_set_d)],
            INIT_SET_E: [MessageHandler(Filters.text, init_set_e)],
            INIT_SET_F: [MessageHandler(Filters.text, init_set_f)]
        },
        fallbacks=[MessageHandler(Filters.regex('^(terminar)$'), end)]
    )
    # Admin
    admin_conv = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_a)],
        states={
            ADMIN_B: [CommandHandler('admin', admin_a),
                      MessageHandler(Filters.regex('^('+admin_opts[0]+'|' \
                                                   +admin_opts[1]+'|' \
                                                   +admin_opts[2]+'|' \
                                                   +admin_opts[3]+'|' \
                                                   +admin_opts[4]+')$'), admin_b)],

            ADMIN_C: [CommandHandler('admin', admin_a),
                      MessageHandler(~Filters.command, admin_c)],
                      
            ADMIN_D: [CallbackQueryHandler(admin_d, pattern='^'+ADMIN_D+'$')]
        },
        fallbacks=[
            CommandHandler('cancelar', cancel), 
            CallbackQueryHandler(cancel, pattern='^'+str(STOP)+'$')
        ]
    )

    start_comm = CommandHandler('start', start)
    dp.add_handler(menu_conv)
    dp.add_handler(admin_conv)
    dp.add_handler(init_set_conv)
    dp.add_handler(start_comm)
    # log all errors
    dp.add_error_handler(error)
    updater.start_polling()

if __name__ == '__main__':
    init()
    main()