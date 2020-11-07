import requests
import pickle
import schedule
import time as tm
import numpy as np
import yfinance as yf
from bs4 import BeautifulSoup
from datetime import datetime as dtt, timedelta, time
from dbhelper import DBHelper
from hidden.donchian import Donchian

db = DBHelper()
dc = Donchian()

class Radar():
    def __init__(self):
        print('Initializing radar - gather & schedule tickers and EOD')
        tables = ['S', 'M']
        scales = ['D', 'W']
        ticker_hour = self.hour_fix('17:45')
        eod_hour = self.hour_fix('18:01')
        for table in tables:
            self.gather_tickers(table)
            self.weekly(ticker_hour, self.gather_tickers, 'tickers', table=table)
            for scale in scales:
                self.gather_eod(table, scale, 0)
                self.weekly(eod_hour, self.gather_eod, 'eod', s_m=table, d_w=scale, choice=0)
        print('Radar ready.')

    def hour_fix(self, hour):
        offset = 0
        hour = dtt.strptime(hour, '%H:%M')
        hour += timedelta(hours=offset)
        hour = hour.strftime('%H:%M')
        return hour
        
    def weekly(self, hour, func, tag, **kwargs):
            schedule.every().monday.at(hour).do(func, **kwargs).tag(tag)
            schedule.every().tuesday.at(hour).do(func, **kwargs).tag(tag)
            schedule.every().wednesday.at(hour).do(func, **kwargs).tag(tag)
            schedule.every().thursday.at(hour).do(func, **kwargs).tag(tag)
            schedule.every().friday.at(hour).do(func, **kwargs).tag(tag)
            schedule.every().saturday.at(hour).do(func, **kwargs).tag(tag)

    def save_obj(self, obj, name):
        with open('obj/' + name + '.pkl', 'wb+') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    def load_obj(self, name):
        with open('obj/' + name + '.pkl', 'rb') as f:
            return pickle.load(f)

    def incl_last(self):
        now_time = dtt.now().time()
        weekday = dtt.today().weekday()
        new_entry = dtt.strptime(self.hour_fix('10:20'), '%H:%M').time()
        mkt_close = dtt.strptime(self.hour_fix('18:00'), '%H:%M').time()
        if now_time > new_entry or now_time <= mkt_close:
            a = 1
        else:
            a = 0
        if (weekday == 0 and now_time > new_entry) \
                or weekday in [1, 2, 3] \
                or (weekday == 4 and now_time <= mkt_close):
            b = 1
        else:
            b = 0
        return [a, b]

    def gather_tickers(self, table):
        print('Gathering tickers for table '+table+'...')
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
        today = str(dtt.now().date())
        db.tickers_upd(table, t_list, today)
        print('Tickers saved.')

    def gather_eod(self, s_m, d_w, choice, t_list=''):
        print('Gathering EOD data for mode '+s_m+d_w+'...')
        # choice 0 - up, close, down
        # choice 1 - close only
        # choice 2 - down only
        mode = s_m + d_w
        if choice == 0:
            print('EOD: high, low, close')
            modes = {
                'SD': [240, '1d'], 'MD': [360, '1d'],
                'SW': [260, '1wk'], 'MW': [380, '1wk']
            }
            days, interval = modes[mode]
            t_list = db.get_everything('stocks_'+s_m)
            t_list = [x[0] for x in t_list]
            #t_list = t_list[1:]
        elif choice == 1:
            print('EOD: close')
            days = 4
            interval = '1d' if d_w == 'D' else '1wk'
            t_list = db.get_everything('stocks_'+s_m)
            t_list = [x[0] for x in t_list]
            #t_list = t_list[1:]
        elif choice == 2:
            print('EOD: down, close')
            modes = {
                'SD': [90, '1d'], 'MD': [130, '1d'],
                'SW': [260, '1wk'], 'MW': [380, '1wk']
            }
            days, interval = modes[mode]
        now = str(dtt.now().date()+timedelta(days=2))
        before = str(dtt.now().date()-timedelta(days=days))
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
                dataY = yf.download(temp_sa_y, interval=interval, 
                                    auto_adjust=True, start=before, end=now)
                data = dataY.to_dict()
                for t, t_sa in zip(temp, temp_sa):
                    if len(temp) == 1:
                        d_high = data['High']
                        d_low = data['Low']
                        d_close = dataY['Close']
                    else:
                        d_high = data[('High', t_sa)]
                        d_low = data[('Low', t_sa)]
                        d_close = dataY[('Close', t_sa)]
                    if choice == 0:
                        high = [float('%.2f' % d_high[x]) for x in d_high]
                        low = [float('%.2f' % d_low[x]) for x in d_low]
                        avg = [(x+y)/2 for x, y in zip(*[high, low])]
                        history_all[t] = [high, low, avg]
                    elif choice == 2:
                        low = [float('%.2f' % d_low[x]) for x in d_low]
                        history_all[t] = low
                    closing = float('%.2f' % d_close[-1])
                    if closing == 0 or np.isnan(closing):
                        close_all[t] = float('%.2f' % d_close[-2])
                    else:
                        close_all[t] = closing
                k += 1
            except Exception as e:
                print('Error gathering EOD:')
                print(e)
                i = m
                tm.sleep(2)
        print('EOD gathered.')
        if choice == 0:
            self.save_obj(history_all, mode)
            self.save_obj(close_all, mode + '_close')
            print('EOD saved.')
        else:
            pass
        if choice == 1:
            return close_all
        else:
            return history_all, close_all

    def trigger_buy(self, mode):
        incl_last = self.incl_last()
        history_all = self.load_obj(mode)
        mkt_open = self.hour_fix('10:00')
        mkt_close = self.hour_fix('18:00')
        if dtt.now().time() < dtt.strptime(mkt_open, '%H:%M').time() \
                or dtt.now().time() > dtt.strptime(mkt_close, '%H:%M').time():
            close_all = self.load_obj(mode + '_close')
        else:
            close_all = self.gather_eod(mode[0], mode[1], 1)
        t_list = db.get_everything('stocks_'+mode[0])
        t_list = [x[0] for x in t_list]
        # pegar portf do user_id
        # pegar gerenciamento de risco do user_id
        portf = '0'
        result = dc.donchian_buy(
            mode, t_list, history_all, close_all, portf, incl_last
        )
        return result

    def trigger_track(self, t_list):
        incl_last = self.incl_last()
        modes = ['SD','SW','MD','MW']
        for m in modes:
            t_temp = [x[0] for x in t_list if x[1] == m]
            if t_temp:
                history_temp, close_temp = self.gather_eod(m[0], m[1], 2, t_temp)
                result = dc.donchian_track(
                    m, t_temp, history_temp, close_temp, incl_last
                )
                yield result, m
            else:
                pass