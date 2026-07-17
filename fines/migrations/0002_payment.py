from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fines', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=8)),
                ('method', models.CharField(choices=[('CARD', 'Card')], default='CARD', max_length=10)),
                ('status', models.CharField(choices=[('SUCCEEDED', 'Succeeded'), ('FAILED', 'Failed')], max_length=10)),
                ('provider_reference', models.CharField(blank=True, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('fine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='fines.fine')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fine_payments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['fine', 'status'], name='fines_paym_fine_id_8f3c2a_idx'),
        ),
    ]
