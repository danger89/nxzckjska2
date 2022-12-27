import json
import sys
from datetime import datetime
from pprint import pprint
from time import sleep

import telebot
import undetected_chromedriver.v2 as uc
from binance.helpers import round_step_size
from bs4 import BeautifulSoup
from ccxt import bybit
from dateutil import parser
from django.core.management.base import BaseCommand
from html2text import html2text
from selenium import webdriver
from selenium.webdriver.common.by import By

from Bot.models import Signal, Traders, Admin

admins = Admin.objects.filter(admin=True)


def get_orders(name_trader, symbol, date):
    """Делает запрос в базу и проверяет есть ли пользователь в базе"""
    try:
        Signal.objects.get(
            symbol=symbol,
        )
        Signal.objects.filter(symbol=symbol).update(upd=datetime.now())
        return True
    except:
        return False


class Command(BaseCommand):
    help = 'бот'

    def handle(self, *args, **options):
        while True:
            try:
                traders = Traders.objects.all()

                options = uc.ChromeOptions()
                options.headless = True
                options.add_experimental_option("excludeSwitches", ["enable-logging"])
                from webdriver_manager.chrome import ChromeDriverManager

                options = webdriver.ChromeOptions()
                options.add_argument("window-size=1920x1480")
                options.add_argument("disable-dev-shm-usage")
                options.add_argument('--headless')

                driver = webdriver.Chrome(
                    chrome_options=options, executable_path=ChromeDriverManager(
                        version='107.0.5304.62'
                    ).install()
                )
                for trade in traders:

                    link = trade.link
                    name = trade.name

                    driver.get(link)
                    driver.implicitly_wait(3)
                    try:
                        driver.find_element(By.ID, 'onetrust-accept-btn-handler').click()
                    except:
                        sleep(1)

                    main_page = driver.page_source

                    soup = BeautifulSoup(main_page, 'html.parser')
                    text = soup.find_all('tbody', {'class': 'bn-table-tbody'})
                    try:
                        for tex in text[0].find_all_next('tr'):
                            data = html2text(str(tex)).replace('\n', '').split('|')
                            if data[0].find('USDT') >= 0:
                                symbol = data[0].split(' ')[0]
                                size = data[1]
                                entry_price = data[2].replace(',', '')
                                mark_price = data[3].replace(',', '')
                                pnl = data[4]
                                date = data[5]
                                # число на сколько нужно округлить объем для ордера
                                round_size = 0
                                # шаг цены в торговой паре
                                step_size = 1
                                pprint(data)
                                with open('data_file.json') as f:
                                    templates = json.load(f)

                                for temp in templates:
                                    if temp['symbol'] == symbol:
                                        step_size = float(temp['stepSize'])
                                        # round_size = (float(temp['min_amount']))
                                        break

                                for admin in admins:
                                    token = admin.bot_token  # dev bot token
                                    my_id = admin.user_id

                                    api_key = admin.api_key
                                    api_secret = admin.api_secret

                                    session = bybit({
                                        "apiKey": api_key,
                                        "secret": api_secret
                                    })
                                    bots = telebot.TeleBot(token)
                                    try:
                                        # session.latest_information_for_symbol(
                                        #     symbol=symbol,
                                        # )
                                        curent_price = float(entry_price)
                                        # округляем и передаем в переменную
                                        wa = (float(admin.balance) * float(admin.admin_leverage))
                                        print('wa ' + str(wa))
                                        # минимальный объем для ордера
                                        while True:
                                            min_amount_m = float(wa) / float(curent_price) // float(
                                                step_size) * float(step_size)
                                            if min_amount_m <= 0:
                                                wa += 1
                                            else:
                                                break

                                        quantity = round_step_size(min_amount_m, step_size)
                                        if not get_orders(name, symbol, date):
                                            if str(data[0]).find('Short') >= 0:
                                                # инициализируем дату и добавляем в базу
                                                signal = Signal(
                                                    name_trader=name,
                                                    symbol=symbol,
                                                    side='Sell',
                                                    size=size,
                                                    entry_price=entry_price,
                                                    mark_price=mark_price,
                                                    pnl=pnl,
                                                    date=date,
                                                    upd=datetime.now()
                                                )
                                                signal.save()
                                                session.create_market_order(
                                                    symbol=symbol,
                                                    side='Sell',
                                                    amount=quantity,
                                                    params={
                                                        'leverage': admin.admin_leverage,
                                                    }
                                                )
                                                try:
                                                    msg = f'🚨 *{name}* OPEN position\n' \
                                                          f'🪙 Coin : {symbol}\n' \
                                                          f'🚀 Trade : SELL (SHORT) 🔻\n\n' \
                                                          f'💰 ROE :  {pnl[1]}%\n' \
                                                          f'💰 PNL :  {pnl[0]}$\n\n' \
                                                          f'✅ Entry : {entry_price} $\n' \
                                                          f'✅ Exit :  $\n' \
                                                          f'📅 Time : {date}'
                                                    print(msg)
                                                    bots.send_message(my_id, msg)
                                                except Exception as e:
                                                    print(e)


                                            else:
                                                signal = Signal(
                                                    name_trader=name,
                                                    symbol=symbol,
                                                    side='Buy',
                                                    size=size,
                                                    entry_price=entry_price,
                                                    mark_price=mark_price,
                                                    pnl=pnl,
                                                    date=date,
                                                    upd=datetime.now()
                                                )
                                                signal.save()
                                                session.create_market_order(
                                                    symbol=symbol,
                                                    side='Buy',
                                                    amount=quantity,
                                                    params={
                                                        'leverage': admin.admin_leverage,
                                                    }
                                                )
                                                try:
                                                    msg = f'🚨 *{name}* OPEN position\n' \
                                                          f'🪙 Coin : {symbol}\n' \
                                                          f'🚀 Trade : Buy (LONG)🟢\n\n' \
                                                          f'💰 ROE :  {pnl[1]}%\n' \
                                                          f'💰 PNL :  {pnl[0]}$\n\n' \
                                                          f'✅ Entry : {entry_price} $\n' \
                                                          f'✅ Exit :  $\n' \
                                                          f'📅 Time : {date}'

                                                    print(msg)
                                                    bots.send_message(my_id, msg)
                                                except Exception as e:
                                                    print(e)
                                    except Exception as e:
                                        exc_type, exc_obj, exc_tb = sys.exc_info()
                                        print(str(e) + 'line = ' + str(exc_tb.tb_lineno))
                                        sleep(1)
                                        print('THIS SYMBOL dont have on exchange = ' + symbol)
                    except Exception as e:
                        print('Trader dont have position')
                        print(e)
                # получаем активные ордера
                sig_ord = Signal.objects.filter(is_active=True)
                # сравниваем истекли срок годности ордера
                for order_s in sig_ord:
                    date_end = order_s.upd

                    now = datetime.now()

                    a = now - parser.parse(date_end)
                    delta = a.seconds / 60
                    # если срок годности ордера больше 3 минут, то получаем информацию об открытой позиции
                    # и закрываем её
                    pnl = str(order_s.pnl).split(' ')
                    print('DELTA = ' + str(delta) + f' {order_s.symbol}')
                    if delta >= 4:
                        for admin in admins:
                            token = admin.bot_token  # dev bot token
                            my_id = admin.user_id

                            api_key = admin.api_key
                            api_secret = admin.api_secret

                            bots = telebot.TeleBot(token)
                            session = bybit({
                                "apiKey": api_key,
                                "secret": api_secret
                            })

                            order_s.delete()
                            if order_s.side == 'Buy':
                                contracts = float(session.fetch_positions(order_s.symbol)[-1]['contracts'])
                                session.create_market_order(
                                    symbol=order_s.symbol,
                                    side='Buy',
                                    amount=contracts,
                                    params={
                                        'Leverage': admin.admin_leverage,
                                        'reduceOnly': True,
                                    }
                                )
                                order_s.delete()
                                try:

                                    msg = f'🚨 *{order_s.name_trader}* CLOSED position\n' \
                                          f'🪙 Coin : {order_s.symbol}\n' \
                                          f'🚀 Trade : Buy (LONG)🟢\n\n' \
                                          f'💰 ROE :  {pnl[1]}%\n' \
                                          f'💰 PNL :  {pnl[0]}$\n\n' \
                                          f'✅ Entry : {order_s.entry_price} $\n' \
                                          f'✅ Exit :  {order_s.mark_price}$\n' \
                                          f'📅 Time : {order_s.date}'

                                    bots.send_message(my_id, msg)
                                except Exception as e:
                                    print(e)
                            else:
                                contracts = float(session.fetch_positions(order_s.symbol)[-1]['contracts'])
                                session.create_market_order(
                                    symbol=order_s.symbol,
                                    side='Sell',
                                    amount=contracts,
                                    params={
                                        'Leverage': admin.admin_leverage,
                                        'reduceOnly': True,
                                    }
                                )
                                order_s.delete()
                                try:
                                    msg = f'🚨 *{order_s.name_trader}* CLOSED position\n' \
                                          f'🪙 Coin : {order_s.symbol}\n' \
                                          f'🚀 Trade : SELL (SHORT) 🔻\n\n' \
                                          f'💰 ROE :  {pnl[1]}%\n' \
                                          f'💰 PNL :  {pnl[0]}$\n\n' \
                                          f'✅ Entry : {order_s.entry_price} $\n' \
                                          f'✅ Exit :  {order_s.mark_price}$\n' \
                                          f'📅 Time : {order_s.date}'
                                    bots.send_message(my_id, msg)
                                except Exception as e:
                                    print(e)
                            Signal.objects.filter(is_active=True).update(is_active=False)

                sig_old = Signal.objects.filter(is_active=False).delete()

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print(str(e) + 'line = ' + str(exc_tb.tb_lineno))
                sleep(1)
            sleep(5)
