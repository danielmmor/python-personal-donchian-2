import string
from telegram import InlineKeyboardButton as IKB
from telegram.ext import ConversationHandler

class Buttons():
    def __init__(self):
        states_codes = [i + j for i in string.ascii_uppercase[:6] for j in string.ascii_lowercase]
        num_states = 0
        # Menu
        x = 6
        self.MENU_RADAR, self.MENU_TRACK, self.MENU_PORTF, self.MENU_INFO, \
            self.MENU_SET, self.MENU_HELP = states_codes[:num_states + x]
        num_states += x
        # Radar
        x = 5
        self.RADAR_SM_DAY, self.RADAR_SM_WEEK, self.RADAR_MI_DAY, self.RADAR_MI_WEEK, \
            self.RADAR_ORDER = states_codes[num_states : num_states + x]
        num_states += x
        # Ticker tracker
        x = 3
        self.TRACK_UPD, self.TRACK_EXIT, self.TRACK_WARN_REM = states_codes[num_states : num_states + x]
        num_states += x
        # Portfolio
        x = 6
        self.PORTF_ADD, self.PORTF_SUBTR, self.PORTF_SUBST, self.PORTF_CLEAR, \
            self.PORTF_CHANGE, self.PORTF_UPD = states_codes[num_states : num_states + x]
        num_states += x
        # Info
        x = 2
        self.INFO, self.INFO_DUMMY = states_codes[num_states : num_states + x]
        num_states += x
        # Settings
        x = 3
        self.SET_TIME, self.SET_MODE, self.SET_RISK = states_codes[num_states : num_states + x]
        num_states += x
        # Time settings
        x = 3
        self.TIME_UPD, self.TIME_EXIT, self.TIME_ACT_DEACT = states_codes[num_states : num_states + x]
        num_states += x
        # Tracker radar mode settings
        x = 2
        self.MODE_UPD, self.MODE_DUMMY = states_codes[num_states : num_states + x]
        num_states += x
        # Risk management settings
        x = 2
        self.RISK_BLOCK, self.RISK_PERC = states_codes[num_states : num_states + x]
        num_states += x
        # Help
        x = 7
        self.HP_HDIW, self.HP_NUMS, self.HP_BUY, self.HP_SET, \
            self.HP_CONTACT, self.HP_SELECT, self.HP_EXIT = states_codes[num_states : num_states + x]
        num_states += x
        # Admin states and initial settings
        x = 9
        self.ADMIN_B, self.ADMIN_C, self.ADMIN_D, self.INIT_SET_A, self.INIT_SET_B, self.INIT_SET_C, \
            self.INIT_SET_D, self.INIT_SET_E, self.INIT_SET_F = states_codes[num_states : num_states + x]
        num_states += x
        # Meta states
        x = 5
        self.MENU, self.START_OVER, self.PREV_LEVEL, self.EXITING, self.EXIT = states_codes[num_states : num_states + x]
        num_states += x
        # Shortcut to ConvHandler.END
        self.STOP = ConversationHandler.END
        # Keyboard Buttons assignment
        self.all_states = {x: 0 for x in states_codes}
        self.all_states[self.ADMIN_C] = [[
            IKB(text='Enviar formulário', callback_data=self.ADMIN_D),
            IKB(text='Sair', callback_data=str(self.STOP))
        ]]
        # deprecated
        self.all_states[self.INIT_SET_A] = [[
            IKB(text='Small Caps', callback_data='S'),
            IKB(text='Mid Caps', callback_data='M')
        ]]
        # deprecated
        self.all_states[self.INIT_SET_B] = [[
            IKB(text='Diário', callback_data='D'),
            IKB(text='Semanal', callback_data='W')
        ]]
        # deprecated
        self.all_states[self.INIT_SET_C] = [[
            IKB(text='Bloquinho por operação', callback_data='B'),
        ], [
            IKB(text='Porcentagem relativa ao stop', callback_data='P')
        ]]
        self.all_states[self.MENU] = [[
            IKB(text='Radar!', callback_data=self.MENU_RADAR),
        ], [
            IKB(text='Carteira', callback_data=self.MENU_TRACK),
            IKB(text='Capital', callback_data=self.MENU_PORTF),
        ], [
            IKB(text='Meu status', callback_data=self.MENU_INFO),
            IKB(text='Configurações', callback_data=self.MENU_SET),
            IKB(text='Ajuda', callback_data=self.MENU_HELP)
        ], [
            IKB(text='Fechar', callback_data=str(self.STOP))
        ]]
        self.all_states[self.MENU_RADAR] = [[
            IKB(text='Small Caps/Diário', callback_data=self.RADAR_SM_DAY),
            IKB(text='Mid Caps/Diário', callback_data=self.RADAR_MI_DAY)
        ], [
            IKB(text='Small Caps/Semanal', callback_data=self.RADAR_SM_WEEK),
            IKB(text='Mid Caps/Semanal', callback_data=self.RADAR_MI_WEEK)
        ], [
            IKB(text='Ordenar resultados por...', callback_data=self.RADAR_ORDER)
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.RADAR_ORDER] = [[
            IKB(text='Nome do ativo (Stock)', callback_data='1')
        ], [
            IKB(text='Canal superior (DUp)', callback_data='2')
        ], [
            IKB(text='Último fechamento (Close)', callback_data='3')
        ], [
            IKB(text='Canal inferior (DDown)', callback_data='4')
        ], [
            IKB(text='Distância (Dist)', callback_data='5')
        ], [
            IKB(text='"Trendabilidade" (Trend)', callback_data='6')
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.MENU_TRACK] = [[
            IKB(text='Adicionar ativo', callback_data='0'),
            IKB(text='Remover ativo', callback_data='1')
        #], [
        #    IKB(text='Desativar último(s) alerta(s)', callback_data=self.TRACK_WARN_REM)
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.MENU_PORTF] = [[
            IKB(text='Adicionar ao valor', callback_data='0'),
            IKB(text='Subtrair do valor', callback_data='1')
        ], [
            IKB(text='Substituir o valor', callback_data='2'),
            IKB(text='Zerar', callback_data='3')
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.MENU_SET] = [[
            IKB(text='Mudar a hora/dia dos alertas automáticos', callback_data=self.SET_TIME)
        ], [
            IKB(text='Modo a ser usado automaticamente', callback_data=self.SET_MODE)
        ], [
            IKB(text='Gerenciamento de risco', callback_data=self.SET_RISK),
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.SET_TIME] = [[
            IKB(text='Mudar a hora dos alertas automáticos', callback_data='0')
        ], [
            IKB(text='Mudar o dia dos alertas automáticos', callback_data='1')
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.SET_MODE] = [[
            IKB(text='Small Caps/Diário', callback_data='S,D'),
            IKB(text='Mid Caps/Diário', callback_data='M,D')
        ], [
            IKB(text='Small Caps/Semanal', callback_data='S,W'),
            IKB(text='Mid Caps/Semanal', callback_data='M,W')
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.SET_RISK] = [[
            IKB(text='Bloquinho por operação', callback_data=self.RISK_BLOCK),
        ], [
            IKB(text='Porcentagem relativa ao stop', callback_data=self.RISK_PERC)
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.MENU_HELP] = [[
            IKB(text='Como o bot funciona?', callback_data=self.HP_HDIW),
        ], [
            IKB(text='O que são os números no radar?', callback_data=self.HP_NUMS)
        ], [
            IKB(text='Qual ação do radar eu devo comprar?', callback_data=self.HP_BUY)
        ], [
            IKB(text='Quais e o que são as configurações?', callback_data=self.HP_SET)
        ], [
            IKB(text='Outras dúvidas e sugestões', callback_data=self.HP_CONTACT)
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.EXIT] = [[
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]

    def buttons(self, state):
        return self.all_states[state]