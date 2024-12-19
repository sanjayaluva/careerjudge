from decouple import config

DJANGO_ENV = config('DJANGO_ENV', default='development')

# Import settings based on environment
if DJANGO_ENV == 'production':
    from .prod import *
elif DJANGO_ENV == 'testing':
    from .test import *
else:
    from .dev import *
