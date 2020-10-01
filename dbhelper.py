'''
***TABLE users***
user_id +++++ name +++++ username +++++ email +++++ allowed +++++ allowed_day +++++ \
              portf +++++ small/mid +++++ daily/week +++++ hour +++++ radar_day +++++ blocks/perc +++++ 8/1%

(radar_day: segunda 1, terça 2...)

***TABLE stocks_small***
ticker +++++ eod

.
.
.

***TABLE +user_id+***
ticker
[stocks]

'''

import sqlite3

class DBHelper:
    def connect(self, user_id=''):
        dbname = 'DB.sqlite'
        self.conn = sqlite3.connect(dbname)
        if user_id: return ('a'+str(user_id))

    def setup(self):
        self.connect()
        stmt = [
            'CREATE TABLE IF NOT EXISTS users' \
                '(user_id TEXT UNIQUE, name TEXT, username TEXT, email TEXT, ' \
                'allowed TEXT, a_day DATE, portf TEXT, s_m TEXT, d_w TEXT, ' \
                'hour TEXT, r_day TEXT, b_p TEXT, b_p_set TEXT)',
            'CREATE INDEX IF NOT EXISTS idIndex ON users(user_id ASC)',
            'CREATE INDEX IF NOT EXISTS nameIndex ON users(name ASC)',
            'CREATE INDEX IF NOT EXISTS usuarioIndex ON users(username ASC)',
            'CREATE INDEX IF NOT EXISTS mailIndex ON users(email ASC)',
            'CREATE INDEX IF NOT EXISTS dayIndex ON users(a_day ASC)',
            # Sempre puxar os EOD da tabela normal, só atualizar do NEW pro normal se pegar
            # a lista de small caps e os EOD com sucesso, ao mesmo tempo.
            'CREATE TABLE IF NOT EXISTS stocks_small(ticker TEXT UNIQUE, eod TEXT)',
            'CREATE TABLE IF NOT EXISTS stocks_mid(ticker TEXT UNIQUE, eod TEXT)',
            'CREATE TABLE IF NOT EXISTS stocks_small_new(ticker TEXT UNIQUE, eod TEXT)',
            'CREATE TABLE IF NOT EXISTS stocks_mid_new(ticker TEXT UNIQUE, eod TEXT)',
            # A primeira linha conterá a data de atualização daqueles eod
            'INSERT OR IGNORE INTO stocks_small (ticker) VALUES (1)',
            'INSERT OR IGNORE INTO stocks_mid (ticker) VALUES (1)',
            'INSERT OR IGNORE INTO stocks_small_new (ticker) VALUES (1)',
            'INSERT OR IGNORE INTO stocks_mid_new (ticker) VALUES (1)',
        ]
        for s in stmt:
            self.conn.execute(s)
        self.conn.commit()

    def user_start(self, user_id, name, username, day):
        user_id = self.connect(user_id)
        stmt = [
            'CREATE TABLE IF NOT EXISTS '+user_id+'(ticker TEXT UNIQUE)',
            'INSERT INTO users (user_id, allowed, name, username, a_day, portf, hour, r_day) ' \
            'VALUES ("'+user_id+'", 0, "'+name+'", "@'+username+'", "'+day+'", 0, "08:00", 1)',
        ]
        for s in stmt:
            self.conn.execute(s)
        self.conn.commit()

    def admin_queries(self, info_A, info_B, info_C, choice):
        # 0 se autoriza: info_A = user_id, info_B = full_name, info_C = dia de hoje; 
        # 1 se desativa: info_A = user_id, info_B = info_C = '';
        # 2 se edita:    info_A = user_id, info_B = campo, info_C = novo dado;
        # 3 se pesquisa: info_A = pesquisa, info_B = campo
        # 4 pesquisa por data: info_A = data inicial, info_B = data final
        if choice < 3:
            user_id = self.connect(info_A)
            exists = self.get_info(info_A)
            if exists:
                if choice == 0:
                    if exists[0][4] == '1': return 1
                    elif info_B != '0':
                        stmt = 'UPDATE users ' \
                               'SET name = ("'+info_B+'"), allowed = (1), a_day = ("'+info_C+'") ' \
                               'WHERE user_id = ("'+user_id+'")'
                    else:
                        stmt = 'UPDATE users ' \
                               'SET allowed = (1), a_day = ("'+info_C+'") ' \
                               'WHERE user_id = ("'+user_id+'")'
                elif choice == 1:
                    if exists[0][4] == '0': return 1
                    stmt = 'UPDATE users SET allowed = (0) WHERE user_id = ("'+user_id+'")'
                elif choice == 2:
                    stmt = 'UPDATE users SET '+info_B+' = ("'+info_C+'") WHERE user_id = ("'+user_id+'")'
                self.conn.execute(stmt)
                self.conn.commit()
                return 2
            else:
                return 0
        else:
            self.connect()
            if choice == 3:
                stmt = 'SELECT * FROM users WHERE '+info_A+' LIKE "%'+info_B+'%"'
            elif choice == 4:
                stmt = 'SELECT * FROM users WHERE a_day BETWEEN "'+info_A+'" AND "'+info_B+'" '
            q = [x for x in self.conn.execute(stmt)]
            q.sort(key=lambda tup: tup[5])
            r = [list(t) for t in q]
            for item in r:
                item[0] = item[0].replace('a', '')
            return r
    
    def user_init(self, user_id, all_data):
        user_id = self.connect(user_id)
        field = ['s_m', 'd_w', 'b_p', 'b_p_set', 'portf']
        for i in range(len(field)):
            s = 'UPDATE users SET '+field[i]+' = ("'+all_data[i]+'") WHERE user_id = ("'+user_id+'")'
            self.conn.execute(s)
        self.conn.commit()

    def get_info(self, user_id):
        # q[0] - 0: user_id
        # 1: name
        # 2: username
        # 3: email
        # 4: allowed
        # 5: a_day
        # 6: portf
        # 7: S_M
        # 8: D_W
        # 9: hour
        # 10: r_day
        # 11: B_P
        # 12: 8/1%
        user_id = self.connect(user_id)
        stmt = 'SELECT * FROM users WHERE user_id = ("'+user_id+'")'
        q = [x for x in self.conn.execute(stmt)]
        return q

    def info_upd(self, user_id, field, data):
        user_id = self.connect(user_id)
        stmt = 'UPDATE users SET '+field+' = ("'+data+'") WHERE user_id = ("'+user_id+'")'
        self.conn.execute(stmt)
        self.conn.commit()

    def get_tickers(self, user_id):
        user_id = self.connect(user_id)
        stmt = 'SELECT * FROM '+user_id
        q = [x for x in self.conn.execute(stmt)]
        return q

    def tickers_upd(self, user_id, ticker, choice):
        user_id = self.connect(user_id)
        if choice == 0:
            stmt = 'INSERT OR IGNORE INTO '+user_id+' (ticker) VALUES ("'+ticker+'")'
        else:
            stmt = 'DELETE FROM '+user_id+' WHERE ticker = ("'+ticker+'")'
        try:
            self.conn.execute(stmt)
            self.conn.commit()
            return True
        except:
            return False
