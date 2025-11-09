from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('novel_platform', '0004_user_action_logs'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='message_type',
            field=models.IntegerField(),
        ),
    ]
