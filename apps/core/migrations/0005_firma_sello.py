from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_logo_svg"),
    ]

    operations = [
        migrations.AddField(
            model_name="datoslaboratorio",
            name="firma_imagen",
            field=models.ImageField(blank=True, null=True, upload_to="firmas/", verbose_name="Firma del bioanalista (PNG transparente)"),
        ),
        migrations.AddField(
            model_name="datoslaboratorio",
            name="sello_imagen",
            field=models.ImageField(blank=True, null=True, upload_to="sellos/", verbose_name="Sello del laboratorio (PNG transparente)"),
        ),
    ]
