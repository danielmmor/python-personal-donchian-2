'''
***TABLE users***
user_id +++++ name +++++ username +++++ email +++++ allowed +++++ allowed_day +++++ \
    portf +++++ small/midlarge +++++ daily/week +++++ hour +++++ radar_day +++++ \
    blocks/perc +++++ 8/1% +++++ order

(radar_day: segunda 1, terça 2...)

***TABLE stocks_small***
ticker
07/10/2020
AAAA3
AAAB3
AAAC3
.
.
.

***TABLE +user_id+***
ticker   +++++ S_M_D_W
[stocks] ----- [S/M][D/W]

'''

import sqlite3

class DBHelper:
    def connect(self, user_id=''):
        dbname = 'DB.sqlite'
        self.conn = sqlite3.connect(dbname)
        if user_id: return str(user_id)

    def setup(self):
        print('Initializing database...')
        self.connect()
        stmt = [
            'CREATE TABLE IF NOT EXISTS users' \
                '(user_id TEXT UNIQUE, name TEXT, username TEXT, email TEXT, ' \
                'allowed TEXT, a_day DATE, portf TEXT, S_M TEXT, D_W TEXT, ' \
                'hour TEXT, r_day TEXT, B_P TEXT, B_P_set TEXT, sorting TEXT)',
            'CREATE INDEX IF NOT EXISTS idIndex ON users(user_id ASC)',
            'CREATE INDEX IF NOT EXISTS nameIndex ON users(name ASC)',
            'CREATE INDEX IF NOT EXISTS usuarioIndex ON users(username ASC)',
            'CREATE INDEX IF NOT EXISTS mailIndex ON users(email ASC)',
            'CREATE INDEX IF NOT EXISTS dayIndex ON users(a_day ASC)',
            # Sempre puxar os EOD da tabela normal, só atualizar do NEW pro normal se pegar
            # a lista de small caps e os EOD com sucesso, ao mesmo tempo.
            'CREATE TABLE IF NOT EXISTS stocks_S(ticker TEXT UNIQUE, eod TEXT)',
            'CREATE TABLE IF NOT EXISTS stocks_M(ticker TEXT UNIQUE, eod TEXT)',
            'CREATE TABLE IF NOT EXISTS stocks_SN(ticker TEXT UNIQUE, eod TEXT)',
            'CREATE TABLE IF NOT EXISTS stocks_MN(ticker TEXT UNIQUE, eod TEXT)',
        ]
        for s in stmt:
            self.conn.execute(s)
        self.conn.commit()
        print('Database ready.')

    def user_start(self, user_id, name, username, day):
        user_id = self.connect(user_id)
        stmt = [
            'CREATE TABLE IF NOT EXISTS "'+user_id+'"(ticker TEXT UNIQUE, ' \
                'S_M_D_W TEXT)',
            'INSERT INTO users (user_id, allowed, name, username, a_day, portf, hour, r_day) ' \
            'VALUES ("'+user_id+'", 0, "'+name+'", "@'+username+'", "'+day+'", 0, "10:30", 1)',
        ]
        for s in stmt:
            self.conn.execute(s)
        self.conn.commit()

    def admin_queries(self, info_A, info_B='', info_C='', choice=''):
        # 0 se autoriza: info_A = user_id, info_B = full_name, info_C = dia de hoje; 
        # 1 se desativa: info_A = user_id, info_B = info_C = '';
        # 2 se edita:    info_A = user_id, info_B = campo, info_C = novo dado;
        # 3 se pesquisa: info_A = campo, info_B = pesquisa, info_C = '';
        # 4 pesquisa por data: info_A = data inicial, info_B = data final, info_C = '';
        # 5 se reseta:   info_A = user_id
        if choice < 3 or choice == 5:
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
                elif choice == 5:
                    stmt = 'DROP TABLE "'+user_id+'"'
                    self.conn.execute(stmt)
                    stmt = 'DELETE FROM users WHERE user_id = ("'+user_id+'")'
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
            return r
    
    def user_init(self, user_id, all_data):
        user_id = self.connect(user_id)
        field = ['S_M', 'D_W', 'B_P', 'B_P_set', 'portf']
        for i in range(len(field)):
            s = 'UPDATE users SET '+field[i]+' = ("'+all_data[i]+'") WHERE user_id = ("'+user_id+'")'
            self.conn.execute(s)
        self.conn.commit()

    def get_info(self, user_id):
        # q[0] - 0: user_id
        # 1: name - Abc
        # 2: username - @Abc
        # 3: email - abc@dce.fg
        # 4: allowed - 0/1
        # 5: a_day - 2020-01-20
        # 6: portf - 123,45
        # 7: S_M - S/M
        # 8: D_W - D_W
        # 9: hour - 13:45
        # 10: r_day - 0~7
        # 11: B_P - B/P
        # 12: B_P_set - 8/1%
        # 13: order - 0~?
        user_id = self.connect(user_id)
        stmt = 'SELECT * FROM users WHERE user_id = ("'+user_id+'")'
        q = [x for x in self.conn.execute(stmt)]
        return q

    def info_upd(self, user_id, field, data):
        user_id = self.connect(user_id)
        stmt = 'UPDATE users SET '+field+' = ("'+data+'") WHERE user_id = ("'+user_id+'")'
        self.conn.execute(stmt)
        self.conn.commit()

    def get_everything(self, table):
        table = self.connect(table)
        stmt = 'SELECT * FROM "'+table+'"'
        q = [x for x in self.conn.execute(stmt)]
        return q

    def tickers_upd_user(self, user_id, tickers, choice):
        user_id = self.connect(user_id)
        modes = ['SD', 'SW', 'MD', 'MW']
        for t in tickers:
            if choice < 4:
                stmt = 'INSERT OR IGNORE INTO "'+user_id+'" (ticker, S_M_D_W) ' \
                    'VALUES ("'+t+'", "'+modes[choice]+'")'
            else:
                stmt = 'DELETE FROM "'+user_id+'" WHERE ticker = ("'+t+'")'
            try:
                self.conn.execute(stmt)
            except:
                return False
        self.conn.commit()
        return True

    def tickers_upd(self, table, tickers_list, date):
        self.connect()
        del_stmt = 'DELETE FROM stocks_'+table
        #date_stmt = 'INSERT INTO stocks_'+table+' (ticker) VALUES ("'+date+'")'
        self.conn.execute(del_stmt)
        #self.conn.execute(date_stmt)
        for ticker in tickers_list:
            stmt = 'INSERT INTO stocks_'+table+' (ticker) VALUES ("'+ticker+'")'
            self.conn.execute(stmt)
        self.conn.commit()