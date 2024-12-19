# from ..settings import *
# Import all base settings here
from .base import *

# import environ
# env = environ.Env()
# environ.Env.read_env()

SECRET_KEY = config('TEST_SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = ['defang.io', 'www.defang.io', 'cjapp.careerjudge.com', 'careerjudge.com', '*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('TEST_DB_NAME'),
        'USER': config('TEST_DB_USER'),
        'PASSWORD': config('TEST_DB_PASSWORD'),
        'HOST': config('TEST_HOST'),
        'PORT': '5432',
    }
}


# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True