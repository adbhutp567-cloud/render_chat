from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_rtchat', '0006_add_group_admins'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupmessage',
            name='delivered',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='groupmessage',
            name='read',
            field=models.BooleanField(default=False),
        ),
    ]
