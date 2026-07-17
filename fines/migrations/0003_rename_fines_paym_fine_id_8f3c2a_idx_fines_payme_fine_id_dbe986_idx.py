from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fines', '0002_payment'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='payment',
            new_name='fines_payme_fine_id_dbe986_idx',
            old_name='fines_paym_fine_id_8f3c2a_idx',
        ),
    ]
