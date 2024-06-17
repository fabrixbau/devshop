"""
WSGI config for developershop project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'developershop.settings.prod')

application = get_wsgi_application()

# Define BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent
