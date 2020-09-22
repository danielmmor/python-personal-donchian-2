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
        user_exists = db.user_check(user_id)
        if user_exists:
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
        