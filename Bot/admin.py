from django.contrib import admin

# Register your models here.

from Bot.models import Admin, Traders, Signal, Orders


@admin.register(Admin)
class AdminsAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'user_id', ]


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ['id', 'symbol', 'side']


@admin.register(Traders)
class TradersAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'link']



@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'symbol', 'status_second']


