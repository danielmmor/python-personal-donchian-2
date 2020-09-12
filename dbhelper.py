'''
***TABLE admin***
user_id +++++ name +++++ username +++++ email +++++ allowed +++++ day

***TABLE stocks_small***
ticker +++++ eod

.
.
.

***TABLE +user_id+***
nums +++++ ticker   +++++ configs
0    ----- null     ----- name
1    ----- null     ----- R$0,00
2    ----- null     ----- 08:00
3    ----- null     ----- small/mid
4    ----- null     ----- daily/week
5    ----- null     ----- perc/blocks
6    ----- null     ----- 1%/8
null ----- [stocks] ----- null

'''

import sqlite3

class DBHelper:
    def __init__(self):
        dbname = 'DB.sqlite'
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def setup(self):

        admin_tbl = 'CREATE TABLE IF NOT EXISTS admin' \
                    '(user_id TEXT UNIQUE, name TEXT, username TEXT, email TEXT, allowed TEXT, day DATE)'
        id_idx = 'CREATE INDEX IF NOT EXISTS idIndex ON admin(user_id ASC)'
        name_idx = 'CREATE INDEX IF NOT EXISTS nameIndex ON admin(name ASC)'
        username_idx = 'CREATE INDEX IF NOT EXISTS usuarioIndex ON admin(username ASC)'
        email_idx = 'CREATE INDEX IF NOT EXISTS mailIndex ON admin(email ASC)'
        day_idx = 'CREATE INDEX IF NOT EXISTS dayIndex ON admin(day ASC)'
        
        # Sempre puxar os EOD da tabela normal, só atualizar do NEW pro normal se pegar
        # a lista de small caps e os EOD com sucesso, ao mesmo tempo.
        small_stmt = 'CREATE TABLE IF NOT EXISTS stocks_small(ticker TEXT UNIQUE, eod TEXT)'
        mid_stmt = 'CREATE TABLE IF NOT EXISTS stocks_mid(ticker TEXT UNIQUE, eod TEXT)'
        n_small_stmt = 'CREATE TABLE IF NOT EXISTS stocks_small_new(ticker TEXT UNIQUE, eod TEXT)'
        n_mid_stmt = 'CREATE TABLE IF NOT EXISTS stocks_mid_new(ticker TEXT UNIQUE, eod TEXT)'

        self.conn.execute(admin_tbl)
        self.conn.execute(id_idx)
        self.conn.execute(name_idx)
        self.conn.execute(username_idx)
        self.conn.execute(email_idx)
        self.conn.execute(day_idx)

        self.conn.execute(small_stmt)
        self.conn.execute(mid_stmt)
        self.conn.execute(n_small_stmt)
        self.conn.execute(n_mid_stmt)
        
        # A primeira linha conterá a data de atualização daqueles eod
        small_stmt = 'INSERT OR IGNORE INTO stocks_small (ticker) VALUES (1)'
        mid_stmt = 'INSERT OR IGNORE INTO stocks_mid (ticker) VALUES (1)'
        n_small_stmt = 'INSERT OR IGNORE INTO stocks_small_new (ticker) VALUES (1)'
        n_mid_stmt = 'INSERT OR IGNORE INTO stocks_mid_new (ticker) VALUES (1)'

        self.conn.execute(small_stmt)
        self.conn.execute(mid_stmt)
        self.conn.execute(n_small_stmt)
        self.conn.execute(n_mid_stmt)
        
        self.conn.commit()


    def user_start(self, user_id, name, username, day):
        user_id = 'a'+str(user_id)

        user_stmt = 'INSERT INTO admin (user_id, allowed, name, username, day) ' \
                   'VALUES ("'+user_id+'", 0, "'+name+'", "@'+username+'", "'+day+'")'
        tbl_stmt = 'CREATE TABLE '+user_id+'(nums TEXT, stocks TEXT, configs TEXT)'

        self.conn.execute(user_stmt)
        self.conn.execute(tbl_stmt)

        A_stmt = 'INSERT INTO '+user_id+' (nums, configs) VALUES (0, "'+name+'")'
        B_stmt = 'INSERT INTO '+user_id+' (nums, configs) VALUES (1, 0)'
        C_stmt = 'INSERT INTO '+user_id+' (nums, configs) VALUES (2, "08:00")'
        D_stmt = 'INSERT INTO '+user_id+' (nums) VALUES (3)'
        E_stmt = 'INSERT INTO '+user_id+' (nums) VALUES (4)'
        F_stmt = 'INSERT INTO '+user_id+' (nums) VALUES (5)'
        G_stmt = 'INSERT INTO '+user_id+' (nums) VALUES (6)'

        self.conn.execute(A_stmt)
        self.conn.execute(B_stmt)
        self.conn.execute(C_stmt)
        self.conn.execute(D_stmt)
        self.conn.execute(E_stmt)
        self.conn.execute(F_stmt)
        self.conn.execute(G_stmt)

        self.conn.commit()


    def user_check(self, user_id, option):
        user_id = 'a'+str(user_id)
        # 0: se existe; 1: se é permitido usar o bot
        if not option:
            stmt = 'SELECT name FROM sqlite_master WHERE type="table" AND name="'+user_id+'"'
            s = [x[0] for x in self.conn.execute(stmt)]
            return s
        else:
            stmt = 'SELECT allowed FROM admin WHERE user_id = ("'+user_id+'")'
            s = [x[0] for x in self.conn.execute(stmt)]
            r = int(s[0])
            return r


    def admin_queries(self, info_A, info_B, info_C, choice):
        # 0 se autoriza: info_A = user_id, info_B = full_name, info_C = dia de hoje; 
        # 1 se desativa: info_A = user_id, info_B = info_C = '';
        # 2 se edita:    info_A = user_id, info_B = campo, info_C = novo dado;
        # 3 se pesquisa: info_A = pesquisa, info_B = campo
        # 4 pesquisa por data: info_A = data inicial, info_B = data final
        if choice < 3:
            user_id = 'a'+str(info_A)
            search = 'SELECT allowed FROM admin WHERE user_id = ("'+user_id+'")'
            r = [x[0] for x in self.conn.execute(search)]
            s = r[0] if r else False
            if not s: return 0

            if choice == 0:
                if s == '1':
                    return 1
                elif info_B != '0':
                    stmt = 'UPDATE admin SET name = ("'+info_B+'"), ' \
                                            'allowed = (1), ' \
                                            'day = ("'+info_C+'") WHERE user_id = ("'+user_id+'")'
                else:
                    stmt = 'UPDATE admin SET allowed = (1), ' \
                                            'day = ("'+info_C+'") WHERE user_id = ("'+user_id+'")'
            elif choice == 1:
                if s == '0':
                    return 1
                stmt = 'UPDATE admin SET allowed = (0) WHERE user_id = ("'+user_id+'")'
            elif choice == 2:
                stmt = 'UPDATE admin SET '+info_B+' = ("'+info_C+'") WHERE user_id = ("'+user_id+'")'
            self.conn.execute(stmt)
            self.conn.commit()
            return 2
        else:
            if choice == 3:
                stmt = 'SELECT * FROM admin WHERE '+info_A+' LIKE "%'+info_B+'%"'
            elif choice == 4:
                stmt = 'SELECT * FROM admin WHERE day BETWEEN "'+info_A+'" AND "'+info_B+'" '
            s = [x for x in self.conn.execute(stmt)]
            s.sort(key=lambda tup: tup[5])
            r = [list(t) for t in s]
            for item in r:
                item[0] = item[0].replace('a', '')
            return r