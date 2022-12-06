import json
import os
import sys
from datetime import datetime
from pprint import pprint
from time import sleep
import telebot
import undetected_chromedriver.v2 as uc
from binance import Client
from binance.helpers import round_step_size
from bs4 import BeautifulSoup
from dateutil import parser
from django.core.management.base import BaseCommand
from html2text import html2text
from selenium import webdriver
from selenium.webdriver.common.by import By

from Bot.models import Signal, Traders, Admin, Orders

admin = Admin.objects.get(admin=True)


token = admin.bot_token  # dev bot token
my_id = admin.user_id

api_key = admin.api_key
api_secret = admin.api_secret

client = Client(api_key, api_secret)

bots = telebot.TeleBot(token)


def get_orders(name_trader, symbol, date):
    """Делает запрос в базу и проверяет есть ли пользователь в базе"""
    try:
        Signal.objects.get(
            name_trader=name_trader,
            symbol=symbol,
            date=date
        ).update(updates=datetime.now())
        return True
    except:
        return False


class Command(BaseCommand):
    help = 'бот'

    def handle(self, *args, **options):
        while True:
            try:
                traders = Traders.objects.all()

                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"

                options = uc.ChromeOptions()
                options.headless = True
                options.add_experimental_option("excludeSwitches", ["enable-logging"])
                # driver = webdriver.Chrome(path, options=options)
                from webdriver_manager.chrome import ChromeDriverManager

                # options = webdriver.ChromeOptions()
                options.add_argument("window-size=1920x1480")
                options.add_argument("disable-dev-shm-usage")
                driver = webdriver.Chrome(
                    chrome_options=options, executable_path=ChromeDriverManager().install()
                )
                for trade in traders:
                    if trade.name == 'data':
                        pass
                    else:
                        link = trade.link
                        name = trade.name

                        driver.get(link)
                        driver.implicitly_wait(3)
                        try:
                            driver.find_element(By.ID, 'onetrust-accept-btn-handler').click()
                        except:
                            sleep(1)
                        sleep(3)
                        main_page = driver.page_source

                        soup = BeautifulSoup(main_page, 'html.parser')
                        text = soup.find_all('tbody', {'class': 'bn-table-tbody'})

                        for tex in text[0].find_all_next('tr'):
                            data = html2text(str(tex)).replace('\n', '').split('|')
                            if data[0].find('USDT') >= 0 or data[0].find('BUSD') >= 0:
                                symbol = data[0].split(' ')[0]
                                size = data[1]
                                entry_price = data[2]
                                mark_price = data[3]
                                pnl = data[4]
                                date = data[5]
                                # число на сколько нужно округлить объем для ордера
                                round_size = 0
                                # шаг цены в торговой паре
                                step_size = 0
                                pprint(data)

                                if not get_orders(name, symbol, date):
                                    if str(data[0]).find('Short') >= 0:
                                        # инициализируем дату и добавляем в базу
                                        signal = Signal(
                                            name_trader=name,
                                            symbol=symbol,
                                            side='SELL',
                                            size=size,
                                            entry_price=entry_price,
                                            mark_price=mark_price,
                                            pnl=pnl,
                                            date=date,
                                            update=datetime.now()
                                        )
                                        signal.save()


                                        msg = f'New trade detected! 🚨\n' \
                                              f'Trader: {name}\n' \
                                              f'Crypto: {symbol}\n' \
                                              f'Trade: SELL (SHORT)🔻\n' \
                                              f'Price: {entry_price}\n'
                                        print(msg)
                                        bots.send_message(my_id, msg)

                                    else:
                                        signal = Signal(
                                            name_trader=name,
                                            symbol=symbol,
                                            side='BUY',
                                            size=size,
                                            entry_price=entry_price,
                                            mark_price=mark_price,
                                            pnl=pnl,
                                            date=date,
                                            update=datetime.now()
                                        )
                                        signal.save()

                                        msg = f'New trade detected! 🚨\n' \
                                              f'Trader: {name}\n' \
                                              f'Crypto: {symbol}\n' \
                                              f'Trade: Buy (LONG)🟢\n' \
                                              f'Price: {entry_price}\n'
                                        print(msg)
                                        bots.send_message(my_id, msg)
                # получаем активные ордера
                sig_ord = Signal.objects.filter(is_active=True)
                # сравниваем истекли срок годности ордера
                for order_s in sig_ord:
                    date_end = order_s.updates

                    now = datetime.now()

                    a = now - parser.parse(date_end)
                    delta = a.seconds / 60
                    # если срок годности ордера больше 15 минут то получаем информацию об открытой позиции
                    # и закрываем её
                    if delta >= 4:
                        order_new = Orders.objects.get(symbol=order_s.symbol)
                        if order_new.side == 'BUY':

                            order_s.delete()
                            order_new.delete()
                            msg = f'POSITION Closed!\n' \
                                  f'Symbol: {order_new.symbol}\n'
                            bots.send_message(my_id, msg)
                        else:

                            order_s.delete()
                            order_new.delete()
                            msg = f'POSITION Closed!\n' \
                                  f'Symbol: {order_new.symbol}\n'
                            bots.send_message(my_id, msg)

                sig_old = Signal.objects.filter(is_active=False).delete()
                order_old = Orders.objects.filter(status_second=False).delete()

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                bots.send_message(798093480, str(e))
                print(e + 'line = ' + exc_tb.tb_lineno)
                sleep(1)
