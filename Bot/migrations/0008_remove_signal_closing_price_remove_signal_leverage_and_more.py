# Generated by Django 4.1.3 on 2022-11-13 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Bot', '0007_alter_signal_date_alter_signal_pnl_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='signal',
            name='closing_price',
        ),
        migrations.RemoveField(
            model_name='signal',
            name='leverage',
        ),
        migrations.RemoveField(
            model_name='signal',
            name='position',
        ),
        migrations.AddField(
            model_name='signal',
            name='mark_price',
            field=models.CharField(default=13, max_length=55, verbose_name='Mark Price'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='signal',
            name='date',
            field=models.CharField(max_length=55, verbose_name='TIME'),
        ),
        migrations.AlterField(
            model_name='signal',
            name='entry_price',
            field=models.CharField(max_length=55, verbose_name='Entry Price'),
        ),
        migrations.AlterField(
            model_name='signal',
            name='pnl',
            field=models.CharField(max_length=55, verbose_name='PNL (ROE %)'),
        ),
        migrations.AlterField(
            model_name='signal',
            name='size',
            field=models.CharField(max_length=55, verbose_name='Size'),
        ),
    ]