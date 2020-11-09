import re
import locale
import requests
import schedule
from datetime import datetime as dtt
from dbhelper import DBHelper
from radar import Radar

db = DBHelper()

class Functions():
    def __init__(self, token):
        self.TOKEN = token
        locale.setlocale(locale.LC_ALL, '')
        self.days = [
            'todos os dias',
            'Segunda-Feira',
            'Terça-Feira',
            'Quarta-Feira',
            'Quinta-Feira',
            'Sexta-Feira',
            'Sábado',
            'Domingo',
        ]
        self.reg = [
            r'^\d*$', # user_id
            r'^(\d\d[/]){2}\d{4}$', # date
            r'^[1-9]+\d*$', # blocks
            r'^\d+([,]\d+)?$', # perc, capital
            r'^([a-zA-Z]{4}\d{1,2}|B3SA3)(, ?([a-zA-Z]{4}\d{1,2}|B3SA3))*?$', # tickers
            r'^([0-1]\d|2[0-3]):[0-5]\d$', # hour
        ]
        self.modes = ['SD','SW','MD','MW']
        self.sm_dw = {
            self.modes[0]: 'Small Caps/Diário',
            self.modes[1]: 'Small Caps/Semanal',
            self.modes[2]: 'Mid Large Caps/Diário',
            self.modes[3]: 'Mid Large Caps/Semanal',
        }
        self.rd = Radar()
    
    def func_send_msg(self, chat_id, text, 
                      reply_to_message_id='', reply_markup=''):
        url = 'https://api.telegram.org/bot{}/sendMessage?' \
            'chat_id={}&text={}&reply_to_message_id={}&' \
            'reply_markup={}&parse_mode=HTML'
        requests.get(url.format(self.TOKEN, chat_id, text, reply_to_message_id, reply_markup))
    
    def schedule(self):
        print('Scheduling user reports...')
        users = db.get_everything('users')
        if users:
            for user in users:
                if user[4]:
                    hour = self.rd.hour_fix(user[9])
                    kwargs = {
                        'user_id': user[0],
                        's_m': user[7],
                        'd_w': user[8],
                    }
                    self.rd.weekly(hour, self.func_radar_auto, str(user[0]), **kwargs)
        else:
            pass
        print('Reports scheduled.')

    def func_time(self, var, separator):
        if separator == '/':
            new_format = dtt.strptime(var,f'%d/%m/%Y').strftime(f'%Y-%m-%d')
        elif separator == '-':
            new_format = dtt.strptime(var, '%Y-%m-%d').strftime('%d/%m/%Y')
        return new_format

    def func_user_start(self, user_id, name, username):
        exists = db.get_info(user_id)
        if exists:
            admin_text = f'Usuário mandou novamente:\nuser_id: {user_id}\n' \
                         f'nome: {name}\nusername: @{username}'
            user_text = 'Você já deu o start! Algum problema? Pergunte ao @DanMMoreira!'
        else:
            dia = str(dtt.now().date())
            db.user_start(user_id, name, username, dia)
            admin_text = f'Novo usuário:\nuser_id: {user_id}\n' \
                         f'nome: {name}\nusername: @{username}'
            user_text = 'Bem-vindo, investidor! Por favor, aguarde enquanto preparamos tudo.'
        return admin_text, user_text

    def func_admin(self, msg, choice):
        info = msg.split(', ')
        # db.admin_queries(info_0, info_1, info_2, choice)
        # 0 se autoriza: info_0 = user_id, info_1 = full_name, info_2 = dia de hoje; 
        # 1 se desativa: info_0 = user_id, info_1 = info_2 = '';
        # 2 se edita:    info_0 = user_id, info_1 = campo, info_2 = novo dado;
        # 3 se pesquisa: info_0 = campo, info_1 = pesquisa;
        # 4 pesquisa por data: info_0 = data inicial, info_1 = data final
        # 5 se reseta:   info_0 = user_id
        # The query:
        try:
            if choice < 3:
                y = re.match(self.reg[0], info[0])
                if not y:
                    response = 'Formato inválido! O user_id deve conter somente números. Tente novamente.'
                    return response, False
            if choice == 0:
                date = str(dtt.now().date())
                res = db.admin_queries(info[0], info[1], date, choice)
                action = 'autorizado'
            elif choice in {1, 5}:
                res = db.admin_queries(info[0], choice=choice)
                action = 'desativado' if choice == 1 else 'resetado'
            elif choice in {2, 3, 4}:
                if ((choice == 2 and re.match('^(nome|username|email)$', info[1], re.I)) \
                        or (choice == 3 and re.match('^(user_id|nome|username)$', info[0], re.I))):
                    if re.match('^nome$', info[0], re.I): info[0] = info[0].replace('o', 'a')
                    if re.match('^nome$', info[1], re.I): info[1] = info[1].replace('o', 'a')
                    res = db.admin_queries(info[0], info[1], choice=choice)

                elif (choice == 4 and re.match(self.reg[1], info[0]) \
                        and re.match(self.reg[1], info[1])):
                    info[0] = self.func_time(info[0], '/')
                    info[1] = self.func_time(info[1], '/')
                    res = db.admin_queries(info[0], info[1], choice=choice)
            # The response:
            if res == 0:
                response = 'Este usuário não existe! Tente novamente ou clique em /cancelar.'
                return response, False
            elif not res:
                response = 'Nada foi encontrado para essa pesquisa! Tente novamente ou clique em /cancelar.'
                return response, False
            elif choice in {0, 1, 5}:
                if res == 1:
                    response = f'Este usuário já está {action}!'
                else:
                    response = f'O usuário foi {action} com sucesso!'
            elif choice == 2:
                response = 'O campo foi editado com sucesso!'
            elif choice in {3, 4}:
                response = 'Resultados da pesquisa:\n\r\n\r'
                for item in res:
                    if item[3] == None: item[3] = '-'
                    item[4] = 'Desativado' if item[4] == '0' else 'Autorizado'
                    item[5] = self.func_time(item[5], '-')
                    response += (
                        f'user_id: {item[0]}\n\r'
                        f'Nome: {item[1]}\n\r'
                        f'username: {item[2]}\n\r'
                        f'E-mail: {item[3]}\n\r'
                        f'{item[4]}\n\r'
                        f'Data de entrada / última autorização: {item[5]}\n\r\n\r'
                    )
            return response, True
        except Exception as e:
            print(e)
            response = 'Formato inválido! Esqueceu algo? Tente novamente ou clique em /cancelar.'
            return response, False
        
    def func_init_check(self, mode, data, user_id='', all_data=''):
        if mode == 'B' and not re.match(self.reg[2], data):
            text = 'Formato inválido. Digite o valor dos bloquinhos neste formato ' \
                '(somente números, sem aspas): "8" ou "12". Tente novamente:'
            return text, False
        elif mode == 'P' and not re.match(self.reg[3], data):
            text = 'Formato inválido. Digite o valor do porcentual neste formato ' \
                '(somente números, sem aspas): "1,5" ou "2". Tente novamente:'
            return text, False
        elif mode in ['B', 'P']:
            text = 'Por último: qual o seu capital atual para investir pelo método ' \
                '(ex.: "1234,56", sem as aspas)?\r\n' \
                'Sem o capital, o gerenciamento de risco não funcionará, mas envie "0"'\
                ' (zero, sem as aspas) se não quiser responder. Ele serve para o cálculo ' \
                'automático do volume a ser comprado.'
            return text, True
        elif mode == 'p':
            if not re.match(self.reg[3], data):
                text = 'Formato inválido. Digite o valor do capital neste formato (somente números, sem aspas): ' \
                    '"1234,56" ou digite "0" se não quiser responder. Tente novamente:'
                return text, False
            else:
                hour = self.rd.hour_fix('10:30')
                kwargs = {
                    'user_id': user_id,
                    's_m': all_data[0],
                    'd_w': all_data[1],
                }
                self.rd.weekly(hour, self.func_radar_auto, str(user_id), **kwargs)
                text = 'Tudo pronto!\nVocê irá receber relatórios diários conforme suas configurações ' \
                    'às 10:30. ' \
                    'Você pode mudar todas essas configurações através do /menu e ' \
                    'lá você também pode obter o relatório manualmente. Para saber mais informações ' \
                    'sobre o bot ou se precisa de ajuda, contate o desenvolvedor @DanMMoreira. ' \
                    'Este bot ainda está em fase de testes, portanto algumas coisas podem estar... ' \
                    'esquisitas. Mas muitas coisas estão por vir!\nAproveite!' # Se escolheu a escala Semanal, receberá apenas às segundas-feiras.
                return text, True
    
    def func_get_info(self, user_id):
        info = db.get_info(user_id)
        stock = 'Small Caps' if info[0][7] == 'S' else 'Mid Large Caps'
        freq = 'Diário' if info[0][8] == 'D' else 'Semanal'
        #day = self.days[0] if info[0][8] == 'D' else self.days[int(info[0][10])]
        if info[0][11] == 'B':
            risk = 'Bloquinho por operação\n\rBloquinhos: '+info[0][12]+''
        else:
            risk = 'Porcentagem relativa ao stop\n\rPorcentual: '+info[0][12]+'%'
        text = 'MEU STATUS:\n\r\n\r' \
            'Capital: R$'+info[0][6]+'\n\r' \
            'Classe de ações padrão: '+stock+'\n\r' \
            'Escala temporal padrão: '+freq+'\n\r' \
            'Hora programada: ' \
            ''+info[0][9]+'\n\r' \
            'Gerenciamento de risco: '+risk #Hora e dia da semana programados:info[], day
        return text

    def func_portf_upd(self, user_id, msg, choice):
        if choice < 3 and re.match(self.reg[3], msg):
            if msg.rfind(','): msg = msg.replace(',', '.')
            msg = float(msg)
            port = db.get_info(user_id)[0][6]
            if port.rfind(','): port = port.replace(',', '.')
            port = float(port)
            if choice == 0: port += msg
            if choice == 1: port -= msg
            if choice == 2: port = msg
            port = '{:.2f}'.format(port).replace('.', ',')
            db.info_upd(user_id, 'portf', port)
            text = 'Pronto! O novo capital é de R$'+port+'.\n\rAté mais!'
            return text, True
        elif choice == 3 and re.match('^(Sim)$', msg):
            port = '0'
            db.info_upd(user_id, 'portf', port)
            text = 'Pronto! O capital foi zerado.\n\rAté mais!'
            return text
        else:
            text = 'Formato inválido. Tente colocar o valor neste formato ' \
                '(somente números): "1234,56" ou clique em /fechar:'
            return text, False

    def func_get_tickers_user(self, user_id, show_only=True):
        t_list = db.get_everything(user_id)
        if t_list:
            if show_only:
                text = ''
                for m in self.modes:
                    tickers = [x[0] for x in t_list if x[1] == m]
                    if tickers:
                        text += '-- ' +self.sm_dw[m]+ ' --\n' + '\n'.join(tickers) + '\n\n'
            else:
                text = [x[0] for x in t_list]
        else:
            text = 'A sua carteira está vazia!'
        return text

    def func_tickers_upd_user(self, user_id, msg, choice):
        if re.match(self.reg[4], msg):
            tickers = map(lambda x: x.upper(), re.split(r'\W+', msg))
            success = db.tickers_upd_user(user_id, tickers, choice)
            action = [
                'Você adicionou o(s) ativo(s) '+msg+' com sucesso!\nAté mais!', 
                'O ativo '+msg+' foi removido com sucesso!\nAté mais!'
            ]
            if success:
                text = action[0] if choice < 4 else action[1]
            else:
                text = 'Não existe este ativo na sua carteira!\nAté mais!'
        else:
            success = False
            text ='Tente colocar o índice neste formato: "PETR4" ' \
                '(sem as aspas) ou clique em /fechar:'
        return text, success

    def func_time_upd(self, user_id, choice):
        time = db.get_info(user_id)[0][9+choice]
        if choice == 0:
            cb_text = 'MUDAR HORA\r\n' \
                'A hora programada atual é '+time+'. Digite a nova hora ' \
                'desejada ou selecione uma das opções:'
            text, keyboard = False, False
        else:
            d_w = db.get_info(user_id)[0][8]
            if d_w == 'D':
                cb_text = 'A escala programada no seu perfil é Diário, portanto ' \
                    'você receberá mensagens todos os dias. Para receber mensagens ' \
                    'apenas 1 vez por semana, você deve mudar a escala para ' \
                    'Semanal, em Menu > Configurações > Configurações de Modo.\r\n' \
                    'Selecione uma das opções:'
                text, keyboard = False, False
            else:
                cb_text = 'MUDAR DIA\r\n' \
                    'O dia programado atual é '+self.days[int(time)]+'.'
                text = 'Escolha abaixo o novo dia desejado:'
                keyboard = [[x] for x in self.days if not x == self.days[0]]
        return cb_text, text, keyboard
        
    def func_time_exit(self, user_id, choice, msg):
        if choice == 0:
            if re.match(self.reg[5], msg):
                user = db.admin_queries('user_id', str(user_id), choice=3)
                hour = self.rd.hour_fix(msg)
                kwargs = {
                    'user_id': user_id,
                    's_m': user[0][7],
                    'd_w': user[0][8],
                }
                schedule.clear(str(user_id))
                self.rd.weekly(hour, self.func_radar_auto, str(user_id), **kwargs)
                db.info_upd(user_id, 'hour', msg)
                text = 'A hora programada foi atualizada com sucesso!\r\nAté mais!'
                success = True
            else:
                text = 'Tente colocar a hora neste formato: "06:18", "13:45" ' \
                    '(sem as aspas) ou clique em /fechar::'
                success = False
        else:
            if re.match('^'+'|'.join(self.days)+'$', msg):
                data = str(self.days.index(msg))
                db.info_upd(user_id, 'r_day', data)
                text = 'O dia programado foi atualizado com sucesso!\r\nAté mais!'
                success = True
            else:
                text = 'Você deve selecionar o dia da lista. Tente novamente:'
                success = False
        return text, success

    def func_mode_upd(self, user_id, choice):
        change = choice.split(',')
        choice = choice.replace(',', '')
        db.info_upd(user_id, 'S_M', change[0])
        db.info_upd(user_id, 'D_W', change[1])
        text = 'O modo foi atualizado com sucesso! As mensagens automáticas de radar e ' \
            'monitoramento de carteira possuirão classe de ações e escala ' \
            'equivalentes a '+self.sm_dw[choice]+'.\r\nAté mais!'
        return text
    
    def func_risk_upd(self, user_id, choice):
        db.info_upd(user_id, 'B_P', choice)
        if choice == 'B':
            text = 'Agora, digite o número de bloquinhos que serão utilizados (ex.: "8", sem as aspas):'
        else:
            text = 'Agora, digite o porcentual de risco (ex.: "1,5", sem as aspas):'
        return text
    
    def func_risk_exit(self, user_id, choice, msg):
        if choice == 'B' and not re.match(self.reg[2], msg):
            text = 'Formato inválido. Digite o valor dos bloquinhos neste formato ' \
                '(somente números, sem aspas): "8" ou "12". Tente novamente ou clique em /fechar:'
            success = False
        elif choice == 'P' and not re.match(self.reg[3], msg):
            text = 'Formato inválido. Digite o valor do porcentual neste formato ' \
                '(somente números, sem aspas): "1,5" ou "2". Tente novamente ou clique em /fechar:'
            success = False
        else:
            db.info_upd(user_id, 'B_P_set', msg)
            text = 'Pronto! Seu gerenciamento de risco já está configurado.\r\nAté mais!'
            success = True
        return text, success

    def func_radar(self, choice, user_id, mode):
        if choice == 'buy':
            m = self.modes[int(mode)]
            stocks = self.rd.trigger_buy(m)
            if stocks == []:
                text = 'No momento, nenhum ativo está perto de romper o canal superior.\r\nRelaxe!'
            else:
                text = '  | ------ Compra - '+self.sm_dw[m]+' ------ | \r\n' \
                    'Ação | Vol | Sup | Fech | Inf\r\nDist | Trend\r\n' \
                    '<i>!!Os ativos em atenção romperam o canal superior nos ' \
                    'últimos 3 dias! Cuidado!!\r\n\r\n</i>'
                for item in stocks:
                    item[2] = locale.format('%1.2f', item[2], 1)
                    item[3] = locale.format('%1.2f', item[3], 1)
                    item[4] = locale.format('%1.2f', item[4], 1)
                    item[5] = '{:.2f}'.format(item[5])
                    item[6] = '{:.2f}'.format(item[6][0])
                    text_A = f'{item[0]} | {item[1]} | ${item[2]} | ${item[3]} | ${item[4]}\r\n'
                    text_B = f'{item[5]}% | {item[6]}'
                    if item[7]:
                        text += '!!'+text_A+'<i>'+text_B+'!!!!</i>\r\n\r\n'
                    else:
                        text += text_A+text_B+'\r\n\r\n'
        elif choice == 'track':
            t_list = db.get_everything(user_id)
            if t_list:
                t_gen = self.rd.trigger_track(t_list)
                text = ' | ------ Carteira ------ | \r\n' \
                    'Ação | Fech | Inf -> Inf(novo)\r\n\r\n'
                for group, m in t_gen:
                    text += '---- '+self.sm_dw[m]+' ----\r\n\r\n'
                    for item in group:
                        if item[1]:
                            item[1] = locale.format('%1.2f', item[1], 1)
                            item[2] = locale.format('%1.2f', item[2], 1)
                            text_A = f'{item[0]} | ${item[1]} | ${item[2]}'
                            if len(item) == 4:
                                item[3] = locale.format('%1.2f', item[3], 1)
                                text += f'<i>!!{text_A} -> ${item[3]}!!</i>\r\n\r\n'
                            else:
                                text += text_A+'\r\n\r\n'
                        else:
                            text += f'{item[0]} | dados não encontrados - ' \
                                'ativo incorreto ou muito novo.'
                    text += '\r\n'
            else:
                text = 'A sua carteira está vazia! Acesse /menu > Carteira para adicionar ativos.'
        return text

    def func_radar_auto(self, user_id, s_m, d_w):
        if s_m == None or d_w == None:
            pass
        else:
            mode = s_m+d_w
            mode = self.modes.index(mode)
            buy_text = self.func_radar('buy', user_id, mode)
            track_text = self.func_radar('track', user_id, mode)
            self.func_send_msg(user_id, buy_text)
            self.func_send_msg(user_id, track_text)