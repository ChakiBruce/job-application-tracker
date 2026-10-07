from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Application",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("company", models.CharField(max_length=255)),
                ("role", models.CharField(max_length=255)),
                ("application_date", models.DateField()),
                ("status", models.CharField(default="Applied", max_length=100)),
            ],
            options={"db_table": "applications", "ordering": ["id"]},
        ),
    ]
