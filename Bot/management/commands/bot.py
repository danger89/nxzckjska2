import os
import sys
from datetime import datetime
from time import sleep

import heroku3
import telebot
from ccxt import bybit
# import undetected_chromedriver.v2 as uc
from dateutil import parser
from django.core.management.base import BaseCommand

from Bot.management.commands.fucn_trader import get_trader
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
            sleep(5)
            try:
                traders = Traders.objects.all()

                for trade in traders:
                    try:
                        get_trader(trade, admins)
                    except Exception as e:
                        get_trader(trade, admins)
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        print(str(e) + 'line = ' + str(exc_tb.tb_lineno))

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
                                try:
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
                                except Exception as e:
                                    print(e)
                                    print('Not have position')
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
                                try:
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
                                except Exception as e:
                                    print(e)
                                    print('Not have position')
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

                Signal.objects.filter(is_active=False).delete()
            except IndexError as e:
                # Your Heroku API key
                api_key_heroku = os.environ.get("api_key_heroku")

                # The name of your app and dyno
                app_name = os.environ.get("app_name")
                heroku_conn = heroku3.from_key(api_key_heroku)
                app = heroku_conn.app(app_name)
                app.restart()

                exc_type, exc_obj, exc_tb = sys.exc_info()
                print(f'{e} line = {str(exc_tb.tb_lineno)}')
            except Exception as e:
                # Your Heroku API key
                api_key_heroku = os.environ.get("api_key_heroku")

                # The name of your app and dyno
                app_name = os.environ.get("app_name")
                heroku_conn = heroku3.from_key(api_key_heroku)
                app = heroku_conn.app(app_name)
                app.restart()

                exc_type, exc_obj, exc_tb = sys.exc_info()
                print(f'{e} line = {str(exc_tb.tb_lineno)}')
                sleep(15)
