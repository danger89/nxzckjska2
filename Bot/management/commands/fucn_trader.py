import json
import os
import sys
from datetime import datetime
from pprint import pprint
from time import sleep

import telebot
from binance.helpers import round_step_size
from bs4 import BeautifulSoup
from ccxt import bybit
from html2text import html2text
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from Bot.models import Signal


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


def get_trader(trade, admins):
    link = trade.link
    name = trade.name
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("window-size=1920x1480")
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_experimental_option('extensionLoadTimeout', 600000)
    options.add_argument('--disable-extensions')
    options.add_argument('--single-process')
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--remote-debugging-port=9222')
    options.page_load_strategy = 'eager'
    options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

    driver = webdriver.Chrome(
        os.environ.get("CHROMEDRIVER_PATH"),
        options=options,  # service=Service(ChromeDriverManager().install()),
    )
    driver.get(link)

    driver.set_page_load_timeout(6000)
    driver.set_script_timeout(30)
    driver.implicitly_wait(5)
    try:
        driver.find_element(By.ID, 'onetrust-accept-btn-handler').click()
    except:
        sleep(1)

    main_page = driver.page_source
    soup = BeautifulSoup(main_page, 'html.parser')
    text = soup.find_all('tbody', {'class': 'bn-table-tbody'})
    driver.implicitly_wait(5)
    # driver.close()
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
                # шаг цены в торговой паре
                step_size = 1
                pprint(data)
                with open('data_file.json') as f:
                    templates = json.load(f)

                for temp in templates:
                    if temp['symbol'] == symbol:
                        step_size = float(temp['stepSize'])
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
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                print(str(e) + 'line = ' + str(exc_tb.tb_lineno))
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
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                print(str(e) + 'line = ' + str(exc_tb.tb_lineno))
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(str(e) + 'line = ' + str(exc_tb.tb_lineno))
