from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='blocked_users',
            field=models.ManyToManyField(related_name='blocked_by', symmetrical=False, to='a_users.CustomUser', blank=True),
        ),
    ]
