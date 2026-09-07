from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exams", "0002_perfil"),
    ]

    operations = [
        migrations.AddField(
            model_name="examen",
            name="tipo_resultado",
            field=models.CharField(
                choices=[("numerico", "Numérico"), ("cualitativo", "Cualitativo"), ("texto", "Texto libre")],
                default="numerico",
                help_text="Tipo de valor que acepta este examen",
                max_length=20,
            ),
        ),
    ]
