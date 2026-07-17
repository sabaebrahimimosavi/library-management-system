from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('loans', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Fine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('overdue_days', models.PositiveIntegerField(default=0)),
                ('daily_rate', models.DecimalField(decimal_places=2, max_digits=6)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=8)),
                ('status', models.CharField(choices=[('UNPAID', 'Unpaid'), ('PAID', 'Paid'), ('WAIVED', 'Waived')], default='UNPAID', max_length=10)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('waived_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('loan', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='fine', to='loans.loan')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fines', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['user', 'status'], name='fines_fine_user_id_b7b3f8_idx')],
            },
        ),
    ]
