# from ..settings import *
# Import all base settings here
from .base import *

# import environ
# env = environ.Env()
# environ.Env.read_env()

SECRET_KEY = config('PROD_SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = [
    'defang.io', 
    'www.defang.io', 
    'cjapp.careerjudge.com', 
    '*.careerjudge.com', 
    '*'
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('PROD_DB_NAME'),
        'USER': config('PROD_DB_USER'),
        'PASSWORD': config('PROD_DB_PASSWORD'),
        'HOST': config('PROD_HOST'),
        'PORT': '5432',
    }
}
