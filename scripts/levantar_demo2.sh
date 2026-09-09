#!/bin/bash
# Levanta el tunel de demo2 usando su token guardado en la BD
cd ~/odontoclin
export LABCLIN_MODO=escritorio
TOKEN=$(DJANGO_SETTINGS_MODULE=config.settings .venv/bin/python -c "
import django; django.setup()
from saas.models import Clinica
c = Clinica.objects.filter(slug='demo2').first()
print(c.token if c else '')
" 2>/dev/null)
if [ -n "$TOKEN" ]; then
  exec cloudflared tunnel --no-autoupdate run --token "$TOKEN"
else
  echo "No hay token para demo2"
  exit 1
fi
