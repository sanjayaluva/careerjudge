# from ..settings import *
# Import all base settings here
from .base import *
# from decouple import config

# import environ
# env = environ.Env()
# environ.Env.read_env(os.path.join(BASE_DIR, '.env')) #BASE_DIR / '.env'

SECRET_KEY = config('DEV_SECRET_KEY')
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DEV_DB_NAME'),
        'USER': config('DEV_DB_USER'),
        'PASSWORD': config('DEV_DB_PASSWORD'),
        'HOST': config('DEV_HOST'),
        'PORT': '5432',
    }
}
