# Generated by Django 5.2.3 on 2025-06-22 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0003_alter_meal_portion_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='image',
            field=models.TextField(blank=True, help_text="User's profile image.", null=True),
        ),
    ]
