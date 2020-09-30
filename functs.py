import re

from datetime import datetime

from dbhelper import DBHelper

db = DBHelper()

class Functions():
    def func_time(self, var, separator):
        if separator == '/':
            new_format = datetime.strptime(var,f'%d/%m/%Y').strftime(f'%Y-%m-%d')
        elif separator == '-':
            new_format = datetime.strptime(var, '%Y-%m-%d').strftime('%d/%m/%Y')
        return new_format

    def func_user_start(self, user_id, name, username):
        exists = db.get_info(user_id)
        if exists:
            admin_text = f'Usuário mandou novamente:\nuser_id: {user_id}\n' \
                         f'nome: {name}\nusername: @{username}'
            user_text = 'Você já deu o start!'
        else:
            dia = str(datetime.now().date())
            db.user_start(user_id, name, username, dia)
            admin_text = f'Novo usuário:\nuser_id: {user_id}\n' \
                         f'nome: {name}\nusername: @{username}'
            user_text = 'Bem-vindo, investidor! Por favor, aguarde enquanto preparamos tudo.'
        return admin_text, user_text

    def func_admin(self, msg, choice):
        info = msg.split(', ')
        # db.admin_queries(info_A, info_B, info_C, choice)
        # 0 se autoriza: info_A = user_id, info_B = full_name, info_C = dia de hoje; 
        # 1 se desativa: info_A = user_id, info_B = info_C = '';
        # 2 se edita:    info_A = user_id, info_B = campo, info_C = novo dado;
        # 3 se pesquisa: info_A = pesquisa, info_B = campo;
        # 4 pesquisa por data: info_A = data inicial, info_B = data final
        try:
            # The query:
            if choice < 3:
                y = re.match(r'^\d*$', info[0])
                if not y:
                    response = 'Formato inválido! O user_id deve conter somente números. Tente novamente.'
                    return response, False
            if choice == 0:
                date = str(datetime.now().date())
                res = db.admin_queries(info[0], info[1], date, choice)
                action = 'autorizado'
            elif choice == 1:
                res = db.admin_queries(info[0], '', '', choice)
                action = 'desativado'
            elif choice in {2, 3, 4}:
                info.append('') # fills the gap for choice 4 and info 2
                if ((choice == 2 and re.match('^(nome|username|email)$', info[1], re.I)) \
                        or (choice == 3 and re.match('^(user_id|nome|username)$', info[0], re.I))):
                    if re.match('^nome$', info[0], re.I): info[0] = info[0].replace('o', 'a')
                    if re.match('^nome$', info[1], re.I): info[1] = info[1].replace('o', 'a')
                    res = db.admin_queries(info[0], info[1], info[2], choice)
                elif (choice == 4 and re.match(r'^(\d\d[/]){2}\d{4}$', info[0]) \
                        and re.match(r'^(\d\d[/]){2}\d{4}$', info[1])):
                    info[0] = self.func_time(info[0], '/')
                    info[1] = self.func_time(info[1], '/')
                    res = db.admin_queries(info[0], info[1], info[2], choice)
            # The response:
            if res == 0:
                response = 'Este usuário não existe! Tente novamente ou clique em /cancelar.'
                return response, False
            elif not res:
                response = 'Nada foi encontrado para essa pesquisa! Tente novamente ou clique em /cancelar.'
                return response, False
            elif choice in {0, 1}:
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
        
    def func_init_check(self, mode, data):
        if mode == 'B' and not re.match('^[1-9]+\d*$', data):
            text = 'Formato inválido. Digite o valor dos bloquinhos neste formato ' \
                '(somente números, sem aspas): "8" ou "12". Tente novamente:'
            return text, False
        elif mode == 'P' and not re.match('^\d+(([,]\d+)|)$', data):
            text = 'Formato inválido. Digite o valor do porcentual neste formato ' \
                '(somente números, sem aspas): "1,5" ou "2". Tente novamente:'
            return text, False
        elif mode in ['B', 'P']:
            text = 'Por último: qual o seu capital atual para investir pelo método? Envie "0" '\
                ' (zero, sem as aspas) se não quiser responder. Isto serve para o cálculo ' \
                'automático do volume a ser comprado (ex.: "1234,56", sem as aspas).'
            return text, True
        elif mode == 'p':
            if not re.match('^\d+(([,]\d+)|)$', data):
                text = 'Formato inválido. Digite o valor do capital neste formato (somente números, sem aspas): ' \
                    '"1234,56" ou digite "0" se não quiser responder. Tente novamente:'
                return text, False
            else:
                text = 'Tudo pronto! Você pode mudar essas configurações através do /menu. ' \
                    'Lá você também pode obter o relatório manualmente ou saber mais informações sobre o bot.'
                return text, True
    
    def func_get_info(self, user_id):
        info = db.get_info(user_id)
        stock = 'Small Caps' if info[0][7] == 'S' else 'Mid Caps'
        freq = 'Diário' if info[0][8] == 'D' else 'Semanal'
        days = [
            'todos os dias',
            'Segunda-Feira',
            'Terça-Feira',
            'Quarta-Feira',
            'Quinta-Feira',
            'Sexta-Feira',
            'Sábado',
            'Domingo',
        ]
        day = days[0] if info[0][8] == 'D' else days[int(info[0][10])]
        if info[0][11] == 'B':
            risk = 'Bloquinho por operação\n\rBloquinhos: '+info[0][12]+''
        else:
            risk = 'Porcentagem relativa ao stop\n\rPorcentual: '+info[0][12]+'%'
        text = 'MEU STATUS:\n\r\n\r' \
            'Capital: R$'+info[0][6]+'\n\r' \
            'Classe de ações padrão: '+stock+'\n\r' \
            'Escala temporal padrão: '+freq+'\n\r' \
            'Hora e dia da semana programados: ' \
            ''+info[0][9]+', '+day+'\n\r' \
            'Gerenciamento de risco: '+risk
        return text

    def func_portf_upd(self, user_id, msg, choice):
        if choice < 3 and re.match('^\d+(([,]\d+)|)$', msg):
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
            text = 'Formato inválido. Tente colocar o valor neste formato (somente números): "1234,56"'
            return text, False

    def func_get_tickers(self, user_id):
        t_list = db.get_tickers(user_id)
        if t_list:
            t_list = [x[0] for x in t_list]
            text = '\n'.join(t_list)
        else:
            text = 'A sua carteira está vazia!'
        return text

    def func_tickers_upd(self, user_id, msg, choice):
        if re.match('^[a-zA-Z]{4}(\d|\d\d)$', msg):
            success = db.tickers_upd(user_id, msg, choice)
            action = ['adicionado', 'removido']
            if success:
                text = 'O ativo '+msg+' foi '+action[choice]+' com sucesso!\nAté mais!'
            else:
                text = 'Não existe este ativo na sua carteira!\nAté mais!'
        else:
            success = False
            text ='Tente colocar o índice neste formato: "PETR4" (sem as aspas):'
        return text, success

        
