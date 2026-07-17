from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='pages',
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text="Total page count. Optional — not all books have this recorded.",
            ),
        ),
    ]