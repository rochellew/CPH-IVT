from os import environ
from .development import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'pipelines',
        'USER': 'test_user',
        'PASSWORD': 'test_user_password',
        'HOST': 'localhost',
        'PORT': 5432,
    }
}
