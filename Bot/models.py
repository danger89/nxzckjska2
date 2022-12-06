from django.db import models


class Admin(models.Model):
    user_name = models.CharField(max_length=30, verbose_name='Name', blank=True, default='Admin')
    user_id = models.CharField(max_length=30, verbose_name='User ID in Telegram', unique=True)
    admin = models.BooleanField(default=False, verbose_name='If user admin true/else false')
    admin_leverage = models.PositiveIntegerField(verbose_name='Admin default leverage', default=10)

    balance = models.CharField(max_length=5,
                               verbose_name='Balance allocated for order',
                               default=10)
    api_key = models.CharField(max_length=265, verbose_name='api_key', blank=True)
    api_secret = models.CharField(max_length=265, verbose_name='api_secret', blank=True)
    bot_token = models.CharField(max_length=255, verbose_name='Token bot telegram')

    def __str__(self):
        return self.user_name

    class Meta:
        verbose_name = 'Admin'
        verbose_name_plural = 'Admins'


class Signal(models.Model):
    name_trader = models.CharField(max_length=25, verbose_name='NAME Trader')
    symbol = models.CharField(max_length=15, verbose_name='Symbol')
    side = models.CharField(max_length=55, verbose_name='SIDE', default='none')
    size = models.CharField(max_length=55, verbose_name='Size')
    entry_price = models.CharField(max_length=55, verbose_name='Entry Price')
    mark_price = models.CharField(max_length=55, verbose_name='Mark Price')
    pnl = models.CharField(max_length=55, verbose_name='PNL (ROE %)')
    date = models.CharField(max_length=55, verbose_name='TIME')
    is_active = models.BooleanField(default=True)
    upd = models.CharField(max_length=86, verbose_name='Update time order')

    def __str__(self):
        return self.name_trader + '/' + self.symbol


class Traders(models.Model):
    name = models.CharField(max_length=15, verbose_name='Name')
    link = models.CharField(max_length=255, verbose_name='LINK TO PROFILE')

    def __str__(self):
        return self.name


class Orders(models.Model):
    symbol = models.CharField(max_length=25, verbose_name='Symbol')
    price = models.FloatField(verbose_name='Price order')
    status_second = models.BooleanField(verbose_name='Status Order', default=True)
    order_id = models.CharField(max_length=35, verbose_name='Order ID')
    side = models.CharField(max_length=35, verbose_name='Order side (long/short)')
    size = models.FloatField(verbose_name='Size order', default=0)

    def __str__(self):
        return f'{self.order_id}/{self.symbol}'

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
