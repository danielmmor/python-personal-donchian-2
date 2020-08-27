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


    def func_user_start(self, user_id, name, username, dbname):
        user_exists = db.user_check(user_id, dbname, 0)
        if user_exists:
            text = 'Você já deu o start!'
            return text
        else:
            dia = str(datetime.now().date())
            db.user_start(user_id, name, username, dia, dbname)
            return False


    def func_admin(self, msg, dbname, choice):
        query_info = msg.split(', ')
        # db.admin_queries(info_A, info_B, info_C, dbname, choice)
        # 0 se autoriza: info_A = user_id, info_B = full_name, info_C = dia de hoje; 
        # 1 se desativa: info_A = user_id, info_B = info_C = '';
        # 2 se edita:    info_A = user_id, info_B = campo, info_C = novo dado;
        # 3 se pesquisa: info_A = pesquisa, info_B = campo;
        # 4 pesquisa por data: info_A = data inicial, info_B = data final
        try:
            if choice < 3:
                y = re.match(r'^\d*$', query_info[0])
                if not y:
                    response = 'Formato inválido! O user_id deve conter somente números. Tente novamente.'
                    return response, False

            if choice == 0:
                date = str(datetime.now().date())
                res = db.admin_queries(query_info[0], query_info[1], date, dbname, choice)
                action = 'autorizado'
            elif choice == 1:
                res = db.admin_queries(query_info[0], '', '', dbname, choice)
                action = 'desativado'
            elif choice in {2, 3, 4}:
                query_info.append('')

                if ((choice == 2 and re.match('^(nome|username|email)$', query_info[1])) \
                    or (choice == 3 and re.match('^(user_id|nome|username)$', query_info[0]))):
                    if re.match('^(user_id)$', query_info[0]):
                        query_info[0] = query_info[0].replace('_', '')
                    res = db.admin_queries(query_info[0], query_info[1], query_info[2], dbname, choice)

                elif (choice == 4 and re.match(r'^(\d\d[/]\d\d[/]\d\d\d\d)$', query_info[0]) \
                      and re.match(r'^(\d\d[/]\d\d[/]\d\d\d\d)$', query_info[1])):
                    query_info[0] = self.func_time(query_info[0], '/')
                    query_info[1] = self.func_time(query_info[1], '/')
                    res = db.admin_queries(query_info[0], query_info[1], query_info[2], dbname, choice)

            if res == 0:
                response = 'Este usuário não existe! Tente novamente ou clique em /cancelar.'
                return response, False
            elif not res:
                response = 'Nada foi encontrado para essa pesquisa! Tente novamente ou clique em /cancelar.'
                return response, False
            elif choice in {0, 1}:
                if res == 1:
                    response = f'Este usuário já está {action}! Sessão encerrada.'
                else:
                    response = f'O usuário foi {action} com sucesso!'
            elif choice == 2:
                response = 'O campo foi editado com sucesso! Sessão encerrada.'
            elif choice in {3, 4}:
                response = 'Resultados da pesquisa:\n\r\n\r'
                for item in res:
                    if item[3] == None:
                        item[3] = '-'
                    item[4] = 'Desativado' if item[4] == '0' else 'Autorizado'
                    item[5] = self.func_time(item[5], '-')
                    response += (
                        f'user_id: {item[0]}\n\r'
                        f'Nome: {item[1]}\n\r'
                        f'username: {item[2]}\n\r'
                        f'E-mail: {item[3]}\n\r'
                        f'{item[4]}\n\r'
                        f'Data de entrada \\ última autorização: {item[5]}\n\r\n\r'
                    )
            return response, True
        except:
            response = 'Formato inválido! Esqueceu algo? Tente novamente ou clique em /cancelar.'
            return response, False
        