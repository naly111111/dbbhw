# Generated manually for behavior logging enhancement

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('novel_platform', '0003_admin_action_logs'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminactionlog',
            name='extra_data',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='adminactionlog',
            name='ip_address',
            field=models.CharField(blank=True, max_length=45),
        ),
        migrations.AddField(
            model_name='adminactionlog',
            name='user_agent',
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name='UserActionLog',
            fields=[
                ('log_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('user_id', models.BigIntegerField()),
                ('action', models.CharField(max_length=100)),
                ('target_type', models.SmallIntegerField(blank=True, null=True)),
                ('target_id', models.BigIntegerField(blank=True, null=True)),
                ('detail', models.TextField(blank=True)),
                ('extra_data', models.TextField(blank=True)),
                ('ip_address', models.CharField(blank=True, max_length=45)),
                ('user_agent', models.TextField(blank=True)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'user_action_logs',
            },
        ),
    ]


