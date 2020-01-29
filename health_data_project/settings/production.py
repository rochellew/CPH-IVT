from os import environ
from .base import *

DEBUG = False

# read the secret from an environment variable
SECRET_KEY = environ["SECRET_KEY"]

ALLOWED_HOSTS = [
    '.elasticbeanstalk.com',
    # '.ushealthmetrics.com'
]

# Use a postgres-compatible RDS instance
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': environ['RDS_DB_NAME'],
        'USER': environ['RDS_USERNAME'],
        'PASSWORD': environ['RDS_PASSWORD'],
        'HOST': environ['RDS_HOSTNAME'],
        'PORT': environ['RDS_PORT'],
    }
}

# Had trouble getting the Elastic Beanstalk proxy to work.
# originally used multi-part paths (app/www/static/), but
# left it here once I got something working
STATIC_ROOT = str(ROOT_PATH / 'wwwstatic')
MEDIA_ROOT = str(ROOT_PATH / 'wwwmedia')
