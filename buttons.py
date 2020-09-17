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
        self.TRACK_ADD, self.TRACK_REM, self.TRACK_WARN_REM = states_codes[num_states : num_states + x]
        num_states += x
        # Portfolio
        x = 4
        self.PORTF_ADD, self.PORTF_SUBTR, self.PORTF_SUBST, self.PORTF_CLEAR = states_codes[num_states : num_states + x]
        num_states += x
        # Info
        x = 1
        self.INFO = states_codes[num_states : num_states + x]
        num_states += x
        # Settings
        x = 3
        self.SET_TIME, self.SET_MODE, self.SET_RISK = states_codes[num_states : num_states + x]
        num_states += x
        # Time settings
        x = 2
        self.TIME_CHANGE, self.TIME_ACT_DEACT = states_codes[num_states : num_states + x]
        num_states += x
        # Tracker radar mode settings
        x = 4 
        self.MODE_SM_DAY, self.MODE_SM_WEEK, self.MODE_MI_DAY, self.MODE_MI_WEEK = states_codes[num_states : num_states + x]
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
        self.all_states[self.INIT_SET_A] = [[
            IKB(text='Vai pro B', callback_data=self.INIT_SET_B),
            IKB(text='Sair', callback_data=str(self.STOP))
        ]]
        self.all_states[self.INIT_SET_B] = [[
            IKB(text='Vai pro C', callback_data=self.INIT_SET_C),
            IKB(text='Sair', callback_data=str(self.STOP))
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
        self.all_states[self.RADAR_ORDER] = [[
            IKB(text='Adicionar ativo', callback_data=self.TRACK_ADD),
            IKB(text='Remover ativo', callback_data=self.TRACK_REM)
        ], [
            IKB(text='Desativar último(s) alerta(s)', callback_data=self.TRACK_WARN_REM)
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.MENU_PORTF] = [[
            IKB(text='Adicionar ao valor', callback_data=self.PORTF_ADD),
            IKB(text='Subtrair do valor', callback_data=self.PORTF_SUBTR)
        ], [
            IKB(text='Substituir o valor', callback_data=self.PORTF_SUBST),
            IKB(text='Zerar', callback_data=self.PORTF_CLEAR)
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.MENU_SET] = [[
            IKB(text='Configs de hora', callback_data=self.SET_TIME)
        ], [
            IKB(text='Modo a ser usado automaticamente', callback_data=self.SET_MODE)
        ], [
            IKB(text='Gerenciamento de risco', callback_data=self.SET_RISK),
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.SET_TIME] = [[
            IKB(text='Mudar a hora dos alertas automáticos', callback_data=self.TIME_CHANGE)
        ], [
            IKB(text='Ativar/Desativar alertas automáticos', callback_data=self.TIME_ACT_DEACT)
        ], [
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]
        self.all_states[self.SET_MODE] = [[
            IKB(text='Small Caps/Diário', callback_data=self.RADAR_SM_DAY),
            IKB(text='Mid Caps/Diário', callback_data=self.RADAR_MI_DAY)
        ], [
            IKB(text='Small Caps/Semanal', callback_data=self.RADAR_SM_WEEK),
            IKB(text='Mid Caps/Semanal', callback_data=self.RADAR_MI_WEEK)
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
        self.all_states[self.HP_EXIT] = [[
            IKB(text='Voltar', callback_data=str(self.STOP)),
            IKB(text='Fechar', callback_data=self.EXIT)
        ]]

    def buttons(self, state):
        return self.all_states[state]