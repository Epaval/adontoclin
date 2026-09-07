from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exams", "0004_tipos_orina"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="examen",
            index=models.Index(fields=["tipo_resultado"], name="examen_tipo_re_8f5002_idx"),
        ),
    ]
