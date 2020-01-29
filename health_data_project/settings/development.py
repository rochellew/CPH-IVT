from .base import *

# Provide lots of info on crashes
DEBUG = True

# WARNING do not use this key in production!
SECRET_KEY = 'e#8$=*gicerm51p_5k5u1%%dcv0y6$u#k7fsa7zhxn8ab&r^ul'

# Default value: validates against localhost, 127.0.0.1, etc. when DEBUG = True
ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(ROOT_PATH / 'db.sqlite3'),
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

# By default, django.contrib.staticfiles will look for files in
# "<project>/<app>/static"; this adds an additional directory to search,
# so we can also put files in "<project>/static/" if the file is used by
# several different apps
STATICFILES_DIRS = [
    str(ROOT_PATH / 'static')
]

# when using the django development server, files are uploaded
# to and  served from a 'media' folder in the project root
# (so add that to .gitignore!)
MEDIA_ROOT = str(ROOT_PATH / 'media')
