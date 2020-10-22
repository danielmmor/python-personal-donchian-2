import requests
import pickle
import schedule
import time as tm
import numpy as np
import yfinance as yf
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, time
from dbhelper import DBHelper
from hidden.donchian import Donchian

db = DBHelper()
dc = Donchian()

class Radar():
    def __init__(self):
        tables = ['S', 'M']
        for table in tables:
            schedule.every().monday.at('14:30').do(self.gather_tickers, table=table)
            schedule.every().tuesday.at('14:30').do(self.gather_tickers, table=table)
            schedule.every().wednesday.at('14:30').do(self.gather_tickers, table=table)
            schedule.every().thursday.at('14:30').do(self.gather_tickers, table=table)
            schedule.every().friday.at('14:30').do(self.gather_tickers, table=table)

    def save_obj(self, obj, name):
        with open('obj/' + name + '.pkl', 'wb+') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    def load_obj(self, name):
        with open('obj/' + name + '.pkl', 'rb') as f:
            return pickle.load(f)

    def gather_tickers(self, table):
        tables = {
            'S': 'SMLL',
            'SN': 'SMLL',
            'M': 'MLCX',
            'MN': 'MLCX'
        }
        url = 'http://bvmf.bmfbovespa.com.br/indices/' \
            'ResumoCarteiraTeorica.aspx?Indice='+tables[table]+'&idioma=pt-br'
        t_list = []
        trials = 1
        while t_list == [] and trials < 300:
            page = requests.get(url)
            resultado = BeautifulSoup(page.content, 'html.parser')
            for ticker in resultado.findAll('td', {'class': 'rgSorted'}):
                t_text = ticker.findAll(text=True)
                t_list.append(t_text[1])
            trials += 1
            tm.sleep(2)
        today = str(datetime.now().date())
        db.tickers_upd(table, t_list, today)

    def gather_eod(self, s_m, d_w, choice, t_list=''):
        mode = s_m + d_w
        if choice == 0:
            modes = {
                'SD': [240, '1d'], 'MD': [360, '1d'],
                'SW': [260, '1wk'], 'MW': [380, '1wk']
            }
            days, interval = modes[mode]
            t_list = db.get_tickers('stocks_'+s_m)
            t_list = [x[0] for x in t_list]
            t_list = t_list[1:]
        elif choice == 1:
            days = 4
            interval = '1d' if d_w == 'D' else '1wk'
            t_list = db.get_tickers('stocks_'+s_m)
            t_list = [x[0] for x in t_list]
            t_list = t_list[1:]
        elif choice == 2:
            modes = {
                'SD': [90, '1d'], 'MD': [130, '1d'],
                'SW': [260, '1wk'], 'MW': [380, '1wk']
            }
            days, interval = modes[mode]
        now = str(datetime.now().date()+timedelta(days=2))
        before = str(datetime.now().date()-timedelta(days=days))
        t_list_sa = [x + '.SA' for x in t_list]
        history_all, close_all = {}, {}
        i, k, jump = 1, 1, 25
        last = len(t_list)
        while i <= last:
            m = i
            temp, temp_sa = [], []
            j = k*jump
            while i <= j and i <= last:
                temp.append(t_list[i-1])
                temp_sa.append(t_list_sa[i-1])
                i += 1
            temp_sa_y = ' '.join(temp_sa)
            try:
                data = yf.download(temp_sa_y, interval=interval, 
                                   auto_adjust=True, start=before, end=now)
                for t, t_sa in zip(temp, temp_sa):
                    if len(temp) == 1:
                        d_high, d_low, d_close = data['High'], data['Low'], data['Close']
                    else:
                        d_high, d_low, d_close = data[('High', t_sa)], data[('Low', t_sa)], data[('Close', t_sa)]
                    if choice == 0:
                        high = [float('%.2f' % d_high[x]) for x in d_high]
                        low = [float('%.2f' % d_low[x]) for x in d_low]
                        avg = [(x+y)/2 for x, y in zip(*[high, low])]
                        history_all[t] = [high, low, avg]
                    if choice == 2:
                        low = [float('%.2f' % d_low[x]) for x in d_low]
                        history_all[t] = low
                    closing = float('%.2f' % d_close[-1])
                    if closing == 0 or np.isnan(closing):
                        close_all[t] = float('%.2f' % d_close[-2])
                    else:
                        close_all[t] = closing
                k += 1
            except Exception as e:
                print(e)
                i = m
                tm.sleep(2)
        if choice == 0:
            self.save_obj(history_all, mode)
            self.save_obj(close_all, mode + '_close')
        if choice == 1:
            return close_all
        else:
            return history_all, close_all

    def trigger(self, mode):
        return mode