#!/usr/bin/env python
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


# ------------------ Definição de states pra navegação -----------------------


states_letters = ['Aa', 'Ab', 'Ac', 'Ad', 'Ae', 'Af', 'Ag', 'Ah', 'Ai', 'Aj', 'Ak', 'Al', 'Am', 'An', 'Ao', 'Ap', 'Aq', 'Ar', 'As', 'At', 'Au', 'Av', 'Aw', 'Ax', 'Ay', 'Az', 'Ba', 'Bb', 'Bc', 'Bd', 'Be', 'Bf', 'Bg', 'Bh', 'Bi', 'Bj', 'Bk', 'Bl', 'Bm', 'Bn', 'Bo', 'Bp', 'Bq', 'Br', 'Bs', 'Bt', 'Bu', 'Bv', 'Bw', 'Bx', 'By', 'Bz', 'Ca', 'Cb', 'Cc', 'Cd', 'Ce', 'Cf', 'Cg', 'Ch', 'Ci', 'Cj', 'Ck', 'Cl', 'Cm', 'Cn', 'Co', 'Cp', 'Cq', 'Cr', 'Cs', 'Ct', 'Cu', 'Cv', 'Cw', 'Cx', 'Cy', 'Cz', 'Da', 'Db', 'Dc', 'Dd', 'De', 'Df', 'Dg', 'Dh', 'Di', 'Dj', 'Dk', 'Dl', 'Dm', 'Dn', 'Do', 'Dp', 'Dq', 'Dr', 'Ds', 'Dt', 'Du', 'Dv', 'Dw', 'Dx', 'Dy', 'Dz', 'Ea', 'Eb', 'Ec', 'Ed', 'Ee', 'Ef', 'Eg', 'Eh', 'Ei', 'Ej', 'Ek', 'El', 'Em', 'En', 'Eo', 'Ep', 'Eq', 'Er', 'Es', 'Et', 'Eu', 'Ev', 'Ew', 'Ex', 'Ey', 'Ez', 'Fa', 'Fb', 'Fc', 'Fd', 'Fe', 'Ff', 'Fg', 'Fh', 'Fi', 'Fj', 'Fk', 'Fl', 'Fm', 'Fn', 'Fo', 'Fp', 'Fq', 'Fr', 'Fs', 'Ft', 'Fu', 'Fv', 'Fw', 'Fx', 'Fy', 'Fz', 'Ga', 'Gb', 'Gc', 'Gd', 'Ge', 'Gf', 'Gg', 'Gh', 'Gi', 'Gj', 'Gk', 'Gl', 'Gm', 'Gn', 'Go', 'Gp', 'Gq', 'Gr', 'Gs', 'Gt', 'Gu', 'Gv', 'Gw', 'Gx', 'Gy', 'Gz', 'Ha', 'Hb', 'Hc', 'Hd', 'He', 'Hf', 'Hg', 'Hh', 'Hi', 'Hj', 'Hk', 'Hl', 'Hm', 'Hn', 'Ho', 'Hp', 'Hq', 'Hr', 'Hs', 'Ht', 'Hu', 'Hv', 'Hw', 'Hx', 'Hy', 'Hz', 'Ia', 'Ib', 'Ic', 'Id', 'Ie', 'If', 'Ig', 'Ih', 'Ii', 'Ij', 'Ik', 'Il', 'Im', 'In', 'Io', 'Ip', 'Iq', 'Ir', 'Is', 'It', 'Iu', 'Iv', 'Iw', 'Ix', 'Iy', 'Iz', 'Ja', 'Jb', 'Jc', 'Jd', 'Je', 'Jf', 'Jg', 'Jh', 'Ji', 'Jj', 'Jk', 'Jl', 'Jm', 'Jn', 'Jo', 'Jp', 'Jq', 'Jr', 'Js', 'Jt', 'Ju', 'Jv', 'Jw', 'Jx', 'Jy', 'Jz', 'Ka', 'Kb', 'Kc', 'Kd', 'Ke', 'Kf', 'Kg', 'Kh', 'Ki', 'Kj', 'Kk', 'Kl', 'Km', 'Kn', 'Ko', 'Kp', 'Kq', 'Kr', 'Ks', 'Kt', 'Ku', 'Kv', 'Kw', 'Kx', 'Ky', 'Kz', 'La', 'Lb', 'Lc', 'Ld', 'Le', 'Lf', 'Lg', 'Lh', 'Li', 'Lj', 'Lk', 'Ll', 'Lm', 'Ln', 'Lo', 'Lp', 'Lq', 'Lr', 'Ls', 'Lt', 'Lu', 'Lv', 'Lw', 'Lx', 'Ly', 'Lz', 'Ma', 'Mb', 'Mc', 'Md', 'Me', 'Mf', 'Mg', 'Mh', 'Mi', 'Mj', 'Mk', 'Ml', 'Mm', 'Mn', 'Mo', 'Mp', 'Mq', 'Mr', 'Ms', 'Mt', 'Mu', 'Mv', 'Mw', 'Mx', 'My', 'Mz', 'Na', 'Nb', 'Nc', 'Nd', 'Ne', 'Nf', 'Ng', 'Nh', 'Ni', 'Nj', 'Nk', 'Nl', 'Nm', 'Nn', 'No', 'Np', 'Nq', 'Nr', 'Ns', 'Nt', 'Nu', 'Nv', 'Nw', 'Nx', 'Ny', 'Nz', 'Oa', 'Ob', 'Oc', 'Od', 'Oe', 'Of', 'Og', 'Oh', 'Oi', 'Oj', 'Ok', 'Ol', 'Om', 'On', 'Oo', 'Op', 'Oq', 'Or', 'Os', 'Ot', 'Ou', 'Ov', 'Ow', 'Ox', 'Oy', 'Oz', 'Pa', 'Pb', 'Pc', 'Pd', 'Pe', 'Pf', 'Pg', 'Ph', 'Pi', 'Pj', 'Pk', 'Pl', 'Pm', 'Pn', 'Po', 'Pp', 'Pq', 'Pr', 'Ps', 'Pt', 'Pu', 'Pv', 'Pw', 'Px', 'Py', 'Pz', 'Qa', 'Qb', 'Qc', 'Qd', 'Qe', 'Qf', 'Qg', 'Qh', 'Qi', 'Qj', 'Qk', 'Ql', 'Qm', 'Qn', 'Qo', 'Qp', 'Qq', 'Qr', 'Qs', 'Qt', 'Qu', 'Qv', 'Qw', 'Qx', 'Qy', 'Qz', 'Ra', 'Rb', 'Rc', 'Rd', 'Re', 'Rf', 'Rg', 'Rh', 'Ri', 'Rj', 'Rk', 'Rl', 'Rm', 'Rn', 'Ro', 'Rp', 'Rq', 'Rr', 'Rs', 'Rt', 'Ru', 'Rv', 'Rw', 'Rx', 'Ry', 'Rz', 'Sa', 'Sb', 'Sc', 'Sd', 'Se', 'Sf', 'Sg', 'Sh', 'Si', 'Sj', 'Sk', 'Sl', 'Sm', 'Sn', 'So', 'Sp', 'Sq', 'Sr', 'Ss', 'St', 'Su', 'Sv', 'Sw', 'Sx', 'Sy', 'Sz', 'Ta', 'Tb', 'Tc', 'Td', 'Te', 'Tf', 'Tg', 'Th', 'Ti', 'Tj', 'Tk', 'Tl', 'Tm', 'Tn', 'To', 'Tp', 'Tq', 'Tr', 'Ts', 'Tt', 'Tu', 'Tv', 'Tw', 'Tx', 'Ty', 'Tz', 'Ua', 'Ub', 'Uc', 'Ud', 'Ue', 'Uf', 'Ug', 'Uh', 'Ui', 'Uj', 'Uk', 'Ul', 'Um', 'Un', 'Uo', 'Up', 'Uq', 'Ur', 'Us', 'Ut', 'Uu', 'Uv', 'Uw', 'Ux', 'Uy', 'Uz', 'Va', 'Vb', 'Vc', 'Vd', 'Ve', 'Vf', 'Vg', 'Vh', 'Vi', 'Vj', 'Vk', 'Vl', 'Vm', 'Vn', 'Vo', 'Vp', 'Vq', 'Vr', 'Vs', 'Vt', 'Vu', 'Vv', 'Vw', 'Vx', 'Vy', 'Vz', 'Wa', 'Wb', 'Wc', 'Wd', 'We', 'Wf', 'Wg', 'Wh', 'Wi', 'Wj', 'Wk', 'Wl', 'Wm', 'Wn', 'Wo', 'Wp', 'Wq', 'Wr', 'Ws', 'Wt', 'Wu', 'Wv', 'Ww', 'Wx', 'Wy', 'Wz', 'Xa', 'Xb', 'Xc', 'Xd', 'Xe', 'Xf', 'Xg', 'Xh', 'Xi', 'Xj', 'Xk', 'Xl', 'Xm', 'Xn', 'Xo', 'Xp', 'Xq', 'Xr', 'Xs', 'Xt', 'Xu', 'Xv', 'Xw', 'Xx', 'Xy', 'Xz', 'Ya', 'Yb', 'Yc', 'Yd', 'Ye', 'Yf', 'Yg', 'Yh', 'Yi', 'Yj', 'Yk', 'Yl', 'Ym', 'Yn', 'Yo', 'Yp', 'Yq', 'Yr', 'Ys', 'Yt', 'Yu', 'Yv', 'Yw', 'Yx', 'Yy', 'Yz', 'Za', 'Zb', 'Zc', 'Zd', 'Ze', 'Zf', 'Zg', 'Zh', 'Zi', 'Zj', 'Zk', 'Zl', 'Zm', 'Zn', 'Zo', 'Zp', 'Zq', 'Zr', 'Zs', 'Zt', 'Zu', 'Zv', 'Zw', 'Zx', 'Zy', 'Zz']
num_states = 0
# Menu
x = 6
MENU_RADAR, MENU_CARTEIRA, MENU_CAPITAL, MENU_INFO, \
    MENU_CONFIG, MENU_AJUDA = states_letters[:num_states + x]
num_states += x
# Radar
x = 5
RADAR_SM_DI, RADAR_SM_SEM, RADAR_MI_DI, RADAR_MI_SEM, \
    RADAR_ORDER = states_letters[num_states : num_states + x]
num_states += x
# Carteira
x = 3
CARTEIRA_ADD, CARTEIRA_REM, CARTEIRA_RET_ALERTA = states_letters[num_states : num_states + x]
num_states += x
# Capital
x = 4
CAPITAL_ADD, CAPITAL_SUBTR, CAPITAL_SUBST, CAPITAL_ZER = states_letters[num_states : num_states + x]
num_states += x
# Info
x = 1
INFO = states_letters[num_states : num_states + x]
num_states += x
# Configurações
x = 3
CONFIG_HORA, CONFIG_MODE, CONFIG_RISCO = states_letters[num_states : num_states + x]
num_states += x
# Config de hora
x = 2
HORA_MUDAR, HORA_ACT_DEACT = states_letters[num_states : num_states + x]
num_states += x
# Config de modo de radar para a carteira
x = 4 
MODE_SM_DI, MODE_SM_SEM, MODE_MI_DI, MODE_MI_SEM = states_letters[num_states : num_states + x]
num_states += x
# Config de gerenciamento de risco
x = 2
RISCO_BLOQ, RISCO_PORC = states_letters[num_states : num_states + x]
num_states += x
# Ajuda
x = 6
AJ_COMO_FUNC, AJ_NUMEROS, AJ_COMPRA, AJ_CONFIGS, \
    AJ_CONTATO, AJ_SELECIONANDO = states_letters[num_states : num_states + x]
num_states += x
# Estados de admin e config iniciais
x = 9
ADMIN_B, ADMIN_C, ADMIN_D, CONFIGS_INI_A, CONFIGS_INI_B, CONFIGS_INI_C, \
    CONFIGS_INI_D, CONFIGS_INI_E, CONFIGS_INI_F = states_letters[num_states : num_states + x]
num_states += x
# Meta estados
x = 5
MENU, START_OVER, LEVEL_ANTERIOR, SAINDO, SAIR = states_letters[num_states : num_states + x]
num_states += x
# Atalho para ConvHandler.END
FIM = ConversationHandler.END


# ------------------ Funcionamento do bot -----------------------


dbname = 'DBDonchian.sqlite'
db = DBHelper()
fc = Functions()
db.setup(dbname)
# ADMINS: [Daniel Moreira]
LIST_OF_ADMINS = [545699841]


def read_token(config):
    parser = cfg.ConfigParser()
    parser.read(config)
    return parser.get('creds', 'token')


TOKEN = read_token('config.cfg')
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
        if user_id not in LIST_OF_ADMINS:
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
        text = fc.func_user_start(user_id, name, username, dbname)
        if text:
            send_msg(user_id, text)
        else:
            admin_text = f'Novo usuário:\nuser_id: {user_id}\nname: {name}\nusername: @{username}\n'
            send_msg(LIST_OF_ADMINS[0], admin_text)

            user_text = 'Bem-vindo, investidor! Por favor, aguarde enquanto preparamos tudo.'
            send_msg(user_id, user_text)


def enviar_id(update, context):
    user_id = update.message.chat_id
    f_name = update.message.chat.first_name
    l_name = update.message.chat.last_name if update.message.chat.last_name else ''
    name = f'{f_name} {l_name}'
    username = update.message.chat.username

    admin_text = f'Usuário mandou:\nuser_id: {user_id}\nname: {name}\nusername: @{username}\n'
    send_msg(LIST_OF_ADMINS[0], admin_text)


@restricted
def admin_a(update, context):
    admin_id = update.message.chat_id
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

    send_msg(admin_id, text, msg_id, k)
    # Configurações rápidas:
    # Qual classe de ações você irá utilizar com mais frequência? Small/Mid
    # Qual escala temporal você prefere? Diário/Semanal
    # Qual gerenciamento de risco acha mais adequado? Bloq/Porc Stop
        # Quantos bloq/Quantos %
    # Qual é o seu capital total para investir pelo método? Envie "0" (zero) se não quiser responder.
    # Tudo pronto! Você pode mudar essas configurações através do /menu.
    return ADMIN_B


def admin_b(update, context):
    admin_id = update.message.chat_id
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
        send_msg(admin_id, text, msg_id, RKR)
        return ADMIN_C


def admin_c(update, context):
    admin_id = update.message.chat_id
    msg_id = update.message.message_id
    msg = update.message.text
    choice = context.user_data['selection']

    text, success = fc.func_admin(msg, dbname, choice)
    if success and choice == 1:
        text += ' Sessão encerrada.'
    send_msg(admin_id, text, msg_id)
    if success:
        if choice == 0:
            msg = msg.split(', ')
            context.user_data['user_id'] = msg[0]
            buttons = [[
                InlineKeyboardButton(text='Enviar formulário', callback_data=str(ADMIN_D)),
                InlineKeyboardButton(text='Sair', callback_data=str(FIM))
            ]]
            keyboard = InlineKeyboardMarkup(buttons)
            text = 'Deseja enviar o formulário de configs iniciais para o usuário?'
            update.message.reply_text(text=text, reply_markup=keyboard)
            return ADMIN_D
        else:
            return FIM
    else:
        return ADMIN_C


def admin_d(update, context):
    text = 'Formulário enviado!'
    update.callback_query.edit_message_text(text=text)
    FIM
    configs_ini_a(update, context)


def configs_ini_a(update, context):
    print('update:')
    print(update)
    print('context:')
    print(context)
    user_id = context.user_data['user_id']
    text = 'funcionou, sim ou não?'
    buttons = [[
        InlineKeyboardButton(text='Vai pro B', callback_data=str(CONFIGS_INI_B)),
        InlineKeyboardButton(text='Sair', callback_data=str(FIM))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)
    context.bot.sendMessage(chat_id=user_id, text=text, reply_markup=keyboard)

def configs_ini_b(update, context):
    text = 'funcionou de novo, sim ou não?'
    buttons = [[
        InlineKeyboardButton(text='Vai pro C', callback_data=str(CONFIGS_INI_C)),
        InlineKeyboardButton(text='Sair', callback_data=str(FIM))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return CONFIGS_INI_C

def configs_ini_c(update, context):
    text = 'chega'
    buttons = [[
        InlineKeyboardButton(text='Sair', callback_data=str(FIM))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return CONFIGS_INI_D

def configs_ini_d(update, context):
    return CONFIGS_INI_E

def configs_ini_e(update, context):
    return CONFIGS_INI_F

def configs_ini_f(update, context):
    return FIM


# ------------------ Menu Principal -----------------------


def menu(update, context):
    if not context.user_data.get(START_OVER):
        user_id = update.message.chat_id
        user_allowed = db.user_check(user_id, dbname, 1)
    else:
        user_allowed = True

    if user_allowed:
        text = 'MENU PRINCIPAL - Selecione uma das opções.'
        buttons = [[
            InlineKeyboardButton(text='Radar!', callback_data=str(MENU_RADAR)),
        ], [
            InlineKeyboardButton(text='Carteira', callback_data=str(MENU_CARTEIRA)),
            InlineKeyboardButton(text='Capital', callback_data=str(MENU_CAPITAL)),
        ], [
            InlineKeyboardButton(text='Meu status', callback_data=str(MENU_INFO)),
            InlineKeyboardButton(text='Configurações', callback_data=str(MENU_CONFIG)),
            InlineKeyboardButton(text='Ajuda', callback_data=str(MENU_AJUDA))
        ], [
            InlineKeyboardButton(text='Fechar', callback_data=str(FIM))
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
    context.user_data[LEVEL_ANTERIOR] = menu
    #ordem = fc.func_ordem (?) db.get_ordem [ordenação, ordenar por]
    text = 'RADAR - Selecione o modo de análise ou modifique a ordenação dos resultados. ' \
           'Atual: ordenar por ''''+ordem'''
    buttons = [[
        InlineKeyboardButton(text='Small Caps/Diário', callback_data=str(RADAR_SM_DI)),
        InlineKeyboardButton(text='Mid Caps/Diário', callback_data=str(RADAR_MI_DI))
    ], [
        InlineKeyboardButton(text='Small Caps/Semanal', callback_data=str(RADAR_SM_SEM)),
        InlineKeyboardButton(text='Mid Caps/Semanal', callback_data=str(RADAR_MI_SEM))
    ], [
        InlineKeyboardButton(text='Ordenar resultados por...', callback_data=str(RADAR_ORDER))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(FIM)),
        InlineKeyboardButton(text='Fechar', callback_data=str(SAIR))
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
    context.user_data[LEVEL_ANTERIOR] = menu_radar
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
        InlineKeyboardButton(text='Voltar', callback_data=str(FIM)),
        InlineKeyboardButton(text='Fechar', callback_data=str(SAIR))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return RADAR_ORDER


def ordenacao(update, context):
    return 'abc'


# Carteira
def menu_carteira(update, context):
    context.user_data[LEVEL_ANTERIOR] = menu
    #carteira = fc.func_get_carteira (?)
    text = 'CARTEIRA - Selecione uma das opções. ' \
           'Composição atual da carteira: ''''+carteira'''
    buttons = [[
        InlineKeyboardButton(text='Adicionar ativo', callback_data=str(CARTEIRA_ADD)),
        InlineKeyboardButton(text='Remover ativo', callback_data=str(CARTEIRA_REM))
    ], [
        InlineKeyboardButton(text='Desativar último(s) alerta(s)', callback_data=str(CARTEIRA_RET_ALERTA))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(FIM)),
        InlineKeyboardButton(text='Fechar', callback_data=str(SAIR))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[START_OVER] = True
    return MENU_CARTEIRA


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
    context.user_data[LEVEL_ANTERIOR] = menu
    #portfolio = db.get_portfolio (?)
    text = 'CAPITAL - Selecione uma das opções. ' \
           'Valor atual de carteira: ''''+portfolio'''
    buttons = [[
        InlineKeyboardButton(text='Adicionar ao valor', callback_data=str(CAPITAL_ADD)),
        InlineKeyboardButton(text='Subtrair do valor', callback_data=str(CAPITAL_SUBTR))
    ], [
        InlineKeyboardButton(text='Substituir o valor', callback_data=str(CAPITAL_SUBST)),
        InlineKeyboardButton(text='Zerar', callback_data=str(CAPITAL_ZER))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(FIM)),
        InlineKeyboardButton(text='Fechar', callback_data=str(SAIR))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[START_OVER] = True
    return MENU_CAPITAL


#def capital_upd(update, context):
    #if add/subtrair/subst
    #text = '''ADD/SUBTRAIR/SUBST'''+'Digite o valor:'
    #elif zerar
    #text = 'Tem certeza que deseja zerar?'


def capital_finalizar(update, context):
    return 'confirmado ou rejeitado'


# Info
def menu_info(update, context):
    context.user_data[LEVEL_ANTERIOR] = menu
    text = 'MEU STATUS:'
    context.user_data[START_OVER] = False
    #blabla reply_text
    return FIM


# Configurações
def menu_config(update, context):
    context.user_data[LEVEL_ANTERIOR] = menu
    text = 'CONFIGURAÇÕES - Selecione uma das opções.'
    buttons = [[
        InlineKeyboardButton(text='Configs de hora', callback_data=str(CONFIG_HORA))
    ], [
        InlineKeyboardButton(text='Modo a ser usado automaticamente', callback_data=str(CONFIG_MODE))
    ], [
        InlineKeyboardButton(text='Gerenciamento de risco', callback_data=str(CONFIG_RISCO)),
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(FIM)),
        InlineKeyboardButton(text='Fechar', callback_data=str(SAIR))
    ]]

    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[START_OVER] = True
    return MENU_CONFIG


# Hora
def config_hora(update, context):
    context.user_data[LEVEL_ANTERIOR] = menu_config
    text = 'CONFIGURAÇÕES DE HORA - Selecione uma das opções.'
    buttons = [[
        InlineKeyboardButton(text='Mudar a hora dos alertas automáticos', callback_data=str(HORA_MUDAR))
    ], [
        InlineKeyboardButton(text='Ativar/Desativar alertas automáticos', callback_data=str(HORA_ACT_DEACT))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(FIM)),
        InlineKeyboardButton(text='Fechar', callback_data=str(SAIR))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return CONFIG_HORA


def hora_upd(update, context):
    return 'abc'


def hora_finalizar(update, context):
    return 'confirmar sucesso da alteração'


# Classe/escala temporal
def config_mode(update, context):
    context.user_data[LEVEL_ANTERIOR] = menu_config
    text = 'CONFIGURAÇÕES DE MODO - Selecione a classe de ativos e a escala temporal a serem ' \
           'usados no alerta automático.'
    buttons = [[
        InlineKeyboardButton(text='Small Caps/Diário', callback_data=str(RADAR_SM_DI)),
        InlineKeyboardButton(text='Mid Caps/Diário', callback_data=str(RADAR_MI_DI))
    ], [
        InlineKeyboardButton(text='Small Caps/Semanal', callback_data=str(RADAR_SM_SEM)),
        InlineKeyboardButton(text='Mid Caps/Semanal', callback_data=str(RADAR_MI_SEM))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(FIM)),
        InlineKeyboardButton(text='Fechar', callback_data=str(SAIR))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return CONFIG_MODE


def mode_upd(update, context):
    return 'atualizar e confirmar sucesso'


# Gerenciamento de risco
def config_risco(update, context):
    context.user_data[LEVEL_ANTERIOR] = menu_config
    text = 'CONFIGURAÇÕES DE RISCO - Selecione o gerenciamento de risco a ser utilizado no cálculo do volume: '
    buttons = [[
        InlineKeyboardButton(text='Bloquinho por operação', callback_data=str(RISCO_BLOQ)),
    ], [
        InlineKeyboardButton(text='Porcentagem relativa ao stop', callback_data=str(RISCO_PORC))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(FIM)),
        InlineKeyboardButton(text='Fechar', callback_data=str(SAIR))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return CONFIG_RISCO


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
    context.user_data[LEVEL_ANTERIOR] = menu
    text = 'AJUDA - Selecione um tópico: '
    buttons = [[
        InlineKeyboardButton(text='Como o bot funciona?', callback_data=str(AJ_COMO_FUNC)),
    ], [
        InlineKeyboardButton(text='O que são os números no radar?', callback_data=str(AJ_NUMEROS))
    ], [
        InlineKeyboardButton(text='Qual ação do radar eu devo comprar?', callback_data=str(AJ_COMPRA))
    ], [
        InlineKeyboardButton(text='Quais e o que são as configurações?', callback_data=str(AJ_CONFIGS))
    ], [
        InlineKeyboardButton(text='Outras dúvidas e sugestões', callback_data=str(AJ_CONTATO))
    ], [
        InlineKeyboardButton(text='Voltar', callback_data=str(FIM)),
        InlineKeyboardButton(text='Fechar', callback_data=str(SAIR))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[START_OVER] = True
    return MENU_AJUDA


def ajuda_finalizar(update, context):
    context.user_data[LEVEL_ANTERIOR] = menu_ajuda
    text = 'AJUDA - TITULO QUALQUER'
    buttons = [[
        InlineKeyboardButton(text='Voltar', callback_data=str(FIM)),
        InlineKeyboardButton(text='Fechar', callback_data=str(SAIR))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[START_OVER] = True
    return MENU_AJUDA


# Voltar
def voltar(update, context):
    update.callback_query.answer()
    context.user_data[START_OVER] = True
    context.user_data[LEVEL_ANTERIOR](update, context)
    return FIM


# Finalizar a conversa
def stop(update, context):
    context.user_data[START_OVER] = False
    update.callback_query.answer()
    text = 'Até mais!'
    update.callback_query.edit_message_text(text=text)
    return SAINDO


def end(update, context):
    context.user_data[START_OVER] = False
    update.callback_query.answer()
    text = 'Até mais!'
    update.callback_query.edit_message_text(text=text)
    return FIM


@restricted
def cancel(update, context):
    text = 'Sessão de adm encerrada.'
    user_id = update.message.chat_id
    send_msg(user_id, text, '', RKR)
    return FIM


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
            pattern='^{0}$|^{1}$|^{2}$|^{3}$|^{4}$'.format(str(AJ_COMO_FUNC),
                                                           str(AJ_NUMEROS),
                                                           str(AJ_COMPRA),
                                                           str(AJ_CONFIGS),
                                                           str(AJ_CONTATO))
        )],
        states={
            AJ_SELECIONANDO: []
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(SAIR)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(FIM)+'$')
        ],
        map_to_parent={
            FIM: MENU_AJUDA,
            SAINDO: SAINDO
        }
    )
    
    menu_ajuda_handlers = [
        ajuda_finalizar_conv
    ]
    menu_ajuda_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_ajuda, pattern='^'+str(MENU_AJUDA)+'$')],
        states={
            MENU_AJUDA: menu_ajuda_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(SAIR)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(FIM)+'$')
        ],
        map_to_parent={
            FIM: MENU,
            SAINDO: FIM
        }
    )


    # Configurações
    config_risco_handlers = [
        CallbackQueryHandler(risco_upd, pattern='^{0}$|^{1}$'.format(str(RISCO_BLOQ),
                                                                     str(RISCO_PORC)))
    ]
    config_risco_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(config_risco, pattern='^'+str(CONFIG_RISCO)+'$')],
        states={
            CONFIG_RISCO: config_risco_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(SAIR)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(FIM)+'$')
        ],
        map_to_parent={
            FIM: MENU_CONFIG,
            SAINDO: SAINDO
        }
    )

    config_mode_handlers = [
        #CallbackQueryHandler(
        #   mode_upd, 
        #   pattern='^{0}$|^{1}$|^{2}$|^{3}$'.format(str(RADAR_SM_DI),
        #                                            str(RADAR_MI_DI),
        #                                            str(RADAR_SM_SEM),
        #                                            str(RADAR_MI_SEM))
        #)
    ]
    config_mode_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(config_mode, pattern='^'+str(CONFIG_MODE)+'$')],
        states={
            CONFIG_MODE: config_mode_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(SAIR)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(FIM)+'$')
        ],
        map_to_parent={
            FIM: MENU_CONFIG,
            SAINDO: SAINDO
        }
    )

    config_hora_handlers = [
        CallbackQueryHandler(hora_upd, pattern='^{0}$|^{1}$'.format(str(HORA_MUDAR),
                                                                    str(HORA_ACT_DEACT)))
    ]
    config_hora_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(config_hora, pattern='^'+str(CONFIG_HORA)+'$')],
        states={
            CONFIG_HORA: config_hora_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(SAIR)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(FIM)+'$')
        ],
        map_to_parent={
            FIM: MENU_CONFIG,
            SAINDO: SAINDO
        }
    )

    menu_config_handlers = [
        config_hora_conv,
        config_mode_conv,
        config_risco_conv
    ]
    menu_config_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_config, pattern='^'+str(MENU_CONFIG)+'$')],
        states={
            MENU_CONFIG: menu_config_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(SAIR)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(FIM)+'$')
        ],
        map_to_parent={
            FIM: MENU,
            SAINDO: FIM
        }
    )


    # Capital
    menu_capital_handlers = [
        #CallbackQueryHandler(
        #   capital_upd, 
        #   pattern='^{0}$|^{1}$|^{2}$|^{3}$'.format(str(CAPITAL_ADD),
        #                                            str(CAPITAL_SUBTR),
        #                                            str(CAPITAL_SUBST),
        #                                            str(CAPITAL_ZER))
        #)
    ]
    menu_capital_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_capital, pattern='^'+str(MENU_CAPITAL)+'$')],
        states={
            MENU_CAPITAL: menu_capital_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(SAIR)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(FIM)+'$')
        ],
        map_to_parent={
            FIM: MENU,
            SAINDO: FIM
        }
    )


    # Carteira
    menu_carteira_handlers = [
        #CallbackQueryHandler(
        #   carteira_upd, 
        #   pattern='^{0}$|^{1}$|^{2}$'.format(str(CARTEIRA_ADD),
        #                                      str(CARTEIRA_REM),
        #                                      str(CARTEIRA_RET_ALERTA))
        #)
    ]
    menu_carteira_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_carteira, pattern='^'+str(MENU_CARTEIRA)+'$')],
        states={
            MENU_CARTEIRA: menu_carteira_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(SAIR)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(FIM)+'$')
        ],
        map_to_parent={
            FIM: MENU,
            SAINDO: FIM
        }
    )


    # Radar
    radar_order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(radar_order, pattern='^'+str(RADAR_ORDER)+'$')],
        states={
            RADAR_ORDER: [CallbackQueryHandler(ordenacao, pattern=r'^\d$')],
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(SAIR)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(FIM)+'$')
        ],
        map_to_parent={
            FIM: MENU_RADAR,
            SAINDO: SAINDO
        }
    )

    menu_radar_handlers = [
        CallbackQueryHandler(radar_activate, pattern='^'+str(RADAR_SM_DI)+'$'),
        radar_order_conv
    ]
    menu_radar_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_radar, pattern='^'+str(MENU_RADAR)+'$')],
        states={
            MENU_RADAR: menu_radar_handlers,
        },
        fallbacks=[
            CallbackQueryHandler(stop, pattern='^'+str(SAIR)+'$'),
            CallbackQueryHandler(voltar, pattern='^'+str(FIM)+'$')
        ],
        map_to_parent={
            FIM: MENU,
            SAINDO: FIM
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
            FIM: [CallbackQueryHandler(end, pattern='^'+str(FIM)+'$')]
        },
        fallbacks=[CallbackQueryHandler(end, pattern='^'+str(FIM)+'$')]
    )


    # Configs Iniciais
    configs_ini_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(configs_ini_b, pattern='^'+str(CONFIGS_INI_B))],
        states={
            CONFIGS_INI_C: [CallbackQueryHandler(configs_ini_c, pattern='^'+str(CONFIGS_INI_C)+'$'),
                MessageHandler(Filters.text, configs_ini_c)],
            CONFIGS_INI_D: [MessageHandler(Filters.text, configs_ini_d)],
            CONFIGS_INI_E: [MessageHandler(Filters.text, configs_ini_e)],
            CONFIGS_INI_F: [MessageHandler(Filters.text, configs_ini_f)]
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
            CallbackQueryHandler(cancel, pattern='^'+str(FIM)+'$')
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