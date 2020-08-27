import sqlite3

class DBHelper:

    def connect(self, user_id, dbname):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)
        user_id = 'a'+str(user_id)
        return user_id


    def setup(self, dbname):
        user_id = ''
        user_id = self.connect(user_id, dbname)

        admin_tbl = 'CREATE TABLE IF NOT EXISTS admin' \
                    '(userid TEXT UNIQUE, nome TEXT, username TEXT, email TEXT, allowed TEXT, dia DATE)'
        id_idx = 'CREATE INDEX IF NOT EXISTS idIndex ON admin(userid ASC)'
        all_idx = 'CREATE INDEX IF NOT EXISTS allIndex ON admin(allowed ASC)'
        name_idx = 'CREATE INDEX IF NOT EXISTS nameIndex ON admin(nome ASC)'
        username_idx = 'CREATE INDEX IF NOT EXISTS usuarioIndex ON admin(username ASC)'
        email_idx = 'CREATE INDEX IF NOT EXISTS mailIndex ON admin(email ASC)'
        dia_idx = 'CREATE INDEX IF NOT EXISTS dayIndex ON admin(dia ASC)'
        
        small_stmt = 'CREATE TABLE IF NOT EXISTS stocks_small(idxid TEXT UNIQUE, eod TEXT)'
        idx_s_idx = 'CREATE INDEX IF NOT EXISTS idxIndex ON stocks_small(idxid ASC)'
        eod_s_idx = 'CREATE INDEX IF NOT EXISTS endIndex ON stocks_small(eod ASC)'

        mid_stmt = 'CREATE TABLE IF NOT EXISTS stocks_mid(idxid TEXT UNIQUE, eod TEXT)'
        idx_m_idx = 'CREATE INDEX IF NOT EXISTS idxIndex ON stocks_mid(idxid ASC)'
        eod_m_idx = 'CREATE INDEX IF NOT EXISTS endIndex ON stocks_mid(eod ASC)'
        
        n_small_stmt = 'CREATE TABLE IF NOT EXISTS stocks_small_new(idxid TEXT UNIQUE, eod TEXT)'
        n_idx_s_idx = 'CREATE INDEX IF NOT EXISTS idxIndex ON stocks_small_new(idxid ASC)'
        n_eod_s_idx = 'CREATE INDEX IF NOT EXISTS endIndex ON stocks_small_new(eod ASC)'

        n_mid_stmt = 'CREATE TABLE IF NOT EXISTS stocks_mid_new(idxid TEXT UNIQUE, eod TEXT)'
        n_idx_m_idx = 'CREATE INDEX IF NOT EXISTS idxIndex ON stocks_mid_new(idxid ASC)'
        n_eod_m_idx = 'CREATE INDEX IF NOT EXISTS endIndex ON stocks_mid_new(eod ASC)'

        self.conn.execute(admin_tbl)
        self.conn.execute(id_idx)
        self.conn.execute(all_idx)
        self.conn.execute(name_idx)
        self.conn.execute(username_idx)
        self.conn.execute(email_idx)
        self.conn.execute(dia_idx)

        self.conn.execute(small_stmt)
        self.conn.execute(idx_s_idx)
        self.conn.execute(eod_s_idx)

        self.conn.execute(mid_stmt)
        self.conn.execute(idx_m_idx)
        self.conn.execute(eod_m_idx)

        self.conn.execute(n_small_stmt)
        self.conn.execute(n_idx_s_idx)
        self.conn.execute(n_eod_s_idx)

        self.conn.execute(n_mid_stmt)
        self.conn.execute(n_idx_m_idx)
        self.conn.execute(n_eod_m_idx)
        
        small_stmt = 'INSERT OR IGNORE INTO stocks_small (idxid) VALUES (1)'
        mid_stmt = 'INSERT OR IGNORE INTO stocks_mid (idxid) VALUES (1)'
        n_small_stmt = 'INSERT OR IGNORE INTO stocks_small_new (idxid) VALUES (1)'
        n_mid_stmt = 'INSERT OR IGNORE INTO stocks_mid_new (idxid) VALUES (1)'

        self.conn.execute(small_stmt)
        self.conn.execute(mid_stmt)
        self.conn.execute(n_small_stmt)
        self.conn.execute(n_mid_stmt)
        
        self.conn.commit()


    def user_start(self, user_id, name, username, dia, dbname):
        user_id = self.connect(user_id, dbname)

        userstmt = 'INSERT INTO admin (userid, allowed, nome, username, dia) ' \
                   'VALUES ("'+user_id+'", 0, "'+name+'", "@'+username+'", "'+dia+'")'

        tblstmt = 'CREATE TABLE '+user_id+'(nums TEXT, stocks TEXT, configs TEXT)'

        self.conn.execute(userstmt)

        self.conn.execute(tblstmt)

        Astmt = 'INSERT INTO '+user_id+' (nums, configs) VALUES (0, "'+name+'")'
        Bstmt = 'INSERT INTO '+user_id+' (nums, configs) VALUES (1, 0)'
        Cstmt = 'INSERT INTO '+user_id+' (nums, configs) VALUES (2, "08:00")'
        Dstmt = 'INSERT INTO '+user_id+' (nums) VALUES (3)'
        Estmt = 'INSERT INTO '+user_id+' (nums) VALUES (4)'
        Fstmt = 'INSERT INTO '+user_id+' (nums) VALUES (5)'
        Gstmt = 'INSERT INTO '+user_id+' (nums) VALUES (6)'

        self.conn.execute(Astmt)
        self.conn.execute(Bstmt)
        self.conn.execute(Cstmt)
        self.conn.execute(Dstmt)
        self.conn.execute(Estmt)
        self.conn.execute(Fstmt)
        self.conn.execute(Gstmt)

        self.conn.commit()


    def user_check(self, user_id, dbname, option):
        user_id = self.connect(user_id, dbname)
        # 0: se existe; 1: se é permitido usar o bot
        if not option:
            stmt = 'SELECT name FROM sqlite_master WHERE type="table" AND name="'+user_id+'"'
            s = [x[0] for x in self.conn.execute(stmt)]
            return s
        else:
            stmt = 'SELECT allowed FROM admin WHERE userid = ("'+user_id+'")'
            s = [x[0] for x in self.conn.execute(stmt)]
            r = int(s[0])
            return r


    def admin_queries(self, info_A, info_B, info_C, dbname, choice):
        # 0 se autoriza: info_A = user_id, info_B = full_name, info_C = dia de hoje; 
        # 1 se desativa: info_A = user_id, info_B = info_C = '';
        # 2 se edita:    info_A = user_id, info_B = campo, info_C = novo dado;
        # 3 se pesquisa: info_A = pesquisa, info_B = campo
        # 4 pesquisa por data: info_A = data inicial, info_B = data final
        if choice < 3:
            user_id = self.connect(info_A, dbname)
            search = 'SELECT allowed FROM admin WHERE userid = ("'+user_id+'")'
            r = [x[0] for x in self.conn.execute(search)]
            s = r[0] if r else False
            if not s: return 0

            if choice == 0:
                if s == '1':
                    return 1
                elif info_B != '0':
                    stmt = 'UPDATE admin SET nome = ("'+info_B+'"), ' \
                                            'allowed = (1), ' \
                                            'dia = ("'+info_C+'") WHERE userid = ("'+user_id+'")'
                else:
                    stmt = 'UPDATE admin SET allowed = (1), ' \
                                            'dia = ("'+info_C+'") WHERE userid = ("'+user_id+'")'
            elif choice == 1:
                if s == '0':
                    return 1
                stmt = 'UPDATE admin SET allowed = (0) WHERE userid = ("'+user_id+'")'
            elif choice == 2:
                stmt = 'UPDATE admin SET '+info_B+' = ("'+info_C+'") WHERE userid = ("'+user_id+'")'
            self.conn.execute(stmt)
            self.conn.commit()
            return 2
        else:
            user_id = ''
            user_id = self.connect(user_id, dbname)
            if choice == 3:
                stmt = 'SELECT * FROM admin WHERE '+info_A+' LIKE "%'+info_B+'%"'
            elif choice == 4:
                stmt = 'SELECT * FROM admin WHERE dia BETWEEN "'+info_A+'" AND "'+info_B+'" '
            s = [x for x in self.conn.execute(stmt)]
            s.sort(key=lambda tup: tup[5])
            r = [list(t) for t in s]
            for item in r:
                item[0] = item[0].replace('a', '')
            return r